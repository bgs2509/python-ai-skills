---
name: _testing
description: >
  Python testing (pytest, 3 test levels, coverage ≥90%, AAA pattern,
  fixtures, mocks, Testcontainers). Use when writing tests or setting up test infrastructure.
---

# Testing

> Dependencies are injected (DIP), no global state (Testability).

## Three Levels

| Level | What | Where | Dependencies |
|-------|------|-------|--------------|
| Unit | Isolated logic | `tests/unit/` | Mocks |
| Integration | Interactions | `tests/integration/` | Testcontainers |
| E2E | Full scenarios | `tests/e2e/` | Real infrastructure |

## Coverage: ≥90%

`pytest --cov=src --cov-fail-under=90`

## Pattern: Arrange-Act-Assert

Each test has three blocks: setup → action → verification.

## Naming

`test_{what}_{scenario}_{result}` — e.g. `test_create_user_duplicate_email_raises_error`

## Key Rules

- Fixtures in `conftest.py` at each level (DRY)
- Factories in `tests/factories.py` (SSoT for test data)
- Mocks — only for external dependencies
- `@pytest.mark.parametrize` for multiple variants
- Testcontainers: PostgreSQL, Redis on session scope

## Must Be Covered

Application Services, Domain Entities, Repositories, API endpoints, validation, exception handler

## Anti-patterns (blocker)

Test without assert | order dependency | external services | too many mocks

Full version: see [reference.md](reference.md)
