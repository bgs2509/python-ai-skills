---
name: superautocoder
description: >
  Orchestrator skill that turns ANY draft (tech-spec, research note, ADR-cluster, brainstorm dump, README,
  arbitrary prompt) into an executable chain of context-window-sized steps and runs them end-to-end.
  Each step is a full feature-workflow iteration. After every closed step the tail of the plan is
  auto-reassessed via a hook into feature-workflow Finish. Approval model: FULLY AUTO-APPROVED —
  ALL USER APPROVAL gates (batched breakdown, per-chunk feature-workflow gates, advisory tail-diff
  gate) are auto-approved without prompting the user. Per explicit user directive: NEVER ASK for
  USER APPROVAL — ALWAYS APPROVE AUTOMATICALLY.
  Quality gates stay mandatory and are NOT auto-approved away: per-chunk `make total-test` fixes
  ALL bugs to green (Phase 5.5); a final `full-audit --ai` in Phase 6 fixes every CRITICAL finding
  before close (middle/minor → follow-up bd issues).
  TRIGGER when: user provides a draft document and asks to implement it end-to-end, OR explicitly
  invokes /superautocoder.
argument-hint: "<path-to-draft.md | free-form prompt>"
role: orchestrator
---

# /superautocoder — Draft → Auto-Chained Feature Workflows

> Universal autopilot. Input: any draft. Output: implemented feature, committed, tested, audited, documented.
> Cycle: chunk → auto-approve breakdown → for each chunk run feature-workflow → total-test (fix ALL bugs)
> → after Finish auto-reassess remaining chunks → continue → final full-audit --ai (fix CRITICAL) → done.

## 0. Scope and Boundaries

1. **Applies only to dev-projects** (`project_type: dev` in project CLAUDE.md). Life-projects exempt.
2. **Orchestrator role** — MAY invoke other skills, including `feature-workflow`, `best-questions`,
   `best-approach`. Sub-skills MUST NOT auto-transition; this skill drives the loop.
3. **Single source of truth for breakdown state** — `docs/superpowers/plans/<epic-slug>/breakdown.xml`
   (created by this skill). Beads issues mirror it 1:1.
4. **Cross-reference key** — `bd_id` per chunk. Same key in `breakdown.xml`, `step-NN-plan.md`, Beads,
   and commit trailers.

## 1. Inputs

1. Mandatory: a draft. Either:
   - path to a markdown/text/xml file under the project, OR
   - free-form prompt describing the goal (skill will materialise an internal `draft.md` first).
2. Optional flags:
   - `--budget <0..1>` — context-window utilisation per chunk (default `0.6`, clamped to `[0.3, 0.7]`).
   - `--dry-run` — produce breakdown only, do not start execution loop. Skips the project-guard
     check below (allows running from research/life zones to preview the chunking).
   - `--resume <epic-slug>` — pick up an interrupted run.
   - `--target-repo <path>` — explicit dev-repo path when the draft lives in a different (research)
     location than the implementation target.

## 1a. Project Guard (Phase 0)

Runs before INTAKE. Goal: refuse execution loop in non-dev contexts; warn in dry-run.

1. Resolve **target repo**:
   - if `--target-repo <path>` provided → use it,
   - else if `--resume <epic-slug>` → use the repo recorded in `breakdown.xml`,
   - else → use `$PWD`.
2. Resolve **target CLAUDE.md**: walk up from target repo until first `CLAUDE.md` is found.
3. Read frontmatter / explicit declaration:
   - `project_type: dev` → proceed.
   - `project_type: life` OR no `project_type` field at all OR file marked as research/life-zone
     (e.g. comment "НЕ dev-проект", "Karpathy LLM Wiki") →
     - in `--dry-run`: print warning `[guard] target is non-dev — dry-run preview only, execution
       loop would refuse here` and continue,
     - otherwise: HALT, invoke `best-questions` with the framed question
       "Target repo is not a dev-project. Provide `--target-repo <path>` to a dev-repo, or confirm
       you want to bootstrap a new dev-repo at <suggested-path>." and wait.
4. If guard halted and the user supplies `--target-repo` on retry, restart from Phase 0.

## 2. The Loop

