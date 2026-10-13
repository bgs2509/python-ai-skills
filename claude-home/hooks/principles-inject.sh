#!/bin/bash
# PreToolUse hook (matcher: Skill): inject the code principles into skills that
# plan, write or review code (bd python-ai-skills-5io).
#
# The principles live in one file, _code-quality/principles.md. A pointer inside
# each skill reaches only skills this repo owns and only when the model follows
# it; superpowers skills (brainstorming, writing-plans, TDD) cannot be edited at
# all. A hook fires on every listed invocation, in already-running sessions too —
# CLAUDE.md is read only at session start (see delegation-pool-nudge.sh).
#
# The skill list below is the only list of injection targets; the guard test
# test_principles_ssot.py checks that every repo skill named here exists.
#
# Contract:
#   - stdin: JSON with .tool_input.skill
#   - env: PRINCIPLES_FILE (default ~/.claude/skills/_code-quality/principles.md)
#   - exit 0 always (advisory only)
#   - stdout: additionalContext JSON for a listed skill with a readable file; empty otherwise

set -uo pipefail

SKILLS=(
  do-feature do-autopilot do-multiagent pipeline
  grace-plan grace-execute grace-multiagent-execute grace-fix grace-refactor grace-reviewer
  best-research best-approach best-rank best-questions audit-loop full-audit _testing
  simplify code-review
  superpowers:brainstorming superpowers:writing-plans superpowers:executing-plans
  superpowers:subagent-driven-development superpowers:test-driven-development
  superpowers:requesting-code-review superpowers:receiving-code-review
  superpowers:systematic-debugging
)

FILE="${PRINCIPLES_FILE:-${HOME:-}/.claude/skills/_code-quality/principles.md}"
SKILL=$(jq -r '.tool_input.skill // empty' 2>/dev/null) || exit 0
[ -n "$SKILL" ] && [ -r "$FILE" ] || exit 0

for s in "${SKILLS[@]}"; do
  [ "$s" = "$SKILL" ] || continue
  jq -n --rawfile p "$FILE" --arg f "$FILE" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      additionalContext: ("Code principles from \($f) (the single source of truth for programming principles) bind the work of this skill. Apply KISS and YAGNI first and run the excess-code check on every plan and diff:\n\n" + $p)
    }
  }'
  exit 0
done
exit 0
