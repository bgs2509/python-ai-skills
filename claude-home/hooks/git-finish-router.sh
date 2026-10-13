#!/bin/bash
# UserPromptSubmit hook: route a free-text "git finish" request to the git-finish skill.
#
# On 2026-10-13 a session asked to "выполнить git finish" invoked
# superpowers:finishing-a-development-branch instead: the request was plain
# text, not /git-finish, and the superpowers bootstrap pushes "invoke at 1%
# chance". That skill has no docs-and-plans phase, offers a Pull Request
# (against the Git Push Policy), does not push after a local merge and ends
# without a verdict.
#
# Why a hook and not a rule in CLAUDE.md: CLAUDE.md is read at session start,
# so running sessions never learn a new rule; this fires in every session at
# the moment the request arrives. Precedent: delegation-pool-nudge.sh.
#
# Contract:
#   - stdin: JSON with .prompt
#   - exit 0 always (advisory only)
#   - stdout: additionalContext JSON when the prompt asks for git finish in
#     free text; empty for /git-finish (already routed) and everything else

set -uo pipefail

INPUT=$(cat)

PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty' 2>/dev/null) || exit 0
[ -n "$PROMPT" ] || exit 0

# The slash command already selects the right skill.
case "$PROMPT" in /git-finish*) exit 0 ;; esac

echo "$PROMPT" | grep -qiE '(^|[^[:alnum:]_/-])(git|гит)[ -]?(finish|финиш)([^[:alnum:]_-]|$)' || exit 0

jq -n '{
  hookSpecificOutput: {
    hookEventName: "UserPromptSubmit",
    additionalContext: "The user asked for \"git finish\": invoke the git-finish skill (Skill tool, skill: \"git-finish\"). Do NOT invoke superpowers:finishing-a-development-branch — git-finish supersedes it in every repository: it updates docs and plans first, merges locally without offering a Pull Request, pushes last and ends with an uppercase verdict."
  }
}'
exit 0
