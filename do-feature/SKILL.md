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

## Flags

Parsed from `argument-hint` / invocation args; first match wins:

| Flag | Effect |
|------|--------|
| `--auto-approve`, `-y` | Skip USER APPROVAL gates (Steps 3, 5, 10) and the Step 11 advisory deviation gate. Announce "Gate auto-approved (--auto-approve)" and continue. |
| `--ask` | Force interactive gates even if a standing `feedback` memory (check `bd memories auto-approve`) says auto-approve. |
| *(none)* | Resolve via memory: if a `feedback` memory blanket-approves gates for this project → auto-approve; else → ask. |

**Scope of auto-approval:** only the three USER APPROVAL gates (3, 5, 10) and the Step 11 *advisory* deviation gate. Auto-approve does NOT bypass:
- Hard quality gates (Sentrux rule violations in Steps 2 & 12, lint baseline drift)
- Pre-commit / git hooks
- Destructive operations listed in global CLAUDE.md (force-push, rm -rf, drop table, etc.) — still require explicit confirmation
- 3x-rule halt-and-ask on genuine uncertainty

### Auto-approve precondition — risk × evidence matrix

Even with `--auto-approve` (or memory override), each gate is auto-approved **only if** the produced artifact passes the matrix below. Otherwise — fall back to interactive: agent writes `Auto-approve fallback: <reason>. Approve? (yes / changes needed)` and waits.

**Risk classifier** (agent writes one line in the artifact: `risk: low|medium|high` with one-sentence justification):
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

**Audit trail (mandatory at every auto-approved gate):**
```
bd update <epic> --notes="Gate <N> auto-approved: risk=<low|medium|high>, evidence=strong. Source: <citation>."
```
Fallback-to-ask events are logged the same way with `auto-approve fallback: <reason>` and the eventual user decision.

## Overview

This workflow combines:
- **Beads** — task tracking (bd create/close, formula, dependencies)
- **Superpowers** — process skills (brainstorming, writing-plans, TDD, code-review, verification)
- **GRACE** — structural integrity (contracts, knowledge graph, verification plan)
- **Custom skills** — Discovery (best-approach + ST), Q&A (best-questions), ADR, logging, code-quality

## Model Routing Matrix

Per-step model dispatch optimizes cost (~−50–60%) and wall-clock (~−30%) vs all-Opus baseline without sacrificing quality on critical decisions or review coverage. Validated A/B on 2026-05-13.

| Step | Tool | Model | Thinking | Δ cost vs all-Opus | Rationale |
|------|------|-------|----------|--------------------|-----------|
| 1. `bd create` | inline / haiku | — | — | −90% | CLI |
| 2. Discovery | `Agent(model="opus")` | opus | low (~2k) | −60% (vs Opus high) | ST×12 + insights deeper on Opus (caregiver, liability, PII) |
| 3. USER APPROVAL — requirements | inline | — | — | — | gate |
| 4. Brainstorming | `Agent(model="opus")` | opus | low (~2k) | −60% | architectural fork, trade-offs |
| 5. USER APPROVAL — design | inline | — | — | — | gate |
| 6. GRACE Ask | `Agent(model="haiku")` | haiku | — | −90% | read-only graph navigation |
| 7. GRACE Plan | `Agent(model="sonnet")` | sonnet | low (~2k) | −80% | structural codegen of contracts |
| 8. Q&A Contracts | `Agent(model="sonnet")` | sonnet | — | −80% | Q&A on forks, ADR |
| 9. Writing Plans | `Agent(model="sonnet")` | sonnet | low (~2k) | −75% | decomposition into TDD steps |
| 10. USER APPROVAL — plan | inline | — | — | — | gate |
| 11. Execution (atomic) | `Agent(model="sonnet")` | sonnet | — | −80% | **default Sonnet, not Haiku** (A/B showed Haiku margin only 33%) |
| 11. Execution (fallback) | `Agent(model="haiku")` | haiku | — | — | only trivial: rename, format |
| 11. Execution (escalation) | `Agent(model="opus")` | opus | low | — | on 2 consecutive test fails on Sonnet |
| 12. Review | `Agent(model="opus")` | opus | low (~2k) | −60% | 2× bugs found vs Sonnet, catches GRACE conventions |
| 13. Finish | inline / haiku | — | — | −90% | mechanical: commit + refresh + close |

