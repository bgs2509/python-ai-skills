---
feature: agents-md-migration
bd_id: python-ai-skills-lvt.2
date: 2026-10-15
status: draft
risk: high
discovery: docs/superpowers/specs/20261015-agents-md-migration-discovery.md
design: docs/superpowers/specs/20261015-agents-md-migration-design.md
approach: manifest-script
tasks: 9
---

# AGENTS.md migration: implementation plan (python-ai-skills-lvt.2)

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:executing-plans` (inline; the apply steps need the user's per-command sandbox-bypass approval, so subagent dispatch gains nothing). Steps use checkbox (`- [ ]`) syntax.

**Goal:** 38 directories under `/home/bgs/ai-steward/Gena_Beeline_Local/` end with one real `AGENTS.md` and `CLAUDE.md` as a relative symlink to it, one local commit per repository, content preserved, no push.

**Bead:** `python-ai-skills-lvt.2`. **Requirements:** [discovery](20261015-agents-md-migration-discovery.md) (FR-1..FR-8, NFR-1..NFR-4, resolutions 1-6). **Design:** [manifest-script](20261015-agents-md-migration-design.md) (implemented exactly; deviations of detail are listed at the end, section "Deviations from the design").

**Architecture:** one throwaway Python 3.11+ stdlib script `$TMPDIR/agents-md-migrate/migrate.py` plus `manifest.json` (task level 5: not committed, no unit tests; its `check` output and independent `git`/`cmp` commands are the evidence). Commands: `plan [dir...]` (read-only dry run), `apply <dir>` (all writes and the commit of one repo, idempotent), `check [dir...]` (read-only post-checks). The python-ai-skills edits of Task 8 are level 4 (text edits; validator `make test` and `pre-commit run --files`).

**Tech stack:** Python 3 stdlib (`json`, `os`, `subprocess`, `pathlib`), `git`, `bd`, `pre-commit`, `codex` CLIs.

## Global constraints (copied from the design and the global rules)

1. Sandbox: Bash writes only inside python-ai-skills and `$TMPDIR`. Every `apply` writes into a sibling repository, so the orchestrator runs it as its own Bash call with `dangerouslyDisableSandbox: true`, **one repository per call**, and the user approves each call. `plan` and `check` are read-only and run inside the sandbox.
2. Commits are local only. `git push`, `gh pr create`, `--no-verify` and `SKIP=` are never used. A failing hook is fixed at its cause, then `apply` is re-run (resume).
3. Destructive rollback (`git reset --hard HEAD~1`, `rm`, `git revert`) only after the user's explicit confirmation, one repository at a time (design 2.6).
4. The commit message is `docs(agents-md): make AGENTS.md the single instruction file` with a body referencing `python-ai-skills-lvt.2`.
5. Merged file size must be below 32768 B (NFR-1) except `aidd-mvp-generator`, `ebooks`, `ML_CAREER_2026` (resolution 4, moved to `python-ai-skills-lvt.3`).
6. `Sinayara-Isuzu` and `Sinayara-Isuzu-web` (lvt.3), the global `~/.claude/CLAUDE.md`, Sensedar's hand-managed bd block, `instructionFiles` and any push are out of scope.
7. Command prefix used below (each Bash call defines it again, shell state does not persist): `B=/home/bgs/ai-steward/Gena_Beeline_Local; M="python3 -I $TMPDIR/agents-md-migrate/migrate.py"`.

## File structure

- Create (not committed): `$TMPDIR/agents-md-migrate/migrate.py`, `$TMPDIR/agents-md-migrate/manifest.json`; generated: `$TMPDIR/agents-md-migrate/out/<dir>/{AGENTS.md,bd.base,CLAUDE.md.orig,dropped.txt}`.
- Modify in the 38 repositories: `CLAUDE.md` (becomes a symlink) and `AGENTS.md` (becomes the real file). Nothing else.
- Modify in python-ai-skills (Task 8): `_init/SKILL.md`, `grace-init/SKILL.md`, `git-finish/SKILL.md`, `AGENTS.md` (the pilot's own file, one note), `CHANGELOG.md`; `claude-home/CLAUDE.md` is write-protected in this session and is edited by the user.

---

## Task 1: Write the script and the manifest

**Serves:** NFR-3 (idempotent), FR-7 (per-project checks), NFR-1/NFR-2 mechanics; carries FR-1..FR-6 for Tasks 3-7.

**Files:** create `$TMPDIR/agents-md-migrate/migrate.py`, `$TMPDIR/agents-md-migrate/manifest.json`.

- [ ] **Step 1: create the directory and write `migrate.py`** with exactly this content.

```python
#!/usr/bin/env python3
"""Throwaway tool for python-ai-skills-lvt.2: plan [dir...] | apply <dir> | check [dir...]."""
import json
import os
import subprocess
import sys
from pathlib import Path

WORK = Path(os.environ["TMPDIR"]) / "agents-md-migrate"
OUT = WORK / "out"
CODEX_HOME = Path(os.environ["TMPDIR"]) / "codex-home"
LIMIT = 32768
MSG = "docs(agents-md): make AGENTS.md the single instruction file"
BODY = (
    "CLAUDE.md becomes a symlink to AGENTS.md, the one real instruction file "
    "read by Claude Code and Codex.\n\nRefs: python-ai-skills-lvt.2"
)
BD, BD_END = "<!-- BEGIN BEADS INTEGRATION", "<!-- END BEADS INTEGRATION -->"
CX, CX_END = "<!-- BEGIN BEADS CODEX SETUP", "<!-- END BEADS CODEX SETUP -->"
NI = "## Non-Interactive Shell Commands"
OPS = {
    "A": "git mv CLAUDE.md AGENTS.md; ln -s AGENTS.md CLAUDE.md",
    "B": "git mv -f CLAUDE.md AGENTS.md; write merged AGENTS.md; ln -s AGENTS.md CLAUDE.md",
    "E": "git rm AGENTS.md (link); git mv CLAUDE.md AGENTS.md; ln -s AGENTS.md CLAUDE.md",
    "G": "ln -s AGENTS.md CLAUDE.md",
}
EXPECT = {  # name-status of the migration commit per layout
    "A": {"AGENTS.md": "A", "CLAUDE.md": "T"},
    "B": {"AGENTS.md": "M", "CLAUDE.md": "T"},
    "E": {"AGENTS.md": "T", "CLAUDE.md": "T"},
    "G": {"CLAUDE.md": "A"},
}


class Fail(Exception):
    pass


def run(args, cwd, check=True, env=None):
    r = subprocess.run(args, cwd=cwd, capture_output=True, env=env)
    if check and r.returncode:
        msg = (r.stderr or r.stdout).decode(errors="replace").strip()
        raise Fail(f"{' '.join(args)} (rc={r.returncode}): {msg[-1500:]}")
    return r


def git(d, *args, check=True):
    return run(["git", *args], d, check)


def txt(b):
    return b.decode("utf-8", "surrogateescape")


def lines_of(t):
    return [x.rstrip() for x in t.splitlines() if x.strip()]


def canon(t):
    return "\n".join(x.rstrip() for x in t.splitlines()).rstrip()


def first(ls, prefix):
    return next((i for i, x in enumerate(ls) if x.startswith(prefix)), None)


