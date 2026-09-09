#!/bin/bash
# PreToolUse hook (matcher: Read): soft, non-blocking token-saving nudge.
#
# When Read targets a file longer than BIG_READ_NUDGE_LINES (default 400) and
# the read is NOT already targeted (no offset / no limit), inject a reminder via
# hookSpecificOutput.additionalContext. The reminder nudges the model to either
# delegate whole-file comprehension to a sonnet subagent, or use grep / a
# targeted offset read for a single fact. Read STILL runs — this never blocks.
#
# Rationale: `rtk gain` shows file reads dominate token spend; this is the soft
# variant of Spotify's "shunt" (no Portal/AiKA dependency, no hard block, no
# loop risk). See bd python-ai-skills-xv1.
#
# Contract:
#   - stdin: JSON with tool_input.{file_path, offset?, limit?} (Read tool)
#   - exit 0 always (advisory only)
#   - stdout: additionalContext JSON only when nudging; empty otherwise
#   - PreToolUse stdout is NOT shown to the model, so plain echo would be
#     invisible — the reminder MUST be delivered as additionalContext JSON.

set -euo pipefail

THRESHOLD="${BIG_READ_NUDGE_LINES:-400}"

INPUT=$(cat)

# Parse file_path and whether the read is already targeted. Any parse error
# (malformed stdin, missing fields) degrades to silence — the hook must never
# crash a Read.
read -r FILE_PATH TARGETED <<EOF
$(echo "$INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print('')
    sys.exit(0)
ti = d.get('tool_input', {}) or {}
fp = ti.get('file_path', '') or ''
targeted = '1' if (ti.get('offset') is not None or ti.get('limit') is not None) else '0'
print(f'{fp}\t{targeted}')
" 2>/dev/null || echo "")
EOF

# Silent cases: no path, an already-targeted read, or a file we cannot stat.
[ -z "${FILE_PATH:-}" ] && exit 0
[ "${TARGETED:-0}" = "1" ] && exit 0
[ -f "$FILE_PATH" ] || exit 0

LINES=$(wc -l < "$FILE_PATH" 2>/dev/null || echo 0)
[ "$LINES" -gt "$THRESHOLD" ] || exit 0

# Emit the nudge as additionalContext (tool still runs).
REASON="This file has ${LINES} lines (> ${THRESHOLD}). To save tokens: if you need to understand the whole file, delegate the read to a sonnet subagent via Agent(model=\"sonnet\") and ask it to return only what matters for the current task; if you need a specific fact, use grep or a targeted Read with offset/limit instead of reading the whole file. Reading it in full is allowed but costs the full token price."

REASON="$REASON" python3 -c "
import json, os
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'additionalContext': os.environ['REASON'],
    }
}))
"
exit 0
