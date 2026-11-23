---
name: git-finish
description: >
  Close the work of the CURRENT SESSION. First, unconditionally and in any repository
  state, update the documentation the session invalidated and bring the session's plans
  up to date (plan files, bd issues, the harness task list). Then, depending on where
  HEAD is: on a work branch — merge into the base branch locally (resolving conflicts),
  delete the branch and its worktree, and push last; on the base branch — push; outside
  git — nothing. Always end with an uppercase verdict line stating whether the session's
  work is finished. TRIGGER when: user calls /git-finish, says "закрой сессию",
  "заверши работу в сессии", "слей ветку", "заверши ветку", "merge and push",
  "finish this branch", "wrap up the session", "git finish", "гит финиш", or asks for
  this sequence in any wording. Supersedes superpowers:finishing-a-development-branch in
  every repository — never invoke that skill for these requests. SKIP when: only committing uncommitted files (use /git-commit), triaging ALL branches
  in the repo rather than closing this session (use /git-branch), syncing a repo across
  machines (use /project-sync), syncing bd issues (use /beads-sync).
argument-hint: "[--base <branch> to override detection] [--no-push to stop after cleanup] [--keep-branch to merge without deleting]"
---

# /git-finish — Close the work of the current session

> **Docs and plans → merge → delete → push → verdict.** Docs and plans always run, and
> always first. The verdict is always the last line.
> Worker/utility skill: it does NOT auto-transition to other skills.

## The two guarantees

1. **Phase 1 runs under any conditions.** Base branch, detached HEAD, dirty tree, not a
   git repository at all, any flag — the documentation and the plans are brought up to
   date before anything else is looked at. No precondition, flag or later stop condition
   skips it. A session that ends with stale plans leaves the next session to act on a
   description of work that no longer matches the code.
2. **The run ends with an uppercase verdict** (Phase 6) — on success AND on every stop.
   A run that stops without a verdict looks the same as a run that was cut off.

## Why the order is the contract

Docs first, so the documentation change is part of the history that gets merged and
pushed, not an orphan commit made afterwards. Push last, so the remote only ever receives
a state that is already merged, already verified and already cleaned up. Pushing the
work branch first inverts this: the remote gains a branch that must be deleted later, and
a half-finished branch on the remote is what other machines will pull.

**Calling this skill IS the explicit push authorization** the global Git Push Policy
requires. Nothing else in this skill grants it: `--no-push` stops before Phase 5, and a
failure in any earlier phase stops the run with nothing pushed.

## Phase 1: Documentation and plans (ALWAYS, FIRST)

### 1.1 Inventory what the session did

The session is the source, git is the cross-check. Collect from the conversation:

1. Files created, edited or deleted, and the commits made.
2. Plans written or followed — plan files (`docs/superpowers/plans/*.md`, `plan.md`,
   `docs/development-plan.xml`, specs), with the step the session reached in each.
3. bd issues created, claimed, worked on or discovered.
4. The harness task list, if one was used (`TaskList`).

Cross-check against the repository with **two** calls — together they also answer all of
Phase 2:

```bash
~/.claude/scripts/git-finish-state.sh .            # add --base <branch> when given
```
```bash
git status --porcelain
```

The script prints `mode` (`no-git` / `detached` / `unknown-base` / `base` / `branch`),
`branch`, `base`, `main_root`, `worktree` (empty unless the branch lives in a linked
worktree), `remote`, `branch_on_remote`, `ahead_of_origin`, any `error=` lines, then
`git log --oneline -20` and `bd list --status=in_progress`. It runs inside the Bash
sandbox and never touches the network, so the remote fields reflect the last fetch, and
it leaves out `git status`, which inside the sandbox lists the sandbox's mount points as
untracked files — hence the second, plain `git status` call (git runs outside the sandbox
as its own command). `ahead_of_origin` is a preview only: Phase 1.4 may add commits, and
Phase 5 recounts before pushing. Every separate call at the end of a long session
re-reads the whole context (measured 2026-10-13: 12 requests per run at ~400k tokens
each), so do not repeat what these two calls already returned.

Uncommitted changes split in two. **Changes this session made** are part of closing it:
commit them in Phase 1.4, in logical conventional commits, after the check that proves
them (tests, linter). **Changes this session did not make** (another session sharing the
checkout) are never committed here — list them in the report and leave them alone.

### 1.2 Update the documentation the session invalidated

In this repo that is at minimum:

