---
name: _adr
description: >
  Create an Architecture Decision Record (ADR). Template with context, alternatives,
  decision, and consequences. Invoke when making an architectural decision.
  TRIGGER when: choosing between technologies/libraries, choosing an architectural pattern,
  deviating from an established standard, decision is hard to reverse, user is comparing options.
  SKIP when: documenting a whole feature's docs pipeline (use _docworkflow),
  writing a completion report (use _report), trivial reversible choices with no trade-off.
---

# Creating an ADR

> Capture important architectural decisions: WHAT was decided, WHAT alternatives existed, WHY it was chosen.

## When to Create

- Choosing a technology or library
- Architectural pattern selection
- Deviating from an established standard
- Decision that is hard to reverse
- Decision someone will ask about in 6 months

## Actions

1. Determine the next ADR number in `docs/adr/`
2. Ask the user about the decision context (if not obvious)
3. Create a file using the template below
4. Save to `docs/adr/ADR-NNN-{name}.md`

## Template

```markdown
# ADR-{NNN}: {Decision Title}

## Task
{TASK-NNN or "Standalone decision"}

## Status
{Proposed | Accepted | Deprecated | Superseded by ADR-XXX}

## Context
What is the problem? What are the constraints? What are the requirements?

## Considered Alternatives

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
- What constraints are introduced
```

## Rules

| Rule | Description |
|------|-------------|
| Numbering | ADR-001, ADR-002, ... |
| Storage | `docs/adr/` |
| Immutability | An accepted ADR is not modified — create a new one with Superseded status |
| Brevity | Context and decision — 3-5 sentences |
| Language | Russian |

Full version: see [reference.md](reference.md)
