#!/bin/bash
# PreToolUse hook: block git commit --no-verify (and friends) without explicit
# user request. Pre-commit policy enforcement (see ~/.claude/CLAUDE.md
# "Pre-commit Policy").
#
# Hook contract:
#   - stdin: JSON with tool_input.command (Bash tool)
#   - exit 0: allow
#   - exit 2: block (stderr is shown to model)

set -euo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Append one JSONL record to the block journal for monthly review.
log_block() {  # $1 = kind
  KIND="$1" CMD="$COMMAND" python3 - <<'PY' 2>/dev/null || true
import datetime, json, os
d = os.path.expanduser("~/.claude/hook-stats")
os.makedirs(d, exist_ok=True)
rec = {
    "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "hook": "block-no-verify",
    "cwd": os.getcwd(),
    "kind": os.environ.get("KIND", ""),
    "command": os.environ.get("CMD", "")[:300],
}
with open(os.path.join(d, "blocks.jsonl"), "a", encoding="utf-8") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
PY
}

# Use shlex-aware token analysis: a bypass flag must appear as a standalone
# token (not as substring inside quoted argument like commit message body).
VERDICT=$(python3 - <<'PY' "$COMMAND"
import shlex, sys
cmd = sys.argv[1]
try:
    tokens = shlex.split(cmd, posix=True)
except ValueError:
    print("ALLOW"); sys.exit(0)

# One Bash line can chain several commands. Inspecting only the first `git`
# let `git add -A && git commit --no-verify` through: the subcommand read
# after that first `git` was `add`, so the whole line was allowed. Split on
# shell separators first, then inspect every command on the line.
SEPARATORS = {"&&", "||", ";", "|", "&"}


def segments(toks):
    cur = []
    for t in toks:
        if t in SEPARATORS:
            yield cur
            cur = []
            continue
        if t.endswith(";"):  # shlex keeps `;` glued to the previous word
            t = t.rstrip(";")
            if t:
                cur.append(t)
            yield cur
            cur = []
            continue
        cur.append(t)
    yield cur


def bypasses(toks):
    """True if this single command is a hook-bypassing git invocation."""
    takes_value = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
    for gi in (i for i, t in enumerate(toks) if t == "git"):
        # Find the subcommand, skipping git's global options (git -C <path>
        # commit, git -c k=v commit, ...) so a prefixed invocation cannot slip
        # past the subcommand check.
        i = gi + 1
        sub = None
        while i < len(toks):
            t = toks[i]
            if t in takes_value:
                i += 2
                continue
            if t.startswith("-"):
                i += 1
                continue
            sub = t
            break
        if sub not in {"commit", "merge", "rebase", "cherry-pick"}:
            continue

        # Look for bypass flags in remaining tokens, but skip values of
        # -m/--message. Short -n means --no-verify only for commit (for merge
        # it is --no-stat, for cherry-pick it is --no-commit — not bypasses).
        bypass = {"--no-verify", "--no-gpg-sign"}
        if sub == "commit":
            bypass.add("-n")
        i += 1
        while i < len(toks):
            t = toks[i]
            if t in {"-m", "--message", "-F", "--file"}:
                i += 2  # skip the value
                continue
            if t.startswith("--message=") or t.startswith("-m="):
                i += 1
                continue
            if t in bypass:
                return True
            i += 1
    return False


for seg in segments(tokens):
    if bypasses(seg):
        print("BLOCK_FLAG"); sys.exit(0)

# Also check SKIP=... env-var prefix (unparsed by shlex if env-syntax)
print("ALLOW")
PY
)

if [ "$VERDICT" = "BLOCK_FLAG" ]; then
  log_block "bypass-flag"
  cat >&2 <<'EOF'
[block-no-verify] Refusing to bypass commit hooks.

Pre-commit policy (see ~/.claude/CLAUDE.md → "Pre-commit Policy") forbids
bypass flags without explicit user request. Hook failure means a defect —
fix the underlying issue, do not skip.
EOF
  exit 2
fi

# Block env-var bypasses (matched on raw string before shlex):
# SKIP=hook skips individual hooks, PRE_COMMIT_ALLOW_NO_CONFIG bypasses the
# framework config requirement (both named in CLAUDE.md → Pre-commit Policy).
if echo "$COMMAND" | grep -qE '(^|[[:space:]])(SKIP=[^[:space:]]+|PRE_COMMIT_ALLOW_NO_CONFIG=[^[:space:]]+)[[:space:]].*(git[[:space:]].*commit|pre-commit)'; then
  log_block "env-bypass"
  cat >&2 <<'EOF'
[block-no-verify] Refusing to bypass via SKIP=... env var.

Pre-commit policy forbids skipping individual hooks without explicit
user request. Fix the failing check rather than bypass it.
EOF
  exit 2
fi

exit 0
