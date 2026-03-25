---
name: _code-quality
description: >
  17 Python code quality principles (DRY, KISS, YAGNI, SOLID, SSoT, LoD, Fail Fast).
  Use for code reviews, refactoring, and writing new modules.
  Checks code standards and naming conventions.
context: fork
agent: Explore
---

# Quality Cascade — 17 Quality Principles

> All 17 principles apply ALWAYS. Violation of any one is a blocker.

## Basic (1-7)

1. **DRY** — no logic duplication. Shared logic goes into reusable modules.
2. **KISS** — simple solutions. Function ≤50 lines, nesting ≤4, cyclomatic complexity <10.
3. **YAGNI** — only what's needed. No "just in case" code.
4. **SoC** — separate concerns. Business logic apart from I/O.
5. **SSoT** — each data type is defined in one place.
6. **CoC** — follow project conventions.
7. **Security** — security at all levels.

## SOLID (8-12)

8. **SRP** — one function = one task. Class ≤500 lines.
9. **OCP** — open for extension, closed for modification.
10. **LSP** — subtypes replace parent types without breaking behavior.
11. **ISP** — small, specific interfaces.
12. **DIP** — depend on abstractions, inject dependencies.

## Additional (13-17)

13. **LoD** — minimal coupling, no `a.b.c.d` chains.
14. **Fail Fast** — validate at entry, guard clauses.
15. **Explicit > Implicit** — type hints, named constants.
16. **Composition > Inheritance** — inheritance depth ≤2-3.
17. **Testability** — dependencies are injected, no global state.

## Red Flags

`except: pass` | God class >500 lines | magic numbers | copy-paste | `*args/**kwargs` without necessity

## Centralization (SSoT + DRY)

| Aspect | Location |
|--------|----------|
| Configuration | `core/config.py` (Pydantic Settings) |
| Logging | `core/logging.py` (structlog) |
| Error handling | `core/exceptions.py` + single handler |
| DI | `api/dependencies.py` |
| Validation | Pydantic schemas at boundaries |

Full principles with examples: see [reference/quality-cascade.md](reference/quality-cascade.md)
Code standards: see [reference/code-standards.md](reference/code-standards.md)
Naming: see [reference/naming.md](reference/naming.md)
