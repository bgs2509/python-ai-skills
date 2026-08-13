#!/usr/bin/env python3
"""Daily cleanup of Claude Code artifacts and stale docker data.

Specification: claude-home/housekeeping/claude-housekeeping-task.md

Cleans four things, all by age:
  1. ~/.claude/jobs/<id>/   background job directories
  2. git worktrees          orphaned working copies, via git itself
  3. docker build cache     records older than 30 days
  4. docker images          unused images older than 100 days

Deletion is OFF by default: without --apply the script only reports what it
would do. Volumes, networks and containers are never touched.

Usage:
    housekeeping.py                 # dry run, changes nothing
    housekeeping.py --apply         # actually delete
    housekeeping.py --skip-docker   # claude artifacts only
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Iterator, Sequence

# --- thresholds, all from the specification ---------------------------------

JOB_MAX_AGE_DAYS = 14  # rule 1: plain age
JOB_BIG_SIZE_BYTES = 1024**3  # rule 2: "larger than 1 GiB"
JOB_BIG_AGE_DAYS = 2  # rule 2: and older than this
JOB_FRESH_AGE_DAYS = 2  # protection: recently modified means possibly alive
JOB_STATE_CEILING_DAYS = 100  # protection by state stops applying past this

DOCKER_CACHE_AGE_DAYS = 30
DOCKER_IMAGE_AGE_DAYS = 100

LOG_MAX_LINES = 500
LOG_PATH = Path.home() / ".claude" / "housekeeping.log"
JOBS_DIR = Path.home() / ".claude" / "jobs"
DEFAULT_WORKTREE_ROOTS = (Path.home() / "ai-steward", Path.home() / "works")
SKIP_DIR_NAMES = frozenset(
    {".cache", ".nvm", ".venv", "node_modules", ".local", ".cargo", ".rustup"}
)


# --- decision types ---------------------------------------------------------


@dataclass(frozen=True)
class Verdict:
    """What to do with one item, and why. `reason` goes verbatim into the log."""

    action: str  # "delete" | "keep"
    reason: str
    unlock: bool = False  # release a stale worktree lock, independent of action

    @property
    def deletes(self) -> bool:
        return self.action == "delete"


# --- pure decision logic ----------------------------------------------------
# These functions take plain values and return a Verdict. They touch nothing,
# which is what makes the rules testable without a real home directory.


def decide_job(
    *,
    age_days: float,
    state: str | None,
    has_state_file: bool,
    live_process: bool,
    is_current: bool,
    size_getter: Callable[[], int],
) -> Verdict:
    """Decide the fate of one ~/.claude/jobs/<id> directory (spec 5.1 + 5.3).

    `size_getter` is called only on the branch that needs a size, so the
    expensive directory walk is skipped for everything already protected.
    """
    # Protections that no age ever overrides.
    if is_current:
        return Verdict("keep", "current job directory (CLAUDE_JOB_DIR)")
    if live_process:
        return Verdict("keep", "a live process references this job id")
    if age_days < JOB_FRESH_AGE_DAYS:
        return Verdict("keep", f"modified less than {JOB_FRESH_AGE_DAYS} days ago")

    # Protection by recorded state, lifted once the ceiling is passed. Without
    # the ceiling a job left in state "blocked" or "working" would survive
    # forever, because the state never changes again once nobody is watching.
    past_ceiling = age_days > JOB_STATE_CEILING_DAYS
    if not past_ceiling:
        if has_state_file and state != "done":
            return Verdict(
                "keep",
                f"state={state!r}, protection lifts after {JOB_STATE_CEILING_DAYS} days",
            )
        if not has_state_file and age_days <= JOB_MAX_AGE_DAYS:
            return Verdict("keep", "no state.json and younger than the age rule")

    if age_days > JOB_MAX_AGE_DAYS:
        suffix = " (state protection lifted by the age ceiling)" if past_ceiling else ""
        return Verdict("delete", f"older than {JOB_MAX_AGE_DAYS} days{suffix}")
    if size_getter() > JOB_BIG_SIZE_BYTES and age_days > JOB_BIG_AGE_DAYS:
        return Verdict(
            "delete", f"larger than 1 GiB and older than {JOB_BIG_AGE_DAYS} days"
        )
    return Verdict("keep", "no deletion rule matched")


def decide_worktree(
    *,
    locked: bool,
    lock_pid: int | None,
    lock_pid_alive: bool,
    branch: str | None,
    dirty: bool,
    ahead: int,
    merged: bool,
) -> Verdict:
    """Decide the fate of one git worktree (spec 5.2 + 5.3).

    A stale lock (pid recorded but dead) is released either way; releasing it
    is not the same as removing the worktree, which still has to pass every
    check below.
    """
    unlock = False
    if locked:
        if lock_pid is None:
            return Verdict("keep", "locked, no readable process id in the lock reason")
        if lock_pid_alive:
            return Verdict("keep", f"locked by live process {lock_pid}")
        unlock = True

    if branch is None:
        return Verdict("keep", "detached HEAD, merge state cannot be verified", unlock)
    if dirty:
        return Verdict("keep", "uncommitted changes inside the worktree", unlock)
    if ahead > 0:
        return Verdict("keep", f"{ahead} commit(s) missing from the main branch", unlock)
    if not merged:
        return Verdict("keep", "branch not merged into the main branch", unlock)
    return Verdict("delete", "clean, merged, no unique commits", unlock)


def decide_image(*, age_days: float, in_use: bool) -> Verdict:
    """Decide the fate of one docker image (spec 5.4)."""
    if in_use:
        return Verdict("keep", "used by a container")
    if age_days <= DOCKER_IMAGE_AGE_DAYS:
        return Verdict("keep", f"younger than {DOCKER_IMAGE_AGE_DAYS} days")
    return Verdict("delete", f"unused and older than {DOCKER_IMAGE_AGE_DAYS} days")


# --- helpers ----------------------------------------------------------------


def run(cmd: Sequence[str], cwd: Path | None = None, timeout: int = 120) -> tuple[int, str]:
    """Run a command, returning (exit code, stdout). Never raises on failure."""
    try:
        done = subprocess.run(
            list(cmd),
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 127, f"{exc}"
    return done.returncode, done.stdout


def age_in_days(path: Path, now: float) -> float:
    return (now - path.stat().st_mtime) / 86400.0


def directory_size(path: Path) -> int:
    total = 0
    for root, dirnames, filenames in os.walk(path, onerror=lambda _: None):
        dirnames[:] = [d for d in dirnames if not os.path.islink(os.path.join(root, d))]
        for name in filenames:
            try:
                stat = os.lstat(os.path.join(root, name))
            except OSError:
                continue
            total += stat.st_size
    return total


def pid_alive(pid: int) -> bool:
    return Path(f"/proc/{pid}").exists()


def processes_mentioning(token: str, own_pids: frozenset[int]) -> bool:
    """True if any live process has `token` in its command line.

    Reads /proc directly rather than shelling out to pgrep: pgrep would also
    match this script's own invocation, and /proc lets us exclude it exactly.
    """
    proc = Path("/proc")
    if not proc.is_dir():
        return False
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid in own_pids:
            continue
        try:
            cmdline = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode(
                "utf-8", "replace"
            )
        except OSError:
            continue
        if token in cmdline:
            return True
    return False


def own_process_chain() -> frozenset[int]:
    """This process and its ancestors, so we never mistake ourselves for a job."""
    pids: set[int] = set()
    pid = os.getpid()
    while pid > 1 and pid not in pids:
        pids.add(pid)
        try:
            fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
            pid = int(fields[1])
        except (OSError, IndexError, ValueError):
            break
    return frozenset(pids)


HUMAN_SIZE = re.compile(r"^([\d.]+)\s*([kKMGTP]?i?B)\*?$")
SIZE_UNITS = {
    "B": 1,
    "kB": 1000,
    "KB": 1000,
    "MB": 1000**2,
    "GB": 1000**3,
    "TB": 1000**4,
    "PB": 1000**5,
    "KiB": 1024,
    "MiB": 1024**2,
    "GiB": 1024**3,
    "TiB": 1024**4,
}


def parse_human_size(text: str) -> int:
    """Parse docker's size strings ("1.958GB", "32B", "3.139GB*") into bytes."""
    match = HUMAN_SIZE.match(text.strip())
    if not match:
        return 0
    number, unit = match.groups()
    try:
        return int(float(number) * SIZE_UNITS.get(unit, 1))
    except ValueError:
        return 0