- `CHANGELOG.md` — an entry under `## [Unreleased]`, in the right subsection
  (Added / Changed / Fixed / Removed), per Keep a Changelog.
- `AGENTS.md` — skill catalog rows, grouped lists and **counters** (`CLAUDE.md` is a symlink to it; Edit refuses the link).
- `claude-home/CLAUDE.md` — the global counters, when the skill set changed.
- `README.md` and any doc that describes behavior the session changed.

In another project, apply the same test: which document now states something the code
no longer does. In a GRACE project whose module boundaries changed, say in the report
that `grace-refresh` is due — this skill does not run it (no auto-transition).

**Verify every counter against the filesystem, never against the old number:**

```bash
find . -maxdepth 2 -name SKILL.md -not -path './.git/*' | wc -l
```

### 1.3 Bring the session's plans up to date

1. **Plan files** — mark the steps the session completed as done; for a step done
   differently than planned, write "deviated, see commit `<hash>`" (global SSoT drift
   rule: execution drift → the commit wins); leave unfinished steps open and visible.
2. **bd** — `bd close <id> --reason="..."` for finished issues; `bd update <id>
   --notes="..."` for issues still in progress, with where the work stopped;
   `bd create` for every leftover the session found but did not do.
3. **Harness task list** — it is a within-session scratchpad and records nothing; any
   task still open in it that must outlive the session goes into bd.

### 1.4 Commit and report

Commit on the current branch with a conventional message (`docs(<scope>): ...`), hooks
NOT bypassed. Outside a git repo nothing is committed.

Then report, as a numbered list, every document and plan **updated**, and every one
**checked and found current**. Silence is indistinguishable from having skipped the
phase.

## Phase 2: Mode (read-only)

Take every value below from the `git-finish-state.sh` output of Phase 1.1 — it applies
exactly these rules. The steps are the specification of that script and the fallback
when it is unavailable.

1. `git rev-parse --is-inside-work-tree` fails → **mode `no-git`**: go to Phase 6.
2. `git branch --show-current` empty → **mode `detached`**: report it, go to Phase 6
   (there is no branch to merge or push).
3. **Detect the base branch.** Do NOT trust `origin/HEAD` alone — in a repo where it was
   never configured, `git rev-parse --abbrev-ref origin/HEAD` exits non-zero and prints
   the literal string `origin/HEAD`, and `git symbolic-ref --short
   refs/remotes/origin/HEAD` fails with "is not a symbolic ref". Both were observed in
   this very repository. Detection order:
   ```bash
   BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')
   [ -z "$BASE" ] && for b in main master; do
       git show-ref --verify --quiet "refs/heads/$b" && BASE=$b && break
   done
   ```
   `--base` was passed → it wins. Still empty → **mode `unknown-base`**: STOP and ask the
   user for the base branch; never continue to Phase 3 without one. Never hardcode
   `master`: the user may say "master" while the repo's base branch is `main`.
4. Current branch equal to `$BASE` → **mode `base`**: go to Phase 5.
   Otherwise → **mode `branch`**: continue with Phase 3.
   Any `error=` line in the probe output → STOP and report it; a failed git command is not
   a state to act on.
5. **Report the plan** — mode, base branch, branch being finished, whether a worktree
   will be removed, whether the branch also exists on the remote. Then proceed.

## Phase 3: Merge into the base locally (mode `branch`)

**Standing in a linked worktree → leave it first.** The base branch is checked out in
the main clone, so `git checkout "$BASE"` fails inside the worktree. A session that
entered the worktree with `EnterWorktree` is also fenced into it: the harness refuses
`cd <main clone> && git …` until the session leaves. Call `ExitWorktree` with
`action: "keep"` (load its schema via ToolSearch first if it is deferred) — `keep`, never
`remove`: the branch is not merged yet. The session returns to the main clone; run
Phases 3–5 from there. Without `EnterWorktree`, plain `cd "$MAIN_ROOT"` is enough.

```bash
git checkout "$BASE"
git pull --ff-only          # skip when there is no remote
git merge --no-ff --no-commit <branch>
```

`--no-commit` leaves the merge open so conflicts are resolved and inspected before
anything is recorded.

**Run these one per Bash call and read each exit code before the next.** A failed
`git pull --ff-only` (no credentials in the sandbox, diverged base) → STOP and report;
merging onto a base that was never synced is how a later push gets rejected. Observed
2026-10-13: the pull died on `could not read Username`, results arrived out of order,
and the merge went ahead as if the pull had succeeded.

