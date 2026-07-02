# do-feature — Reference (Step Details)

> Full version per the repo convention (ADR-001: SKILL.md short + reference.md full).
> Control logic — flags, risk × evidence matrix, Model Routing Matrix, Pre-dispatch Protocol,
> orchestrator rules — lives in `SKILL.md`. This file holds per-step execution details.
> Read the section for the step you are executing; do not load the whole file into a worker prompt.

## Step 1: bd create

**Dispatch:** inline (no subagent)

```bash
bd create --title="Feature: {name}" --type=epic --priority=2 \
  --description="Epic for feature development workflow"
```

## Step 2: DISCOVERY

**Goal:** Understand the REAL intent, find blind spots, extract FR/NFR.

### Pre-dispatch (orchestrator, inline — MUST complete before the subagent dispatch)

Runs at the orchestrator per the Pre-dispatch Protocol in `SKILL.md`. The research subagent
NEVER executes this part — its STOP gates require user interaction, which subagents cannot do.

1. **Preliminary risk triage** — classify `risk: low|medium|high` per the criteria in
   `SKILL.md ## Flags`, from the feature request + `knowledge-graph.xml` (no research needed).
   This value drives Adaptive Depth below. Discovery later confirms or raises it in the
   artifact's `risk:` line. Escalation is upward-only (see Pre-dispatch Protocol).
2. **Pre-commit infrastructure check:**
   - `git config --get core.hooksPath` returns a path AND that path/pre-commit is executable,
     OR `.pre-commit-config.yaml` exists at repo root with `pre-commit` binary available.
   - If neither — STOP and prompt user: "Pre-commit hooks are not configured for this repo
     (Pre-commit Policy in ~/.claude/CLAUDE.md). Set up before continuing? (yes / skip with reason)".
   - Skip this check entirely if a previous do-feature run in this repo already verified it
     (recorded in epic notes) and the hooks config is unchanged.
3. **Lint baseline:** run the project's lint target (`make lint`, or `uv run ruff check`) and
   record the current error count in Discovery notes. Drift in lint count during the feature
   must be addressed in the same PR.
4. **Sentrux quality baseline (mandatory if `.sentrux/rules.toml` exists in repo):**
   - Run `mcp__sentrux__scan` (or `sentrux scan --json`) and persist the result to
     `.sentrux/baselines/{bd_id}.json` (gitignored).
   - Record in Discovery notes: `quality_signal_before`, top bottleneck (e.g. `modularity Q=...`),
     and `rules_pass / rules_fail` count.
   - **Hard gate:** if any architectural rule (`mcp__sentrux__check_rules`) is currently FAIL —
     STOP and prompt user: "Sentrux rule violation already present: <rule names>. Known
     regression — allow as starting baseline? (yes / fix-first / cancel)".
   - If `.sentrux/rules.toml` is absent — skip Sentrux preflight silently (project not onboarded).

### Dispatch (research subagent)

**Dispatch:** per Model Routing Matrix; interaction per Research Subagent Pattern.

**Tools:** `mcp__sequential-thinking__sequentialthinking` + `/best-approach` (research mode) + WebSearch

**Adaptive depth** (driven by the preliminary risk from Pre-dispatch; steps are never skipped —
only their depth scales, per global rule "lightweight content per step"):
- `low` → ST 3–4 thoughts; skip WebSearch when the pattern already exists in the project (cite `file:line` as evidence); skip `/best-approach`
- `medium` → ST 6–8 thoughts; WebSearch only for unfamiliar areas
- `high` → full protocol: ST up to 12 thoughts + WebSearch + `/best-approach`

**Process:**
1. **Phase 1 — Intent Analysis** (sequential-thinking):
   - What user said literally
   - What they MEAN (real business goal)
   - What assumptions they make unconsciously
   - What they DIDN'T say but should have
   - Blind spots — what could go wrong
   - Stakeholders — who is affected

2. **Phase 2 — Best Practices Research** (/best-approach in research mode; depth per risk):
   - WebSearch: "best practices for [task type]"
   - WebSearch: "common mistakes when implementing [task type]"
   - Industry patterns and anti-patterns

