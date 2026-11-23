---
name: beads-sync
description: >
  Verify that the local beads/Dolt issue state is committed and pushed to the
  remote, then synchronize it. Report-first: diagnose drift read-only, show a
  report, and push only after explicit confirmation. Companion to /git-commit
  (which is git-only and never pushes). TRIGGER when: user calls /beads-sync,
  user wants to confirm beads issues are synced to remote, user says "push beads",
  "sync beads", "are my issues pushed", or after a work session that changed
  bd issues. Do NOT use for committing source code — that is /git-commit.
argument-hint: "[--check to diagnose only, never push] [--yes to skip the confirmation gate]"
---

# /beads-sync — Verify & Sync Beads/Dolt to Remote

> Diagnose the beads/Dolt sync state, report drift, and push to the remote on
> confirmation. The authoritative manual gate when git hooks may not have fired.

## Why this exists

Beads stores issues in a local Dolt database. Sync to the remote is supposed to
happen via git hooks (`pre-push`, `post-merge`) that call `bd hooks run`, but
those hooks are not always wired into the **active** `core.hooksPath`, and they
can time out. This skill is the source-of-truth reconciler: it does not trust
that a hook fired — it checks and synchronizes explicitly, idempotently.

## Arguments

- `--check` — diagnose and report only; **never** commit or push (pure read-only).
- `--yes` — skip the confirmation gate; commit+push immediately after the report.
- (no arg) — **default**: diagnose → report → ask for confirmation → sync.

## Phase 1: Collect diagnostics (READ-ONLY)

Run from the repository root. Do NOT mutate anything in this phase. Run in parallel:

1. `bd dolt status` — Dolt engine status (embedded vs server, reachable).
2. `bd dolt show` — database name, configured **remotes**, connection status.
3. `git config core.hooksPath` (fallback: `git rev-parse --git-path hooks`) — the
   **active** hooks directory git actually uses.
4. List the active hooks directory and check whether `pre-push`, `post-merge`,
   `prepare-commit-msg` contain the marker `BEGIN BEADS INTEGRATION`
   (e.g. `grep -l "BEGIN BEADS INTEGRATION" <activeHooksDir>/* 2>/dev/null`).
5. List `.beads/hooks/` and check the same marker there (the beads-managed source).

### Embedded-mode constraint (IMPORTANT)

`bd doctor` is **not supported in embedded Dolt mode** — do NOT call it for
verification; it returns an error, not a sync status. Rely only on the commands
above. Exact "ahead/behind N commits" is not reliably available in embedded mode:
the authoritative reconciliation is the `bd dolt commit` + `bd dolt push` step
itself, plus the post-sync re-verify. Do not claim a precise pending count you
cannot read — say "unknown until sync" instead.

## Phase 2: Build the report

Assess and present, with no mutations yet:

1. **Engine** — up / embedded / unreachable (Fail-Fast: if unreachable, stop and
   report; nothing else is meaningful).
2. **Remote** — is a Dolt remote configured? If **none**, Fail-Fast: there is
   nothing to push to; report and stop with the `bd dolt remote add` hint.
3. **Hook wiring** — compare active hooks dir vs `.beads/hooks/`:
   - If the active `pre-push`/`post-merge`/`prepare-commit-msg` lack the
     `BEGIN BEADS INTEGRATION` marker → **WARN**: beads git-hook integration is
     not wired into the active `core.hooksPath`, so auto-sync on push/merge will
     not fire. State that `/beads-sync` must be run manually, and point to the
     follow-up issue for fixing the wiring (do NOT fix it here).
4. **Sync intent** — what the sync step will do: `bd dolt commit` (flush any
   pending working-set changes) then `bd dolt push` to the named remote.

Report format (no tables — terminal/Telegram friendly):