def count(t, prefix):
    return sum(x.startswith(prefix) for x in t.splitlines())


def layout(row):
    """EXPECT key: how the migration commit looks."""
    g = row["group"]
    if g in ("B", "D") or (g == "C" and row["merged_file"]):
        return "B"
    return "E" if g in ("C", "E") else g


def names(row):
    """Old files whose text must survive."""
    if row["group"] == "G":
        return ["AGENTS.md"]
    return ["CLAUDE.md", "AGENTS.md"] if layout(row) == "B" else ["CLAUDE.md"]


def old(d, row, rev, name):
    if row["git"]:
        return txt(git(d, "show", f"{rev}:{name}").stdout)
    return txt((OUT / d.name / "CLAUDE.md.orig").read_bytes())


def carried(cl, ag):
    """Sections of the old AGENTS.md that the merged file takes over."""
    al = ag.splitlines(keepends=True)
    ni, cx = [], []
    i, j = first(al, NI), first(al, BD)
    if first(cl.splitlines(), NI) is None and i is not None and j is not None and j > i:
        ni = al[i:j]
    i, j = first(al, CX), first(al, CX_END)
    if first(cl.splitlines(), CX) is None and i is not None and j is not None:
        cx = al[i:j + 1]
    return ni, cx


def assemble(cl, ag):
    ni, cx = carried(cl, ag)
    c = cl.splitlines(keepends=True)
    b, e = first(c, BD), first(c, BD_END)
    if b is None or e is None or count(cl, BD) != 1:
        raise Fail("CLAUDE.md must hold exactly one BEADS INTEGRATION block")
    head = c[:b]
    while head and not head[-1].strip():
        head.pop()
    out = head + ["\n"]
    if ni:
        while not ni[-1].strip():
            ni.pop()
        out += ni + ["\n"]
    out += c[b:e + 1]
    if not out[-1].endswith("\n"):
        out[-1] += "\n"
    rest = c[e + 1:]
    while rest and not rest[0].strip():
        rest.pop(0)
    if cx:
        out += ["\n"] + cx
    if rest:
        out += ["\n"] + rest
    return "".join(out)


def target(d, row):
    """Merged AGENTS.md text, or None when the content only moves."""
    if row["group"] in ("B", "D"):
        text = assemble(old(d, row, "HEAD", "CLAUDE.md"), old(d, row, "HEAD", "AGENTS.md"))
        (OUT / d.name).mkdir(parents=True, exist_ok=True)
        (OUT / d.name / "AGENTS.md").write_bytes(text.encode("utf-8", "surrogateescape"))
        return text
    if row["group"] == "C" and row["merged_file"]:
        p = OUT / row["merged_file"]
        if not p.is_file():
            raise Fail(f"hand-merged file missing: {p}")
        return txt(p.read_bytes())
    return None


def content(d, row, rev, new):
    """(ok, message): the new text keeps every old line that must survive."""
    src = {n: old(d, row, rev, n) for n in names(row)}
    if len(src) == 1:
        o = next(iter(src.values()))
        if o == new:
            return True, "byte-identical"
        same = canon(o) == canon(new)
        return same, "whitespace-only differences" if same else "TEXT DIFFERS"
    if row["group"] in ("B", "D"):
        ni, cx = carried(src["CLAUDE.md"], src["AGENTS.md"])
        need = set(lines_of(src["CLAUDE.md"] + "".join(ni) + "".join(cx)))
    else:
        need = set().union(*(lines_of(t) for t in src.values()))
        drop = OUT / d.name / "dropped.txt"
        if drop.exists():
            need -= {x.rstrip() for x in txt(drop.read_bytes()).splitlines()}
    missing = sorted(need - set(lines_of(new)))
    return not missing, f"{len(missing)} old lines missing {missing[:3]}" if missing else "all old lines kept"


def porcelain(d):
    return txt(git(d, "status", "--porcelain", "--", "CLAUDE.md", "AGENTS.md").stdout).splitlines()


def linked(d):
    c, a = d / "CLAUDE.md", d / "AGENTS.md"
    return c.is_symlink() and os.readlink(c) == "AGENTS.md" and a.is_file() and not a.is_symlink()


def state(d, row):
    c, a = d / "CLAUDE.md", d / "AGENTS.md"
    if not row["git"]:
        if linked(d):
            return "done"
        return "fresh" if c.is_file() and not c.is_symlink() and not a.exists() else "partial"
    committed = txt(git(d, "ls-files", "-s", "--", "CLAUDE.md").stdout).split()[:1] == ["120000"]
    dirty = set(porcelain(d))
    if linked(d) and committed and dirty <= {" M AGENTS.md"}:
        return "done"
    if not committed and dirty <= ({" M CLAUDE.md"} if row["group"] == "A" else set()):
        return "fresh"
    return "partial"


def pre(d, row, st):
    lock = Path(d, txt(git(d, "rev-parse", "--git-path", "index.lock").stdout).strip())
    if lock.exists():
        raise Fail("index.lock present")
    br = txt(git(d, "rev-parse", "--abbrev-ref", "HEAD").stdout).strip()
    if br != row["branch"]:
        raise Fail(f"branch {br}, expected {row['branch']}")
    if st == "fresh" and git(d, "diff", "--cached", "--name-only").stdout.strip():
        raise Fail("index already holds staged paths")


def bd_status(d):
    r = run(["bd", "setup", "claude", "--check"], d, check=False)
    t = txt(r.stdout + r.stderr)
    return "stale" if "stale" in t else "current" if "(current)" in t else "none"


def codex(d):
    env = {**os.environ, "CODEX_HOME": str(CODEX_HOME)}
    r = run(["codex", "debug", "prompt-input"], d, check=False, env=env)
    if r.returncode:
        return False, f"codex rc={r.returncode}"

    def strings(o):
        if isinstance(o, str):
            yield o
        elif isinstance(o, dict):
            for v in o.values():
                yield from strings(v)
        elif isinstance(o, list):
            for v in o:
                yield from strings(v)

    seen = "\n".join(strings(json.loads(r.stdout)))
    ls = lines_of(txt((d / "AGENTS.md").read_bytes()))
    ok = ls[0] in seen and ls[-1] in seen
    return ok, "first and last line loaded" if ok else "first or last line NOT in Codex input"