**On conflict — resolve, never abandon:**

1. `git diff --name-only --diff-filter=U` — the conflicting files.
2. **Append-only files (`CHANGELOG.md` is the usual one): keep BOTH sides.** Two
   branches adding entries to the same `### Added` section is not a disagreement — each
   entry describes work that genuinely happened. Deleting either loses history.
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

**Red tests → STOP** (go to Phase 6 with the stop reason). Leave the branch and the
worktree in place. Nothing has been pushed, so the whole state is local and recoverable.

## Phase 4: Delete the branch and its worktree (mode `branch`)

Skipped with `--keep-branch`. Order matters: the worktree goes first — a branch checked
out in a worktree cannot be deleted — and worktree removal must run from outside that
worktree.

Take `WT` = `worktree` and `MAIN_ROOT` = `main_root` from the Phase 1.1 probe output —
it detects a linked worktree by its own git dir, which stays correct for paths with spaces
and for repositories created with `--separate-git-dir`; do not recompute them by parsing
`git worktree list` or taking `dirname` of the common git dir.

> **Two traps here, both hit in practice.**
>
> 1. **A path is not proof of a separate worktree.** When the branch is simply checked
>    out in the main clone, this lookup returns the main repository root — and acting on
>    it means trying to delete the workspace you are standing in. Always compare:
>    `[ "$WT" = "$MAIN_ROOT" ]` means there is no worktree to remove. Only a path
>    *different* from `MAIN_ROOT` is a removable worktree.
> 2. **Under the RTK hook the parse used to return nothing** — the hook rewrote
>    `git worktree list` and reshaped its output. Since 2026-10-13 `git` is excluded
>    from RTK rewriting (`CLAUDE.md` → "RTK — Rust Token Killer"), so plain git is porcelain again; `rtk proxy` stays
>    in the snippet because it is correct either way and survives a machine whose RTK
>    config predates the exclusion.

**Strictly sequential: one command per Bash call, never two in the same message.**
`git branch -d` depends on the worktree being gone, and both commands lock
`.git/config`. Observed 2026-10-13: `worktree remove --force` and `branch -d` issued in
parallel — the branch was deleted, the removal failed with "Device or resource busy",
and a full checkout plus a `.git/worktrees/<name>` stub without `gitdir` were left
behind while the run reported success.

1. `$WT` empty or equal to `$MAIN_ROOT` → no worktree to remove, go to step 3.
   Otherwise `cd "$MAIN_ROOT"`, then `git worktree remove "$WT"`.
   Refuses because of local changes → STOP and report; never `--force` on your own.
2. **Verify the worktree is gone before touching the branch** — both checks, each its
   own call:
   ```bash
   rtk proxy git worktree list --porcelain | grep -Fx "worktree $WT"   # expect: no output
   ls -d "$WT" .git/worktrees/"$(basename "$WT")" 2>&1                 # expect: No such file
   ```
   Then `git worktree prune`. Any leftover → STOP: "worktree that refuses to go".
   Bash-sandbox mount points inside the worktree make removal fail with "Device or
   resource busy"; that is a stop too, reported with the path, not a footnote.
3. `git branch -d <branch>` — lowercase `-d` only. It refuses anything unmerged, which
   is the safety check. A refusal means the merge did not land — investigate, never
   reach for `-D`.
4. Branch also on the remote → deleting it there is a push. Ask first, then
   `git push origin --delete <branch>`.

## Phase 5: Push, last (modes `branch` and `base`)

Skipped with `--no-push`, and when the repo has no remote. In mode `base`, nothing to
push (`git rev-list --count "origin/$BASE..$BASE"` is `0`) → skip and say so.

```bash
git push origin "$BASE"
```

Then **verify from three sources**, because the push command's own output is the one
thing that cannot confirm itself:

```bash
git rev-parse "$BASE"; git rev-parse "origin/$BASE"; git ls-remote origin "refs/heads/$BASE"
```

All three must be the same hash. `git ls-remote` is the only one that asks the server.

**Rejected push → STOP** (go to Phase 6 with the stop reason). A rejection means the
remote moved; force-pushing is never this skill's decision.

## Phase 6: Verdict (ALWAYS, LAST)

Close the final message with a short summary (numbered: docs and plans updated, merge,
deletion, push with the verified hash, what remains in bd), and then the verdict as the
very last line, in uppercase, in the user's language (Russian for this user):

