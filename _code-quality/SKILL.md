---
name: _code-quality
description: >
  17 Python code quality principles (DRY, KISS, YAGNI, SOLID, SSoT, LoD, Fail Fast).
  Checks code standards and naming conventions.
  TRIGGER when: reviewing a diff/PR, refactoring, writing a new module, naming/structure review,
  validating code against DRY/KISS/YAGNI/SOLID before commit.
  SKIP when: security-specific review (use _security), test design (use _testing),
  linter/CI config (use _linters), system-level structure decisions (use _architecture).
context: fork
agent: Explore
---

# Code Quality — 17 Principles

> **SSoT:** the principles are defined only in [principles.md](principles.md) — read it before
> planning, writing or reviewing code. KISS and YAGNI come first; its excess-code check applies
> to every diff and every plan. Do not restate principles in other files.

## Centralization (SSoT + DRY)

| Aspect | Location |
|--------|----------|
| Configuration | `core/config.py` (Pydantic Settings) |
| Logging | `core/logging.py` (structlog) |
| Error handling | `core/exceptions.py` + single handler |
| DI | `api/dependencies.py` |
| Validation | Pydantic schemas at boundaries |

## Where topics are detailed

| Topic | File |
|-------|------|
| Layer architecture (DIP, SoC, SRP) | skill `_architecture` (_architecture/reference/ddd.md, _architecture/reference/hexagonal.md) |
| Logging | skill `_logging` (_logging/reference.md) |
| Error handling | skill `_error-handling` (_error-handling/reference.md) |
| Database | skill `_database` (_database/reference.md) |
| Naming | [reference/naming.md](reference/naming.md) |
| Code standards (typing, docstrings) | [reference/code-standards.md](reference/code-standards.md) |
| Security | skill `_security` (_security/reference/security.md) |
| Testability | skill `_testing` (_testing/reference.md) |