### Escalation rule on Step 11

```
1. Default: Agent(model="sonnet") per atomic task
2. If test fails 2× in a row → re-dispatch as Agent(model="opus", thinking=low)
3. If task is "rename / format / mechanical" → optionally Agent(model="haiku")
4. If task involves new library / Context7 trigger → stay on Sonnet (cache friendly)
```

### Audit trail

Every routing decision is logged in Beads notes on the epic for post-hoc analysis, using the same `bd update <epic> --notes` convention as the gate audit trail above. Message format: `Step <N> dispatched on <model>. Reason: <one line>.`

## The Flow

```
Step 1:  bd create (epic)
Step 2:  DISCOVERY (sequential-thinking + best + WebSearch)
Step 3:  [USER APPROVAL] — FR/NFR/Scope
Step 4:  BRAINSTORMING (brainstorming + ST + Context7 + Q&A if needed)
Step 5:  [USER APPROVAL] — design
Step 6:  GRACE ASK (grace-refresh + grace-ask)
Step 7:  GRACE PLAN (grace-plan + Context7 + _code-quality + _logging)
Step 8:  Q&A CONTRACTS (best-questions + _adr if significant)
Step 9:  WRITING PLANS (writing-plans + self-review vs FR/NFR/verification)
Step 10: [USER APPROVAL] — implementation plan
Step 11: EXECUTION (grace-execute + TDD + grace-multiagent-execute if independent)
Step 12: REVIEW (grace-reviewer full-integrity + code-reviewer agent + verification-before-completion)
Step 13: FINISH (git-commit meta + grace-refresh + _adr if new + _report if major + changelog if major + bd close)
```

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

## Step Details

### Step 1: bd create

**Dispatch:** inline (no subagent)

```bash
bd create --title="Feature: {name}" --type=epic --priority=2 \
  --description="Epic for feature development workflow"
```

### Step 2: DISCOVERY

**Goal:** Understand the REAL intent, find blind spots, extract FR/NFR.

**Dispatch:** `Agent(model="opus", subagent_type="general-purpose", thinking=low)` (~2k thinking budget)

**Tools:** `mcp__sequential-thinking__sequentialthinking` + `/best-approach` (research mode) + WebSearch

**Process:**
1. **Phase 1 — Intent Analysis** (sequential-thinking, thoughts 1-6):
   - What user said literally
   - What they MEAN (real business goal)
   - What assumptions they make unconsciously
   - What they DIDN'T say but should have
   - Blind spots — what could go wrong
   - Stakeholders — who is affected

2. **Phase 2 — Best Practices Research** (/best-approach in research mode):
   - WebSearch: "best practices for [task type]"
   - WebSearch: "common mistakes when implementing [task type]"
   - Industry patterns and anti-patterns

3. **Phase 3 — Requirements Extraction** (sequential-thinking, thoughts 7-12):
   - FR — what system MUST do
   - NFR — performance, security, scalability, observability
   - Constraints — what CANNOT change
   - Dependencies — what it affects, what it breaks
   - Risks — what could go wrong + mitigations
   - Scope boundaries — IN / OUT / LATER

**Preflight (mandatory, before Phase 1):**
- Verify pre-commit infrastructure is alive in this repo:
  - `git config --get core.hooksPath` returns a path AND that path/pre-commit is executable, OR `.pre-commit-config.yaml` exists at repo root with `pre-commit` binary available.
  - If neither — STOP and prompt user: "Pre-commit hooks are not configured for this repo (Pre-commit Policy in ~/.claude/CLAUDE.md). Set up before continuing? (yes / skip with reason)".
  - Skip this check entirely if a previous do-feature run in this repo already verified it (recorded in epic notes) and the hooks config is unchanged.
