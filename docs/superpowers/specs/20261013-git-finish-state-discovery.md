---
feature: git-finish-state
bd_id: python-ai-skills-8of.6
date: 2026-10-13
status: approved
risk: medium
risk_justification: New read-only script, one sandbox exclusion in settings.json.template, git-finish SKILL.md text; git-finish runs at the end of most sessions, but the probe never writes.
evidence: strong
evidence_justification: 74 git-finish runs measured from transcripts - median 12 requests per run, median 399k context per request (341k at call); Phase 1.1 and Phase 2 issue 5-7 separate read-only git/bd calls; precedent of a sandbox-excluded runner (model-run.sh in settings.json.template).
open_questions: []
functional_requirements:
  - id: FR-1
    text: One call prints mode, branch, base, main_root, worktree, remote, branch_on_remote, ahead_of_origin, git status --porcelain, git log --oneline -20 and bd in_progress.
  - id: FR-2
    text: Base detection follows git-finish Phase 2 (explicit --base, origin/HEAD, main/master); a branch checked out in the main clone reports no removable worktree.
  - id: FR-3
    text: The script runs outside the Bash sandbox when called by path with an argument, so git status shows no sandbox mount points.
non_functional_requirements:
  - id: NFR-1
    text: Read-only (git --no-optional-locks), exit 0 always, works without bd on PATH and outside git.
  - id: NFR-2
    text: Effect re-measured with skill-stats.py after 7 days (requests per git-finish run).
constraints:
  - Phases 3-5 keep their one-command-per-call rule; only the read-only probing is merged.
---

# Discovery: git-finish state probe (python-ai-skills-8of.6, revision plan step 5)

git-finish runs when the session context is largest (median 341k at the call). Every tool round-trip
re-reads it: median 12 requests per run, ~4.8M tokens per run. The read-only cross-check (1.1) and mode
detection (2) are mechanical and can be one call.
