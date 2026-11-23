"""Shared repo-sync core for the project-sync / projects-sync skills.

Design: pure parsing + classification functions (fully unit-tested), plus thin
subprocess wrappers for side-effecting git/gh/rsync/ssh actions. The decision
of *what* to do with an anomalous repo (dirty, diverged) is NOT made here — the
skill surfaces it to the user via the best-explain contract. This module only:

1. diagnoses a repo into a :class:`RepoStatus`,
2. classifies that status into a single state string,
3. exposes safe mechanical actions (ff-pull, push, create-remote, rsync),
4. discovers git repos on a remote host (for projects-sync).

All side-effecting helpers take an injectable ``run`` callable so they can be
unit-tested without touching a real shell.
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass, field


# --- data ------------------------------------------------------------------

@dataclass
class RepoStatus:
    path: str
    branch: str
    has_remote: bool
    dirty_files: list[str] = field(default_factory=list)
    ahead: int = 0
    behind: int = 0
    state: str = "up_to_date"

    @property
    def dirty(self) -> bool:
        return bool(self.dirty_files)


# --- subprocess runner -----------------------------------------------------

def _run(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    """Run a command, capturing text output. Never raises on non-zero exit."""
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, check=False,
    )


# --- pure parsing ----------------------------------------------------------

def parse_status_porcelain(text: str) -> list[str]:
    """Return the list of changed file paths from ``git status --porcelain``."""
    files: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        # Porcelain v1: first 2 chars are status code, then a space, then path.
        files.append(line[3:].strip())
    return files


def parse_ahead_behind(text: str) -> tuple[int, int]:
    """Parse ``git rev-list --left-right --count @{u}...HEAD`` => (behind, ahead)."""
    parts = text.split()
    if len(parts) < 2:
        return (0, 0)
    return (int(parts[0]), int(parts[1]))


def classify(*, has_remote: bool, dirty: bool, ahead: int, behind: int) -> str:
    """Collapse repo facts into one state. Order encodes priority."""
    if not has_remote:
        return "no_remote"
    if dirty:
        return "dirty"
    if ahead > 0 and behind > 0:
        return "diverged"
    if ahead > 0:
        return "ahead"
    if behind > 0:
        return "behind"
    return "up_to_date"


def parse_find_output(text: str) -> list[str]:
    """Turn ``find ... -name .git`` output into a sorted, de-duplicated repo list."""
    repos: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line.endswith("/.git") and line != ".git":
            continue
        repos.add(line[: -len("/.git")] if line.endswith("/.git") else ".")
    return sorted(repos)


# --- diagnosis -------------------------------------------------------------

def diagnose_repo(path: str, run=_run) -> RepoStatus:
    """Read-only inspection of a local git repo at ``path``."""
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], path).stdout.strip()
    has_remote = "origin" in run(["git", "remote"], path).stdout.split()
    dirty_files = parse_status_porcelain(
        run(["git", "status", "--porcelain"], path).stdout
    )
    ahead = behind = 0
    if has_remote:
        ab = run(
            ["git", "rev-list", "--left-right", "--count", "@{u}...HEAD"], path
        )
        if ab.returncode == 0:
            behind, ahead = parse_ahead_behind(ab.stdout)
    state = classify(
        has_remote=has_remote, dirty=bool(dirty_files), ahead=ahead, behind=behind
    )
    return RepoStatus(
        path=path, branch=branch, has_remote=has_remote,
        dirty_files=dirty_files, ahead=ahead, behind=behind, state=state,
    )


# --- safe mechanical actions ----------------------------------------------

def fetch(path: str, run=_run) -> subprocess.CompletedProcess:
    return run(["git", "fetch", "--all", "--prune"], path)


def fast_forward_pull(path: str, run=_run) -> subprocess.CompletedProcess:
    return run(["git", "pull", "--ff-only"], path)


def push(path: str, run=_run) -> subprocess.CompletedProcess:
    return run(["git", "push"], path)


def create_github_remote_and_push(
    path: str, *, visibility: str = "private", run=_run
) -> subprocess.CompletedProcess:
    """Create a GitHub repo for a remote-less local repo and push it.

    Uses ``gh repo create <dir> --<visibility> --source . --remote origin --push``.
    """
    return run(
        ["gh", "repo", "create", "--source", ".",
         f"--{visibility}", "--remote", "origin", "--push"],
        path,
    )


def rsync_artifacts(
    src: str, dest_host: str, dest_path: str, *, dry_run: bool = False, run=_run
) -> subprocess.CompletedProcess:
    """rsync a (gitignored) artifact path to a remote host over ssh."""
    flags = ["-az", "--delete"]
    if dry_run:
        flags.append("--dry-run")
    return run(["rsync", *flags, src, f"{dest_host}:{dest_path}"], None)


# --- remote discovery (projects-sync) --------------------------------------

def discover_remote_repos(host: str, root: str, run=_run) -> list[str]:
    """List git repos under ``root`` on ``host`` via ssh + find."""
    remote_cmd = f"find {shlex.quote(root)} -type d -name .git 2>/dev/null"
    res = run(["ssh", host, remote_cmd], None)
    return parse_find_output(res.stdout)


# --- CLI (deterministic, low-token entry point for the skills) -------------

def status_to_dict(st: RepoStatus) -> dict:
    """Serialize a RepoStatus to a plain dict (adds the derived ``dirty`` flag)."""
    d = asdict(st)
    d["dirty"] = st.dirty
    return d


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sync", description="repo-sync core")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_diag = sub.add_parser("diagnose", help="diagnose one local repo -> JSON")
    p_diag.add_argument("path")

    p_disc = sub.add_parser("discover", help="list git repos on a remote host -> JSON")
    p_disc.add_argument("host")
    p_disc.add_argument("root")

    ns = parser.parse_args(argv)
    if ns.cmd == "diagnose":
        print(json.dumps(status_to_dict(diagnose_repo(ns.path)), ensure_ascii=False))
    elif ns.cmd == "discover":
        print(json.dumps(discover_remote_repos(ns.host, ns.root), ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
