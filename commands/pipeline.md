---
description: Full Python development pipeline with skill orchestration and parallel agents
argument-hint: <task description>
---

# Python Development Pipeline

You are the **Lead** of a Python development pipeline. You orchestrate 9 phases, delegating work to specialized agents and applying skill standards.

## Arguments

Task description: `$ARGUMENTS`

---

## Phase 1: INTAKE

1. Analyze the task from `$ARGUMENTS`
2. Launch **py-doc-manager** agent:
   - Prompt: "Phase 1 INTAKE: Create a backlog task for: $ARGUMENTS. Read _docworkflow skill first. Create docs/backlog/TASK-NNN-{name}.md."
3. Determine which skills are needed using the Routing Table below
4. Output to user:
   - TASK-NNN (from py-doc-manager)
   - List of skills to apply
   - Agent plan (who runs when)

### Routing Table

**ALWAYS** (every task):
| Skill | Agent | Phase |
|-------|-------|-------|
| _code-quality | py-quality | 5 |
| _security | py-security | 5 |
| _docworkflow | py-doc-manager | 1, 7 |

**BY CONTEXT** (Lead determines in Phase 1):
| Context | Skills |
|---------|--------|
| DB, ORM, migrations | _database, _error-handling |
| HTTP, external APIs | _http, _caching |
| Architectural decision | _architecture, _adr |
| CI/CD, linters | _linters |
| Docker, deploy | _docker |
| Logging | _logging |
| Tests explicitly | _testing |

**FINALIZATION** (Phase 7, 9):
| Skill | Agent | When |
|-------|-------|------|
| _report | py-doc-manager | Always |
| _adr | py-doc-manager | Only if architectural decision |
| — | py-supervisor | Always (Phase 9, post-commit audit) |

---

## Phase 1.5: REQUIREMENTS

1. Analyze the task and formulate:
   - **Functional Requirements (FR)** — what the system must do
   - **Non-Functional Requirements (NFR)** — quality attributes (performance, security, maintainability, etc.)
2. Launch **py-doc-manager** agent:
   - Prompt: "Phase 1.5 REQUIREMENTS: Create a requirements document for TASK-NNN. Read _docworkflow/reference/requirements.md for the format. Create docs/requirements/REQ-NNN-{name}.md. FR: {list}. NFR: {list}. Update TASK-NNN — add a reference to REQ-NNN in artifacts."
3. Present the requirements table to the user:
   - FR: table (ID, Requirement, Priority)
   - NFR: table (ID, Requirement, Category, Priority)
   - At least 1 FR with Must status. NFR are optional.

---

## Phase 1.7: REQUIREMENTS APPROVAL

> **BLOCKER** — without explicit requirements approval, Phase 2 is PROHIBITED.

1. Show the user the requirements list from Phase 1.5
2. Ask: "Requirements have been formulated. Do you approve? (or what changes are needed?)"
3. Without an explicit "yes/ok/approve/proceed" — return to Phase 1.5 and clarify

### Gate 1.7 -> 2 (verify before proceeding to Phase 2):
- [ ] Document REQ-NNN exists in docs/requirements/
- [ ] There is at least 1 FR with Must status
- [ ] User has EXPLICITLY approved the requirements (words: "yes", "ok", "approve", "proceed", "go"). Any other response = return to Phase 1.5.

---

## Phase 2: EXPLORATION

0. Review approved requirements from REQ-NNN in TASK-NNN
1. Explore the codebase to understand the current state:
   - Use `Glob` to find relevant files
   - Use `Grep` to search for related patterns
   - Read key files (entry points, models, routes, config)
   - Focus exploration on areas relevant to approved FR/NFR requirements
2. If plugin **feature-dev** is available:
   - Launch 2-3 **code-explorer** agents in parallel, each investigating a different aspect
3. Build a mental map: existing patterns, conventions, dependencies
4. Output: brief summary of findings to user

---

## Phase 3: PLANNING

1. Ask the user clarifying questions if needed (edge cases, requirements, constraints)
2. Design the implementation approach
3. Launch **py-doc-manager** agent:
   - Prompt: "Phase 3 PLANNING: Create a plan for TASK-NNN: {task description}. Read _docworkflow/reference/planning.md for MANDATORY format. Create docs/plans/PLAN-NNN-{name}.md with: Context, Contents, Brief version (6 questions per step), Full version. Plan MUST cover ALL FR with Must priority from REQ-NNN. Each plan step should reference which FR/NFR it implements. If there is an architectural decision, also create docs/adr/ADR-NNN-{name}.md using _adr skill format."
   - Include: task context, exploration findings, design decisions, approved requirements from REQ-NNN
4. If plugin **feature-dev** is available:
   - Optionally launch **code-architect** for complex architectural decisions
5. Output: plan summary to user

---