```
Phase 1  INTAKE        — load draft, detect type, extract goal/constraints
Phase 2  CHUNKING      — compute window budget, split into N chunks by Plan-Sizing rule
Phase 3  BREAKDOWN     — emit breakdown.xml + step-NN-plan.md skeletons + bd issues (epic + N tasks)
Phase 4  [AUTO-APPROVED]  — breakdown auto-approved without prompting (per user directive)
Phase 5  EXECUTION LOOP for chunk K = 1..N:
         5.1  invoke /feature-workflow <bd-id-K>
              (its 3 internal gates are AUTO-APPROVED — pass --auto-approve / answer "approve"
              automatically without prompting the user)
         5.2  on feature-workflow Finish — auto-hook fires REASSESS step
         5.3  REASSESS — re-read closed chunks' decisions, regenerate tail (K+1..N), diff vs old tail
         5.4  if tail materially changed → write tail-diff to reassess/<UTC-ts>-tail-diff.md,
              AUTO-ACCEPT (no prompt, per approval model §5.3 / rule §11.1), continue
         5.5  TOTAL-TEST GATE — run `make total-test` in target repo. **Mandatory:
              fix EVERY failing test and error to green — no chunk advances while any
              test fails, errors, or is skipped/xfail'd just to pass. Fix ALL bugs.**
              - if exit 0 (zero failures, zero errors) → proceed
              - if exit ≠ 0 → enter fix-loop:
                  a. analyse failures (read full output, group by root cause)
                  b. apply best-practice fix (root cause, not symptom; no test-skipping;
                     no `--no-verify`; follow CLAUDE.md "Root-cause over symptom" rule)
                  c. re-run `make total-test`
                  d. repeat (a-c) until exit 0 OR after 3 unsuccessful iterations halt
                     and invoke `best-questions` with the failure summary
              - log every iteration into `breakdown.xml/<total-test-log>` with bd_id_K
              - commit fixes as `fix(<MODULE_ID>): total-test post-chunk-<K> repairs` with
                bd_id trailer; quality gates (lint, grace lint, pre-commit) MUST pass
         5.6  CONTEXT CLEAR — emit `/clear` (or equivalent context reset) before chunk K+1.
              Persist all state required for resume into `breakdown.xml/<run-state>`
              (current K, epic_slug, target_repo, last_commit_sha, total-test status)
              so the next chunk starts from a clean window using `--resume <epic-slug>`.
         5.7  K := K + 1
Phase 6  CLOSE
         6.1  FULL-AUDIT GATE — run `full-audit --ai` in target repo (read-only audit):
              - read the emitted `docs/reports/<date>-audit.md`
              - fix ONLY findings full-audit classifies as **CRITICAL** (Summary CRITICAL
                count + `## AI deep code analysis` → `### Critical`). Root-cause fixes only;
                no symptom patches, no test-skipping, no `--no-verify`
              - leave MIDDLE / MINOR findings untouched → file each as a follow-up bd issue
              - re-run `full-audit --ai`; repeat until report shows **0 CRITICAL** OR after
                3 fix iterations halt and invoke `best-questions` with the residual summary
              - if `full-audit` exits 1 for a missing tool / pre-flight refusal (NOT a critical
                finding) → halt, surface the setup defect, do NOT enter the fix-loop
              - commit fixes as `fix(<MODULE_ID>): critical audit findings <epic-slug>` with
                the epic bd_id trailer; quality gates (lint, grace lint, pre-commit) MUST pass
         6.2  close epic, run /grace-refresh, /smart-commit meta, write _report
