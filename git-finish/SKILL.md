---
name: git-finish
description: >
  Finish the CURRENT branch in a fixed order: update the documentation the work
  invalidated, merge into the base branch locally (resolving conflicts), delete the
  branch and its worktree, and only then push. The order is the contract — pushing
  first would publish a state that still has to be cleaned up afterwards.
  TRIGGER when: user calls /git-finish, the work on this branch is done and the user
  says "слей ветку", "заверши ветку", "merge and push", "finish this branch", or asks
  for the merge-then-delete-then-push sequence in any wording.
  SKIP when: only committing uncommitted files (use /git-commit), triaging ALL branches
  in the repo rather than finishing this one (use /git-branch), syncing a repo across
  machines (use /project-sync), syncing bd issues (use /beads-sync).
argument-hint: "[--base <branch> to override detection] [--no-push to stop after cleanup] [--keep-branch to merge without deleting]"
---

# /git-finish — Finish the current branch

> **Docs → merge → delete → push.** One branch, one fixed order, push last.
> Worker/utility skill: it does NOT auto-transition to other skills.

## Why the order is the contract

Push last, so the remote only ever receives a state that is already merged, already
verified and already cleaned up. Pushing the feature branch first inverts this: the
remote gains a branch that must be deleted later, and a half-finished branch on the
remote is what other machines will pull.

**Calling this skill IS the explicit push authorization** the global Git Push Policy
requires. Nothing else in this skill grants it: `--no-push` stops before Phase 5, and
a failure in any earlier phase stops the run with nothing pushed.

## Phase 1: Preconditions (read-only)

1. `git rev-parse --is-inside-work-tree` — not a repo → stop.
2. `git branch --show-current` — this is the branch being finished.
   - Empty (detached HEAD) → stop: there is no branch to finish.
   - Equal to the base branch → stop: "already on <base>, nothing to finish".
3. **Detect the base branch.** Do NOT trust `origin/HEAD` alone — in a repo where it
   was never configured, `git rev-parse --abbrev-ref origin/HEAD` exits non-zero and
   prints the literal string `origin/HEAD`, and `git symbolic-ref --short
   refs/remotes/origin/HEAD` fails with "is not a symbolic ref". Both were observed in
   this very repository. Detection order:
   ```bash
   BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')
   [ -z "$BASE" ] && for b in main master; do
       git show-ref --verify --quiet "refs/heads/$b" && BASE=$b && break
   done
   ```
   Still empty, or `--base` was passed → use the argument; otherwise ask. Never hardcode
   `master`: the user may say "master" while the repo's base branch is `main`.
4. `git status --porcelain` — uncommitted changes. Documentation edits are expected in
   Phase 2; unrelated changes → report them and ask before proceeding.
5. **Report the plan** — base branch, branch being finished, whether a worktree will be
   removed, whether the branch also exists on the remote. Then proceed.

## Phase 2: Update the documentation

Run BEFORE the merge, so the documentation change is part of the branch's own history
rather than an orphan commit on the base branch.

1. **See what the branch actually changed:** `git diff --stat $BASE...HEAD`.
2. **Update what that invalidates.** In this repo that is at minimum:
   - `CHANGELOG.md` — an entry under `## [Unreleased]`, in the right subsection
     (Added / Changed / Fixed / Removed), per Keep a Changelog.
   - `CLAUDE.md` — skill catalog rows, grouped lists and **counters**.
   - `claude-home/CLAUDE.md` — the global counters, when the skill set changed.
3. **Verify every counter against the filesystem, never against the old number:**
   ```bash
   find . -maxdepth 2 -name SKILL.md -not -path './.git/*' | wc -l
   ```
   A counter is a claim about the repo; check it the way a reader would.
4. Commit on the branch, conventional commit message, hooks NOT bypassed.

**If nothing is stale, say so explicitly** and move on. Silence is indistinguishable
from having skipped the phase.

## Phase 3: Merge into the base locally

```bash
git checkout "$BASE"
git pull --ff-only          # skip when there is no remote
git merge --no-ff --no-commit <branch>
```

`--no-commit` leaves the merge open so conflicts are resolved and inspected before
anything is recorded.

**On conflict — resolve, never abandon:**

1. `git diff --name-only --diff-filter=U` — the conflicting files.
2. **Append-only files (`CHANGELOG.md` is the usual one): keep BOTH sides.** Two
   branches adding entries to the same `### Added` section is not a disagreement —
   each entry describes work that genuinely happened. Deleting either loses history.
3. Real semantic conflicts: resolve on the merits, and say in the report which side won
   and why.
