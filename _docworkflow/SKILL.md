---
name: _docworkflow
description: >
  Mandatory documentation pipeline: backlog → requirements → planning → ADR → changelog →
  completion report → commit. TASK/REQ/PLAN/ADR numbering. Git conventions.
  TRIGGER when: starting a new task (backlog/requirements), before any commit,
  numbering TASK/REQ/PLAN/ADR artifacts, applying git/commit conventions.
  SKIP when: only a final completion report is needed (use _report),
  only a single architectural decision doc is needed (use _adr).
---

# Documentation Pipeline

> Every implemented task goes through these stages.

## 7 Stages

```
1. BACKLOG              → docs/backlog/TASK-NNN-*.md (required)
1.5. REQUIREMENTS       → docs/requirements/REQ-NNN-*.md (required)
2. PLANNING (optional)  → docs/plans/PLAN-NNN-*.md
3. ADR (optional)       → docs/adr/ADR-NNN-*.md
4. CHANGELOG            → CHANGELOG.md Unreleased section (required)
5. COMPLETION REPORT    → docs/reports/{date}-{feature}.md (required)
6. COMMIT               → TASK-NNN: <type>: <description> (required)
```

## Traceability

Task ID (TASK-NNN) flows through all artifacts: plan, ADR, report, commit.

## Commit Format

```
TASK-NNN: <type>: <short title>

<Detailed description: what, why, how>

Changes:
- <file>: <what was done>
```

Types: feat, fix, refactor, docs, test, ci, chore.

## Checklist (before committing)

- [ ] Task in backlog (TASK-NNN)
- [ ] Requirements approved by user (REQ-NNN)
- [ ] Plan in docs/plans/ (if applicable)
- [ ] ADR in docs/adr/ (if needed) — if not created automatically, invoke `/_adr`
- [ ] Entry in CHANGELOG.md
- [ ] Completion Report in docs/reports/ — if not created automatically, invoke `/_report`
- [ ] Documentation language — Russian (commit messages — English)
- [ ] Commit with Task ID

> **Reminder:** create-adr and completion-report may trigger automatically based on context.
> If they did not — invoke them manually before committing.

More details:
- Pipeline: [reference/workflow.md](reference/workflow.md)
- Backlog: [reference/backlog.md](reference/backlog.md)
- Requirements: [reference/requirements.md](reference/requirements.md)
- Planning: [reference/planning.md](reference/planning.md)
- Git: [reference/git-conventions.md](reference/git-conventions.md)