3. **Phase 3 — Requirements Extraction** (sequential-thinking):
   - FR — what system MUST do
   - NFR — performance, security, scalability, observability
   - Constraints — what CANNOT change
   - Dependencies — what it affects, what it breaks
   - Risks — what could go wrong + mitigations
   - Scope boundaries — IN / OUT / LATER

**Output:**
- `docs/superpowers/specs/YYYYMMDD-{feature}-discovery.md` (markdown for human)
- `docs/requirements.xml` (XML for GRACE — FR/NFR/UseCases)
- Structured `open_questions` returned to the orchestrator (resolved with the user before the Step 3 gate)
- Beads: `bd update <epic> --notes="Discovery done. N FR, N NFR, N risks. See docs/..."`

## Step 3: [USER APPROVAL]

**Dispatch:** inline (no subagent)

Present Discovery Report to user. Ask: "Approve FR/NFR and scope? (yes / changes needed)"
- If changes → update Discovery Report + requirements.xml → re-present
- If approved → proceed to Step 4

**Auto-approve handling:** if `--auto-approve` is active (flag or memory) → run risk × evidence matrix (see `SKILL.md ## Flags`). On `auto-approve` outcome — announce decision + log to Beads notes + proceed. On `fallback to ask` — write the fallback reason and ask interactively.

## Step 4: BRAINSTORMING

**Goal:** Design the solution for approved requirements.

**Dispatch:** per Model Routing Matrix; interaction per Research Subagent Pattern.

**Tools:** `superpowers:brainstorming` + `sequential-thinking` + `Context7`

**Process:**
1. Subagent reviews Discovery Report and compiles remaining Open Questions → orchestrator resolves them with the user (one at a time, light Q&A)
2. Subagent designs the solution with ST (2–3 architecture approaches, trade-offs) and returns options with a recommendation
3. Orchestrator presents options to user inline, user chooses
4. Re-dispatch: subagent details the chosen approach — data model sketch, API sketch, UX flow, module map
5. Context7 — verify library APIs if involved (inside the subagent)
6. Remaining questions → orchestrator light Q&A; genuine ADR-candidates → `/best-questions`

**Output:**
- `docs/superpowers/specs/YYYYMMDD-{feature}-design.md` (markdown for human)
- `docs/technology.xml` (XML for GRACE — stack decisions)
- Beads: `bd update <epic> --notes="Design done. Approach: [name]. See docs/..."`

**NOT in Design Document (lives in Discovery Report):** FR/NFR, risks, scope — reference only.

## Step 5: [USER APPROVAL]

**Dispatch:** inline (no subagent)

Present Design Document. Ask: "Approve design? (yes / changes needed)"

**Auto-approve handling:** same matrix as Step 3. Note: any new ADR-candidate in the design (architectural fork) automatically makes `evidence = weak` and — combined with `risk ≥ medium` — forces fallback to ask.

## Step 6: GRACE ASK

**Goal:** Understand current project state before planning.

**Dispatch:** per Model Routing Matrix (`general-purpose` — the step writes graph updates during refresh, so a read-only agent type does not fit).

**Tools:** `grace-refresh` (targeted or full, by actual drift) → `grace-ask`

**Process:**
1. `grace-refresh` — sync knowledge-graph.xml with actual code
2. `grace-ask` — "What modules will feature X affect? What contracts exist? Any similar logic?"

**Output:** Context for GRACE Plan (no new documents).

## Step 7: GRACE PLAN

**Goal:** Formalize design into contracts, graph, verification plan.

**Dispatch:** per Model Routing Matrix.

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

## Step 8: Q&A CONTRACTS

**Goal:** User validates contracts, resolves architectural decisions.

**Dispatch:** per Model Routing Matrix; interaction per Research Subagent Pattern.

**Tools:** analysis subagent + `_adr` (if significant); `/best-questions` only for ADR-candidates

**Process:**
1. Subagent produces a compact summary of ALL contracts and identifies ambiguities / trade-offs → returns a structured question list
2. Orchestrator runs Q&A **only on architectural forks** (not every contract). Default — light inline Q&A (question + 2–4 options + one-line why, no re-research: context was gathered in Steps 2/4/7). Full `/best-questions` ONLY for genuine ADR-candidates.
3. ADR for significant decisions → `docs/adr/ADR-NNN-*.md`
4. Update contracts based on decisions (re-dispatch)
5. `grace-refresh` (targeted) — **only if contracts actually changed** in this step

