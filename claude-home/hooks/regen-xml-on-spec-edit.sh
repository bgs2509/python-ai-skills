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

# Only absolute paths can be ascended reliably (a relative path outside a
# git tree would loop forever: dirname "." is "."). Edit/Write pass absolute
# paths; anything else is skipped.
case "$FILE_PATH" in
  /*) ;;
  *) exit 0 ;;
esac

# Ascend to project root (directory containing .git, either a real repo
# directory or a git-worktree ".git" file — must stop at the worktree's own
# root, not ascend past it into a parent checkout).
PROJECT_ROOT="$(dirname "$FILE_PATH")"
while [ "$PROJECT_ROOT" != "/" ] && [ "$PROJECT_ROOT" != "." ] && [ -n "$PROJECT_ROOT" ]; do
  if [ -e "$PROJECT_ROOT/.git" ]; then
    break
  fi
  PROJECT_ROOT="$(dirname "$PROJECT_ROOT")"
done

if [ -z "$PROJECT_ROOT" ] || [ "$PROJECT_ROOT" = "/" ] || [ "$PROJECT_ROOT" = "." ]; then
  exit 0
fi

# A project that ships its own generator owns its XML format. Sensedar (bd
# Sensedar-be97) has scripts/md_to_xml.py wired into its pre-commit hook, and
# this hook's generator writes a different, much larger frontmatter-derived
# format: on 2026-08-04 its output was committed once and grew
# requirements.xml from 724 to 8178 lines, after which the repo no longer
# reproduced its own committed artifacts (running the committed generator
# produced a 14,917-line diff). Prefer the project's generator wherever one
# exists (the project's own tooling, same trust level as its pre-commit
# hooks); fall back to the personal one only for projects that have none.
# Failures are surfaced via exit 2 (stderr reaches the model) — a silent
# "|| true" here once masked a generator that needed CLI arguments.
if [ -f "$PROJECT_ROOT/scripts/md_to_xml.py" ]; then
  if ! ( cd "$PROJECT_ROOT" && python3 scripts/md_to_xml.py >&2 ); then
    echo "[regen-xml] project generator scripts/md_to_xml.py failed in $PROJECT_ROOT — regenerate the XML manually" >&2
    exit 2
  fi
  exit 0
fi

if ! python3 "$HOME/.claude/scripts/generate_xml_from_md.py" --project-root "$PROJECT_ROOT" >&2; then
  echo "[regen-xml] generate_xml_from_md.py failed for $PROJECT_ROOT — regenerate the XML manually" >&2
  exit 2
fi
exit 0
