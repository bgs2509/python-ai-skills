#!/bin/bash
# UserPromptSubmit hook: before every answer, re-send the "Questions and Numbers"
# section of the global CLAUDE.md (question header, numbers rule, two-score rule
# X% / Y%) as additionalContext (bd python-ai-skills-r1f.3).
#
# The rules live only in that section; this hook cuts it at run time and keeps no
# copy. CLAUDE.md is read only at session start, so a session older than the rule
# would never learn it — a hook fires in running sessions too (see
# task-level-inject.sh and delegation-pool-nudge.sh). No post-answer (Stop) check:
# it would make the model write a second message. A per-project glossary delivery
# (bd python-ai-skills-du5) may reuse this hook later; it is not built.
#
# Contract:
#   - stdin: JSON object (UserPromptSubmit input); the prompt text is not used
#   - env: QUESTION_MEMO_FILE (default: CLAUDE.md one level above this hook's directory,
#     i.e. <claude home>/CLAUDE.md, whatever CLAUDE_HOME the installer used)
#   - exit 0 always (advisory only; no decision field, nothing on stderr)
#   - stdout: additionalContext JSON when the section is found; empty otherwise
#     (stdin not a JSON object, file missing or unreadable, section absent)

set -uo pipefail

FILE="${QUESTION_MEMO_FILE:-$(dirname "$0")/../CLAUDE.md}"
jq -e 'type == "object"' >/dev/null 2>&1 || exit 0
[ -f "$FILE" ] && [ -r "$FILE" ] || exit 0

SECTION=$(awk '/^## /{inside = /^## Questions and Numbers/} inside' "$FILE" 2>/dev/null)
[ -n "$SECTION" ] || exit 0

jq -n --arg s "$SECTION" --arg f "$FILE" '{
  hookSpecificOutput: {
    hookEventName: "UserPromptSubmit",
    additionalContext: ("Rules for questions, numbers and option scores from \($f) (the only copy). Apply them to this answer:\n\n" + $s)
  }
}'
exit 0