def human(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f}{unit}" if unit != "B" else f"{int(value)}B"
        value /= 1024
    return f"{value:.1f}TB"


# --- journal ----------------------------------------------------------------


class Journal:
    """The only record of what happened; see spec 5.5.

    Records the run itself, not just deletions — otherwise "the scheduler never
    fired" and "there was nothing to delete" look identical in the log, and the
    first of those is exactly the failure nobody would notice.
    """

    def __init__(self, path: Path, host: str, echo: bool = True) -> None:
        self.path = path
        self.host = host
        self.echo = echo
        self.lines: list[str] = []
        self.errors = 0

    def write(self, **fields: object) -> None:
        stamp = datetime.now().astimezone().isoformat(timespec="seconds")
        parts = " ".join(f"{k}={_fmt(v)}" for k, v in fields.items())
        line = f"{stamp} host={self.host} {parts}"
        self.lines.append(line)
        if self.echo:
            print(line)

    def error(self, message: str, **fields: object) -> None:
        self.errors += 1
        self.write(level="ERROR", message=message, **fields)

    def flush(self) -> None:
        """Trim first, then append this run, so the newest run is never cut."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            previous: list[str] = []
            if self.path.exists():
                previous = self.path.read_text(encoding="utf-8").splitlines()
            keep = previous[-LOG_MAX_LINES:] if len(previous) > LOG_MAX_LINES else previous
            self.path.write_text("\n".join(keep + self.lines) + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"cannot write journal {self.path}: {exc}", file=sys.stderr)


def _fmt(value: object) -> str:
    text = str(value)
    return f'"{text}"' if (" " in text or "=" in text) else text


# --- job directories --------------------------------------------------------


def clean_jobs(journal: Journal, apply: bool, now: float) -> int:
    """Returns bytes freed (or that would be freed in dry-run mode)."""
    if not JOBS_DIR.is_dir():
        journal.write(part=
            "jobs", action="skip", reason="job directory does not exist")
        return 0

    current = os.environ.get("CLAUDE_JOB_DIR", "")
    own = own_process_chain()
    freed = 0

    for entry in sorted(JOBS_DIR.iterdir()):
        if not entry.is_dir() or entry.is_symlink():
            continue
        try:
            age = age_in_days(entry, now)
        except OSError as exc:
            journal.error(f"cannot stat job directory: {exc}", job=entry.name)
            continue

        state, has_state = read_job_state(entry, journal)
        verdict = decide_job(
            age_days=age,
            state=state,
            has_state_file=has_state,
            live_process=processes_mentioning(entry.name, own),
            is_current=bool(current) and Path(current).resolve() == entry.resolve(),
            size_getter=lambda e=entry: directory_size(e),
        )

        if not verdict.deletes:
            journal.write(
                part="jobs", job=entry.name, action="keep",
                age_days=round(age, 1), reason=verdict.reason,
            )
            continue

        size = directory_size(entry)
        journal.write(
            part="jobs", job=entry.name, action="delete" if apply else "would-delete",
            age_days=round(age, 1), size=human(size), reason=verdict.reason,
        )
        if apply:
            try:
                shutil.rmtree(entry)
            except OSError as exc:
                journal.error(f"cannot remove job directory: {exc}", job=entry.name)
                continue
        freed += size
    return freed


def read_job_state(entry: Path, journal: Journal) -> tuple[str | None, bool]:
    """Read state.json. A missing file is normal; a broken one is worth a line."""
    state_file = entry / "state.json"
    if not state_file.is_file():
        return None, False
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        journal.error(f"unreadable state.json, treating as unknown: {exc}", job=entry.name)
        return None, False
    state = data.get("state") if isinstance(data, dict) else None
    return (state if isinstance(state, str) else None), True


# --- git worktrees ----------------------------------------------------------


@dataclass
class Worktree:
    repo: Path
    path: Path
    branch: str | None = None
    locked: bool = False
    lock_reason: str = ""
    lock_pid: int | None = None


LOCK_PID = re.compile(r"\(pid\s+(\d+)")


def parse_worktree_list(repo: Path, porcelain: str) -> list[Worktree]:
    """Parse `git worktree list --porcelain`, skipping the main worktree."""
    records: list[Worktree] = []
    current: Worktree | None = None
    for line in porcelain.splitlines():
        if line.startswith("worktree "):
            if current is not None:
                records.append(current)
            current = Worktree(repo=repo, path=Path(line[len("worktree "):]))
        elif current is None:
            continue
        elif line.startswith("branch "):
            current.branch = line[len("branch "):].removeprefix("refs/heads/")
        elif line == "locked" or line.startswith("locked "):
            current.locked = True
            current.lock_reason = line[len("locked "):] if " " in line else ""
            found = LOCK_PID.search(current.lock_reason)
            current.lock_pid = int(found.group(1)) if found else None
    if current is not None:
        records.append(current)
    return records[1:]  # the first record is the repository itself


def find_repositories(roots: Iterable[Path]) -> Iterator[Path]:
    for root in roots:
        if not root.is_dir():
            continue
        for dirpath, dirnames, _ in os.walk(root, onerror=lambda _: None):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
            if ".git" in dirnames or (Path(dirpath) / ".git").exists():
                dirnames[:] = [d for d in dirnames if d != ".git"]
                yield Path(dirpath)
                dirnames.clear()  # do not descend into a repository


def main_branch_of(repo: Path) -> str | None:
    code, out = run(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], cwd=repo)
    if code == 0 and out.strip():
        return out.strip().split("/", 1)[-1]
    for candidate in ("master", "main"):
        code, _ = run(["git", "rev-parse", "--verify", "--quiet", candidate], cwd=repo)
        if code == 0:
            return candidate
    return None


def clean_worktrees(journal: Journal, apply: bool, roots: Sequence[Path]) -> int:
    removed = 0
    for repo in find_repositories(roots):
        code, porcelain = run(["git", "worktree", "list", "--porcelain"], cwd=repo)
        if code != 0:
            continue
        worktrees = parse_worktree_list(repo, porcelain)
        if not worktrees:
            continue
        main = main_branch_of(repo)
        if main is None:
            journal.error("cannot determine the main branch", repo=str(repo))
            continue

        touched = False
        for wt in worktrees:
            verdict = evaluate_worktree(repo, wt, main)

            if verdict.unlock:
                journal.write(
                    part="worktrees", worktree=str(wt.path),
                    action="unlock" if apply else "would-unlock",
                    reason=f"stale lock, process {wt.lock_pid} is gone",
                )
                if apply:
                    code, out = run(["git", "worktree", "unlock", str(wt.path)], cwd=repo)
                    if code != 0:
                        journal.error(f"cannot unlock: {out.strip()}", worktree=str(wt.path))
                        continue
                    touched = True

            if not verdict.deletes:
                journal.write(
                    part="worktrees", worktree=str(wt.path), action="keep",
                    branch=wt.branch or "-", reason=verdict.reason,
                )
                continue

            journal.write(
                part="worktrees", worktree=str(wt.path),
                action="delete" if apply else "would-delete",
                branch=wt.branch or "-", reason=verdict.reason,
            )
            if apply:
                code, out = run(["git", "worktree", "remove", str(wt.path)], cwd=repo)
                if code != 0:
                    journal.error(f"cannot remove worktree: {out.strip()}", worktree=str(wt.path))
                    continue
                touched = True
            removed += 1

        if apply and touched:
            run(["git", "worktree", "prune"], cwd=repo)
    return removed


def answers_for_itself(wt: Worktree) -> bool:
    """True when git commands run inside `wt.path` are answered by that
    worktree and not by the repository above it.

    A worktree is scoped by the `.git` link file at its root. Lose that link
    and git walks up to the PARENT repository instead, cheerfully reporting
    the parent's state with `../../../` paths — the `?? ../../../.beads/`
    seen on 2026-08-12. The danger is not the noise: it is that the answer
    then says nothing at all about the copy's own uncommitted work, so a
    worktree full of unsaved changes can read as clean.
    """
    code, toplevel = run(["git", "rev-parse", "--show-toplevel"], cwd=wt.path)
    if code != 0 or not toplevel.strip():
        return False
    try:
        return Path(toplevel.strip()).resolve() == wt.path.resolve()
    except OSError:
        return False


def evaluate_worktree(repo: Path, wt: Worktree, main: str) -> Verdict:
    """Collect the facts about one worktree and hand them to the pure rule."""
    dirty = False
    ahead = 0
    merged = False
    if wt.branch is not None and wt.path.is_dir():
        if not answers_for_itself(wt):
            return Verdict(
                "keep",
                "git here does not answer for this worktree; its own state "
                "cannot be read",
            )
        # Scoping is kept as defence in depth: with the check above in place
        # it can no longer change a verdict, but it costs nothing and keeps
        # the command honest about what it is asking for.
        _, status = run(["git", "status", "--short", "--", "."], cwd=wt.path)
        dirty = bool(status.strip())
        code, count = run(["git", "rev-list", "--count", f"{main}..{wt.branch}"], cwd=repo)
        ahead = int(count.strip()) if code == 0 and count.strip().isdigit() else 1
        code, _ = run(["git", "merge-base", "--is-ancestor", wt.branch, main], cwd=repo)
        merged = code == 0

    return decide_worktree(
        locked=wt.locked,
        lock_pid=wt.lock_pid,
        lock_pid_alive=wt.lock_pid is not None and pid_alive(wt.lock_pid),
        branch=wt.branch,
        dirty=dirty,
        ahead=ahead,
        merged=merged,
    )


# --- docker -----------------------------------------------------------------


def docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    code, _ = run(["docker", "version", "--format", "{{.Server.Version}}"], timeout=30)
    return code == 0


def clean_docker(journal: Journal, apply: bool, now: float) -> None:
    if not docker_available():
        journal.write(part="docker", action="skip", reason="docker unavailable")
        return
    clean_build_cache(journal, apply)
    clean_images(journal, apply, now)


def clean_build_cache(journal: Journal, apply: bool) -> int:
    """Build cache not used for 30 days. Never pass --all: for the cache that
    flag means something else entirely (internal builder images).

    Nothing is predicted here, on purpose. Docker selects records by when they
    were last USED, and exposes that only as prose ("4 months ago"); the
    precise `CreatedAt` it does expose selects a different set entirely. On
    2026-08-13 counting by creation promised 262 records and the prune removed
    9 — the records were old but still in use. Reported instead is docker's
    own reclaimable figure for the whole cache, and afterwards the amount the
    prune itself says it freed.
    """
    age = f"{DOCKER_CACHE_AGE_DAYS * 24}h"
    if not apply:
        journal.write(
            part="docker", target="build-cache", action="would-prune",
            reclaimable=reclaimable_ceiling("Build Cache"),
            reason=f"records not used for {DOCKER_CACHE_AGE_DAYS} days",
        )
        return 0

    code, out = run(
        ["docker", "buildx", "prune", "--filter", f"until={age}", "--force"], timeout=900
    )
    if code != 0:
        journal.error(f"build cache prune failed: {out.strip()[:200]}", part="docker")
        return 0
    freed = parse_reclaimed(out)
    journal.write(part="docker", target="build-cache", action="prune", freed=human(freed))
    return freed


def clean_images(journal: Journal, apply: bool, now: float) -> int:
    """Unused images older than 100 days. Returns how many were removed.

    Removal is done here, image by image, rather than handed to
    `docker image prune --filter until=`. That filter does not select by build
    date: on docker 29.3.1 it reclaimed nothing from images 344 to 375 days
    old, with a duration and with an absolute date alike, while a plain
    `docker image rm` removed the same image instantly. Delegating would mean
    the daily log promised a rule the tool does not carry out.

    Docker refuses to remove an image another image is built on. That is a
    normal outcome, not a failure, so it is logged as a skip.
    """
    in_use = images_in_use(journal)
    code, out = run(["docker", "image", "ls", "--all", "--no-trunc", "--format", "json"])
    if code != 0:
        journal.error(f"cannot list images: {out.strip()[:200]}", part="docker")
        return 0

    seen: set[str] = set()
    candidates: list[tuple[str, str]] = []
    for record in iter_json_lines(out):
        image_id = str(record.get("ID", ""))
        if not image_id or image_id in seen:
            continue
        seen.add(image_id)
        created = parse_docker_time(str(record.get("CreatedAt", "")))
        if created is None:
            continue
        if decide_image(age_days=(now - created) / 86400.0, in_use=image_id in in_use).deletes:
            name = f"{record.get('Repository', '<none>')}:{record.get('Tag', '<none>')}"
            candidates.append((image_id, name))

    if not apply:
        journal.write(
            part="docker", target="images", action="would-remove",
            images=len(candidates), reclaimable=reclaimable_ceiling("Images"),
            reason=f"unused, older than {DOCKER_IMAGE_AGE_DAYS} days",
        )
        return 0

    removed = 0
    for image_id, name in candidates:
        code, out = run(["docker", "image", "rm", image_id], timeout=300)
        if code == 0:
            removed += 1
            continue
        journal.write(
            part="docker", target="images", action="skip", image=name,
            reason=out.strip().splitlines()[-1][:120] if out.strip() else "removal refused",
        )
    journal.write(
        part="docker", target="images", action="remove",
        removed=removed, of=len(candidates),
    )
    return removed


def iter_json_lines(text: str) -> Iterator[dict]:
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict):
            yield record


# Two wordings for the same thing: `docker image prune` says "Total reclaimed
# space: 1.5GB", `docker buildx prune` just says "Total: 1.5GB". Matching only
# the first made every cache prune report 0B freed.
RECLAIMED = re.compile(r"(?:Total reclaimed space|Total):\s*(\S+)\s*$", re.MULTILINE)


def parse_reclaimed(output: str) -> int:
    """Read the freed-space line docker prints after a prune, either wording."""
    match = RECLAIMED.search(output)
    return parse_human_size(match.group(1)) if match else 0


def reclaimable_ceiling(kind: str) -> str:
    """Docker's own reclaimable figure for one resource type, as it reports it."""
    code, out = run(["docker", "system", "df", "--format", "json"])
    if code != 0:
        return "unknown"
    for record in iter_json_lines(out):
        if record.get("Type") == kind:
            return str(record.get("Reclaimable", "unknown")).split(" ")[0]
    return "unknown"