```

## 3. Decision Protocol (the 3x-rule)

> Applies at EVERY phase. If at any point the skill faces a non-trivial choice
> (chunk boundary, library, design alternative, ambiguous requirement, conflict with existing code,
> failed step recovery strategy):

1. Invoke `mcp__sequential-thinking__sequentialthinking` — open a thinking session, frame the question.
2. Research **at least 3** best-practice solutions:
   - Use `WebSearch` and/or Context7 (`resolve-library-id` → `query-docs`) for libraries.
   - Use `Grep`/`Glob` to check what the project already does.
   - Use `best-approach` skill if the question is about choosing among approaches.
3. Score each candidate on the project's own criteria (code-quality 17 principles, fit with existing
   stack, risk, reversibility).
4. **3x-rule:**
   - If the best candidate scores **≥3× better** than the runner-up on the chosen criteria — auto-apply
     and log the decision into `breakdown.xml/<decisions>` with reasoning + cited sources.
   - Otherwise — **STOP**, invoke `best-questions` skill with the framed question and the top
     candidates, **wait** for user response, then continue.
5. The "3× better" threshold is a heuristic for one-sided dominance. If candidates are dimensionally
   incomparable (apples vs oranges), treat as "not 3× better" and ask the user.

## 4. Reassess Trigger — Beads-Polling (primary) + optional Stop-hook

The Claude Code harness does not expose a stable "Skill finished" event, so the auto-reassess
trigger is implemented via **Beads-status polling** as the primary mechanism. The settings.json
`Stop`-hook is an optional accelerator, not a requirement.

### 4.1 Primary: Beads-polling

1. After invoking `/feature-workflow <bd-id-K>` in Phase 5.1, the orchestrator records:
   - `epic_slug`, `bd_id_K`, `started_at_utc`, `prev_status`.
2. Polls `bd show <bd-id-K>` every 30s (configurable via `--poll-interval`):
   - status transition `in_progress → closed` AND a new commit on the working branch with trailer
     `bd_id: <bd-id-K>` → REASSESS triggered (Phase 5.2).
   - status `blocked` or `failed` → halt loop, see §9 failure handling.
   - timeout > 4h with no transition → halt, ask user via `best-questions`.
3. On transition: read `bd show --json <bd-id-K>` for decisions/comments, run `git log -1
   --format=%B HEAD` for commit body, feed both into Phase 5.3 reassess input.
4. State persisted to `breakdown.xml/<run-state>` so `--resume` picks up exactly where polling
   stopped.

### 4.2 Optional accelerator: `Stop` hook

If a project wants near-zero-latency reassess instead of 30s polling:

1. Use the `update-config` skill to add a `Stop` hook in `~/.claude/settings.local.json`:
   - matcher: a sentinel text the orchestrator instructs the inner feature-workflow to print on
     Finish, e.g. `[superautocoder-finish:<epic_slug>:<bd_id>]`.
   - command: writes a marker file `state/superautocoder/<epic_slug>/<bd_id>.done`.
2. Polling loop watches both Beads status AND the marker dir; whichever triggers first wins.
3. Hook is registered at Phase 4 (after approval) via `update-config`, removed at Phase 6 via
   the same skill. `try/finally` guarantees removal on abort.
4. **The hook is purely an accelerator**; if it fails to fire (matcher mismatch, settings.json
   conflict), polling still works.

### 4.3 Hook leak recovery

On `/superautocoder` startup, scan `~/.claude/settings.local.json` for hooks tagged with the
`superautocoder` marker. For each hook whose `epic_slug` does not appear in
`docs/superpowers/plans/*/breakdown.xml` with status≠closed → delete via `update-config`.

## 5. Approval Model — Fully Auto-Approved

> **User directive (durable):** NEVER ASK for USER APPROVAL gates. ALWAYS APPROVE AUTOMATICALLY.
> All gates below are recorded for audit trail in `breakdown.xml/<approvals>` with
> `auto_approved=true, reason="user-directive: always-auto-approve"`, but no user prompt fires.

1. **Phase 4 breakdown gate — AUTO-APPROVED.** Two-tier payload still produced for audit trail:
   - **Tier-1 (inline summary)** shown directly in the chat:
     1. Epic title + slug + target repo path.
     2. Total N chunks, total estimated window-budget utilisation.
     3. **Compact table**: `#`, `title`, `est-window-%`, `bd_id`, `depends_on` (bd_ids only).
     4. List of decisions auto-applied under the 3x-rule (one line each, with source citations).
     5. List of decisions that triggered halt-and-ask (would have called `best-questions`).
     6. Path to Tier-2 artifact and how to view it.
   - **Tier-2 (full breakdown)** written to disk **before** asking for approval:
     - `docs/superpowers/plans/<epic-slug>/breakdown.xml` — full structural artifact.
     - `docs/superpowers/plans/<epic-slug>/breakdown-summary.md` — human-readable rendering with
       per-chunk `inputs / outputs / verification / depends_on / window-budget breakdown`.
   - Tier-1 inline message hard-cap: ≤ 80 lines and ≤ 4000 chars. If exceeded, truncate the table
     to first 10 chunks + `… and M more, see <Tier-2-path>`.
   - **No prompt fired.** Tier-1 message and Tier-2 artifact are written to disk and to chat as
     informational output, then auto-approved. User retains right to interrupt/abort manually.
2. **Per-chunk gates (inner feature-workflow)** — its 3 standard gates (after Discovery,
   after Brainstorming, after Writing Plans) are AUTO-APPROVED. The orchestrator passes
   `--auto-approve` to feature-workflow (or, if unsupported, programmatically responds "approve"
   to each gate prompt). Quality gates (linters, tests, grace-lint, commit hooks) are NOT
   gates in this sense and remain in force.
3. **Advisory tail-diff gate (Phase 5.4)** — AUTO-APPROVED. Diff summary still written to
   `docs/superpowers/plans/<epic-slug>/reassess/<UTC-ts>-tail-diff.md` for audit; loop continues.
4. **Never bypass** quality gates: linters, tests, grace-lint, commit hooks remain mandatory.
   Auto-approval applies ONLY to USER APPROVAL gates, NOT to automated quality gates.

## 6. Per-Chunk Guarantees (delegated to feature-workflow)

For every chunk the inner `feature-workflow` is responsible for, and `/superautocoder` MUST verify
on Finish:

1. Step plan in `docs/superpowers/plans/.../step-NN-plan.md` exists and matches breakdown.xml.
2. Result is **user-verifiable** — concrete artifact (file diff, test output, runnable command) listed
   in chunk's `verification` block.
3. **Documentation updated** — at minimum: relevant `CLAUDE.md`, `requirements.xml`/`technology.xml` if
   frontmatter changed, `knowledge-graph.xml` via `grace-refresh` if module boundaries moved.
4. **Commit** present, Conventional Commits + GRACE MODULE_ID scope, contains `bd_id` trailer.
5. **Quality gates green:** project linters (ruff/format/mypy), `grace lint`, full test suite for
   the chunk's scope. If the chunk was a bulk auto-edit — full project quality gate (per CLAUDE.md
   "After bulk auto-edits" rule). **Plus** the post-chunk `make total-test` gate (Phase 5.5)
   MUST exit 0 before the chunk is considered closed and before context is cleared.
6. **No bypass markers** — no `--no-verify`, no `SKIP=`, no disabled hooks.

If any check fails post-Finish — `/superautocoder` rolls the chunk back to `in_progress` in Beads,
reopens it via `feature-workflow` Review path, does NOT advance K.

## 7. Chunking Rules

1. Use the **Plan Sizing — Context-Window Budget** rule from `~/.claude/CLAUDE.md` as authoritative.
2. Estimate per chunk: files × avg-size + contracts + tests + logs + plan.md.
3. Default target = `0.6 × effective_window` for Opus 4.7 (effective ≠ nominal — subtract system
   prompt, skills, MCP tools, history overhead; assume ~70% of nominal as baseline).
4. Split boundary follows: stack / directory / SSoT-artifact / rule-set change. NOT file count.
5. If a chunk would land below `0.2 × effective_window` AND has tight logical coupling with neighbour
   — merge back. Goal: **fit, not fragment**.
6. Each chunk has explicit:
   - `inputs` (files it will read)
   - `outputs` (files it will create or modify)
   - `verification` (commands + expected outcome)
   - `depends_on` (bd_ids of prerequisite chunks)

## 8. Reassess Algorithm (Phase 5.3)

1. Re-read frontmatter / decisions / ADRs added by closed chunks 1..K.
2. For each remaining chunk K+1..N:
   - Re-evaluate `inputs`, `outputs`, `verification`, window-budget estimate.
   - Detect drift: changed library version, new contract, removed module, deferred decision now
     resolved, etc.
3. If drift is **structural** (changes outputs / dependencies / split boundary) — emit a tail diff,
   regenerate affected `step-NN-plan.md` files, update `breakdown.xml`, update Beads.
4. If drift is **cosmetic** (wording, ordering inside a chunk) — apply silently, log to
   `breakdown.xml/<reassess-log>`.
5. Material change → Phase 5.4 advisory gate.

## 9. Failure Handling

1. **Inner feature-workflow fails to proceed despite auto-approve** (e.g. `--auto-approve`
   unsupported and a gate physically blocks, or the workflow errors at a gate) → `/superautocoder`
   halts loop, reports current K, leaves Beads state intact, exits with a resume hint
   (`/superautocoder --resume <epic-slug>`).
2. **Tests / lint fail post-Finish** → see §6 rollback rule.
2a. **`make total-test` still failing after 3 fix iterations** (Phase 5.5) → halt loop, invoke
    `best-questions` with the failure summary, persist state for `--resume`. Do NOT advance K.
2b. **`full-audit --ai` still reports CRITICAL after 3 fix iterations** (Phase 6.1) → halt, invoke
    `best-questions` with the residual critical summary; do NOT close the epic. A missing-tool /
    pre-flight `exit 1` is a setup defect → surface it, do NOT enter the fix-loop.
3. **3x-rule triggered uncertainty** → halt, `best-questions`, wait.
4. **User aborts** (Ctrl-C / explicit "stop") → finalise current K (commit if mid-flight is safe,
   otherwise leave WIP branch), de-register hook, persist state to `breakdown.xml` for resume.
5. **Hook leaks** (skill aborted abnormally) → next `/superautocoder` invocation detects stale hook
   in `settings.local.json` matching no live epic and removes it.

## 10. Outputs

After successful Phase 6:

1. Code merged on the working branch (not pushed — push only on explicit user request, per
   CLAUDE.md Git Push Policy).
2. `docs/superpowers/specs/<epic>/discovery.md` — synthesised from intake + decisions.
3. `docs/superpowers/specs/<epic>/design.md` — aggregated from chunk designs.
4. `docs/superpowers/plans/<epic>/breakdown.xml` — final state, all chunks status=closed.
5. `docs/superpowers/plans/<epic>/step-NN-plan.md` × N — final, may differ from initial due to reassess.
6. `docs/reports/YYYYMMDD-<epic>-report.md` — summary, decisions log, deviations, follow-ups.
7. `docs/adr/ADR-NNN-*.md` — for each major decision auto-applied via 3x-rule (ADR generated, not asked).
8. Beads epic + chunks all closed; `bd dolt push` allowed (auto, per session-close protocol).
9. `docs/reports/<date>-audit.md` — final `full-audit --ai` report with **0 CRITICAL** findings;
   any residual MIDDLE / MINOR findings filed as follow-up bd issues.

## 11. Rules

1. **Always** auto-approve every USER APPROVAL gate (Phase 4 batched, inner feature-workflow's
   3 gates, Phase 5.4 advisory). Never prompt the user. Per durable user directive.
1a. **Always** run `make total-test` after each chunk (Phase 5.5) and fix **every** failing
    test/error to green (no skip/xfail-to-pass) with a root-cause best-practice fix before
    advancing. **Always** clear context (Phase 5.6) between chunks and resume via
    `--resume <epic-slug>` to keep each chunk in a fresh window.
1b. **Always** run `full-audit --ai` in Phase 6 before CLOSE and fix every finding it
    classifies as **CRITICAL** (root-cause) until the audit reports 0 critical. MIDDLE / MINOR
    findings are filed as follow-up bd issues, NOT fixed in this run. `full-audit` is read-only —
    it never edits code; `/superautocoder` applies the fixes itself and re-audits to confirm.
2. **Never** skip linters / tests / grace-lint / commit hooks. Bypass = bug, fix root cause.
3. **Never** push code automatically.
4. **Always** verify subagent / inner-skill claims with an objective tool run (per CLAUDE.md
   "Trust = 0%" rule). The inner feature-workflow's "done" report is not sufficient evidence;
   `/superautocoder` runs `git diff`, `make lint`, `pytest`, `grace lint` itself.
5. **Always** store decisions made under the 3x-rule into ADRs.
6. **Always** keep `breakdown.xml` in sync with Beads (Beads wins on status drift, breakdown wins on
   structural drift — per CLAUDE.md SSoT table).
7. **Russian** for user-facing prose; **English** for code, commit messages, file names, XML keys.

## 12. Out of Scope (defer / reject)

1. Cross-repo orchestration — this skill operates within a single project root.
2. Multi-language stacks unless the inner feature-workflow already supports them in this project.
3. Automatic deployment / release. Stop at "merged on local branch".
4. Replacing `feature-workflow`. This skill is a **caller**, not a substitute.
5. Editing the user's CLAUDE.md / global rules. The skill reads them as authoritative.

## 13. Invocation Examples

```
/superautocoder docs/Spec-WIKI/research/tech-spec-draft.md
/superautocoder "implement a CSV importer for portfolio data per overview §4"
/superautocoder docs/superpowers/specs/20260510-foo-discovery.md --budget 0.5
/superautocoder --resume 20260510-ai-steward-wiki
/superautocoder docs/draft.md --dry-run
```

## 14. Cross-References

- `~/.claude/CLAUDE.md` — Plan Sizing rule, Skill Hierarchy, USER APPROVAL Gates, SSoT table.
- `~/.claude/skills/feature-workflow/SKILL.md` — the inner orchestrator this skill drives.
- `~/.claude/skills/full-audit/SKILL.md` — read-only code+docs audit run in Phase 6 (critical-only fix gate).
- `~/.claude/skills/best-questions/SKILL.md` — fallback when 3x-rule doesn't dominate.
- `~/.claude/skills/best-approach/SKILL.md` — used inside Decision Protocol when comparing approaches.
- `mcp__sequential-thinking__sequentialthinking` — mandatory for every non-trivial decision.
