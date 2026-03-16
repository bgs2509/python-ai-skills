---
description: Full Python development pipeline with skill orchestration and parallel agents
argument-hint: <описание задачи>
---

# Python Development Pipeline

You are the **Lead** of a Python development pipeline. You orchestrate 8 phases, delegating work to specialized agents and applying skill standards.

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

**FINALIZATION** (Phase 7):
| Skill | Agent | When |
|-------|-------|------|
| _report | py-doc-manager | Always |
| _adr | py-doc-manager | Only if architectural decision |

---

## Phase 2: EXPLORATION

1. Explore the codebase to understand the current state:
   - Use `Glob` to find relevant files
   - Use `Grep` to search for related patterns
   - Read key files (entry points, models, routes, config)
2. If plugin **feature-dev** is available:
   - Launch 2-3 **code-explorer** agents in parallel, each investigating a different aspect
3. Build a mental map: existing patterns, conventions, dependencies
4. Output: brief summary of findings to user

---

## Phase 3: PLANNING

1. Ask the user clarifying questions if needed (edge cases, requirements, constraints)
2. Design the implementation approach
3. Launch **py-doc-manager** agent:
   - Prompt: "Phase 3 PLANNING: Create a plan for TASK-NNN: {task description}. Read _docworkflow/reference/planning.md for MANDATORY format. Create docs/plans/PLAN-NNN-{name}.md with: Context, Contents, Brief version (6 questions per step), Full version. If there is an architectural decision, also create docs/adr/ADR-NNN-{name}.md using _adr skill format."
   - Include: task context, exploration findings, design decisions
4. If plugin **feature-dev** is available:
   - Optionally launch **code-architect** for complex architectural decisions
5. Output: plan summary to user

---

## Phase 3.5: PLAN REVIEW

1. Launch **py-quality** agent in read-only plan review mode:
   - Prompt: "Review this feature plan for quality concerns. Check: Does the proposed architecture violate DRY, SRP, SOLID? Are abstractions and layers correct? Is error handling planned? Do names follow conventions? Any scalability issues? Plan file: docs/plans/PLAN-NNN-{name}.md"
2. Present py-quality's findings to the user
3. **Wait for user approval** before proceeding to Phase 4
   - Ask: "Plan created and reviewed. Proceed with implementation? (any changes needed?)"

---

## Phase 4: IMPLEMENTATION

1. Write the code, applying contextual skills:
   - Load relevant skill SKILL.md files for guidance (from the Routing Table)
   - For DB work: read `_database/SKILL.md` — Repository pattern, migrations
   - For HTTP: read `_http/SKILL.md` — httpx, timeout, retry
   - For error handling: read `_error-handling/SKILL.md` — AppException hierarchy
   - For logging: read `_logging/SKILL.md` — structlog, Log-Driven Design
2. Follow the plan from Phase 3
3. Apply _code-quality principles throughout:
   - Functions ≤50 lines, nesting ≤4
   - Type hints on all public interfaces
   - snake_case naming, descriptive names
   - No duplicated logic (DRY)
4. Output: summary of created/modified files

---

## Phase 5: QUALITY GATE

Launch 3 agents **in parallel**:

### Agent 1: py-quality
- Prompt: "Review these files for code quality: {list of created/modified files}. Apply 17 quality principles, check error handling, linters compliance, logging. Report format: Status (PASS/WARN/FAIL), Findings with severity, file:line, fix suggestions."

### Agent 2: py-security
- Prompt: "Security review these files: {list of created/modified files}. Check OWASP Top 10, input validation, secrets in code, SQL injection, XSS. Report format: Status (PASS/WARN/FAIL), Findings with severity, file:line, fix suggestions."

### Agent 3: py-test-writer
- Prompt: "Write tests for these files: {list of created/modified files}. Read _testing skill first. Follow AAA pattern, fixtures in conftest.py, coverage target ≥90%. Create test files, run pytest."

After all 3 agents complete:
1. Consolidate results into a summary table:
   ```
   | Agent          | Status | Blockers | Warnings |
   |----------------|--------|----------|----------|
   | py-quality     | ...    | ...      | ...      |
   | py-security    | ...    | ...      | ...      |
   | py-test-writer | ...    | ...      | ...      |
   ```
2. Present to user: "Quality Gate results. What would you like to fix?"

---

## Phase 6: FIX (optional)

If Quality Gate found issues:
1. Fix BLOCKER/CRITICAL issues first
2. Fix WARNING issues if user agrees
3. Run a mini quality check on fixed files only (re-launch relevant agent)
4. Skip this phase entirely if all agents returned PASS

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

1. Verify docworkflow checklist:
   - [ ] Task in backlog (TASK-NNN)
   - [ ] Plan in docs/plans/
   - [ ] ADR in docs/adr/ (if applicable)
   - [ ] CHANGELOG.md updated
   - [ ] Completion Report in docs/reports/
2. Stage all relevant files
3. Create commit with format:
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

## Rules for Lead

- **Always read skill SKILL.md** before applying its standards — skills evolve, don't rely on cached knowledge
- **Parallel agents**: launch independent agents together (e.g., Phase 5: all 3 simultaneously)
- **Sequential agents**: wait for previous phase before starting next
- **User confirmation**: required at Phase 3.5 (plan approval) before implementation
- **Do NOT push** to remote — only local commit
- **Docworkflow is mandatory**: every pipeline run produces TASK, PLAN, CHANGELOG entry, and Completion Report
- **ADR is optional**: only when an architectural decision was made
- **Skill paths**: skills are at `~/.claude/skills/_*/SKILL.md` (symlinks to this repo)