def check(d, row):
    st = state(d, row)
    if st != "done":
        return [("state", False, st)]
    res = []

    def ok(name, cond, msg=""):
        res.append((name, bool(cond), msg))

    a = d / "AGENTS.md"
    ok("layout", linked(d), "CLAUDE.md -> AGENTS.md, AGENTS.md regular")
    if row["git"]:
        rows = txt(git(d, "ls-files", "-s", "--", "CLAUDE.md", "AGENTS.md").stdout).splitlines()
        modes = {x.split("\t")[1]: x.split()[0] for x in rows}
        ok("git modes", modes == {"CLAUDE.md": "120000", "AGENTS.md": "100644"}, str(modes))
    if row["group"] == "F":
        return res
    rev, new = "HEAD", txt(a.read_bytes())
    if row["git"]:
        m = txt(git(d, "log", "-n1", "--format=%H", f"--grep=^{MSG}").stdout).strip()
        ok("migration commit", m, m[:10] or "no commit with the migration subject")
        if not m:
            return res
        rev, new = f"{m}~1", txt(git(d, "show", f"{m}:AGENTS.md").stdout)
        ns = txt(git(d, "show", "--format=", "--no-renames", "--name-status", m).stdout).splitlines()
        got = {x.split("\t")[1]: x.split("\t")[0] for x in ns}
        ok("commit paths", got == EXPECT[layout(row)], str(got))
        ok("tree clean", set(porcelain(d)) <= ({" M AGENTS.md"} if row["group"] == "A" else set()),
           str(porcelain(d)))
    ok("content", *content(d, row, rev, new))
    src = [old(d, row, rev, n) for n in names(row)]
    for tag, begin, end in (("integration", BD, BD_END), ("codex", CX, CX_END)):
        want = max(count(t, begin) for t in src)
        got, got_end = count(new, begin), count(new, end)
        ok(f"markers {tag}", got == got_end == want, f"begin={got} end={got_end} want={want}")
    if (d / ".beads").is_dir() and count(new, BD):
        base = OUT / d.name / "bd.base"
        want = txt(base.read_bytes()).strip() if base.exists() else "current"
        got = bd_status(d)
        ok("bd setup claude --check", got == want, f"{got} (baseline {want})")
    size = len(a.read_bytes())
    ok("size", size < LIMIT or row["oversize_ok"], f"{size} B")
    if row["codex"]:
        ok("codex prompt-input", *codex(d))
    return res


def plan(d, row):
    st = state(d, row)
    print(f"{d.name}\tgroup={row['group']}\tstate={st}" + ("\tMANUAL" if row["manual"] else ""))
    if st == "done":
        return
    if row["group"] == "F":
        print("  ERROR: group F must already be done")
        return
    if not row["git"]:
        print("  ops: mv CLAUDE.md AGENTS.md; ln -s AGENTS.md CLAUDE.md (no git, no commit)")
        return
    try:
        pre(d, row, st)
        new = target(d, row)
    except Fail as e:
        print(f"  ERROR: {e}")
        return
    print(f"  ops: {OPS[layout(row)]}; pre-commit run if configured; commit")
    if new is None:
        size = len(old(d, row, "HEAD", names(row)[0]).encode("utf-8", "surrogateescape")) if row["git"] else 0
        print(f"  content: moves unchanged; size {size} B")
    else:
        size = len(new.encode("utf-8", "surrogateescape"))
        print(f"  content: {content(d, row, 'HEAD', new)[1]}; size {size} B")
        if layout(row) == "B":
            kept = set(lines_of(new))
            gone = [x for x in lines_of(old(d, row, "HEAD", "AGENTS.md")) if x not in kept]
            print(f"  dropped from old AGENTS.md ({len(gone)} lines): {gone}")
    print(f"  limit: {'OVER' if size >= LIMIT else 'under'} {LIMIT}" + (" (allowed)" if size >= LIMIT and row["oversize_ok"] else ""))
    if row["git"] and (d / ".beads").is_dir() and st == "fresh":
        base = bd_status(d)
        (OUT / d.name).mkdir(parents=True, exist_ok=True)
        (OUT / d.name / "bd.base").write_text(base + "\n")
        print(f"  bd baseline: {base}")


def apply_plain(d):
    c, a = d / "CLAUDE.md", d / "AGENTS.md"
    orig = OUT / d.name / "CLAUDE.md.orig"
    orig.parent.mkdir(parents=True, exist_ok=True)
    if c.is_file() and not c.is_symlink():
        if a.exists():
            raise Fail("AGENTS.md already exists")
        if not orig.exists():
            orig.write_bytes(c.read_bytes())
        os.replace(c, a)
    if not os.path.lexists(c):
        os.symlink("AGENTS.md", c)


def apply(d, row):
    st = state(d, row)
    print(f"{d.name}: group={row['group']} state={st}")
    if st == "done":
        print("  skip")
        return
    if row["group"] == "F":
        raise Fail("group F must already be done")
    if not row["git"]:
        return apply_plain(d)
    pre(d, row, st)
    new = target(d, row)
    c, a = d / "CLAUDE.md", d / "AGENTS.md"
    if row["group"] != "G" and c.is_file() and not c.is_symlink():
        if a.is_symlink():
            git(d, "rm", "-q", "--", "AGENTS.md")
        git(d, "mv", *(["-f"] if new is not None else []), "CLAUDE.md", "AGENTS.md")
    if new is not None:
        a.write_bytes(new.encode("utf-8", "surrogateescape"))
    if not os.path.lexists(c):
        os.symlink("AGENTS.md", c)
    stage_agents = new is not None or git(d, "diff", "--quiet", "--", "AGENTS.md", check=False).returncode == 0
    if (d / ".pre-commit-config.yaml").exists():
        for _ in range(2):  # a fixer hook fails the first run after rewriting files
            r = run(["pre-commit", "run", "--files", "AGENTS.md", "CLAUDE.md"], d, check=False)
            if r.returncode == 0:
                break
        else:
            raise Fail("pre-commit: " + txt(r.stdout + r.stderr)[-1500:])
    git(d, "add", "--", *(["AGENTS.md", "CLAUDE.md"] if stage_agents else ["CLAUDE.md"]))
    good, msg = content(d, row, "HEAD", txt(git(d, "show", ":AGENTS.md").stdout))
    if not good:
        raise Fail(f"content check: {msg}")
    staged = set(txt(git(d, "diff", "--cached", "--name-only").stdout).split())
    if not staged <= {"AGENTS.md", "CLAUDE.md"}:
        raise Fail(f"unexpected staged paths: {sorted(staged)}")
    if staged:
        git(d, "commit", "-q", "-m", MSG, "-m", BODY)


def report(d, row):
    res = check(d, row)
    for name, good, msg in res:
        print(f"  {'OK  ' if good else 'FAIL'} {name}: {msg}")
    verdict = all(g for _, g, _ in res)
    print(f"{d.name}\t{row['group']}\t{'PASS' if verdict else 'FAIL'}")
    return verdict


def main(argv):
    manifest = json.loads((WORK / "manifest.json").read_text())
    cmd, dirs = argv[1], argv[2:] or list(manifest)
    if cmd == "apply" and len(argv) != 3:
        raise Fail("apply takes exactly one dir")
    failed = False
    for name in dirs:
        d = Path(name)
        row = manifest[str(d)]
        if cmd == "plan":
            plan(d, row)
        elif cmd == "apply":
            apply(d, row)
            failed = not report(d, row)
        elif cmd == "check":
            failed |= not report(d, row)
        else:
            raise Fail(f"unknown command {cmd}")
    return int(failed)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Fail as e:
        print(f"FAIL: {e}")
        sys.exit(1)