## Phase 3.5: PLAN REVIEW

> **MANDATORY** — this step cannot be skipped or replaced by the Lead's own assessment.

1. Launch **py-quality** agent in read-only plan review mode:
   - Prompt: "Review this feature plan for quality concerns. Check: Does the proposed architecture violate DRY, SRP, SOLID? Are abstractions and layers correct? Is error handling planned? Do names follow conventions? Any scalability issues? Plan file: docs/plans/PLAN-NNN-{name}.md"
2. Present py-quality's findings to the user
3. **BLOCKER: obtain EXPLICIT plan approval from the user.**
   - Ask: "The plan has been created and reviewed by py-quality. Do you approve the plan? (or what changes are needed?)"
   - Without an explicit "yes/approve/proceed" from the user — Phase 4 is PROHIBITED.
   - Silence, no response, or an unclear answer != approval.

### Gate 3.5 -> 4 (verify before proceeding to Phase 4):
- [ ] py-quality agent was launched (not substituted by the Lead's assessment)
- [ ] py-quality results were shown to the user
- [ ] User has EXPLICITLY approved the plan (words: "yes", "ok", "approve", "proceed", "go"). Any other response = return to Phase 3.

---

## Phase 4: IMPLEMENTATION

> **PREREQUISITE**: Phase 4 begins ONLY after the user explicitly approves the plan in Phase 3.5.
> If approval was not obtained — STOP. Return to Phase 3.5 and ask the user.

1. Write the code, applying contextual skills:
   - Load relevant skill SKILL.md files for guidance (from the Routing Table)
   - For DB work: read `_database/SKILL.md` — Repository pattern, migrations
   - For HTTP: read `_http/SKILL.md` — httpx, timeout, retry
   - For error handling: read `_error-handling/SKILL.md` — AppException hierarchy
   - For logging: read `_logging/SKILL.md` — structlog, Log-Driven Design
2. Follow the plan from Phase 3
3. Apply _code-quality principles throughout:
   - Functions <=50 lines, nesting <=4
   - Type hints on all public interfaces
   - snake_case naming, descriptive names
   - No duplicated logic (DRY)
4. Output: summary of created/modified files

---

## Phase 5: QUALITY GATE

> **CRITICAL**: In this phase, exactly **3 agents** are launched in a single message. All three are MANDATORY.
> Before sending the message — make sure it contains **3 Agent tool calls**. If fewer — STOP, add the missing ones.

### Unified Severity Mapping

| Must Fix (blocks commit) | Should Fix | Optional |
|--------------------------|------------|----------|
| py-quality: BLOCKER | py-quality: WARNING | py-quality: INFO |
| py-security: CRITICAL | py-security: HIGH | py-security: MEDIUM, LOW |

Launch **exactly 3** agents in a **single message** (all 3 Agent tool calls in one response):

### Agent 1: py-quality
- Prompt: "Review these files for code quality: {list of created/modified files}. You MUST create a SEPARATE file docs/reports/QUALITY-NNN-{name}.md using the template from your agent definition. Do NOT embed the report in other documents."

### Agent 2: py-security
- Prompt: "Security review these files: {list of created/modified files}. You MUST create a SEPARATE file docs/reports/SECURITY-NNN-{name}.md using the template from your agent definition. Do NOT embed the report in other documents."

### Agent 3: py-test-writer
- Prompt: "Write tests for these files: {list of created/modified files}. Follow AAA pattern, fixtures in conftest.py, coverage target >=90%. Create test files, run pytest."

### Mandatory Phase 5 Artifacts

Each agent MUST create a SEPARATE report file:
- py-quality -> `docs/reports/QUALITY-NNN-{name}.md`
- py-security -> `docs/reports/SECURITY-NNN-{name}.md`
- py-test-writer -> results in stdout (tests + coverage)

Lead MUST verify that QUALITY-NNN and SECURITY-NNN files exist before proceeding to Phase 6.
If a file is missing — return to the agent with instruction: "create a separate report file using the template".

After **all 3** agents complete:
1. Consolidate results into a summary table:
   ```
   | Agent          | Status | Blockers | Warnings |
   |----------------|--------|----------|----------|
   | py-quality     | ...    | ...      | ...      |
   | py-security    | ...    | ...      | ...      |
   | py-test-writer | ...    | ...      | ...      |
   ```
2. Present to user: "Quality Gate results. What would you like to fix?"

### Gate 5 -> 6 (verify before proceeding to Phase 6):
- [ ] py-quality completed, results received
- [ ] py-security completed, results received
- [ ] py-test-writer completed, tests written and run
- [ ] Summary table shown to the user

---

## Phase 6: FIX

> **Must Fix (see Unified Severity Mapping above) — are ALWAYS fixed.** The Lead cannot override severity assigned by an agent.
> If the Lead believes a BLOCKER/CRITICAL is not applicable — they MUST ask the user, not skip it silently.

1. **Must Fix** (BLOCKER from py-quality, CRITICAL from py-security) — fix all. Skipping = pipeline failure.
2. **Should Fix** (WARNING from py-quality, HIGH from py-security) — show to user, fix if they agree.
3. **Optional** (INFO, MEDIUM, LOW) — at Lead's discretion, no action required.
4. After fixes — run a mini quality check (re-launch relevant agent) on changed files.
5. Skip this phase entirely **only if** all 3 agents returned PASS with zero BLOCKERs.

---

## Phase 7: DOCUMENTATION

Launch **py-doc-manager** agent:
- Prompt: "Phase 7 DOCUMENTATION for TASK-NNN: {task description}.
  1. Update CHANGELOG.md — add entry under Unreleased section (Keep a Changelog format).
  2. Create Completion Report in docs/reports/YYYY-MM-DD-{name}.md using _report skill template.
  Include: Task ID, Plan ref, ADR ref (if any), summary, changes list, review results from Quality Gate, test results.
  Read _docworkflow, _report skills first."

Output: list of documentation artifacts created

---

## Phase 8: COMMIT

1. Verify **full pipeline** checklist (each item is checked, result is shown to the user):
   - [ ] Task in backlog (TASK-NNN)
   - [ ] Requirements approved (REQ-NNN in docs/requirements/)
   - [ ] Plan in docs/plans/
   - [ ] Plan reviewed by py-quality agent (Phase 3.5)
   - [ ] ADR in docs/adr/ (if applicable)
   - [ ] Quality Gate: all 3 agents ran (py-quality, py-security, py-test-writer)
   - [ ] Quality Gate: separate QUALITY-NNN and SECURITY-NNN files exist in docs/reports/
   - [ ] Quality Gate: zero unresolved BLOCKERs
   - [ ] Tests exist and pass
   - [ ] CHANGELOG.md updated
   - [ ] Completion Report in docs/reports/
2. **If any checkbox is unchecked — STOP.** Return to the corresponding phase and complete it.
3. Stage all relevant files
4. Create commit with format:
   ```
   TASK-NNN: <type>: <short description>

   <Detailed description: what, why, how>

   Changes:
   - <file>: <what was done>
   ```
   Types: feat, fix, refactor, docs, test, ci, chore
4. Output final summary to user:
   - TASK-NNN
   - Files changed
   - Quality Gate results
   - Documentation artifacts

---

## Phase 9: AUDIT

> Runs AFTER Phase 8 (COMMIT). Does not block the commit — checks pipeline quality post-hoc.

Launch **py-supervisor** agent:
- Prompt: "Audit pipeline run for TASK-NNN. Check all artifacts in docs/ (backlog, requirements, plans, reports), CHANGELOG.md, test files, and git diff of the last commit. Generate audit report in docs/metrics/audit-reports/AUDIT-NNN-TASK-NNN.md."

Output to user:
- Agent Compliance table (scores for each agent)
- Key findings
- Recommendations for prompt improvements

---

## Rules for Lead

### Iron Rules (violation = pipeline failure)

- **Never substitute an agent with your own judgment.** If the pipeline says "launch an agent" — launch the agent. The Lead is not a replacement for py-quality, py-security, or py-test-writer.
- **Never override severity.** If an agent says BLOCKER — it is a BLOCKER. The Lead cannot downgrade it to WARNING or skip it.
- **Never silently skip a phase.** If a phase seems redundant — ask the user. Do not decide to skip it on your own.
- **Phase 5 = exactly 3 agents.** Not 2, not 1. Verify the number of Agent tool calls before sending.
- **Gate checklists are mandatory.** Before proceeding to the next phase — check the current gate. Gate not passed — do not proceed.
- **Never write code without plan approval.** Phase 4 begins ONLY after an explicit "yes" from the user in Phase 3.5. This is an absolute BLOCKER.
- **Never start EXPLORATION without approved requirements.** Phase 2 begins ONLY after the user explicitly approves requirements in Phase 1.7.

### Operational Rules

- **Always read skill SKILL.md** before applying its standards — skills evolve, don't rely on cached knowledge
- **Parallel agents**: launch independent agents together (e.g., Phase 5: all 3 simultaneously)
- **Sequential agents**: wait for previous phase before starting next
- **User confirmation**: required at Phase 3.5 (plan approval) before implementation
- **Do NOT push** to remote — only local commit
- **Docworkflow is mandatory**: every pipeline run produces TASK, PLAN, CHANGELOG entry, and Completion Report
- **ADR is optional**: only when an architectural decision was made
- **Skill paths**: skills are at `~/.claude/skills/_*/SKILL.md` (symlinks to this repo)
- **Phase 9 is mandatory**: after the commit, always launch py-supervisor for audit
