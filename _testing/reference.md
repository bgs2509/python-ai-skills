# Testing

> Code can be tested in isolation (Testability). Dependencies are injected (DIP), there is no global state.

---

## Three Levels

| Level | What it tests | Where | Dependencies |
|-------|--------------|-------|-------------|
| **Unit** | Isolated logic | `tests/unit/` | Mocks |
| **Integration** | Component interaction | `tests/integration/` | Testcontainers (PostgreSQL, Redis) |
| **E2E** | Full scenarios from API to DB | `tests/e2e/` | Real infrastructure |

---

## Coverage

- Minimum: ≥90%
- Command: `pytest --cov=src --cov-fail-under=90`
- CI pipeline: coverage gate — pipeline fails if < 90% (see skill `_linters` (_linters/reference/ci-cd.md))

---

## Naming

Format: `test_{what}_{scenario}_{result}` (general naming conventions — see skill `_code-quality` (_code-quality/reference/naming.md))

Examples:
- `test_create_user_valid_data_returns_user`
- `test_create_user_duplicate_email_raises_error`
- `test_get_user_not_found_returns_none`

---

## Pattern: Arrange-Act-Assert

Every test has three clear blocks:
1. **Arrange** — prepare data and dependencies
2. **Act** — execute the action under test
3. **Assert** — verify the result

---

## Fixtures

- `conftest.py` at each level (`tests/unit/conftest.py`, `tests/integration/conftest.py`)
- Scope: function (default), module, session — depending on creation cost
- Parameterization: `@pytest.mark.parametrize` for testing multiple variants
- Shared fixtures: `tests/conftest.py` (DRY)

---

## Test Data Factories

- Factories in `tests/factories.py` (SSoT for test data, DRY)
- Creating entities with valid default data
- Override only the fields that matter for the test

---

## Mocking

- `unittest.mock.AsyncMock` for async dependencies
- `unittest.mock.patch` for substitution
- Mock only external dependencies (DIP enables substitution through interfaces)
- Do not mock internal classes and functions — test through the public interface
- Excessive mocking is a sign of bad architecture

---

## Testcontainers

- PostgreSQL: `testcontainers.postgres.PostgresContainer`
- Redis: `testcontainers.redis.RedisContainer`
- Used in integration tests
- Container is created at session scope, rollback between tests

---

## What to Cover Mandatorily

- Application Services (business logic)
- Domain Services
- Domain Entities (validation, business rules)
- Repositories (CRUD, specific queries)
- API endpoints (status codes, response format)
- Schema validation (Pydantic)
- Error handling (all branches of the exception handler — see skill `_error-handling` (_error-handling/reference.md))

---

## What Can Be Excluded

- `__init__.py`
- Configuration files
- Abstract base classes (ABC)
- Simple getters/setters
- Alembic-generated code (migrations)

---

## Anti-patterns

| Anti-pattern | Why it is bad |
|--------------|---------------|
| Test without assert | Verifies nothing |
| Test depends on execution order | Unstable, breaks on parallel runs |
| Test accesses external services | Unstable, depends on the network |
| Too many mocks | Test tests mocks, not code |
| One assert for an entire file | Does not localize the error |
| Test data in test code (without factories) | Duplication (DRY) |
