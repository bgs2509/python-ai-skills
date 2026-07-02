# Completion Report: do-feature Skill Audit and Restructure

## Task

- bd IDs: `python-ai-skills-jbq`, `python-ai-skills-7cq` (round 1), `python-ai-skills-7u9`, `python-ai-skills-abl` (round 2, closed), `python-ai-skills-4f4` (follow-up, open)
- Plan: none (fixes resolved directly via `/best-questions`, per user request — no formal do-feature cycle run on do-feature itself)
- ADR: `docs/adr/ADR-002-model-routing-ab-validation.md` (new)

## Executive Summary

Two audit rounds of the `do-feature` orchestrator skill found and fixed 21 findings total (6 critical + 12 medium + 10 minor in round 1; 3 critical + 8 medium in round 2), plus one confirmed process defect from the prior session (context-window overflow during the round-1 audit itself — a recurrence of the global "Plan Sizing — Context-Window Budget" failure mode). The most structural outcome: `do-feature/SKILL.md` (previously a single 447-line file — the only skill in the repo without a `reference.md`) was split into a control-logic `SKILL.md` (192 lines) and a step-detail `reference.md` (333 lines), per the repo's own `SKILL.md` + `reference.md` convention (ADR-001) and Anthropic's skill-authoring guidance (split past ~300 lines). All decisions with cited evidence were resolved via `/best-questions`, auto-selecting every option that scored above the standing 80%-confidence threshold — no option fell at or below it, so no interactive stop was needed in either round.

## Changes

### Round 1 (prior session, commits `0f35ff6`, `6ad11ff`)
- Fixed 6 critical findings: nonexistent `bd close --allow-regression` flag, nonexistent `superpowers:code-reviewer` agent, interactive skills wrongly dispatched into subagents (Steps 2/4/8), nonexistent `Agent thinking=` param, `--auto-approve` contradicting the global "Gates MUST NOT be skipped" rule, double orchestration in Step 11 (per-task Agent calls vs the `grace-execute` controller model).
- Fixed 12 medium + 10 minor findings: review redundancy, per-task subagent overhead, 4× routing-info duplication, fixed-size Step 2, exact-code-in-plan vs TDD tension, 4× `grace-refresh`, `_docworkflow` vs `do-feature` pipeline overlap, `Explore`+`grace-refresh` write conflict, `--auto-approve` semantics, hardcoded changelog path, audit-trail cost, `best-questions` weight in Step 8, plus 10 minor wording/typo fixes.

### Round 2 (this session)

**Critical (3):**
- **Circular risk-classifier dependency** — Adaptive Depth for Step 2 needed `risk`, but `risk` was written into the artifact Step 2 itself produces. Fixed with a two-pass classifier: a **preliminary** risk triage now runs inline at the orchestrator, in a new **Pre-dispatch Protocol**, before the Discovery subagent is ever dispatched (from the feature request + `knowledge-graph.xml`, no research needed); the **final** classification still happens in the Discovery/Design artifact and can only escalate the risk upward, never downgrade completed work.
- **Unreachable preflight STOP gates** — Step 2's preflight (pre-commit check, lint baseline, Sentrux baseline) contained two STOP-prompts requiring user interaction, but Step 2 was dispatched to a research subagent, and "subagents can never interact with the user" is a hard rule of the skill. Preflight is now explicitly orchestrator-owned and runs inline in the same Pre-dispatch Protocol, before the subagent dispatch.
- **Monolithic SKILL.md** — 447 lines, no `reference.md`, violating the repo's own file convention (ADR-001) and Anthropic's skill-authoring guidance (split past ~300 lines) — implicated in a context-window overflow in the prior session (auto-compaction at 194,415 tokens). Split into `SKILL.md` (control logic: flags, risk×evidence matrix, Model Routing Matrix, Pre-dispatch Protocol, Orchestrator Rules) + `reference.md` (13 step-by-step sections). A/B routing evidence moved out of `SKILL.md` into `ADR-002` (new).

