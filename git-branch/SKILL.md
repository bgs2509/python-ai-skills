---
name: git-branch
description: >
  Discover ALL branches in the repo and triage each one: which are actively in use
  (current HEAD or checked out in another worktree/session — never touch), which are
  merged into the default branch (safe to delete), which are unmerged and abandoned
  (with how long ago), and which are junk. Report-first, then delete only after
  explicit confirmation. TRIGGER when: user calls /git-branch, user wants to clean up
  / triage / audit branches, user says "what branches can I delete", "clean up
  branches", "which branches are stale/merged/abandoned". SKIP when: committing
  changes (use /git-commit), pushing/syncing across machines (use /project-sync),
  syncing bd issues (use /beads-sync).
argument-hint: "[--report to diagnose only, never delete] [--stale-days N (default 30)] [--include-remote to also report remote-tracking branches]"
---

# /git-branch — Branch Triage & Cleanup

> Find every branch, classify what to do with each, and delete safely — after confirmation.
> **Report-first, destructive-last.** This skill is a worker/utility: it does NOT auto-transition to other skills.

## Phase 1: Collect Data

Run these read-only commands in parallel:

1. `git rev-parse --is-inside-work-tree` — confirm we are in a git repo (else stop: "Not a git repository").
2. `git branch --show-current` — the current HEAD branch (**protected**).
3. Default branch:
   `git rev-parse --abbrev-ref origin/HEAD 2>/dev/null | sed 's#^origin/##'`
   Treat an **empty result OR the literal `HEAD`** as "not set" (the latter happens
   when `origin/HEAD` is unconfigured) → fall back to whichever of `main` / `master`
   exists (**protected**). Tip: `git remote set-head origin -a` records `origin/HEAD`
   so future runs resolve it directly.
4. `git worktree list --porcelain` — branches checked out in OTHER worktrees are **occupied by another session** (this is the only reliable "in use elsewhere" signal — see Rules).
5. All local branches with metadata:
   ```bash
   git for-each-ref \
     --format='%(refname:short)|%(committerdate:relative)|%(committerdate:iso8601)|%(upstream:short)|%(upstream:track)|%(authorname)' \
     refs/heads/
   ```
6. Merged into the default branch: `git branch --merged <default>`
7. Not merged into the default branch: `git branch --no-merged <default>`
8. `git status --porcelain` — if the working tree is dirty, note it (the current branch has uncommitted work; suggest `/git-commit` first, but do not block triage of OTHER branches).

Only if `--include-remote` was passed, also collect (report-only, never auto-delete):
- `git branch -r` and `git remote prune origin --dry-run` — stale remote-tracking refs.

If there is only one branch (the default) — say "Only the default branch exists, nothing to triage" and stop.

## Phase 2: Classify Each Branch

Assign every local branch to exactly ONE category. Evaluate in this priority order (first match wins):

1. **🔒 Protected / active** — NEVER delete, NEVER suggest deleting:
   - the default branch (`main`/`master`),
   - the current HEAD branch,
   - any branch listed in `git worktree list` (checked out in another worktree = **occupied by an adjacent session**).

2. **⚠️ Likely-active (hypothesis)** — unmerged AND last commit within the recency window (default: < 7 days), OR has unpushed commits (`upstream:track` shows `[ahead N]` or no upstream at all with local-only commits). Treat as *probably someone's in-progress work*. **Do not delete by default**; flag as a hypothesis (see Rules — recency is a proxy, not proof).

3. **✅ Merged (safe to delete)** — appears in `git branch --merged <default>` and is not Protected. Its work is already in the default branch → deletable with `git branch -d` (which itself refuses if not truly merged).

4. **🗑️ Junk** — name matches a throwaway pattern (`tmp/*`, `temp/*`, `test-*`, `wip/*`, `scratch/*`, `experiment/*`, `backup/*`, or trailing `-old`/`-bak`) AND last commit older than `--stale-days` (default 30) AND unmerged. Candidate for force-delete, but ask.