```
## Beads sync report

Engine:   embedded (reachable)
Database: <name>
Remote:   <name> → <url>

Hook wiring:
  active hooksPath: <path>
  beads integration in active hooks: NO  ← auto-sync on push won't fire
  (.beads/hooks/ has it; not wired into active path — see follow-up <bd-id>)

Plan on confirm:
  1) bd dolt commit   (flush pending issue changes into a Dolt commit)
  2) bd dolt push     (push to <remote>)
```

If `--check` was passed → **stop here**. Print the report and exit. No mutations.

## Phase 3: Confirmation gate

Default (no `--yes`): after the report, ask
**"Commit and push beads to `<remote>`? (yes / no)"**

- **no** → stop, change nothing.
- **yes** → Phase 4.

If `--yes` was passed → skip the question, go to Phase 4.

## Phase 4: Sync (only after confirm or `--yes`)

1. `bd dolt commit` — capture output. It reports either "committed N change(s)"
   or "nothing to commit" (idempotent — both are fine).
2. `bd dolt push` — capture output. On success it prints
   `Pushing to Dolt remote... / Push complete.` (the same text whether or not
   there was anything new — it is idempotent, success = exit 0). Use `--json`
   when you need machine-parseable output.
3. On push failure:
   - Authentication error (Hosted Dolt) → report that `DOLT_REMOTE_USER` /
     `DOLT_REMOTE_PASSWORD` env vars are required; do NOT print or guess secrets.
   - Remote has diverged ("uncommitted changes in working set" / non-fast-forward)
     → do NOT auto `--force`. Report the divergence and suggest `bd dolt pull`
     first, then re-run `/beads-sync`. Only mention `--force` as an explicit,
     user-driven last resort.

## Phase 5: Re-verify & summary

1. Re-run `bd dolt push` once more as an idempotency check. **Note:** `bd` (as of
   1.0.5) always prints `Pushing to Dolt remote... / Push complete.` on success —
   it does **not** emit an "everything up-to-date" string even when there is
   nothing new. So the proof of a synced state is that the re-run **exits 0 with
   no error**, not any specific phrase. Do NOT report "up-to-date" as if `bd` said
   it — report "re-run clean (exit 0)". If `bd dolt show` is preferred, a healthy
   connection status is also acceptable evidence.
2. Summary:

```
Done.
  bd dolt commit: <committed N | nothing to commit>
  bd dolt push:   <Push complete | error>
  re-verify:      re-run clean (exit 0, idempotent) ✓

Note: beads git hooks not wired into active hooksPath — run /beads-sync manually
until follow-up <bd-id> is resolved.
```

## Rules

1. **Report-first** — never commit or push in Phase 1–2. Mutations happen only in
   Phase 4, after confirmation (or `--yes`). `--check` never mutates at all.
2. **Idempotent** — `bd dolt commit` and `bd dolt push` are safe to re-run; a
   clean repo yields "nothing to commit" / a successful "Push complete." (exit 0),
   not an error. Success is exit 0, not a specific output phrase.
3. **Embedded-safe** — never call `bd doctor` for verification (unsupported in
   embedded mode). Never claim a pending-commit count you could not actually read.
4. **No secrets** — never print, log, or guess `DOLT_REMOTE_USER` /
   `DOLT_REMOTE_PASSWORD` or any credential.
5. **No auto-force** — never `bd dolt push --force` automatically; divergence is
   reported and resolved by the user (usually `bd dolt pull` first).
6. **Does NOT fix hook wiring** — detecting mis-wired `core.hooksPath` is in
   scope; repairing it is a separate, user-approved operation (follow-up issue).
7. **Stays out of git** — this skill touches the Dolt remote only. Source-code
   commits/pushes remain the job of /git-commit and explicit user requests.
8. **Fail-Fast** — unreachable engine or no configured remote → stop with a clear
   report; do not proceed to a meaningless push.

## Relationship to other skills

- `/git-commit` — git-only; classifies and commits source files; never pushes.
  Natural pairing: `/git-commit` for code, then `/beads-sync` for issue state.
- This skill is a **worker/utility**: it does not auto-transition to other skills.