def images_in_use(journal: Journal) -> frozenset[str]:
    code, out = run(["docker", "ps", "--all", "--quiet", "--no-trunc"])
    if code != 0 or not out.strip():
        return frozenset()
    containers = out.split()
    code, out = run(["docker", "inspect", "--format", "{{.Image}}", *containers])
    if code != 0:
        journal.error("cannot resolve image ids of containers", part="docker")
        return frozenset()
    return frozenset(line.strip() for line in out.splitlines() if line.strip())


# Two shapes in the wild: images give "2026-08-09 11:03:22 +0300 +03", build
# cache records add fractional seconds — "2026-02-10 15:47:56.578713681 +0000 UTC".
DOCKER_TIME = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?:\.\d+)? ([+-]\d{4})")


def parse_docker_time(text: str) -> float | None:
    """Parse docker's "2026-08-09 11:03:22 +0300 +03" into a unix timestamp."""
    match = DOCKER_TIME.match(text.strip())
    if not match:
        return None
    try:
        stamp = datetime.strptime(
            f"{match.group(1)} {match.group(2)}", "%Y-%m-%d %H:%M:%S %z"
        )
    except ValueError:
        return None
    return stamp.timestamp()


# --- entry point ------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--apply", action="store_true",
        help="actually delete; without this nothing is removed",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="report only (the default; accepted for explicitness)",
    )
    parser.add_argument("--skip-docker", action="store_true", help="clean claude artifacts only")
    parser.add_argument(
        "--worktree-root", action="append", type=Path, default=None,
        help="directory to search for git repositories (repeatable)",
    )
    parser.add_argument("--quiet", action="store_true", help="write to the journal only")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    apply = args.apply and not args.dry_run
    roots = args.worktree_root or list(DEFAULT_WORKTREE_ROOTS)
    now = datetime.now(timezone.utc).timestamp()

    journal = Journal(LOG_PATH, host=os.uname().nodename, echo=not args.quiet)
    journal.write(run="start", mode="apply" if apply else "dry-run")

    # Measured across the whole run: the per-part figures cannot be added up
    # honestly, because docker's are sums over shared layers. This one is what
    # the filesystem actually gained.
    free_before = shutil.disk_usage(Path.home()).free

    freed_claude = clean_jobs(journal, apply, now)
    removed = clean_worktrees(journal, apply, roots)
    if not args.skip_docker:
        clean_docker(journal, apply, now)

    gained = shutil.disk_usage(Path.home()).free - free_before
    journal.write(
        run="finish", exit=1 if journal.errors else 0, errors=journal.errors,
        jobs_freed=human(freed_claude), worktrees_removed=removed,
        disk_gained=human(gained) if gained > 0 else "0B",
    )
    journal.flush()
    return 1 if journal.errors else 0


if __name__ == "__main__":
    sys.exit(main())