**Output:** Updated contracts, ADR files (if any).

## Step 9: WRITING PLANS

**Goal:** Translate contracts into step-by-step implementation tasks.

**Dispatch:** per Model Routing Matrix.

**Tools:** `superpowers:writing-plans`

**Process:**
1. writing-plans reads contracts from development-plan.xml + Design Document
2. Creates step-by-step tasks (2-5 min each) with TDD, exact code, commands — per the writing-plans convention the plan is written for an executor with zero context: each task carries complete test code (RED) and implementation code (GREEN)
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

## Step 10: [USER APPROVAL]

**Dispatch:** inline (no subagent)

Present implementation plan. Ask: "Approve plan and start coding? (yes / changes needed)"

**Auto-approve handling:** same matrix. Risk inherits from the design (Step 5). Evidence = `strong` only if the plan's self-review checklist (FR/NFR coverage, no placeholders, every contract has tasks) passes and every external library in the plan was Context7-verified during Steps 4 or 7.

## Step 11: EXECUTION

**Goal:** Implement the plan with TDD discipline.

**Ownership:** the orchestrator **is the controller** per `grace-execute`: it parses the plan + XML artifacts once, builds the execution queue and an ExecutionPacket per step, and applies graph/verification deltas returned by workers. Workers never own the queue. For independent task groups → `grace-multiagent-execute` (parallel waves, same controller model).

