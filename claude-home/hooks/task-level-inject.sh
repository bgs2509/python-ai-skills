#!/bin/bash
# PreToolUse hook (matcher: Skill): when do-feature is invoked, inject the task-level
# table so the model checks that the task really needs it (bd python-ai-skills-ynt.4).
#
# The table lives only in the "Dev-project workflow" section of the global CLAUDE.md;
# this hook cuts that section at run time and keeps no copy. CLAUDE.md is read only
# at session start, so a session older than the table would still send every change
# through full do-feature — a hook fires in running sessions too (see
# delegation-pool-nudge.sh).
#
# Contract:
#   - stdin: JSON with .tool_input.skill
#   - env: TASK_LEVELS_FILE (default ~/.claude/CLAUDE.md)
#   - exit 0 always (advisory only)
#   - stdout: additionalContext JSON for do-feature when the section is found; empty otherwise

set -uo pipefail

[ -n "${TASK_LEVELS_FILE:-}${HOME:-}" ] || exit 0   # no override and no home: nothing to resolve
FILE="${TASK_LEVELS_FILE:-$HOME/.claude/CLAUDE.md}"
SKILL=$(jq -r '.tool_input.skill // empty' 2>/dev/null) || exit 0
[ "$SKILL" = "do-feature" ] && [ -r "$FILE" ] || exit 0

SECTION=$(awk '/^## /{inside = /^## Dev-project workflow/} inside' "$FILE")
[ -n "$SECTION" ] || exit 0

jq -n --arg s "$SECTION" --arg f "$FILE" '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    additionalContext: ("Task levels from \($f). Before running do-feature, confirm the task is level 1 (full mode) or level 2 (--lite) and announce Level N: <signal>; for levels 3-5 stop and use that procedure instead:\n\n" + $s)
  }
}'
exit 0