- Verify lint baseline is clean (or document the delta): run the project's lint target (`make lint`, or `uv run ruff check`) and record current error count in Discovery notes. Drift in lint count during the feature must be addressed in the same PR.
- **Sentrux quality baseline (mandatory if `.sentrux/rules.toml` exists in repo):**
  - Run `mcp__sentrux__scan` (or `sentrux scan --json`) and persist the result to `.sentrux/baselines/{bd_id}.json` (gitignored).
  - Record in Discovery notes: `quality_signal_before`, top bottleneck (e.g. `modularity Q=...`), and `rules_pass / rules_fail` count.
  - **Hard gate:** if any architectural rule (`mcp__sentrux__check_rules`) is currently FAIL — STOP and prompt user: "Sentrux rule violation already present: <rule names>. Known regression — allow as starting baseline? (yes / fix-first / cancel)".
  - If `.sentrux/rules.toml` is absent — skip Sentrux preflight silently (project not onboarded).

**Output:**
- `docs/superpowers/specs/YYYYMMDD-{feature}-discovery.md` (markdown for human)
- `docs/requirements.xml` (XML for GRACE — FR/NFR/UseCases)
- Beads: `bd update <epic> --notes="Discovery done. N FR, N NFR, N risks. See docs/..."`

### Step 3: [USER APPROVAL]

**Dispatch:** inline (no subagent)

Present Discovery Report to user. Ask: "Approve FR/NFR and scope? (yes / changes needed)"
- If changes → update Discovery Report + requirements.xml → re-present
- If approved → proceed to Step 4

**Auto-approve handling:** if `--auto-approve` is active (flag or memory) → run risk × evidence matrix (see `## Flags`). On `auto-approve` outcome — announce decision + log to Beads notes + proceed. On `fallback to ask` — write the fallback reason and ask interactively.

### Step 4: BRAINSTORMING

**Goal:** Design the solution for approved requirements.

**Dispatch:** `Agent(model="opus", subagent_type="general-purpose", thinking=low)` (~2k thinking budget)

**Tools:** `superpowers:brainstorming` + `sequential-thinking` + `Context7` + `best-questions` (if needed)

**Process:**
1. Review Discovery Report — address Open Questions with user (one at a time)
2. Solution design with ST (2-3 architecture approaches, trade-offs)
3. Present options to user, user chooses
4. Detail chosen approach: data model sketch, API sketch, UX flow, module map
5. Context7 — verify library APIs if involved
6. best-questions — if unresolved questions remain (ST + best inside)

**Output:**
- `docs/superpowers/specs/YYYYMMDD-{feature}-design.md` (markdown for human)
- `docs/technology.xml` (XML for GRACE — stack decisions)
- Beads: `bd update <epic> --notes="Design done. Approach: [name]. See docs/..."`

**NOT in Design Document (lives in Discovery Report):** FR/NFR, risks, scope — reference only.

### Step 5: [USER APPROVAL]

**Dispatch:** inline (no subagent)

Present Design Document. Ask: "Approve design? (yes / changes needed)"

**Auto-approve handling:** same matrix as Step 3. Note: any new ADR-candidate in the design (architectural fork) automatically makes `evidence = weak` and — combined with `risk ≥ medium` — forces fallback to ask.

### Step 6: GRACE ASK

**Goal:** Understand current project state before planning.

**Dispatch:** `Agent(model="haiku", subagent_type="Explore", thinking=none)`

**Tools:** `grace-refresh` (targeted or full) → `grace-ask`

**Process:**
1. `grace-refresh` — sync knowledge-graph.xml with actual code
2. `grace-ask` — "What modules will feature X affect? What contracts exist? Any similar logic?"

**Output:** Context for GRACE Plan (no new documents).

### Step 7: GRACE PLAN

**Goal:** Formalize design into contracts, graph, verification plan.

**Dispatch:** `Agent(model="sonnet", subagent_type="general-purpose", thinking=low)` (~2k thinking budget)