**Dispatch:** per Model Routing Matrix — one Sonnet worker per **phase batch** (a GRACE phase, or a sub-stage split per the global Plan Sizing rule: one coherent file set within 40–60% of the model's effective window). The worker receives the ExecutionPackets of all steps in the batch and executes them sequentially. Escalation and Haiku downgrade — per `### Escalation rule` in `SKILL.md`.

**CRITICAL:** the markdown plan is the SSoT for execution; XML artifacts serve structural integrity checks.

**TDD discipline:** each step executes the plan's pre-written RED → GREEN cycle with REAL runs: write the failing test from the plan → run it, verify it fails → implement from the plan → run, verify it passes → refactor. The executor *executes and verifies* the plan's TDD cycle — design discovery already happened at plan time; any divergence goes through the deviation gate.

**Context7 triggers in Execution** (4 triggers requiring `resolve-library-id` + `query-docs`):
- First contact with a library in current session
- Version bump vs design-phase decision
- Unknown / unfamiliar method name
- Library error in tests

When following an approved plan with pre-verified APIs — Context7 not required.

**Advisory gate — deviation detection:**
If any step diverges from the approved plan (new module not in plan, different approach than designed, unexpected dependency), the worker MUST NOT proceed silently and MUST NOT ask the user directly (it can't) — it pauses that step and returns the deviation to the controller. The controller classifies it via the risk × evidence matrix:
- `low + strong` (e.g. rename within one module, add log anchor matching `_logging` rules) → auto-approve, one-line flag in commit body: `Deviation auto-approved: <reason>`.
- `low + weak` → auto-approve + log open question.
- `medium / high` → **always ask the user**, regardless of flag. Destructive deviations (delete module not in plan, change DB schema, drop API) are `high` by definition.

**Process:**
1. Controller reads plan, builds execution queue + ExecutionPackets, presents the queue (per grace-execute)
2. Worker, for each step in its batch:
   - TDD cycle from the plan: RED → verify fail → GREEN → verify pass → REFACTOR
   - Context7 check on any of the 4 library triggers (see above)
   - Deviation check vs plan — return to controller if diverged
   - Implement log anchors per contract
   - **Self-check against the packet (no extra dispatch):** matches contract? within write scope? log anchors present? tests pass?
   - Commit: `<type>(<MODULE_ID>): <description>`
   - Return graph/verification delta proposals to the controller
3. Controller, at each phase boundary: apply accumulated graph/verification deltas + dispatch a scoped `grace-reviewer` review of the phase
4. Stuck steps (2 consecutive TDD fails) → controller extracts and escalates per `### Escalation rule` in `SKILL.md`

**Commit format:** Conventional Commits + GRACE MODULE_ID as scope. Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`. Example: `feat(M-VOICE-STT): add Whisper transcription pipeline`.

## Step 12: REVIEW

**Goal:** Verify quality before finalizing.

**Dispatch:** per Model Routing Matrix — `Agent(model="opus", subagent_type="general-purpose")` prompted with the reviewer template from `superpowers:requesting-code-review` (`code-reviewer.md`), fed the feature's git SHA range + FR/NFR from Discovery. Model choice evidence: ADR-002.

**Tools:** `grace-reviewer` (full-integrity) + `superpowers:requesting-code-review` template + `superpowers:verification-before-completion`

**Process:**
1. `grace-reviewer` full-integrity — contracts match code? Graph synced? Verification plan fulfilled?
2. Code review via the template subagent — code quality, architecture, testing, requirements coverage
3. `verification-before-completion` — a discipline, not a separate agent: run ALL tests, read the output, prove it works. Evidence before claims.

**Sentrux postflight (mandatory if baseline was captured in Step 2):**
- Run `mcp__sentrux__scan` (or `sentrux scan --json`) and persist to `.sentrux/results/{bd_id}.json` (gitignored).
- Compare to `.sentrux/baselines/{bd_id}.json`:
  - `Δ quality_signal = signal_after − signal_before`
  - `new_rule_violations = rules_fail_after − rules_fail_before`
  - `Δ modularity_Q`, `Δ cohesion`, top movers (file/module level)
- **Hard gate (rule violations):** any `new_rule_violations > 0` → STOP. Two paths to proceed:
  - Fix the violation in this feature (preferred), then re-scan.
  - Document via ADR (`_adr` skill) explaining why the new architectural coupling is intentional, AND mark the accepted regression: `bd label add <epic> regression-accepted` — the epic is then closed in Step 13 with `--reason="see ADR-NNN"`.
- **Soft gate (signal drop):** `Δ quality_signal < −100` → WARNING. Two paths to proceed:
  - Address the regression in this feature.
  - Document via ADR + `bd label add <epic> regression-accepted` (close reason in Step 13: `see ADR-NNN`). The Δ MUST appear in the completion report (Step 13).
- **No gate (improvement / minor drift):** `Δ quality_signal ≥ −100` AND `new_rule_violations == 0` → proceed silently, but include the Δ in the Step 13 completion report.
- If a hard or soft gate fired, append the full Sentrux diff (signal, rules, top movers) to `docs/reports/YYYYMMDD-{feature}-report.md`; otherwise a one-line Δ summary in the report suffices.

## Step 13: FINISH

**Goal:** Commit remaining changes, update docs, close task.

**Dispatch:** inline (no subagent) — mechanical commit + refresh + close

**Tools:** `git-commit` + `grace-refresh` + `_adr` (if new decisions) + `_report` (if major) + `bd close`

**Process:**
1. `grace-refresh` (full) — final sync of graph and verification plan
2. `_adr` — if new architectural decisions were made during coding
3. `_report` (if major feature) — completion report to `docs/reports/`
4. Update the project changelog (`CHANGELOG.md` per Keep a Changelog, or the path configured in the project's CLAUDE.md) — if the project maintains one (major features)
5. `git-commit` — commit remaining meta files (ADR, report, changelog, graph updates)
   - Commit format: `<type>(<short-name>):` Conventional Commits. Examples: `docs(changelog): add voice feature section`, `chore(knowledge-graph): refresh after M-VOICE changes`, `docs(adr): ADR-042 Whisper model selection`
6. `bd close <epic> --reason="Feature complete"` — or, when a Sentrux regression was accepted in Step 12: verify the `regression-accepted` label is set and close with `--reason="see ADR-NNN"`

## Quick Reference: What Creates What

| Step | Skill | Creates/Updates |
|------|-------|-----------------|
| 2 | Discovery | discovery.md, requirements.xml |
| 4 | Brainstorming | design.md, technology.xml |
| 7 | GRACE Plan | MODULE_CONTRACTs, knowledge-graph.xml, development-plan.xml, verification-plan.xml |
| 8 | Q&A | Updated contracts, ADR files |
| 9 | Writing Plans | plan.md (SSoT for execution) |
| 11 | Execution | Source code, tests, grace commits |
| 13 | Finish | Meta commits, report, changelog |
