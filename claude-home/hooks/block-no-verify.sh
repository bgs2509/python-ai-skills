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

# Use shlex-aware token analysis: a bypass flag must appear as a standalone
# token (not as substring inside quoted argument like commit message body).
VERDICT=$(python3 - <<'PY' "$COMMAND"
import shlex, sys
cmd = sys.argv[1]
try:
    tokens = shlex.split(cmd, posix=True)
except ValueError:
    print("ALLOW"); sys.exit(0)

# Find git subcommand
if "git" not in tokens:
    print("ALLOW"); sys.exit(0)
gi = tokens.index("git")
if gi + 1 >= len(tokens):
    print("ALLOW"); sys.exit(0)
sub = tokens[gi + 1]
if sub not in {"commit", "merge", "rebase", "cherry-pick"}:
    print("ALLOW"); sys.exit(0)

# Look for bypass flags in remaining tokens, but skip values of -m/--message
bypass = {"--no-verify", "--no-gpg-sign"}
i = gi + 2
while i < len(tokens):
    t = tokens[i]
    if t in {"-m", "--message", "-F", "--file"}:
        i += 2  # skip the value
        continue
    if t.startswith("--message=") or t.startswith("-m="):
        i += 1
        continue
    if t in bypass:
        print("BLOCK_FLAG"); sys.exit(0)
    i += 1

# Also check SKIP=... env-var prefix (unparsed by shlex if env-syntax)
print("ALLOW")
PY
)

if [ "$VERDICT" = "BLOCK_FLAG" ]; then
  cat >&2 <<'EOF'
[block-no-verify] Refusing to bypass commit hooks.

Pre-commit policy (see ~/.claude/CLAUDE.md → "Pre-commit Policy") forbids
bypass flags without explicit user request. Hook failure means a defect —
fix the underlying issue, do not skip.
EOF
  exit 2
fi

# Block SKIP=... env var bypass (matched on raw string before shlex)
if echo "$COMMAND" | grep -qE '(^|[[:space:]])SKIP=[^[:space:]]+[[:space:]]+(git[[:space:]]+commit|pre-commit)\b'; then
  cat >&2 <<'EOF'
[block-no-verify] Refusing to bypass via SKIP=... env var.

Pre-commit policy forbids skipping individual hooks without explicit
user request. Fix the failing check rather than bypass it.
EOF
  exit 2
fi

exit 0
