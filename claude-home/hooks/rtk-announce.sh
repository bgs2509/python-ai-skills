#!/usr/bin/env bash
# RTK announce hook — visible notification when RTK would rewrite the command.
# Runs alongside rtk-rewrite.sh but does not modify anything (passive observer).
#
# Claude Code PreToolUse hooks can emit {"systemMessage": "..."} to surface
# a user-visible notification without affecting permission decisions.

if ! command -v jq &>/dev/null || ! command -v rtk &>/dev/null; then
  exit 0
fi

# Version guard (mirrors rtk-rewrite.sh): rtk rewrite exists since 0.23.0.
# On an older binary the rewriter no-ops, so announcing would show garbage.
RTK_VERSION=$(rtk --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
if [ -n "$RTK_VERSION" ]; then
  MAJOR=$(echo "$RTK_VERSION" | cut -d. -f1)
  MINOR=$(echo "$RTK_VERSION" | cut -d. -f2)
  if [ "$MAJOR" -eq 0 ] && [ "$MINOR" -lt 23 ]; then
    exit 0
  fi
fi

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [ -z "$CMD" ]; then
  exit 0
fi

REWRITTEN=$(rtk rewrite "$CMD" 2>/dev/null)
EXIT_CODE=$?

# Only announce when RTK actually produces a different command (exit 0 with
# changed output, or exit 3 = ask). Silent for no-op or no-equivalent.
case "$EXIT_CODE" in
  0)
    [ "$CMD" = "$REWRITTEN" ] && exit 0
    ;;
  3) ;;
  *) exit 0 ;;
esac

jq -n --arg note "🔧 [rtk] $CMD  →  $REWRITTEN" '{systemMessage: $note}'
