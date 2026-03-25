# Requirements — Requirements Management

> Every task records functional and non-functional requirements before codebase exploration begins.

---

## Requirements Document Template

```markdown
# REQ-{NNN}: Requirements for TASK-{NNN}

## Task
TASK-{NNN}: {Task Title}

## Status
{Draft | Approved | Changed}

## Functional Requirements (FR)

| ID   | Requirement | Priority |
|------|-----------|-----------|
| FR-1 | {What the system must do} | {Must/Should/Could/Won't} |

## Non-Functional Requirements (NFR)

| ID    | Requirement | Category | Priority |
|-------|-----------|-----------|-----------|
| NFR-1 | {Quality attribute} | {Category} | {Must/Should/Could/Won't} |
```

---

## Rules

| Rule | Description |
|------|-------------|
| Storage | `docs/requirements/` in the target project repository |
| File naming | `REQ-NNN-{short-name}.md` |
| Numbering | REQ-001, REQ-002, ... — matches TASK-NNN |
| Minimum | At least 1 FR with Must status |
| NFR | Optional but recommended for tasks with non-trivial quality attributes |
| Approval | The user must explicitly approve the requirements |
| Language | Russian (requirement descriptions, categories, priorities) |

---

## Priorities (MoSCoW)

| Priority | Meaning |
|----------|---------|
| **Must** | Mandatory. The task is not considered complete without this |
| **Should** | Important, but the task can be completed without it |
| **Could** | Desirable if time and resources allow |
| **Won't** | Consciously excluded from the current task (recorded for transparency) |

---

## NFR Categories

| Category | Examples |
|----------|---------|
| **Performance** | Response time, throughput, memory consumption |
| **Security** | Authentication, authorization, encryption, OWASP |
| **Maintainability** | Readability, testability, modularity |
| **Reliability** | Fault tolerance, graceful degradation, retry |
| **Usability** | UX, API ergonomics, documentation |

---

## Statuses

| Status | Meaning |
|--------|---------|
| **Draft** | Requirements formulated, awaiting approval |
| **Approved** | User approved the requirements |
| **Changed** | Requirements changed after approval (specify reason) |
