#!/usr/bin/env bash
# PreToolUse(Bash) gate in front of an RTK hook: no RTK rewriting of git inside
# a linked worktree.
#
# A background session isolated in a worktree has its git commands vetted by
# the harness, which refuses `rtk git ...` ("runs rtk with a git command among
# its operands"). Observed 2026-10-13 in tg-video-downloader: every rewritten
# git call was refused and the model fell back to /usr/bin/git. Wrapping here
# instead of editing rtk-rewrite.sh keeps that file byte-identical to what
# `rtk` ships and checks against .rtk-hook.sha256.
#
# Usage: rtk-isolation-gate.sh <hook-file-in-this-dir>
#   - stdin: the PreToolUse JSON (.cwd, .tool_input.command)
#   - git command + cwd inside a linked worktree -> exit 0, no output
#     (the command runs unchanged; plain git is what the harness accepts)
#   - anything else -> the wrapped hook gets the same stdin, its output and
#     exit code pass through unchanged
#
# Detection is deliberately coarse: any linked worktree, not only harness-
# isolated sessions. Outside an isolated session it costs only the token
# savings on git output.

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$HOOK_DIR/${1:?usage: rtk-isolation-gate.sh <hook>}"

INPUT=$(cat)

skip() {
  command -v jq &>/dev/null || return 1
  local cmd cwd git_dir common_dir
  cmd=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
  # git as a word of its own: start of command or after a separator/space.
  echo "$cmd" | grep -qE '(^|[;&|( ])git( |$)' || return 1
  cwd=$(echo "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)
  [ -n "$cwd" ] || cwd=$PWD
  git_dir=$(git -C "$cwd" rev-parse --path-format=absolute --git-dir 2>/dev/null) || return 1
  common_dir=$(git -C "$cwd" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || return 1
  [ "$git_dir" != "$common_dir" ]
}

skip && exit 0

printf '%s' "$INPUT" | "$TARGET"