- All phases that apply to the mode completed:
  ```
  **РАБОТА В СЕССИИ ЗАВЕРШЕНА**
  ```
  When a phase was skipped by a flag or by the mode (`--no-push`, `--keep-branch`, no
  remote, `no-git`, `detached`), the work is still finished — name the skipped phase in
  the summary line right above the verdict, not inside it.
- Any stop condition fired:
  ```
  **РАБОТА В СЕССИИ НЕ ЗАВЕРШЕНА: <ПРИЧИНА В ВЕРХНЕМ РЕГИСТРЕ>**
  ```
  e.g. `**РАБОТА В СЕССИИ НЕ ЗАВЕРШЕНА: ТЕСТЫ ПОСЛЕ СЛИЯНИЯ КРАСНЫЕ**`.

Never print the "finished" verdict over a stop: an uppercase "finished" that is false is
worse than no verdict.

## Quick reference

1. **Phase 1** — ALWAYS: session inventory, docs updated, plans (files, bd, task list)
   brought up to date, committed, reported item by item.
2. **Phase 2** — mode: `no-git` / `detached` / `base` / `branch`; base-branch detection.
3. **Phase 3** — `branch`: `--no-ff` merge into base, conflicts resolved, tests green.
4. **Phase 4** — `branch`: worktree removed, branch deleted with `-d`.
5. **Phase 5** — `branch` / `base`: push, then three-source hash verification.
6. **Phase 6** — ALWAYS: summary, then the uppercase verdict as the last line.

Stop conditions, at Phases 2–5: red tests, a `-d` refusal, a rejected push, a worktree
that refuses to go. Each one ends in the "НЕ ЗАВЕРШЕНА" verdict with its reason.

## Common mistakes

| Mistake | Why it bites |
|---|---|
| Skipping Phase 1 because HEAD is on the base branch, or "nothing changed" | The guarantee is unconditional. "Nothing changed" is a finding Phase 1 reports item by item, not a reason to skip it. |
| Marking a plan step done because it was planned, not because it was done | Plan status follows the commits. A step done differently is "deviated, see commit X"; a step not done stays open. |
| Leaving leftover work only in the harness task list | It records nothing after the session. Anything that must survive goes into bd. |
| Committing another session's uncommitted changes | Only this session's work is closed here. Foreign changes are reported, never committed. |
| Ending without the verdict, or with "ЗАВЕРШЕНА" after a stop | Missing verdict looks like a cut-off run; a false one is worse. Stops end in "НЕ ЗАВЕРШЕНА: <ПРИЧИНА>". |
| Pushing the branch first "to be safe" | The remote gains a branch that must be cleaned up later, and other machines pull the half-finished state. Push last. |
| Trusting `origin/HEAD` to name the base branch | Unconfigured in this repo: one form exits non-zero printing `origin/HEAD`, the other fails with "is not a symbolic ref". Always keep the `show-ref` fallback. |
| Taking the user's word "master" literally | This repo's base branch is `main`. Detect it; do not transcribe it from the request. |
| Resolving a `CHANGELOG.md` conflict by picking one side | Both entries describe work that happened. Append-only files keep both. |
| Skipping tests because they were green on the branch | The merged tree is a tree nothing has tested yet. |
| Invoking `superpowers:finishing-a-development-branch` for "git finish" | It has no docs-and-plans phase, offers a Pull Request (against the Git Push Policy), never pushes on local merge and ends without a verdict. This skill supersedes it. |
| Removing the worktree and deleting the branch in parallel calls | The branch goes, the worktree stays half-removed, the report says success. One call at a time, verify, then `-d`. |
| `git branch -D` when `-d` refuses | `-d` refusing IS the safety check reporting an unmerged branch. |
| Parsing `git worktree list --porcelain` under the RTK hook | On a machine whose RTK config still rewrites `git`, the output is reshaped and the parse returns nothing. `rtk proxy` is safe everywhere. |
| Treating the path the worktree lookup returns as a removable worktree | For a branch checked out in the main clone the lookup returns the repository root itself — acting on it means deleting the workspace you are standing in. Compare against `MAIN_ROOT` first. |
| Leaving a branch unmerged because "it is just a skill" | A skill directory that exists only on a branch leaves the symlink installer pointing at a path that is not there — exactly how `progress-watch` produced two dangling links. |
| Reporting "done" from the push command's output | It is condensed by the hook. Compare hashes, including `git ls-remote`. |
