---
feature: git-finish-state
bd_id: python-ai-skills-8of.6
date: 2026-10-13
status: approved
risk: medium
open_questions: []
context7_verified: []
---

# Design: git-finish state probe (python-ai-skills-8of.6)

- D-1 `claude-home/scripts/git-finish-state.sh <dir> [--base B]` (bash, git, optional bd), key=value lines + three blocks.
- D-2 (revised after review) No sandbox exclusion; `git status --porcelain` stays a separate plain git call; remote state from `refs/remotes/origin/*` without network; linked worktree detected by `--git-dir` ≠ `--git-common-dir`.
- D-3 `git-finish/SKILL.md`: Phase 1.1 cross-check is the one call; Phase 2 takes its values from it (steps kept as the specification and fallback).
- D-4 Tests `claude-home/scripts/test_git_finish_state.py`: no-git, base without remote, branch in main clone, linked worktree, detached, --base override, remote ahead count, blocks present, writes nothing.
