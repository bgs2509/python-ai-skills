# Mandatory Documentation Pipeline

> Every implemented task goes through these documentation stages. The pipeline applies to ANY task: feature, refactoring, test setup, linters, logging, etc.

---

## Stages

```
1. BACKLOG              → Task recorded
1.5. REQUIREMENTS       → Requirements recorded → docs/requirements/
2. PLANNING (opt.)      → Plan file created → docs/plans/
3. ADR (opt.)           → Architecture decision → docs/adr/
4. CHANGELOG            → Record of what was done
5. COMPLETION REPORT    → Report with references → docs/reports/
6. COMMIT               → Committed to git
```

---

## Numbering and Artifact Traceability

Each artifact has its own numbering prefix:

| Artifact | Prefix | Example | Storage |
|----------|--------|---------|---------|
| Task | TASK- | TASK-001 | `docs/backlog/` |
| Requirements | REQ- | REQ-001 | `docs/requirements/` |
| Plan | PLAN- | PLAN-001 | `docs/plans/` |
| ADR | ADR- | ADR-001 | `docs/adr/` |
| Completion Report | — | by date | `docs/reports/` |

### Traceability

A cross-cutting **Task ID** passes through all artifacts:

- Requirements reference the task: `Task: TASK-001`
- Plan references the task: `Task: TASK-001`
- ADR references the task: `Task: TASK-001`
- Completion Report references the task, plan, and ADR
- Commit contains the Task ID: `TASK-001: description`

---

## Stage Details

### 1. BACKLOG

**Mandatory stage.**

- The task is recorded in `docs/backlog/` using the template from skill `_docworkflow` (_docworkflow/reference/backlog.md)
- Assigned the number TASK-NNN (next in sequence)
- Without a backlog entry, work on the task does not start

### 1.5. REQUIREMENTS

**Mandatory stage.**

- The lead analyzes the task and formulates functional (FR) and non-functional (NFR) requirements
- The document is created in `docs/requirements/` using the template from `_docworkflow/reference/requirements.md`
- Naming: `REQ-NNN-{short-name}.md`
- Numbering matches TASK-NNN
- At least 1 FR with Must status
- **BLOCKER**: the user must explicitly approve requirements before proceeding to the next stages

### 2. PLANNING (optional)

**When needed:** Claude created a plan file = the planning stage has occurred.

- Plan format: see skill `_docworkflow` (_docworkflow/reference/planning.md)
- The plan file is saved in `docs/plans/` of the target project
- Naming: `PLAN-NNN-{short-name}.md`
- The plan references the task: `Task: TASK-NNN`

**When not needed:** small tasks where the implementation is obvious.

> **Note:** planning can also happen outside this pipeline (research, estimation, "do or don't"). Such plans do not go into `docs/plans/`.

### 3. ADR (optional)

**When needed:** see criteria in skill `_adr` (_adr/reference.md).

- ADR references the task: `Task: TASK-NNN`
- Storage: `docs/adr/`
- Naming: `ADR-NNN-{short-name}.md`

**When not needed:** no choice between alternatives, the decision is obvious or easy to roll back.

### 4. CHANGELOG

**Mandatory stage.**

- Format: [Keep a Changelog](https://keepachangelog.com/)
- Add an entry to the `Unreleased` section of `CHANGELOG.md`
- Sections: Added, Changed, Deprecated, Removed, Fixed, Security
- Each entry contains the Task ID: `- Description (TASK-NNN)`

### 5. COMPLETION REPORT

**Mandatory stage.**

- Format: see skill `_report` (_report/reference.md)
- Contains references to: the task, the plan (if any), ADRs (if any)
- Storage: `docs/reports/{date}-{feature}.md`

### 6. COMMIT

**Mandatory stage.**

- Format: see skill `_docworkflow` (_docworkflow/reference/git-conventions.md)
- Commit contains the Task ID
- Language: English

---

## docs/ Structure

```
docs/
├── backlog/        # Tasks (TASK-NNN)
├── requirements/   # Requirements (REQ-NNN)
├── plans/          # Implementation plans (PLAN-NNN)
├── adr/            # Architecture decisions (ADR-NNN)
└── reports/        # Completion reports
```

---

## Checklist (before commit)

- [ ] Task recorded in backlog (TASK-NNN)
- [ ] Requirements recorded and approved (REQ-NNN)
- [ ] Plan created and saved in `docs/plans/` (if applicable)
- [ ] ADR created and saved in `docs/adr/` (if needed)
- [ ] Entry added to CHANGELOG.md
- [ ] Completion Report written in `docs/reports/`
- [ ] Commit contains the Task ID