5. **💤 Abandoned** — unmerged, not junk-named, last commit older than `--stale-days` (default 30). Report age; candidate for deletion after the user confirms the work is not needed.

Each branch also carries: **age** (relative + absolute of last commit), **merged?**, **ahead/behind upstream**, and **unpushed?** (data-loss risk flag).

## Phase 3: Report

Present a grouped, list-based report (no tables — Telegram/terminal friendly). Example:

```
## Branch Triage — <repo> (default: main)

🔒 Protected / active (untouchable)
  - main                 (default)
  - feat/x-parser        (current HEAD, dirty: 3 uncommitted files)
  - feat/y-api           (checked out in worktree ../wt-y — ADJACENT SESSION)

✅ Merged into main (safe to delete)
  - chore/centralize-settings-hooks   merged • last commit 5 days ago
  - fix/login-typo                    merged • last commit 3 weeks ago

💤 Abandoned (unmerged, > 30d — confirm before delete)
  - feat/old-dashboard   last commit 4 months ago • 12 ahead / 40 behind • ⚠️ 12 unpushed commits (data loss if deleted)

🗑️ Junk (throwaway name + stale — force-delete on confirm)
  - tmp/quick-test       last commit 2 months ago • unmerged

⚠️ Likely-active (HYPOTHESIS — recency proxy, NOT confirmed occupied)
  - feat/z-refactor      last commit 2 days ago • 4 unpushed commits — probably in progress, left untouched
```

Then propose actions and ask via `AskUserQuestion` (multiSelect):
- **Q1 "Which branches to DELETE?"** — offer ONLY 🗑️ Junk, 💤 Abandoned, and ✅ Merged. Pre-recommend ✅ Merged (lowest risk). Never list Protected or Likely-active as delete options.
- For any selected branch that has **unpushed commits**, warn explicitly and require a second confirmation before force-deleting.

If `--report` was passed — stop here (diagnose-only, never delete).

## Phase 4: Execute (only after confirmation)

For each confirmed branch:

- **Merged** → `git branch -d <branch>` (safe; refuses if not merged — if it refuses, re-report, do not silently force).
- **Junk / Abandoned** confirmed for deletion → `git branch -d <branch>`; only if that refuses AND the user explicitly approved force → `git branch -D <branch>`.
- **Remote branches** (`--include-remote`) → do NOT delete automatically. Report the exact command (`git push origin --delete <branch>`) for the user to run — remote deletion is an external, irreversible push (see Rules).

After execution, show a summary:
```
Deleted N branches:
  ✓ chore/centralize-settings-hooks (merged)
  ✓ tmp/quick-test (junk, forced)
Kept: <protected + likely-active + declined>
Remote deletions to run manually: git push origin --delete <branch>   (if any)
```

## Rules

1. **NEVER delete a protected branch** — default (`main`/`master`), current HEAD, or any worktree-checked-out branch. These are hard exclusions from every delete list.
2. **Worktree = the only proof of "occupied elsewhere"** — `git worktree list` reliably shows branches held by other sessions. Recency of commits is a *proxy*, not proof: **always label a "likely-active" verdict as a hypothesis**, never auto-delete on recency alone.
3. **Report-first** — always show the full triage report and get explicit confirmation before ANY deletion.
4. **Unpushed commits = data-loss risk** — a branch with local-only commits (`[ahead N]` or no upstream) requires an explicit second confirmation before force-delete.
5. **Prefer `-d` over `-D`** — use the safe delete first; force (`-D`) only with explicit per-branch user approval.
6. **Never `git push`** — including `--delete` of remote branches. Only report the command for the user to run (respects the global Git Push Policy).
7. **Local-only by default** — `--include-remote` upgrades reporting only, never auto-deletion of remote refs.
8. **Deterministic classification** — every branch lands in exactly one category via the Phase-2 priority order; if signals are ambiguous, downgrade to the *safer* (keep) category and say why.
9. **Not a commit tool** — if the current branch is dirty, point to `/git-commit`; do not commit here.
10. **No auto-transition** — worker/utility skill; return control to the user after triage.