**Tools:** `grace-plan` + `Context7` + `_code-quality` + `_logging`

**Process:**
1. `grace-plan` — creates/updates MODULE_CONTRACTs, knowledge-graph.xml, development-plan.xml, verification-plan.xml
2. `Context7` — verify library APIs for contract INPUTS/OUTPUTS
3. `_code-quality` — validate contracts against 17 principles
4. `_logging` — plan log anchors in each contract (events, correlation IDs, decision points)

**Output:**
- Updated MODULE_CONTRACTs in source files
- Updated `docs/knowledge-graph.xml`
- Updated `docs/development-plan.xml`
- Updated `docs/verification-plan.xml`

### Step 8: Q&A CONTRACTS

**Goal:** User validates contracts, resolves architectural decisions.

**Dispatch:** `Agent(model="sonnet", subagent_type="general-purpose", thinking=none)`

**Tools:** `best-questions` + `_adr` (if significant)

**Process:**
1. Show summary of ALL contracts (compact view)
2. ST identifies ambiguities and trade-offs in contracts
3. Q&A only on architectural forks (not every contract)
4. ADR for significant decisions → `docs/adr/ADR-NNN-*.md`
5. Update contracts based on decisions
6. `grace-refresh` (targeted) — sync graph

**Output:** Updated contracts, ADR files (if any).

### Step 9: WRITING PLANS

**Goal:** Translate contracts into step-by-step implementation tasks.

**Dispatch:** `Agent(model="sonnet", subagent_type="general-purpose", thinking=low)` (~2k thinking budget)

**Tools:** `superpowers:writing-plans`

**Process:**
1. writing-plans reads contracts from development-plan.xml + Design Document
2. Creates step-by-step tasks (2-5 min each) with TDD, exact code, commands
3. Self-review checklist:
   - [ ] Every MODULE_CONTRACT → has task(s)
   - [ ] Every FR from Discovery → covered by task
   - [ ] Every NFR → has verification step
   - [ ] Verification plan → every test/trace reflected
   - [ ] Log anchors from _logging → included in tasks
   - [ ] ADR decisions → implemented in plan
   - [ ] Task order respects DEPENDS
   - [ ] No placeholders (scan)

**Output:**
- `docs/superpowers/plans/YYYYMMDD-{feature}-plan.md` (SSoT for execution)
- Beads: `bd update <epic> --notes="Plan ready. N tasks. See docs/..."`

### Step 10: [USER APPROVAL]

**Dispatch:** inline (no subagent)

Present implementation plan. Ask: "Approve plan and start coding? (yes / changes needed)"

**Auto-approve handling:** same matrix. Risk inherits from the design (Step 5). Evidence = `strong` only if the plan's self-review checklist (FR/NFR coverage, no placeholders, every contract has tasks) passes and every external library in the plan was Context7-verified during Steps 4 or 7.

### Step 11: EXECUTION

**Goal:** Implement the plan with TDD discipline.

**Dispatch:** `Agent(model="sonnet", subagent_type="general-purpose", thinking=none)` per atomic task. Fallback to `Agent(model="haiku", ...)` only for trivial mechanical tasks (rename, format). Escalate to `Agent(model="opus", thinking=low)` on 2 consecutive test failures. See `## Escalation on Failure`.

**Tools:** `grace-execute` + `superpowers:test-driven-development` + `grace-multiagent-execute` (if independent tasks)

**CRITICAL:** grace-execute follows the markdown plan (SSoT for execution), uses XML artifacts for structural integrity checks.

**Context7 triggers in Execution** (4 triggers requiring `resolve-library-id` + `query-docs`):
- First contact with a library in current session
- Version bump vs design-phase decision
- Unknown / unfamiliar method name
- Library error in tests

When following an approved plan with pre-verified APIs — Context7 not required.

**Advisory gate — deviation detection:**
If any task diverges from the approved plan (new module not in plan, different approach than designed, unexpected dependency) → prompt user: "Deviation detected: <description>. Approve? (yes / change plan / cancel)" before proceeding.