**Medium (8):**
1. Discovery no longer runs `/best-approach` solution research — that duplicated Step 4 Brainstorming's job *before* the Step 3 requirements gate, so a scope change threw the work away. Discovery is now problem-space-only (WebSearch + sequential-thinking).
2. Step 13's `grace-refresh` is now **targeted** (scoped to modules touched since the last Step 11 phase-boundary sync) instead of an unconditional full refresh — Step 11 already applies per-phase deltas incrementally.
3. Step 12 review is now scoped to cross-phase deltas, integration seams, and FR/NFR coverage — it no longer re-reviews code already passed by Step 11's per-phase `grace-reviewer` (tiered-review model, evidenced against the Google/Linux-kernel practice of layered review with distinct per-stage focus).
4. Step 2/4 XML outputs (`requirements.xml`, `technology.xml`) are now explicitly annotated "auto-generated — do NOT write manually", resolving the contradiction with the pre-existing Auto-Generated XML Rule.
5. The Model Routing Matrix was rewritten in **tier language** (`strong`/`mid`/`cheap`) instead of hardcoded model names (`opus`/`sonnet`/`haiku`), with an explicit revalidation rule for when the Agent tool's model lineup changes. Follow-up issue `python-ai-skills-4f4` (open, P3) tracks re-running the A/B validation against the Claude 5 lineup.
6. Added a `context7_verified:` frontmatter key to `design.md` (written during Steps 4/7, read by the Step 10 evidence check) — makes the previously unverifiable "every external library was Context7-verified" criterion computable.
7. Inlined a one-line definition of the "3x-rule" term in `SKILL.md`'s `## Flags` section (it was previously defined only in the sibling `do-autopilot/SKILL.md`, making standalone `do-feature` invocations reference an undefined term).
8. Added an explicit commit-authority rule to Orchestrator Rules: invoking `do-feature` grants authority for the workflow's own commits (Step 11 per-step TDD, Step 13 meta) — satisfying the Beads Conservative-profile bar of "unless explicitly asked" — but this authority never extends to `git push`.

### Downstream consistency fix
- `agents/do-feature-clean.md` still named `Sonnet`/`Opus` explicitly for Step 11's default/escalation and described Step 12 as an unscoped "Opus code-reviewer" review — both went stale once the tier-language and Step 12 rescoping landed. Updated to match (commit `441dab2`).

## Review Results

- [x] Consistency sweep — grepped the whole repo for other `do-feature` references; only `agents/do-feature-clean.md` needed updating (fixed). `README.md` and `claude-home/CLAUDE.md` reference `do-feature` only in generic terms (no stale specifics).
- [x] Cross-reference integrity — verified `SKILL.md` ↔ `reference.md` pointers resolve both ways; no dangling literal model names (`"opus"`, `"sonnet"`, `"haiku"`) remain in either file.
- [x] `bd` traceability — all 5 bd issues verified via `bd show` before being cited in this report (not recalled from memory).
- [ ] Quality gates (lint/tests) — N/A: this is a documentation/instruction-only change (`.md` skill files), no Python source touched.

## Test Results

- Unit: N/A (no code)
- Integration: N/A (no code)
- Coverage: N/A (no code)
- Manual verification: re-read both split files end-to-end post-edit; frontmatter parses; line counts confirmed (`SKILL.md` 192, `reference.md` 333).

## Architecture Decision Records

- **ADR-002** (new): `docs/adr/ADR-002-model-routing-ab-validation.md` — records the 2026-05-13 A/B evidence for the Model Routing Matrix (moved out of `SKILL.md` to stop it loading on every invocation) and flags that the A/B predates the Claude 5 family, pending revalidation (`python-ai-skills-4f4`).

## Scope Changes

None. All findings were pre-existing defects in `do-feature/SKILL.md` surfaced by the two audit rounds; no new functionality was requested or added beyond fixing them.

## Known Follow-ups

- `python-ai-skills-4f4` (P3, open) — revalidate the Model Routing Matrix A/B against the Claude 5 model lineup and update `ADR-002` + the tier-to-model mapping accordingly.
