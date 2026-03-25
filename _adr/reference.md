# Architecture Decision Records (ADR)

> Recording important architectural decisions. Documents WHAT was decided, WHAT alternatives were considered, WHY this option was chosen.

---

## When to Create an ADR

- Choosing a technology or library
- Architectural pattern (monolith vs microservices, synchronous vs asynchronous)
- Deviation from an adopted standard
- Decision that is hard to roll back
- Decision that someone will ask "why did we do it this way?" about in 6 months

---

## Template

```markdown
# ADR-{number}: {Decision Title}

## Task

{TASK-NNN or "Standalone decision"}

## Status

{Proposed | Accepted | Deprecated | Superseded by ADR-XXX}

## Context

What is the problem? What are the constraints? What are the requirements?

## Alternatives Considered

### Option 1: {Name}
- Pros: ...
- Cons: ...

### Option 2: {Name}
- Pros: ...
- Cons: ...

## Decision

Option {N} was chosen because {rationale}.

## Consequences

- What becomes easier
- What becomes harder
- What new constraints appear
- What needs to be changed
```

---

## Rules

| Rule | Description |
|------|-------------|
| Numbering | ADR-001, ADR-002, ... — sequential |
| Storage | `docs/adr/` in the project repository |
| Immutability | An accepted ADR is not modified — a new one with Superseded status is created |
| Brevity | Context and decision — 3-5 sentences, not an essay |
| Date | Date when the decision was made |

---

## Statuses

| Status | Meaning |
|--------|---------|
| **Proposed** | Decision proposed, under discussion |
| **Accepted** | Decision accepted, being followed |
| **Deprecated** | Decision is outdated but not replaced |
| **Superseded** | Replaced by another ADR (specify which one) |
