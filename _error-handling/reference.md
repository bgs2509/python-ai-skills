# Error Handling

> **Centralized** handling — a single exception handler (SSoT, DRY). Exceptions are defined in one place. Duplicated try/except blocks — blocker.

---

## Exception Hierarchy (SSoT)

All exceptions are defined in `core/exceptions.py`:

```
AppException (base)
├── DomainError
│   ├── EntityNotFoundError
│   ├── BusinessRuleViolationError
│   └── InvalidStateError
├── InfrastructureError
│   ├── DatabaseError
│   ├── ExternalServiceError
│   └── CacheError
├── ValidationError
│   ├── InputValidationError
│   └── SchemaValidationError
├── AuthenticationError
└── AuthorizationError
```

**Rules (SRP)**:
- Each exception represents one error type
- An exception contains: error_code, message, details (optional)
- Inherits from `AppException` — no bare `Exception`

---

## Centralized Exception Handler (DRY)

- One handler for the entire application — in middleware or at the app level
- Converts exceptions into a standardized HTTP response
- Duplicated try/except in controllers — blocker

### Standardized Response Format

```json
{
    "error": {
        "code": "ENTITY_NOT_FOUND",
        "message": "User with id 123 not found",
        "request_id": "req-abc-123"
    }
}
```

### Exception to HTTP Code Mapping

| Exception | HTTP Code |
|-----------|-----------|
| `InputValidationError` | 400 |
| `AuthenticationError` | 401 |
| `AuthorizationError` | 403 |
| `EntityNotFoundError` | 404 |
| `BusinessRuleViolationError` | 409/422 |
| `ExternalServiceError` | 502 |
| Unknown exception | 500 |

---

## Fail Fast

- Validate at input — guard clauses instead of deep nesting
- Pydantic for validation at system boundaries (API, configuration)
- Invalid data must not penetrate into business logic
- Error messages should be clear and include context

---

## Stack Trace

- In production (DEBUG=False): only error_code + message
- In development (DEBUG=True): full stack trace
- Stack trace is NEVER returned to the client in production

---

## Retry Strategies

| Error Type | Retryable? | Strategy |
|------------|-----------|----------|
| 4xx (client) | No | Return error immediately |
| 5xx (server) | Yes | Exponential backoff |
| Timeout | Yes | Retry with increased timeout |
| Connection error | Yes | Retry with backoff |
| Rate limit (429) | Yes | Retry after Retry-After |

- Exponential backoff: 1s → 2s → 4s → max 30s
- Maximum 3-5 attempts
- Jitter to prevent thundering herd

---

## Prohibitions (blocker)

| Anti-pattern | Why it is bad |
|--------------|---------------|
| `except: pass` | Silent error swallowing — impossible to diagnose |
| `except Exception` without logging | Error is lost |
| try/except in every controller | Duplication (DRY) — use the centralized handler |
| Returning None instead of raising an exception | Hidden error, NullPointerException later |
| String errors instead of typed ones | Cannot be handled programmatically |
| Logging + re-raising the same error twice | Duplication in logs (DRY) |
