#!/bin/bash
# Claude Code PostToolUse hook: regenerate XML when discovery.md/design.md is edited.
# Triggers on Edit/Write of docs/superpowers/specs/*-discovery.md or *-design.md.
# Receives tool-call JSON via stdin, extracts file_path, runs generator.

set -euo pipefail

INPUT="$(cat)"
FILE_PATH="$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)"

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

if [[ ! "$FILE_PATH" =~ docs/superpowers/specs/.*-(discovery|design)\.md$ ]]; then
  exit 0
fi

# Ascend to project root (directory containing .git)
PROJECT_ROOT="$(dirname "$FILE_PATH")"
while [ "$PROJECT_ROOT" != "/" ] && [ -n "$PROJECT_ROOT" ]; do
  if [ -d "$PROJECT_ROOT/.git" ]; then
    break
  fi
  PROJECT_ROOT="$(dirname "$PROJECT_ROOT")"
done

if [ -z "$PROJECT_ROOT" ] || [ "$PROJECT_ROOT" = "/" ]; then
  exit 0
fi

python3 "$HOME/.claude/scripts/generate_xml_from_md.py" --project-root "$PROJECT_ROOT" >&2 || true
exit 0