4. Verify no markers survive: `grep -n '^<<<<<<<\|^=======$\|^>>>>>>>' <file>`.
5. `git add <files>` and commit the merge with a message that states *why* the branch
   existed, not just that it was merged.

**Then verify the merged result** — the tree about to be published is a tree no test has
ever run on:

```bash
grep -q '^test:' Makefile && make test    # or pytest / npm test / cargo test
```

**Red tests → STOP.** Leave the branch and the worktree in place and investigate.
Nothing has been pushed, so the whole state is local and recoverable.

## Phase 4: Delete the branch and its worktree

Order matters: the worktree goes first — a branch checked out in a worktree cannot be
deleted — and worktree removal must run from outside that worktree.

```bash
WT=$(rtk proxy git worktree list --porcelain | awk -v b="refs/heads/<branch>" \
    '/^worktree /{p=$2} /^branch /{if ($2==b) print p}')
MAIN_ROOT=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
```

> **Two traps here, both hit in practice.**
>
> 1. **A path is not proof of a separate worktree.** When the branch is simply checked
>    out in the main clone, this lookup returns the main repository root — and acting on
>    it means trying to delete the workspace you are standing in. Always compare:
>    `[ "$WT" = "$MAIN_ROOT" ]` means there is no worktree to remove. Only a path
>    *different* from `MAIN_ROOT` is a removable worktree.
> 2. **Under the RTK hook the parse silently returns nothing** — the hook rewrites
>    `git worktree list` and reshapes its output, so `--porcelain` is no longer
>    porcelain. Verified in this repo: the pipeline yields the path only through
>    `rtk proxy`. Machine-parsing git output goes through `rtk proxy`, exactly as
>    `RTK.md` requires for `diff`.

1. `$WT` empty or equal to `$MAIN_ROOT` → no worktree to remove, go to step 2.
   Otherwise `cd "$MAIN_ROOT"`, then `git worktree remove "$WT"` and `git worktree prune`.
   Refuses because of local changes → STOP and report; never `--force` on your own.
2. `git branch -d <branch>` — lowercase `-d` only. It refuses anything unmerged, which
   is the safety check. A refusal means the merge did not land — investigate, never
   reach for `-D`.
3. Branch also on the remote → deleting it there is a push. Ask first, then
   `git push origin --delete <branch>`.

## Phase 5: Push, last

```bash
git push origin "$BASE"
```

Then **verify from three sources**, because the push command's own output is the one
thing that cannot confirm itself:

```bash
git rev-parse "$BASE"; git rev-parse "origin/$BASE"; git ls-remote origin "refs/heads/$BASE"
```

All three must be the same hash. `git ls-remote` is the only one that asks the server.

**Rejected push → investigate.** A rejection means the remote moved; force-pushing is
never this skill's decision.

## Quick reference

1. **Phase 1** — preconditions, base-branch detection, plan reported.
2. **Phase 2** — documentation updated on the branch, counters verified against files.
3. **Phase 3** — `--no-ff` merge into base, conflicts resolved, tests green.
4. **Phase 4** — worktree removed, branch deleted with `-d`.
5. **Phase 5** — push, then three-source hash verification.

Stop conditions, at any phase: red tests, a `-d` refusal, a rejected push, a worktree
that refuses to go, unrelated uncommitted changes.

## Common mistakes

| Mistake | Why it bites |
|---|---|
| Pushing the branch first "to be safe" | The remote gains a branch that must be cleaned up later, and other machines pull the half-finished state. Push last. |
| Trusting `origin/HEAD` to name the base branch | Unconfigured in this repo: one form exits non-zero printing `origin/HEAD`, the other fails with "is not a symbolic ref". Always keep the `show-ref` fallback. |
| Taking the user's word "master" literally | This repo's base branch is `main`. Detect it; do not transcribe it from the request. |
| Resolving a `CHANGELOG.md` conflict by picking one side | Both entries describe work that happened. Append-only files keep both. |
| Skipping tests because they were green on the branch | The merged tree is a tree nothing has tested yet. |
| `git branch -D` when `-d` refuses | `-d` refusing IS the safety check reporting an unmerged branch. |
| Parsing `git worktree list --porcelain` under the RTK hook | The hook reshapes the output and the parse returns nothing. Use `rtk proxy`. |
| Treating the path the worktree lookup returns as a removable worktree | For a branch checked out in the main clone the lookup returns the repository root itself — acting on it means deleting the workspace you are standing in. Compare against `MAIN_ROOT` first. |
| Leaving a branch unmerged because "it is just a skill" | A skill directory that exists only on a branch leaves the symlink installer pointing at a path that is not there — exactly how `progress-watch` produced two dangling links. |
| Reporting "done" from the push command's output | It is condensed by the hook. Compare hashes, including `git ls-remote`. |