**Auto-approve handling for deviation gate:** classify the deviation via the risk × evidence matrix.
- `low + strong` (e.g. rename within one module, add log anchor matching `_logging` rules) → auto-approve, one-line flag in commit body: `Deviation auto-approved: <reason>`.
- `low + weak` → auto-approve + log open question.
- `medium / high` → **always ask**, regardless of flag. Destructive deviations (delete module not in plan, change DB schema, drop API) are `high` by definition.

**Process:**
1. grace-execute reads plan, builds execution queue
2. For each task:
   - TDD cycle: RED → verify fail → GREEN → verify pass → REFACTOR
   - Context7 check on any of the 4 library triggers (see above)
   - Deviation check vs plan — advisory gate if diverged
   - Implement log anchors per contract
   - grace-reviewer scoped review after each step
   - Commit: `<type>(<MODULE_ID>): <description>`
3. For independent task groups → grace-multiagent-execute (parallel waves)
4. Phase-level checks at boundaries

**Commit format:** Conventional Commits + GRACE MODULE_ID as scope. Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`. Example: `feat(M-VOICE-STT): add Whisper transcription pipeline`.

### Step 12: REVIEW

**Goal:** Verify quality before finalizing.

**Dispatch:** `Agent(model="opus", subagent_type="superpowers:code-reviewer", thinking=low)` (~2k thinking budget) — Opus finds 2× bugs vs Sonnet on same input (A/B 2026-05-13).

**Tools:** `grace-reviewer` (full-integrity) + `superpowers:code-reviewer` agent + `superpowers:verification-before-completion`

**Process:**
1. `grace-reviewer` full-integrity — contracts match code? Graph synced? Verification plan fulfilled?
2. `code-reviewer` agent — code quality, architecture, testing, requirements coverage
3. `verification-before-completion` — run ALL tests, read output, prove it works. Evidence before claims.

**Sentrux postflight (mandatory if baseline was captured in Step 2):**
- Run `mcp__sentrux__scan` (or `sentrux scan --json`) and persist to `.sentrux/results/{bd_id}.json` (gitignored).
- Compare to `.sentrux/baselines/{bd_id}.json`:
  - `Δ quality_signal = signal_after − signal_before`
  - `new_rule_violations = rules_fail_after − rules_fail_before`
  - `Δ modularity_Q`, `Δ cohesion`, top movers (file/module level)
- **Hard gate (rule violations):** any `new_rule_violations > 0` → STOP. Two paths to proceed:
  - Fix the violation in this feature (preferred), then re-scan.
  - Document via ADR (`_adr` skill) explaining why the new architectural coupling is intentional, AND pass `bd close --allow-regression --reason="see ADR-NNN"`.
- **Soft gate (signal drop):** `Δ quality_signal < −100` → WARNING. Two paths to proceed:
  - Address the regression in this feature.
  - Document via ADR + `bd close --allow-regression --reason="see ADR-NNN"`. The Δ MUST appear in the completion report (Step 13).
- **No gate (improvement / minor drift):** `Δ quality_signal ≥ −100` AND `new_rule_violations == 0` → proceed silently, but include the Δ in the Step 13 completion report.
- If a hard or soft gate fired, append the full Sentrux diff (signal, rules, top movers) to `docs/reports/YYYYMMDD-{feature}-report.md`; otherwise a one-line Δ summary in the report suffices.

### Step 13: FINISH

**Goal:** Commit remaining changes, update docs, close task.

**Dispatch:** inline (no subagent) — mechanical commit + refresh + close

**Tools:** `git-commit` + `grace-refresh` + `_adr` (if new decisions) + `_report` (if major) + `bd close`

**Process:**
1. `grace-refresh` (full) — final sync of graph and verification plan
2. `_adr` — if new architectural decisions were made during coding
3. `_report` (if major feature) — completion report to `docs/reports/`
4. Update `docs/20260408_changelog.md` (if major feature)
5. `git-commit` — commit remaining meta files (ADR, report, changelog, graph updates)
   - Commit format: `<type>(<short-name>):` Conventional Commits. Examples: `docs(changelog): add voice feature section`, `chore(knowledge-graph): refresh after M-VOICE changes`, `docs(adr): ADR-042 Whisper model selection`
6. `bd close <epic> --reason="Feature complete"`

## Orchestrator Rules

1. **This workflow controls ALL transitions.** Sub-skills do NOT auto-transition (enforced by global Skill Hierarchy in `~/.claude/CLAUDE.md` — workers and utilities MUST NOT auto-transition to other skills).
2. **USER APPROVAL gates:** Steps 3, 5, 10 are mandatory. Never skip. Step 11 has one advisory gate on plan deviation. With `--auto-approve` (flag or memory) gates may be auto-approved **only when the risk × evidence matrix passes** — see `## Flags`. `high`-risk gates always fall back to interactive regardless of flag.
3. **Beads tracking:** Update epic notes at each major milestone. Cross-reference `bd_id` in `plan.md` and XML artifacts (universal key across three planning SSoT zones).
4. **md → xml automation:** Discovery and Brainstorming write prose + YAML frontmatter in `discovery.md` / `design.md`. XML (`requirements.xml`, `technology.xml`) auto-generated via pre-commit hook + Claude PostToolUse hook + CI check. Never edit XML manually.
5. **SSoT discipline:** One artifact per concern (see global Documentation SSoT rules in `~/.claude/CLAUDE.md`). No duplication between documents.
6. **Adaptive depth:** All 13 steps apply to dev-projects. Trivial changes may have lightweight content per step but MUST NOT skip steps.
7. **Per-step model routing follows the Model Routing Matrix.** Dispatch via `Agent(model=...)` tool. Routing decisions are audited via `bd update <epic> --notes`.

