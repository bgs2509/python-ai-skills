# Backlog — Task Management

> Every task is recorded before work begins. Without a backlog entry, work on a task does not start.

---

## Task Template

```markdown
# TASK-{NNN}: {Task Title}

## Status

{New | Requirements | In Progress | Done | Cancelled}

## Description

{What needs to be done and why. 2-5 sentences.}

## Priority

{Critical | High | Medium | Low}

## Related Artifacts

- Requirements: {REQ-NNN or "None"}
- Plan: {PLAN-NNN or "None"}
- ADR: {ADR-NNN or "None"}
- Report: {link to docs/reports/ or "None"}
```

---

## Rules

| Rule | Description |
|------|-------------|
| Storage | `docs/backlog/` in the target project repository |
| File naming | `TASK-NNN-{short-name}.md` |
| Numbering | TASK-001, TASK-002, ... — sequential |
| Statuses | New → Requirements → In Progress → Done / Cancelled |
| Updates | Status is updated when transitioning between pipeline stages |
| Language | Russian (description, comments, statuses) |

---

## Statuses

| Status | Meaning |
|--------|---------|
| **New** | Task created, work has not started |
| **Requirements** | Requirements are being formulated or awaiting approval |
| **In Progress** | Task is in progress |
| **Done** | Task completed, all artifacts created |
| **Cancelled** | Task cancelled (specify reason in description) |
