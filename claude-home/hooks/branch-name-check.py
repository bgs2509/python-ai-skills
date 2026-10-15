"""PreToolUse hook: deny creating a git branch whose name has no `branch` segment.

Enforcement half of the N-BRANCH rule (claude-home/CLAUDE.md -> "Naming"; the
rule text lives only there, bd python-ai-skills-31d). Checked tools:

  - Bash: git commands that create a branch (checkout -b/-B/--orphan,
    switch -c/-C/--create/--force-create/--orphan, branch <name>,
    branch -m/-M/-c/-C <old> <new>, worktree add [-b/-B <name>] <path>).
  - EnterWorktree: tool_input.name (a call with only `path` enters an existing worktree).

Contract:
  - stdin: PreToolUse JSON (tool_name, tool_input, cwd).
  - exit 0: allow, silent. Any unparsable input, missing field or exception also
    ends in exit 0: only a verified non-compliant name is denied.
  - exit 2: deny, reason on stderr; one record is appended to
    ~/.claude/hook-stats/blocks.jsonl first.
  - Override: the line `N-BRANCH: off` under `## Naming overrides` in
    <git toplevel of cwd>/AGENTS.md; read only after an offending name is found.
"""

import datetime
import json
import os
import re
import shlex
import sys

# Rule constants. The wording of the rule is in claude-home/CLAUDE.md -> "Naming"
# (segment boundaries) and -> "Commit Convention" (types); keep these in step.
SEGMENT = re.compile(r"(^|[-/_+])branch($|[-/_+])")
FORM = "<type>/branch-<slug>"
TYPES = ("feat", "fix", "docs", "style", "refactor", "test", "chore", "perf", "build", "ci")

# Shell splitting, as in block-no-verify.sh (second consumer; extract on a third).
SEPARATORS = {"&&", "||", ";", "|", "&"}
GIT_OPTIONS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
PREFIX_WORDS = {"command", "env", "nice", "time"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

# `git branch` flags that never create a branch, and the ones that move or copy.
BRANCH_NON_CREATING = {
    "-d", "-D", "--delete", "-l", "--list", "-a", "--all", "-r", "--remotes", "-v", "-vv",
    "--verbose", "--show-current", "-u", "--set-upstream-to", "--unset-upstream",
    "--edit-description", "--merged", "--no-merged", "--contains", "--no-contains",
    "--points-at", "--format", "--sort", "--column", "--color",
}
BRANCH_MOVE_COPY = {"-m", "-M", "--move", "-c", "-C", "--copy"}

DENY = """[branch-name-check] Refusing to create branch '{names}': no `branch` segment.

Naming rule N-BRANCH (~/.claude/CLAUDE.md -> "Naming"): form {form},
<type> one of {types} (Commit Convention).
Worktrees: pass that form as the EnterWorktree name (Claude Code adds `worktree-` and turns `/` into `+`).
Project override: a line `N-BRANCH: off` under `## Naming overrides` in {toplevel}/AGENTS.md.
"""


def segments(tokens):
    """Split a token list into the commands of one shell line."""
    cur = []
    for tok in tokens:
        if tok in SEPARATORS:
            yield cur
            cur = []
        elif tok.endswith(";"):  # shlex keeps `;` glued to the previous word
            if tok.rstrip(";"):
                cur.append(tok.rstrip(";"))
            yield cur
            cur = []
        else:
            cur.append(tok)
    yield cur


def git_subcommand(segment):
    """(subcommand, its arguments) when the segment is a git command, else None."""
    i = 0
    while i < len(segment):
        if ASSIGNMENT.match(segment[i]) or segment[i] in PREFIX_WORDS:
            i += 1
        elif segment[i:i + 2] == ["rtk", "proxy"]:
            i += 2
        else:
            break
    if i >= len(segment) or not (segment[i] == "git" or segment[i].endswith("/git")):
        return None
    i += 1
    while i < len(segment):
        if segment[i] in GIT_OPTIONS_WITH_VALUE:
            i += 2
        elif segment[i].startswith("-"):
            i += 1
        else:
            return segment[i], segment[i + 1:]
    return None


def option_value(args, flags):
    """Value of the first option of `flags` (`-b x`, `-bx`, `--orphan x`, `--orphan=x`), else None."""
    for i, tok in enumerate(args):
        if tok == "--":
            return None
        for flag in flags:
            if tok == flag:
                return args[i + 1] if i + 1 < len(args) else ""
            if flag.startswith("--") and tok.startswith(flag + "="):
                return tok[len(flag) + 1:]
            if not flag.startswith("--") and not tok.startswith("--") and tok.startswith(flag):
                return tok[len(flag):]
    return None


def branch_name(args):
    """New name from `git branch` arguments: create, move or copy; None when it only lists or edits."""
    end = args.index("--") if "--" in args else len(args)
    flags = [a for a in args[:end] if a.startswith("-")]
    if any(f.split("=", 1)[0] in BRANCH_NON_CREATING for f in flags):
        return None
    positional = [a for a in args[:end] if not a.startswith("-")] + args[end + 1:]
    if not positional:
        return None
    return positional[-1] if any(f in BRANCH_MOVE_COPY for f in flags) else positional[0]


def worktree_name(args):
    """Branch name `git worktree add` creates: -b/-B value, else the path basename; None otherwise."""
    if not args or args[0] != "add":
        return None
    rest = args[1:]
    value = option_value(rest, ("-b", "-B"))
    if value is not None:
        return value
    if "--detach" in rest or "-d" in rest:
        return None
    positional, i = [], 0
    while i < len(rest):
        if rest[i] == "--reason":
            i += 2
            continue
        if not rest[i].startswith("-"):
            positional.append(rest[i])
        i += 1
    if len(positional) == 1:  # `<path> <commit-ish>` checks out an existing branch
        return os.path.basename(positional[0].rstrip("/"))
    return None


def new_branch_name(sub, args):
    if sub == "checkout":
        return option_value(args, ("-b", "-B", "--orphan"))
    if sub == "switch":
        return option_value(args, ("-c", "-C", "--create", "--force-create", "--orphan"))
    if sub == "branch":
        return branch_name(args)
    if sub == "worktree":
        return worktree_name(args)
    return None


def offending_bash(command):
    """New branch names without the segment in a Bash command line."""
    if "git" not in command:
        return []
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return []
    names = []
    for segment in segments(tokens):
        found = git_subcommand(segment)
        name = new_branch_name(*found) if found else None
        if name and not SEGMENT.search(name):
            names.append(name)
    return names


def log_block(kind, text):
    """Append one record to the block journal; a write error never changes the verdict."""
    try:
        directory = os.path.expanduser("~/.claude/hook-stats")
        os.makedirs(directory, exist_ok=True)
        record = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "hook": "branch-name-check",
            "cwd": os.getcwd(),
            "kind": kind,
            "command": text[:300],
        }
        with open(os.path.join(directory, "blocks.jsonl"), "a", encoding="utf-8") as journal:
            journal.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def main():
    try:
        data = json.load(sys.stdin)
        if data["tool_name"] != "Bash":
            return 0
        text = data["tool_input"]["command"]
        names = offending_bash(text)
        if not names:
            return 0
        toplevel = data.get("cwd") or os.getcwd()
    except Exception:  # fail open on anything unexpected: only a verified name is denied
        return 0
    log_block("bash-git", text)
    message = DENY.format(names=", ".join(names), form=FORM, types=", ".join(TYPES), toplevel=toplevel)
    sys.stderr.write(message)
    return 2


if __name__ == "__main__":
    sys.exit(main())
