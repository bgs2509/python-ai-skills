---
name: do-feature
description: >
  Orchestrator for full feature development lifecycle: Discovery → Brainstorming → GRACE → Planning → Execution → Review → Finish.
  Combines Superpowers (process), GRACE (structure), Beads (tracking).
  TRIGGER when: user wants to implement a new feature, new service, or significant change in a dev-project.
argument-hint: "[описание фичи или задачи] [--auto-approve|-y | --ask]"
---

# Feature Development Workflow — Orchestrator

> Full lifecycle: intent analysis → design → contracts → planning → TDD execution → review → commit.
> This skill CONTROLS all transitions. Sub-skills do NOT auto-transition.
> This file holds the control logic only. Per-step execution details live in `reference.md`
> (same directory) — read the section for the step you are executing, not the whole file.

## Flags

Parsed from `argument-hint` / invocation args; first match wins:

| Flag | Effect |
|------|--------|
| `--auto-approve`, `-y` | USER APPROVAL gates (Steps 3, 5, 10) and the Step 11 advisory deviation gate are auto-approved **when the risk × evidence matrix below passes**; `high`-risk gates always fall back to interactive. Announce "Gate auto-approved (--auto-approve)" and continue. |
| `--ask` | Force interactive gates even if a standing `feedback` memory (check `bd memories auto-approve`) says auto-approve. |
| *(none)* | Resolve via memory: if a `feedback` memory blanket-approves gates for this project → auto-approve; else → ask. |

**Scope of auto-approval:** only the three USER APPROVAL gates (3, 5, 10) and the Step 11 *advisory* deviation gate. Auto-approve does NOT bypass:
- Hard quality gates (Sentrux rule violations in Steps 2 & 12, lint baseline drift)
- Pre-commit / git hooks
- Destructive operations listed in global CLAUDE.md (force-push, rm -rf, drop table, etc.) — still require explicit confirmation
- 3x-rule halt-and-ask on genuine uncertainty

### Auto-approve precondition — risk × evidence matrix

Even with `--auto-approve` (or memory override), each gate is auto-approved **only if** the produced artifact passes the matrix below. Otherwise — fall back to interactive: agent writes `Auto-approve fallback: <reason>. Approve? (yes / changes needed)` and waits.

**Risk classifier.** Classification happens twice, same criteria both times:
1. **Preliminary (owner: orchestrator, timing: Pre-dispatch Protocol, before Step 2)** — classified inline from the feature request + `knowledge-graph.xml`, no research needed. Drives Adaptive Depth in Step 2.
2. **Final (owner: Discovery/Design artifact)** — the agent writes one line in the artifact: `risk: low|medium|high` with one-sentence justification, confirming or raising the preliminary value. **Escalation is upward-only:** final > preliminary → deepen/re-run the affected phases at the greater depth; final < preliminary → completed work is not redone.

Criteria:
1. `low` — ≤1 module touched, reversible, no DB schema change, no public-API breaking change, no security/auth surface
2. `medium` — 2–3 modules OR one new module, no breaking API, no migration
3. `high` — cross-cutting (≥4 modules), breaking public API, DB migration, security/auth/permissions change, any irreversible op