```

- [ ] **Step 2: write `manifest.json`** with exactly this content (38 rows: D 1, A 22 incl. the non-git `my_funny_images`, G 1, E 1, B 6, C 4 incl. `ai-steward-wiki`, F 3 already migrated; fields: `group`, `git`, `branch`, `oversize_ok`, `merged_file` relative to `out/` or null, `manual` informational, `codex` = Codex sample check in `check`). Every directory was verified with `ls` on 2026-10-15; branch per `git rev-parse --abbrev-ref HEAD` (36 `master`, 1 `main` = python-ai-skills, 1 non-git).

```json
{
 "/home/bgs/ai-steward/Gena_Beeline_Local/python-ai-skills": {"group": "D", "git": true, "branch": "main", "oversize_ok": false, "merged_file": null, "manual": false, "codex": true},
 "/home/bgs/ai-steward/Gena_Beeline_Local/2025_Noveo": {"group": "A", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/2026-03-11-magnit-clusterization-ai-classification": {"group": "A", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/aidd-mvp-generator": {"group": "A", "git": true, "branch": "master", "oversize_ok": true, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/Bio-Chem-Career-2026": {"group": "A", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/boilerplate_microservices": {"group": "A", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/claude_bot": {"group": "A", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": true},
 "/home/bgs/ai-steward/Gena_Beeline_Local/claude_bot.bak": {"group": "A", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/docker-deploy-playbook": {"group": "A", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/ebooks": {"group": "A", "git": true, "branch": "master", "oversize_ok": true, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/fastapi-crud-aidd-generated": {"group": "A", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/ML_CAREER_2026": {"group": "A", "git": true, "branch": "master", "oversize_ok": true, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/ML_Sobes_2026": {"group": "A", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/mvp_tg_monitor": {"group": "A", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/nginx-proxy-vps": {"group": "A", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/Preduniversary-High-Schools-Moscow-2026": {"group": "A", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/Prognosis": {"group": "A", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/Sensedar-Spark": {"group": "A", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/study-check-bot": {"group": "A", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/taro_project": {"group": "A", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/telegram-e2e-runner": {"group": "A", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/try_microservices": {"group": "A", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/my_funny_images": {"group": "A", "git": false, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/bge-m3-api": {"group": "G", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": true},
 "/home/bgs/ai-steward/Gena_Beeline_Local/taro_project_2026-04-01": {"group": "E", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": true},
 "/home/bgs/ai-steward/Gena_Beeline_Local/free-ai-selector": {"group": "B", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/Local_LLM_selection": {"group": "B", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": true},
 "/home/bgs/ai-steward/Gena_Beeline_Local/quickexambot": {"group": "B", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/server-monitor": {"group": "B", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/spark-public-bot": {"group": "B", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/tg-video-downloader": {"group": "B", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/ai-generator-asyncmicroservices": {"group": "C", "git": true, "branch": "master", "oversize_ok": false, "merged_file": "ai-generator-asyncmicroservices/AGENTS.md", "manual": true, "codex": true},
 "/home/bgs/ai-steward/Gena_Beeline_Local/Sinayara-Indonesia": {"group": "C", "git": true, "branch": "master", "oversize_ok": false, "merged_file": "Sinayara-Indonesia/AGENTS.md", "manual": true, "codex": true},
 "/home/bgs/ai-steward/Gena_Beeline_Local/VPS-VPN-Home-Server-Guide": {"group": "C", "git": true, "branch": "master", "oversize_ok": false, "merged_file": "VPS-VPN-Home-Server-Guide/AGENTS.md", "manual": true, "codex": true},
 "/home/bgs/ai-steward/Gena_Beeline_Local/ai-steward-wiki": {"group": "C", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": true, "codex": true},
 "/home/bgs/ai-steward/Gena_Beeline_Local/Sensedar": {"group": "F", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/checkmyskillsbot": {"group": "F", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false},
 "/home/bgs/ai-steward/Gena_Beeline_Local/doc4microservices": {"group": "F", "git": true, "branch": "master", "oversize_ok": false, "merged_file": null, "manual": false, "codex": false}
}
```

- [ ] **Step 3: compile and validate.**

```bash
python3 -m py_compile $TMPDIR/agents-md-migrate/migrate.py && echo compile-ok
python3 -m json.tool $TMPDIR/agents-md-migrate/manifest.json > /dev/null && echo json-ok
python3 -I - <<'E'
import json, os, collections
m = json.load(open(os.environ["TMPDIR"] + "/agents-md-migrate/manifest.json"))
print(len(m), dict(collections.Counter(v["group"] for v in m.values())), sum(v["codex"] for v in m.values()))
print([k for k in m if not os.path.isdir(k)])
E
```

Expected: `compile-ok`, `json-ok`, `38 {'D': 1, 'A': 22, 'G': 1, 'E': 1, 'B': 6, 'C': 4, 'F': 3} 9`, `[]`.

- [ ] **Step 4: tool availability.** `which pre-commit codex bd` prints three paths; `ls -l $TMPDIR/codex-home/AGENTS.md` shows the symlink to `/home/bgs/.codex/AGENTS.md` (if `$TMPDIR/codex-home` is missing: `mkdir -p $TMPDIR/codex-home && ln -s /home/bgs/.codex/AGENTS.md $TMPDIR/codex-home/AGENTS.md`).

---

## Task 2: Dry run over all 38 rows

**Serves:** FR-7, NFR-1, NFR-3 (state detection), FR-3 (dropped-line list shown before any write). Read-only (writes only under `$TMPDIR`).

- [ ] **Step 1: run the plan.**

```bash
M="python3 -I $TMPDIR/agents-md-migrate/migrate.py"; $M plan > $TMPDIR/agents-md-migrate/plan.txt 2>&1; cut -c1-200 $TMPDIR/agents-md-migrate/plan.txt
```

- [ ] **Step 2: verify the counts.**

```bash
P=$TMPDIR/agents-md-migrate/plan.txt
grep -c 'state=fresh' $P; grep -c 'state=done' $P; grep -c 'ERROR' $P; grep 'ERROR' $P | cut -c1-120
```

Expected: `35`, `3` (Sensedar, checkmyskillsbot, doc4microservices), `3` ERROR lines, all `hand-merged file missing` for `ai-generator-asyncmicroservices`, `Sinayara-Indonesia`, `VPS-VPN-Home-Server-Guide` (prepared in Task 7). Any other ERROR (branch, `index.lock`, staged paths) blocks: stop and report.

- [ ] **Step 3: verify per-group figures** (observed in the 2026-10-15 dry run; a different number means the repo changed since: re-read before going on).

```bash
grep -E 'size [0-9]+ B' $P | head -40 | cut -c1-80
```

1. D `python-ai-skills`: `all old lines kept; size 18557 B`, `dropped ... (16 lines)`, bd baseline `current`.
2. B sizes and dropped counts: `free-ai-selector` 15681 B/17, `Local_LLM_selection` 31876 B/16 (the largest, under 32768), `quickexambot` 7064 B/15, `server-monitor` 6941 B/15, `spark-public-bot` 11991 B/14, `tg-video-downloader` 5668 B/15; bd baseline `stale` for all six (see Deviations, item 5).
3. A sizes: `aidd-mvp-generator` 38102, `ebooks` 38234, `ML_CAREER_2026` 39512 are flagged `OVER 32768 (allowed)`; every other A repo `under 32768`; `my_funny_images` prints the no-git ops line.
4. E `taro_project_2026-04-01` and C `ai-steward-wiki`: `ops: git rm AGENTS.md (link); git mv CLAUDE.md AGENTS.md; ...`, `moves unchanged`, 11874 B and 7161 B.
5. G `bge-m3-api`: `ops: ln -s AGENTS.md CLAUDE.md`, 2899 B.

- [ ] **Step 4: show the dropped-line lists of the seven B/D repos to the user** (`grep -A0 'dropped from' $P`): they are the title, the `bd prime` pointer, the architecture note, the Quick Reference and (pilot) the line-3 pointer; the user confirms this is the intended loss (Q2). Gate: proceed to Task 3 after the user's OK.

---

## Task 3: Pilot python-ai-skills (gate for everything after)

**Serves:** FR-3, FR-7, FR-1, NFR-1, NFR-2, NFR-4. Design 2.4 step 1 and section 3.

- [ ] **Step 1: precheck.** `git status --porcelain -- CLAUDE.md AGENTS.md` prints nothing (run as a standalone call). `bd setup claude --check` prints `(current)`.
- [ ] **Step 2: apply** (own Bash call; try inside the sandbox first, bypass only if it fails with "Operation not permitted"):

```bash
M="python3 -I $TMPDIR/agents-md-migrate/migrate.py"; B=/home/bgs/ai-steward/Gena_Beeline_Local; $M apply $B/python-ai-skills
```

Expected: `python-ai-skills: group=D state=fresh`, then OK lines: `git modes` `{'AGENTS.md': '100644', 'CLAUDE.md': '120000'}`, `commit paths` `{'AGENTS.md': 'M', 'CLAUDE.md': 'T'}` (git records a type change plus a modification, not a rename: verified in a temp repo; the design's `R0xx`/`A` expectation is not what git prints), `tree clean`, `content all old lines kept`, `markers integration begin=1 end=1 want=1`, `markers codex begin=1 end=1 want=1`, `bd setup claude --check current (baseline current)`, `size 18557 B`, `codex prompt-input first and last line loaded`, last line `python-ai-skills	D	PASS`. The commit passes the repo hooks (gitleaks staged scan, `principles-ssot`, ...). If a hook fails: fix the cause, re-run the same command (state `partial` resumes).
- [ ] **Step 3: independent evidence** (each a standalone call):

```bash
git ls-files -s -- CLAUDE.md AGENTS.md
git show --format=%s --name-status --no-renames HEAD
grep -c '<!-- BEGIN BEADS' AGENTS.md; grep -c '^## Non-Interactive Shell Commands' AGENTS.md; grep -c 'Repository rules live' AGENTS.md; wc -c AGENTS.md; readlink CLAUDE.md
```

Expected: `120000 ... 0	CLAUDE.md` and `100644 ... 0	AGENTS.md`; subject = the migration message, `M AGENTS.md`, `T CLAUDE.md`; `2` (one INTEGRATION, one CODEX), `1`, `0`, `18557 AGENTS.md`, `AGENTS.md`.
- [ ] **Step 4: repo tests unaffected.** `make test` prints `457 passed` (the count may differ only by tests added since; no failure).
- [ ] **Step 5: GATE with the user (NFR-4, Claude Code side, no offline probe exists).** Ask the user to open `claude` in the pilot directory and run `/memory`: the list must show the project file (`CLAUDE.md`/`AGENTS.md`) and `~/ai-steward/Gena_Beeline_Local/CLAUDE.md` (profile still loads). Do not start Task 4 before the user confirms. If the project file is missing: stop, report, no further `apply`.

---

## Task 4: Batch A (21 repositories + non-git `my_funny_images`)

**Serves:** FR-1, FR-2, FR-7, NFR-1, NFR-2, NFR-3. Design 2.2 group A, 2.4 step 2.

Rules: one `apply` per Bash call with sandbox bypass; read each result before the next; `Prognosis` and `telegram-e2e-runner` have a pre-commit config (fixers / `pytest-collect`), `2025_Noveo` has an uncommitted CLAUDE.md edit that stays unstaged (resolution 5).

- [ ] **Step 1: apply, in this order** (`claude_bot` first: it is also a Codex sample):

```bash
M="python3 -I $TMPDIR/agents-md-migrate/migrate.py"; B=/home/bgs/ai-steward/Gena_Beeline_Local; $M apply $B/claude_bot
```

then the same command with `$B/` plus each of: `2025_Noveo`, `2026-03-11-magnit-clusterization-ai-classification`, `aidd-mvp-generator`, `Bio-Chem-Career-2026`, `boilerplate_microservices`, `claude_bot.bak`, `docker-deploy-playbook`, `ebooks`, `fastapi-crud-aidd-generated`, `ML_CAREER_2026`, `ML_Sobes_2026`, `mvp_tg_monitor`, `nginx-proxy-vps`, `Preduniversary-High-Schools-Moscow-2026`, `Prognosis`, `Sensedar-Spark`, `study-check-bot`, `taro_project`, `telegram-e2e-runner`, `try_microservices`, and last `my_funny_images`.

Expected for each git repo: `commit paths` `{'AGENTS.md': 'A', 'CLAUDE.md': 'T'}`, `content byte-identical` (Prognosis may print `whitespace-only differences` if a fixer touched it: acceptable, read the diff), markers `begin == end == want` (unchanged from the old file; most group A files have no bd block, `want=0`), `size` as in Task 2, final `<dir>	A	PASS`. `2025_Noveo`: `tree clean: [' M AGENTS.md']` (the unstaged edit) and still PASS. `claude_bot` also prints `codex prompt-input first and last line loaded`. `my_funny_images`: `layout`, `content byte-identical` (against `out/my_funny_images/CLAUDE.md.orig`), `size 284 B`, PASS, no git lines.
- [ ] **Step 2: independent evidence over the batch** (standalone calls, one per repo or a loop run inside the sandbox where `git` is read-only):

```bash
B=/home/bgs/ai-steward/Gena_Beeline_Local; for d in claude_bot 2025_Noveo ebooks Prognosis taro_project; do echo "== $d"; git -C $B/$d ls-files -s -- CLAUDE.md AGENTS.md; cmp <(git -C $B/$d show HEAD:AGENTS.md) <(git -C $B/$d show HEAD~1:CLAUDE.md) && echo bytes-equal; done
```

Expected per repo: `120000` for CLAUDE.md, `100644` for AGENTS.md, `bytes-equal` (Prognosis: no output from `cmp` only if identical; otherwise inspect).
- [ ] **Step 3: idempotence (NFR-3).** `$M apply $B/claude_bot` prints `claude_bot: group=A state=done` and `skip`, then PASS; `git -C $B/claude_bot log --oneline -2` shows no new commit.
- [ ] **Step 4: batch status.** `$M check | grep -cP '\tA\tPASS$'` prints `22`.

---

## Task 5: Batch G and E (`bge-m3-api`, then `taro_project_2026-04-01`)

**Serves:** FR-6 (G), FR-5 (E), FR-7. Design 2.2 groups G and E, 2.4 step 3.

- [ ] **Step 1: bge-m3-api.**

```bash
M="python3 -I $TMPDIR/agents-md-migrate/migrate.py"; B=/home/bgs/ai-steward/Gena_Beeline_Local; $M apply $B/bge-m3-api
```

Expected: `commit paths` `{'CLAUDE.md': 'A'}`, `content byte-identical`, `size 2899 B`, `codex prompt-input first and last line loaded`, `bge-m3-api	G	PASS`. Independent: `cmp <(git -C $B/bge-m3-api show HEAD:AGENTS.md) <(git -C $B/bge-m3-api show HEAD~1:AGENTS.md) && echo bytes-equal`.
- [ ] **Step 2: taro_project_2026-04-01 last** (its commit runs `pytest-unit-fast`, `sentrux-check`, `marker-compliance`: slow, may fail for unrelated reasons; a failure leaves state `partial`, fix the cause, re-run `apply`; set a long Bash timeout, 600000 ms).

```bash
M="python3 -I $TMPDIR/agents-md-migrate/migrate.py"; B=/home/bgs/ai-steward/Gena_Beeline_Local; $M apply $B/taro_project_2026-04-01
```

Expected: `commit paths` `{'AGENTS.md': 'T', 'CLAUDE.md': 'T'}`, `content byte-identical`, `size 11874 B`, Codex line OK, `taro_project_2026-04-01	E	PASS`. Independent: `git -C $B/taro_project_2026-04-01 ls-files -s -- CLAUDE.md AGENTS.md` shows `120000` and `100644`; `cmp <(git -C $B/taro_project_2026-04-01 show HEAD:AGENTS.md) <(git -C $B/taro_project_2026-04-01 show HEAD~1:CLAUDE.md) && echo bytes-equal`.

---

## Task 6: Batch B (six template pairs)

**Serves:** FR-3, FR-7, NFR-1. Design 2.2 groups B, 2.7 item 2 (hook risks).

Order: `quickexambot`, `server-monitor`, `tg-video-downloader`, `spark-public-bot`, `free-ai-selector` (markdownlint, eof/ws fixers), `Local_LLM_selection` (largest, `vocab-check`, Codex sample).

- [ ] **Step 1: apply, one per call with bypass.**

```bash
M="python3 -I $TMPDIR/agents-md-migrate/migrate.py"; B=/home/bgs/ai-steward/Gena_Beeline_Local; $M apply $B/quickexambot
```

then the same with each remaining name above.

Expected per repo: `commit paths` `{'AGENTS.md': 'M', 'CLAUDE.md': 'T'}`, `content all old lines kept`, `markers integration begin=1 end=1 want=1`, `markers codex begin=1 end=1 want=1` (`tg-video-downloader`: `begin=0 end=0 want=0`, it never had a CODEX block), `bd setup claude --check` equal to the baseline from Task 2 (`stale (baseline stale)`; the migration must not change the status), `size` as in Task 2 (all under 32768; `Local_LLM_selection` 31876 B), PASS; `Local_LLM_selection` also `codex prompt-input first and last line loaded`.
- [ ] **Step 2: hook failures.** `free-ai-selector`: a markdownlint finding on text that was never linted is fixed in the repo's working-tree `AGENTS.md` (already moved by the failed run), then `apply` is re-run (state `partial` resumes; `apply` rewrites the merged text from `HEAD`, so a hand fix there must be made in the merge source instead: stop and ask the user which line to change). `Local_LLM_selection`: a `vocab-check` objection is surfaced by `apply` before the commit; report it to the user, do not skip the hook.
- [ ] **Step 3: independent evidence** per repo: `git -C $B/<dir> ls-files -s -- CLAUDE.md AGENTS.md` (`120000`/`100644`); `grep -c '<!-- BEGIN BEADS' $B/<dir>/AGENTS.md` prints `2` (`tg-video-downloader`: `1`); `wc -c $B/<dir>/AGENTS.md` equals the Task 2 size (a hook fixer may add or remove a few bytes: then the size is within the Task 2 size +-16 B and below 32768); `git -C $B/Local_LLM_selection show HEAD:AGENTS.md | wc -c` below `32768`.

---

## Task 7: Group C (three hand merges and `ai-steward-wiki`)

**Serves:** FR-4, FR-7. Design 2.2 group C. The user sees every result before `apply`.

- [ ] **Step 1: prepare the hand-merged files** (orchestrator, or a mid-tier subagent from a written spec; verify the result yourself, trust = 0): for `ai-generator-asyncmicroservices`, `Sinayara-Indonesia`, `VPS-VPN-Home-Server-Guide` write `$TMPDIR/agents-md-migrate/out/<name>/AGENTS.md` by the rule "the whole text of `CLAUDE.md` first, then every section of the old `AGENTS.md` whose heading is absent from `CLAUDE.md`, verbatim, in its original order". Read both source files completely before writing (sizes: 14362 B + 10156 B; 5492 B + 8264 B; 1205 B + 5854 B, `VPS-VPN-Home-Server-Guide` AGENTS.md is the grace-init GRACE protocol). Any line deliberately left out goes to `out/<name>/dropped.txt` (one line per dropped line) and is shown to the user.
- [ ] **Step 2: dry run and diff for each, shown to the user.**

```bash
M="python3 -I $TMPDIR/agents-md-migrate/migrate.py"; B=/home/bgs/ai-steward/Gena_Beeline_Local; $M plan $B/ai-generator-asyncmicroservices
git diff --no-index --stat $B/ai-generator-asyncmicroservices/CLAUDE.md $TMPDIR/agents-md-migrate/out/ai-generator-asyncmicroservices/AGENTS.md
git diff --no-index $B/ai-generator-asyncmicroservices/CLAUDE.md $TMPDIR/agents-md-migrate/out/ai-generator-asyncmicroservices/AGENTS.md
```

(`git diff --no-index` exits 1 when the files differ: expected; each `git` call stands alone.) Expected from `plan`: `content: all old lines kept` (or the count of lines the user approved in `dropped.txt`), size below 32768 (expected sum of both files minus overlaps: at most 24.5 KB, 13.8 KB, 7.1 KB), no ERROR. The same for `Sinayara-Indonesia` and `VPS-VPN-Home-Server-Guide`. For `ai-steward-wiki` show: `ls -l $B/ai-steward-wiki/AGENTS.md` (link to `docs/Spec-WIKI/CLAUDE.md`), `wc -c $B/ai-steward-wiki/CLAUDE.md` (7161), and the plan line `git rm AGENTS.md (link); git mv CLAUDE.md AGENTS.md; ...`; `docs/Spec-WIKI/CLAUDE.md` stays untouched (resolution 2). **Gate: apply each repo only after the user's OK for that repo.**
- [ ] **Step 3: apply, one per call with bypass** (after the OK):

```bash
M="python3 -I $TMPDIR/agents-md-migrate/migrate.py"; B=/home/bgs/ai-steward/Gena_Beeline_Local; $M apply $B/ai-generator-asyncmicroservices
```

then `Sinayara-Indonesia`, `VPS-VPN-Home-Server-Guide`, `ai-steward-wiki`.

Expected: merged repos `commit paths` `{'AGENTS.md': 'M', 'CLAUDE.md': 'T'}`, `content all old lines kept`, markers `want` equal to the old files, `codex prompt-input ... loaded`, PASS; `ai-steward-wiki`: `commit paths` `{'AGENTS.md': 'T', 'CLAUDE.md': 'T'}`, `content byte-identical`, pre-commit eof/ws fixers may print `whitespace-only differences`, PASS. Independent: `git -C $B/<dir> ls-files -s -- CLAUDE.md AGENTS.md` and `git -C $B/ai-steward-wiki ls-files -s -- docs/Spec-WIKI/CLAUDE.md` still `100644`.

---

## Task 8: Generator and layout-rule edits in python-ai-skills (FR-8)

**Serves:** FR-8, resolution 6. Level 4 text edits; validators: `make test` and `pre-commit run --files <edited files>`. Every old text below was found with grep on 2026-10-15 (line numbers of that moment, before Task 3 changed the pilot).

- [ ] **Step 1: `_init/SKILL.md`.**
  1. Line 4, replace `Creates CLAUDE.md, CHANGELOG.md,` with `Creates AGENTS.md (plus a `CLAUDE.md -> AGENTS.md` symlink), CHANGELOG.md,`.
  2. Line 26, replace `### 1. CLAUDE.md (in project root)` with `### 1. AGENTS.md (in project root) + `CLAUDE.md` symlink`.
  3. After the closing code fence of the block that follows line 26 (the first closing fence after it), insert: `Then `ln -s AGENTS.md CLAUDE.md`. Claude Code reads the file through the link (a `CLAUDE.md` above the project, the user profile, otherwise hides a bare `AGENTS.md`); Codex reads `AGENTS.md`. Edit `AGENTS.md`, never the link.`
- [ ] **Step 2: `grace-init/SKILL.md`.**
  1. Line 3, replace `creates docs/ directory, AGENTS.md, and XML templates` with `creates docs/ directory, AGENTS.md with a `CLAUDE.md` symlink, and XML templates`.
  2. Line 15, replace the cell `` `AGENTS.md` (project root)  `` with `` `AGENTS.md` (project root) + `CLAUDE.md -> AGENTS.md` symlink ``.
  3. After line 46 (`- If `AGENTS.md` already exists — warn the user ...`) add the bullet: `    - Create the symlink `CLAUDE.md -> AGENTS.md` (`ln -s AGENTS.md CLAUDE.md`) when `CLAUDE.md` is absent; when a regular `CLAUDE.md` exists, stop and ask the user to merge it into `AGENTS.md` first.` (keep the indentation of lines 45-46). `assets/AGENTS.md.template` stays unchanged.
- [ ] **Step 3: `git-finish/SKILL.md`, line 93.** Replace `- `CLAUDE.md` — skill catalog rows, grouped lists and **counters**.` with `- `AGENTS.md` — skill catalog rows, grouped lists and **counters** (`CLAUDE.md` is a symlink to it; Edit refuses the link).`
- [ ] **Step 4: pilot note in `AGENTS.md`** (Edit through the real file, never `CLAUDE.md`). Find it with `grep -n "outside the managed" AGENTS.md`. Replace the two lines `> `BEADS INTEGRATION` block above: `bd setup claude` rewrites everything between` / `> its markers and would silently delete them.` with `> `BEADS INTEGRATION` and `BEADS CODEX SETUP` blocks above: `bd init` and `bd setup codex` rewrite everything between` / `> their markers (`bd setup claude` skips the `CLAUDE.md` symlink) and would silently delete them.` The sentence before ("The sections below are hand-written and MUST stay outside the managed") is unchanged; the remaining lines of the note stay as they are. Sequencing note: this reword is a separate commit after the migration commit, so the migration commit stays a pure move and its content check needs no exception.
- [ ] **Step 5: `claude-home/CLAUDE.md:31` (write-protected here; the user applies it, or approves it in a session without the deny rule).** Replace `in its root CLAUDE.md/AGENTS.md:` with `in its root `AGENTS.md` (the single real instruction file; `CLAUDE.md` is a symlink to it, `ln -s AGENTS.md CLAUDE.md`):`. Lines 258 and 270 stay. Ask the user; the commit below does not wait: if the edit is not done, the commit lands without that file and the gap is recorded in the bead notes.
- [ ] **Step 6: `CHANGELOG.md`, `## [Unreleased]` -> `### Changed` (line 32 on 2026-10-15), add as the first entry:**

```
- Project instruction files: every project under `Gena_Beeline_Local` keeps one real `AGENTS.md` with `CLAUDE.md` as a symlink to it (bd `python-ai-skills-lvt.2`; Claude Code >= 2.1.277 reads `AGENTS.md`, Codex reads only it). Pilot here: `CLAUDE.md` content + the `Non-Interactive Shell Commands` section and the `BEADS CODEX SETUP` block from the old `AGENTS.md`, line-3 pointer dropped. Generators and rules now produce/describe that layout: `_init`, `grace-init` (symlink step), `claude-home/CLAUDE.md` Project Classification, `git-finish` doc list. Sinayara-Isuzu, Sinayara-Isuzu-web and three > 32 KiB files -> lvt.3.
```
- [ ] **Step 7: verify.**

```bash
grep -n "Creates AGENTS.md\|### 1. AGENTS.md" _init/SKILL.md; grep -n "CLAUDE.md. symlink" grace-init/SKILL.md; grep -n "AGENTS.md. — skill catalog" git-finish/SKILL.md; grep -n "BEADS CODEX SETUP. blocks above" AGENTS.md; grep -n "python-ai-skills-lvt.2" CHANGELOG.md | cut -c1-80
make test
pre-commit run --files _init/SKILL.md grace-init/SKILL.md git-finish/SKILL.md AGENTS.md CHANGELOG.md
```

Expected: each grep prints its new line (two lines for `_init`), `make test` ends `457 passed` (no failure; `test_principles_ssot.py` now also visits `AGENTS.md` and the link with identical text and passes), `pre-commit` prints `Passed` for every hook. Also confirm the old texts are gone: `grep -n "Creates CLAUDE.md" _init/SKILL.md` and `grep -n "^- .CLAUDE.md. — skill catalog" git-finish/SKILL.md` print nothing.
- [ ] **Step 8: commit** (standalone `git` calls; hooks run, no bypass; `claude-home/CLAUDE.md` only if the user edited it):

```bash
git add -- _init/SKILL.md grace-init/SKILL.md git-finish/SKILL.md AGENTS.md CHANGELOG.md
git commit -m "docs(agents-md): point generators and rules at AGENTS.md as the single instruction file" -m "Refs: python-ai-skills-lvt.2"
```

---

## Task 9: Final verification and bead notes

**Serves:** NFR-1..NFR-4, FR-1..FR-8 acceptance.

- [ ] **Step 1: check over all 38 directories.**

```bash
M="python3 -I $TMPDIR/agents-md-migrate/migrate.py"; $M check > $TMPDIR/agents-md-migrate/final.txt 2>&1; echo rc=$?; grep -c '	PASS$' $TMPDIR/agents-md-migrate/final.txt; grep -c 'FAIL' $TMPDIR/agents-md-migrate/final.txt
```

Expected: `rc=0`, `38`, `0`. The 3 group-F directories print only `layout` and `git modes`.
- [ ] **Step 2: Codex sample (NFR-4).** `grep 'codex prompt-input' $TMPDIR/agents-md-migrate/final.txt` prints 9 lines `OK   codex prompt-input: first and last line loaded` (python-ai-skills, claude_bot, bge-m3-api, taro_project_2026-04-01, Local_LLM_selection, the three C merges, ai-steward-wiki).
- [ ] **Step 3: size gate (NFR-1).** `grep 'size:' $TMPDIR/agents-md-migrate/final.txt | sort -t: -k2 -n | tail -5` shows the three allowed oversize files (39512, 38234, 38102) and `Local_LLM_selection` 31876 as the largest remaining; no `FAIL size`.
- [ ] **Step 4: idempotence of the plan.** `$M plan | grep -c 'state=done'` prints `38`.
- [ ] **Step 5: nothing was pushed (NFR-2).** `git status -sb` in python-ai-skills shows `ahead N` (local commits only); no `git push` was run in this session (`bd dolt push` is separate and allowed).
- [ ] **Step 6: summary table for the user** (38 lines from `final.txt`: directory, group, state, commit hash from `git -C <dir> log -1 --format=%h` where the commit subject matches, PASS).
- [ ] **Step 7: bead notes.** First `bd update --help` (verify the notes flag and whether it appends or replaces; the do-feature reference uses `--notes=`). Record on `python-ai-skills-lvt.2`: Execution done, 38 PASS, the commit list, the stale bd-block finding (Deviations item 5) and, if applicable, that `claude-home/CLAUDE.md:31` is still waiting for the user. On `python-ai-skills-lvt.3` add: `aidd-mvp-generator` (38102 B), `ebooks` (38234 B), `ML_CAREER_2026` (39512 B) exceed the Codex 32 KiB limit; six repositories (`free-ai-selector`, `Local_LLM_selection`, `quickexambot`, `server-monitor`, `spark-public-bot`, `tg-video-downloader`) carry a stale `BEADS INTEGRATION` block that `bd setup claude` can no longer refresh through the symlink. Closing `lvt.2` happens in the Finish step of `do-feature`, not here.

---

## Deviations from the design

All are details the design left open or got wrong against observed behaviour; none changes the approved approach, groups, order or outcome.

1. **Commit name-status.** The design expects `R100 CLAUDE.md AGENTS.md` + `A CLAUDE.md` (A) and `R0xx` + `A` (B/D). Verified in a temp repo (git 2.43): git never reports a rename when the old path still exists as a symlink; the real output is A: `A AGENTS.md`, `T CLAUDE.md`; B/C-merge/D: `M AGENTS.md`, `T CLAUDE.md`; E and wiki: `T`, `T`; G: `A CLAUDE.md`. `check` asserts these (`git show --no-renames`).
2. **Group F in the manifest.** The design lists groups A/B/C/D/E/G, yet its final `check` runs over 38 dirs; the 3 already-migrated directories (Sensedar, checkmyskillsbot, doc4microservices) are rows of group `F`: `apply` refuses them, `check` verifies layout and git modes only.
3. **Extra manifest fields** (data, not logic): `branch` (the design requires the "HEAD is the inventory branch" precondition without naming where the value lives), `codex` (selects the design's Codex sample dirs, 9 of 38), `manual` (marks hand-merged group C rows; informational, printed by `plan`).
4. **`dropped.txt`.** The design's "user-approved dropped list" for group C is the optional file `out/<name>/dropped.txt`.
5. **`bd setup claude --check` baseline.** The design demands `(current)`. Measured 2026-10-15: all six B repositories are `stale` before the migration (`bd` wants a newer INTEGRATION block; the pilot is `current`), so a `(current)` demand would fail for reasons the migration does not cause. `plan` records the pre-migration status in `out/<name>/bd.base`; `check` requires the status to be unchanged (no baseline file: `current`). Consequence for the user: after the symlink, `bd setup claude` skips `CLAUDE.md`, so these six stale blocks can no longer be refreshed that way; recorded for lvt.3 (Task 9, step 7).
6. **Pilot note reword** (design 2.5 item 5) is committed in Task 8, not inside the migration commit, so the pilot's content check needs no special-cased line.
7. **Content check is canonical-line based for single-source groups** (A/E/G/wiki): byte-identical, or equal after trailing-whitespace/blank-line normalisation (reported as `whitespace-only differences`); this lets the `pre-commit` fixers of Prognosis, free-ai-selector, spark-public-bot and ai-steward-wiki pass while any text change fails.
8. **Staging.** `apply` stages `AGENTS.md` only when it wrote merged text or when the worktree file equals the index (so fixer edits are committed); for the dirty `2025_Noveo` it stays unstaged (resolution 5). The commit uses no pathspec so nothing but the two paths can enter it (a pre-commit guard aborts on any other staged path).
9. **Script exercised before delivery.** The plan author ran `apply` + `check` of this exact script against synthetic temp repositories (A, dirty-A, B, D, E, G, non-git, resume after partial, re-run on done) in a separate `TMPDIR`; no real repository was touched (only `plan`/`check`-style read-only calls and writes under `$TMPDIR`).

## Self-review checklist (do-feature Step 9)

- [x] **Every FR covered.** FR-1 layout: Tasks 3-7 (`check` layout/git modes) and Task 9. FR-2 group A: Task 4. FR-3 B and pilot: Tasks 3 and 6. FR-4 group C and wiki: Task 7. FR-5 E: Task 5 step 2. FR-6 G: Task 5 step 1. FR-7 per-project checks (`bd setup claude --check`, pre-commit via `apply`, content, markers): `check` in every apply task. FR-8 generators and rules: Task 8.
- [x] **Every NFR has a verification step.** NFR-1 size < 32768: Task 2 step 3, per-apply `size`, Task 9 step 3. NFR-2 one commit per repo, hooks run, no push: `migration commit` and `commit paths` checks, hooks run inside `git commit` (no `--no-verify` anywhere), Task 9 step 5. NFR-3 idempotence: Task 4 step 3 and Task 9 step 4 (and `partial` resume, exercised on a temp repo). NFR-4 acceptance: Task 3 steps 2 and 5, Task 9 step 2.
- [x] **MODULE_CONTRACT / verification-plan / log anchors / ADR:** not applicable (no GRACE module; the script is a level-5 throwaway; no ADR in scope).
- [x] **Task order respects dependencies:** 1 (tool) -> 2 (dry run) -> 3 (pilot gate) -> 4 (A) -> 5 (G, E last) -> 6 (B) -> 7 (C, user-reviewed) -> 8 (edits, after the pilot exists) -> 9 (final).
- [x] **No placeholders:** the full script and manifest are inline; every command has an expected output; the only variable parts are the directory names, listed explicitly per task. Task 8 gives old and new text for every edit.
- [x] **Reverse traceability:** `plan`/`apply`/`check` -> Tasks 2-9; `manifest` fields `group`, `git`, `merged_file`, `oversize_ok` -> design group table and resolutions 1-6; `branch` -> design precondition; `codex` -> design check 6 sample list; `manual` -> the brief (group C marking); `dropped.txt` -> design "user-approved dropped list"; `bd.base` -> Deviation 5; `EXPECT` -> Deviation 1; each function in the script serves one of: state detection (NFR-3), assembly (FR-3), content check (FR-2..FR-4), markers/bd/size/Codex checks (FR-7, NFR-1, NFR-4).
- [x] **Excess-code check (`_code-quality/principles.md`) on `migrate.py`:** deletion test per piece: `apply_plain` (one non-git directory), `carried`/`assemble` (groups B/D), `EXPECT` (commit-path assertion), `codex` (NFR-4), `bd_status` (FR-7) each remove a requirement if deleted; no option flags beyond the three commands, no classes besides the exception, no abstraction with one implementation, no guard against a state the callers cannot produce except the `index.lock`/branch/staged-path preconditions the design names.