## Escalation on Failure

Step 11 (Execution) uses tiered model dispatch:

1. **Default — Sonnet.** Each atomic task dispatched as `Agent(model="sonnet", subagent_type="general-purpose")`. Sonnet is the validated baseline (A/B 2026-05-13: Sonnet 26.8k tokens vs Haiku 56.9k on identical atomic task).
2. **Escalate to Opus on 2 consecutive test fails.** If the same task fails its TDD cycle twice in a row on Sonnet → re-dispatch the *same* task as `Agent(model="opus", thinking=low)`. Log the escalation: `bd update <epic> --notes="Step 11 task <id> escalated to Opus after 2 fails on Sonnet. Reason: <one line>."`. After Opus produces a passing implementation, subsequent tasks return to Sonnet default.
3. **Haiku only for trivial mechanical tasks.** Pure rename, format-only changes, mass find-replace, mechanical comment updates → may dispatch as `Agent(model="haiku")`. Anything that requires reasoning about types, control flow, or library APIs — stay on Sonnet.
4. **Context7 / new-library tasks stay on Sonnet.** Do NOT downgrade to Haiku when a Context7 trigger fires (the 4 triggers listed in Step 11). Sonnet handles documentation context better and benefits from prompt cache reuse across the task.

Failure to escalate after 2 fails is a workflow defect — the orchestrator MUST track per-task fail counts in epic notes.

## Quick Reference: What Creates What

| Step | Skill | Creates/Updates | Model |
|------|-------|-----------------|-------|
| 2 | Discovery | discovery.md, requirements.xml | opus (low) |
| 4 | Brainstorming | design.md, technology.xml | opus (low) |
| 7 | GRACE Plan | MODULE_CONTRACTs, knowledge-graph.xml, development-plan.xml, verification-plan.xml | sonnet (low) |
| 8 | Q&A | Updated contracts, ADR files | sonnet |
| 9 | Writing Plans | plan.md (SSoT for execution) | sonnet (low) |
| 11 | Execution | Source code, tests, grace commits | sonnet (default) / opus (escalation) / haiku (trivial) |
| 13 | Finish | Meta commits, report, changelog | inline / haiku |
