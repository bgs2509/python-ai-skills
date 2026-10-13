#!/bin/bash
# PreToolUse hook (matcher: Skill): deny superpowers:finishing-a-development-branch.
#
# git-finish supersedes it in every repository. git-finish-router.sh steers a
# user's free-text "git finish", but superpowers subagent-driven-development and
# executing-plans chain into the superpowers finish skill on their own, where no
# prompt hook can see it. That skill offers a Pull Request (against the Git Push
# Policy), never pushes after a local merge and ends without a verdict
# (tg-video-downloader incident, 2026-10-13; bd python-ai-skills-blc).
#
# A permissions rule `Skill(...)` would deny it too, but silently — the model
# would not learn where to go instead. permissionDecisionReason tells it.
#
# Contract:
#   - stdin: JSON with .tool_input.skill (field name verified in transcript
#     3e591694: {"skill": "superpowers:finishing-a-development-branch"})
#   - exit 0 always
#   - stdout: deny JSON for exactly that skill; empty otherwise

set -uo pipefail

SKILL=$(jq -r '.tool_input.skill // empty' 2>/dev/null) || exit 0
[ "$SKILL" = "superpowers:finishing-a-development-branch" ] || exit 0

jq -n '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: "superpowers:finishing-a-development-branch is replaced by the git-finish skill in every repository. Invoke the Skill tool with skill: \"git-finish\" instead: it updates docs and plans first, merges locally without offering a Pull Request, pushes last and ends with an uppercase verdict."
  }
}'
exit 0
