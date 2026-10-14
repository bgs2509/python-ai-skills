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
#   - env: TASK_LEVELS_FILE (default: CLAUDE.md one level above this hook's directory,
#     i.e. <claude home>/CLAUDE.md, whatever CLAUDE_HOME the installer used)
#   - exit 0 always (advisory only)
#   - stdout: additionalContext JSON for do-feature when the section is found; empty otherwise

set -uo pipefail

FILE="${TASK_LEVELS_FILE:-$(dirname "$0")/../CLAUDE.md}"
SKILL=$(jq -r '.tool_input.skill // empty' 2>/dev/null) || exit 0
[ "$SKILL" = "do-feature" ] && [ -f "$FILE" ] && [ -r "$FILE" ] || exit 0

SECTION=$(awk '/^## /{inside = /^## Dev-project workflow/} inside' "$FILE" 2>/dev/null)
[ -n "$SECTION" ] || exit 0

jq -n --arg s "$SECTION" --arg f "$FILE" '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    additionalContext: ("Task levels from \($f) (the only copy). Check the task level against it before continuing:\n\n" + $s)
  }
}'
exit 0
