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
  - exit 2: deny, reason on stderr; one record (ts, hook, cwd, kind, names: the
    offending branch names, never the command text) is appended to
    ~/.claude/hook-stats/blocks.jsonl first.
  - Override: the line `N-BRANCH: off` under `## Naming overrides` in
    <git toplevel of cwd>/AGENTS.md; read only after an offending name is found.
"""

import datetime
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

# Rule constants. The wording of the rule is in claude-home/CLAUDE.md -> "Naming"
# (segment boundaries) and -> "Commit Convention" (types); keep these in step.
SEGMENT = re.compile(r"(^|[-/_+])branch($|[-/_+])")
FORM = "<type>/branch-<slug>"
TYPES = ("feat", "fix", "docs", "style", "refactor", "test", "chore", "perf", "build", "ci")

# Shell splitting, as in block-no-verify.sh (second consumer; extract on a third).
SEPARATORS = {"&&", "||", ";", "|", "|&", "&", "(", ")"}
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

OVERRIDE_HEADING = "## Naming overrides"
OVERRIDE_OFF = re.compile(r"^\s*N-BRANCH:\s*off\s*$")

DENY = """[branch-name-check] Refusing to create branch '{names}': no `branch` segment.

Naming rule N-BRANCH (~/.claude/CLAUDE.md -> "Naming"): form {form},
<type> one of {types} (Commit Convention).
Worktrees: pass that form as the EnterWorktree name (Claude Code adds `worktree-` and turns `/` into `+`).
Project override: a line `N-BRANCH: off` under `## Naming overrides` in {toplevel}/AGENTS.md.
"""
DENY_NOTE = (
    "Note: {toplevel}/AGENTS.md mentions N-BRANCH under Naming overrides, "
    "but only `N-BRANCH: off` is machine-readable.\n"
)


def newlines_to_separators(command):
    """Replace each newline outside quotes by ` ; ` (shlex treats a newline as a space)."""
    out, quote, i = [], "", 0
    while i < len(command):
        ch = command[i]
        if ch == "\\" and quote != "'":  # an escaped character, a newline included, is never a separator
            out.append(command[i:i + 2])
            i += 2
            continue
        if quote:
            if ch == quote:
                quote = ""
        elif ch in "'\"":
            quote = ch
        elif ch == "\n":
            out.append(" ; ")
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def segments(tokens):
    """Split a token list into the commands of one shell line."""
    cur = []
    for tok in tokens:
        if tok in SEPARATORS:
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


def option_value(args, short, long):
    """Value of the first option taking one: a letter of `short` (`-b x`, `-bx`, in a group `-qbx`)
    or a name of `long` (`--orphan x`, `--orphan=x`); else None."""
    for i, tok in enumerate(args):
        if tok == "--":
            return None
        if tok.startswith("--"):
            for flag in long:
                if tok == flag:
                    return args[i + 1] if i + 1 < len(args) else ""
                if tok.startswith(flag + "="):
                    return tok[len(flag) + 1:]
        elif tok.startswith("-"):
            for j, letter in enumerate(tok[1:], 1):  # a group of single-letter flags (git's getopt rule)
                if letter in short:
                    return tok[j + 1:] or (args[i + 1] if i + 1 < len(args) else "")
    return None


def expand_flags(args):
    """Flags as separate items: `-fm` -> `-f`, `-m`; a long flag loses its `=value`."""
    flags = []
    for tok in args:
        if tok.startswith("--"):
            flags.append(tok.split("=", 1)[0])
        elif tok.startswith("-"):
            flags.extend("-" + letter for letter in tok[1:])
    return flags


def branch_name(args):
    """New name from `git branch` arguments: create, move or copy; None when it only lists or edits."""
    end = args.index("--") if "--" in args else len(args)
    flags = expand_flags(args[:end])
    if any(f in BRANCH_NON_CREATING for f in flags):
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
    value = option_value(rest, "bB", ())
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
        return option_value(args, "bB", ("--orphan",))
    if sub == "switch":
        return option_value(args, "cC", ("--create", "--force-create", "--orphan"))
    if sub == "branch":
        return branch_name(args)
    if sub == "worktree":
        return worktree_name(args)
    return None


def offending_bash(command):
    """New branch names without the segment in a Bash command line."""
    if "git" not in command:
        return []
    lexer = shlex.shlex(newlines_to_separators(command), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""  # shlex.split() does the same: `#` is not a comment here
    try:
        tokens = list(lexer)
    except ValueError:
        return []
    names = []
    words, i = [], 0
    while i < len(tokens):
        if tokens[i] == "<<<":  # a here-string is the one following word: text, unchecked
            i += 2
        elif tokens[i] == "<<":  # a heredoc body follows on the next lines: text, unchecked
            break
        elif set(tokens[i]) <= set("<>&") and set(tokens[i]) & set("<>"):
            # a redirection (`>`, `2>&1`, `&>`): drop the operator, its target and the fd number
            if words and words[-1].isdigit():
                words.pop()
            i += 2
        else:
            words.append(tokens[i])
            i += 1
    for segment in segments(words):
        found = git_subcommand(segment)
        name = new_branch_name(*found) if found else None
        if name and not SEGMENT.search(name):
            names.append(name)
    return names


def offending_worktree(tool_input):
    """EnterWorktree: the name must carry the segment; `path` alone enters an existing worktree."""
    name = tool_input.get("name")
    if not name:
        return [] if tool_input.get("path") else ["<generated>"]
    return [] if SEGMENT.search(name) else [name]


def project_override(cwd):
    """(git toplevel of cwd, override is `off`, section mentions N-BRANCH) from AGENTS.md."""
    toplevel = cwd
    try:
        run = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if run.returncode == 0:
            toplevel = run.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        lines = Path(toplevel, "AGENTS.md").read_text(encoding="utf-8").splitlines()
    except (OSError, ValueError):
        return toplevel, False, False
    section, inside = [], False
    for line in lines:
        if line.startswith("## "):
            inside = line.rstrip() == OVERRIDE_HEADING
        elif inside:
            section.append(line)
    return (
        toplevel,
        any(OVERRIDE_OFF.match(line) for line in section),
        any("N-BRANCH" in line for line in section),
    )


def log_block(kind, names):
    """Append one record to the block journal; a write error never changes the verdict."""
    try:
        directory = os.path.expanduser("~/.claude/hook-stats")
        os.makedirs(directory, exist_ok=True)
        record = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "hook": "branch-name-check",
            "cwd": os.getcwd(),
            "kind": kind,
            "names": names,
        }
        with open(os.path.join(directory, "blocks.jsonl"), "a", encoding="utf-8") as journal:
            journal.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def main():
    try:
        data = json.load(sys.stdin)
        tool, tool_input = data["tool_name"], data["tool_input"]
        if tool == "Bash":
            kind = "bash-git"
            names = offending_bash(tool_input["command"])
        elif tool == "EnterWorktree":
            kind = "enter-worktree"
            names = offending_worktree(tool_input)
        else:
            return 0
        if not names:
            return 0
        toplevel, off, mentioned = project_override(data.get("cwd") or os.getcwd())
        if off:
            return 0
    except Exception:  # fail open on anything unexpected: only a verified name is denied
        return 0
    log_block(kind, names)
    message = DENY.format(names=", ".join(names), form=FORM, types=", ".join(TYPES), toplevel=toplevel)
    if mentioned:
        message += DENY_NOTE.format(toplevel=toplevel)
    sys.stderr.write(message)
    return 2


if __name__ == "__main__":
    sys.exit(main())