**Evidence classifier** (computed from the artifact's YAML frontmatter + body):
1. `strong` — ALL of:
   - ≥1 best-practice source cited (Context7 query result, official docs URL, existing project pattern with `file:line`, or industry ADR/standard)
   - `open_questions: []` (empty) in frontmatter
   - Brainstorming/discovery converged to one dominant option (others have red flags from `_code-quality` or are explicitly rejected with reason)
   - No new ADR-candidate detected on this step (no architectural fork)
2. `weak` — any of the above missing

**Decision matrix:**

| Risk \ Evidence | strong | weak |
|---|---|---|
| `low` | auto-approve | auto-approve + log open question in `bd update <epic> --notes` |
| `medium` | auto-approve | **fallback to ask** (spawn `/best-questions` if open questions ≥ 1) |
| `high` | **fallback to ask** (flag has no effect) | **fallback to ask** (flag has no effect) |

**Boundary with Sentrux (Step 12):** this matrix is a *design-time* gate (Steps 3/5/10/11). Sentrux is a *post-execution* hard quality gate (Step 12). They are orthogonal: passing auto-approve does NOT exempt Step 12, and Sentrux failure cannot be silenced by `--auto-approve`.

## Overview

This workflow combines:
- **Beads** — task tracking (bd create/close, formula, dependencies)
- **Superpowers** — process skills (brainstorming, writing-plans, TDD, code-review, verification)
- **GRACE** — structural integrity (contracts, knowledge graph, verification plan)
- **Custom skills** — Discovery (best-approach + ST), Q&A (best-questions), ADR, logging, code-quality

## Model Routing Matrix (SSoT for routing)

Per-step model dispatch optimizes cost and wall-clock vs a single-model baseline without sacrificing quality on critical decisions or review coverage. Evidence and A/B methodology: `docs/adr/ADR-002-model-routing-ab-validation.md`.

**This matrix is the single source of truth for routing.** Step Details reference it and MUST NOT restate models. The Agent tool has NO `thinking` parameter — reasoning depth is steered only by prompt wording in the dispatch.

| Step | Dispatch | Model | Rationale |
|------|----------|-------|-----------|
| 1. `bd create` | inline | — | CLI |
| 2. Discovery | research subagent (returns artifact + open questions) | opus | ST + insights deeper on Opus (caregiver, liability, PII) |
| 3. USER APPROVAL — requirements | inline | — | gate |
| 4. Brainstorming | research subagent (returns design options + trade-offs) | opus | architectural fork, trade-offs |
| 5. USER APPROVAL — design | inline | — | gate |
| 6. GRACE Ask | `Agent(model="haiku", subagent_type="general-purpose")` | haiku | graph sync (writes) + navigation |
| 7. GRACE Plan | `Agent(model="sonnet", subagent_type="general-purpose")` | sonnet | structural codegen of contracts |
| 8. Q&A Contracts | analysis subagent; Q&A run inline by orchestrator | sonnet | ambiguity extraction from contracts |
| 9. Writing Plans | `Agent(model="sonnet", subagent_type="general-purpose")` | sonnet | decomposition into TDD steps |
| 10. USER APPROVAL — plan | inline | — | gate |
| 11. Execution — controller | inline (orchestrator, per grace-execute) | — | queue + ExecutionPackets |
| 11. Execution — workers | one subagent per phase batch | sonnet | **default Sonnet, not Haiku** (ADR-002) |
| 11. Execution — escalation | re-dispatch stuck step alone | opus | on 2 consecutive test fails on Sonnet |
| 11. Execution — trivial | optional | haiku | only rename / format / mechanical |
| 12. Review | `Agent(model="opus", subagent_type="general-purpose")` + reviewer template | opus | strongest review coverage, catches GRACE conventions (ADR-002) |
| 13. Finish | inline | — | mechanical: commit + refresh + close |

### Escalation rule (Step 11)

1. **Default — Sonnet worker per phase batch.** Sonnet is the validated baseline (ADR-002).
2. **Escalate to Opus on 2 consecutive test fails.** If the same step fails its TDD cycle twice in a row, the controller extracts that step from the batch and re-dispatches it *alone* as `Agent(model="opus")`. After Opus produces a passing implementation, subsequent steps return to the Sonnet default. Failure to escalate after 2 fails is a workflow defect — the controller MUST track per-step fail counts.
3. **Haiku only for trivial mechanical steps.** Pure rename, format-only changes, mass find-replace, mechanical comment updates. Anything that requires reasoning about types, control flow, or library APIs — stay on Sonnet.
4. **Context7 / new-library steps stay on Sonnet.** Do NOT downgrade to Haiku when a Context7 trigger fires (the 4 triggers listed in Step 11, reference.md).

### Audit trail — exceptions only

Log to `bd update <epic> --notes` **only routing exceptions and gate events**: escalation to Opus, downgrade to Haiku, auto-approved gates (format: `Gate <N> auto-approved: risk=<low|medium|high>, evidence=strong. Source: <citation>.`), fallback-to-ask (with reason and the eventual user decision), and plan deviations. Default matrix routing is NOT logged — it is derivable from this file's git history. Milestone notes per step (`Discovery done`, `Design done`, `Plan ready`) remain mandatory.

## Research Subagent Pattern (Steps 2, 4, 8)

Subagents can NEVER interact with the user — their final message returns to the orchestrator. Every step that needs user input follows this split:

1. **Subagent** does the heavy research/design and returns: the draft artifact + a structured `open_questions` list (each question with 2–4 options and a one-line recommendation).
2. **Orchestrator** resolves open questions with the user inline. Default format — light Q&A: question + options + one-line why, **without** re-running research (context was already gathered by the subagent). Full `/best-questions` treatment ONLY for genuine architectural forks (ADR-candidates).
3. If the answers change the artifact → re-dispatch the subagent with the decisions for rework.

## Pre-dispatch Protocol (orchestrator, inline — before the Step 2 dispatch)

The orchestrator runs this block itself, BEFORE dispatching the Discovery subagent. It is never
delegated: both STOP gates below require user interaction, which subagents cannot do.

1. **Preliminary risk triage** — classify `risk: low|medium|high` per the criteria in `## Flags`
   from the feature request + `knowledge-graph.xml`. This drives Adaptive Depth in Step 2;
   Discovery confirms or raises it (upward-only escalation — see the risk classifier above).
2. **Preflight** — verify the repo is fit to develop in (exact commands: reference.md, Step 2 Pre-dispatch):
   - pre-commit infrastructure alive — else STOP prompt (Pre-commit Policy)
   - lint baseline recorded — drift must be addressed in the same PR
   - Sentrux baseline captured if `.sentrux/rules.toml` exists — a currently-FAIL architectural
     rule is a STOP prompt (allow-as-baseline / fix-first / cancel)

## The Flow

```
Pre-dispatch: risk triage + preflight (orchestrator, inline)
Step 1:  bd create (epic)
Step 2:  DISCOVERY (sequential-thinking + best + WebSearch)
Step 3:  [USER APPROVAL] — FR/NFR/Scope
Step 4:  BRAINSTORMING (brainstorming + ST + Context7 + Q&A if needed)
Step 5:  [USER APPROVAL] — design
Step 6:  GRACE ASK (grace-refresh + grace-ask)
Step 7:  GRACE PLAN (grace-plan + Context7 + _code-quality + _logging)
Step 8:  Q&A CONTRACTS (analysis subagent + inline Q&A + _adr if significant)
Step 9:  WRITING PLANS (writing-plans + self-review vs FR/NFR/verification)
Step 10: [USER APPROVAL] — implementation plan
Step 11: EXECUTION (controller per grace-execute + sonnet workers + TDD)
Step 12: REVIEW (grace-reviewer full-integrity + code-review subagent + verification-before-completion)
Step 13: FINISH (git-commit meta + grace-refresh + _adr if new + _report if major + changelog if major + bd close)
```

**Step-by-step details (goals, tools, processes, outputs, Sentrux gates): `reference.md`.**

## SSoT Documents

| Document | SSoT for | Created at | Format |
|----------|----------|------------|--------|
| Discovery Report | Requirements (FR/NFR, risks, scope, best practices) | Step 2 | Markdown + XML |
| Design Document | Solution (approach, data model sketch, UX flow) | Step 4 | Markdown + XML |
| MODULE_CONTRACTs | Formal module spec (PURPOSE, INPUTS, OUTPUTS, DEPENDS) | Step 7 | Python headers |
| knowledge-graph.xml | Module map + dependencies | Step 7 | XML |
| verification-plan.xml | Tests, traces, log anchors | Step 7 | XML |
| Implementation Plan | Step-by-step tasks with TDD and code | Step 9 | Markdown |
| ADR files | Architectural decisions | Step 8/13 | Markdown |

## Auto-Generated XML Rule

Discovery and Brainstorming write prose + YAML frontmatter in markdown. XML counterparts (`docs/requirements.xml`, `docs/technology.xml`) are **auto-generated** from frontmatter via:
- pre-commit hook (primary — blocks commit on drift)
- Claude PostToolUse hook (convenience — regenerates immediately after Edit/Write)
- CI check (safety net — verifies on PR)

This eliminates dual-write drift while keeping both human-readable prose (markdown) and agent-parseable structure (YAML frontmatter → XML). Never edit XML counterparts manually.

Required frontmatter key in `discovery.md` and `design.md`: `open_questions:` — a YAML list, empty (`[]`) when all questions are resolved. The auto-approve evidence classifier reads this key; a missing key counts as `weak` evidence.

## Orchestrator Rules

1. **This workflow controls ALL transitions.** Sub-skills do NOT auto-transition (enforced by global Skill Hierarchy in `~/.claude/CLAUDE.md` — workers and utilities MUST NOT auto-transition to other skills).
2. **USER APPROVAL gates:** Steps 3, 5, 10 are mandatory and are never skipped on the agent's own initiative. Step 11 has one advisory gate on plan deviation. Auto-approval is allowed ONLY with explicit user opt-in (`--auto-approve` flag or standing feedback memory) AND a passing risk × evidence matrix — see `## Flags` and the gate exception in `~/.claude/CLAUDE.md`. `high`-risk gates always fall back to interactive regardless of flag.
3. **Pre-dispatch Protocol is orchestrator-owned.** Risk triage and preflight run inline before the Step 2 dispatch — never inside a subagent (its STOP gates need the user).
4. **Beads tracking:** Update epic notes at each major milestone. Cross-reference `bd_id` in `plan.md` and XML artifacts (universal key across three planning SSoT zones).
5. **md → xml automation:** Discovery and Brainstorming write prose + YAML frontmatter in `discovery.md` / `design.md`. XML (`requirements.xml`, `technology.xml`) auto-generated via pre-commit hook + Claude PostToolUse hook + CI check. Never edit XML manually.
6. **SSoT discipline:** One artifact per concern (see global Documentation SSoT rules in `~/.claude/CLAUDE.md`). No duplication between documents.
7. **Adaptive depth:** All 13 steps apply to dev-projects. Depth scales with the risk classifier (preliminary value from Pre-dispatch; see reference.md, Step 2); steps MUST NOT be skipped — only lightened.
8. **Per-step model routing follows the Model Routing Matrix** (the single SSoT for routing). Dispatch via `Agent(model=...)`. Only exceptions are audited via `bd update <epic> --notes` (see `### Audit trail`).
9. **Subagents never talk to the user.** All user interaction happens inline at the orchestrator — see `## Research Subagent Pattern`.
