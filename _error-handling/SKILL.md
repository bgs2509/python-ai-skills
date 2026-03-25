---
name: _error-handling
description: >
  Centralized Python error handling (AppException hierarchy, HTTP mapping,
  retry strategies, Fail Fast). Use when writing exception handling, middleware, or retry logic.
---

# Error Handling

> Centralized handling — a single exception handler (SSoT, DRY). Duplicated try/except is a blocker.

## Exception Hierarchy

All in `core/exceptions.py`:

```
AppException (base)
├── DomainError (EntityNotFound, BusinessRuleViolation, InvalidState)
├── InfrastructureError (Database, ExternalService, Cache)
├── ValidationError (InputValidation, SchemaValidation)
├── AuthenticationError
└── AuthorizationError
```

## HTTP Mapping

| Exception | HTTP |
|-----------|------|
| InputValidationError | 400 |
| AuthenticationError | 401 |
| AuthorizationError | 403 |
| EntityNotFoundError | 404 |
| BusinessRuleViolation | 409/422 |
| ExternalServiceError | 502 |
| Unknown | 500 |

## Retry Strategies

| Error | Retry? | Strategy |
|-------|--------|----------|
| 4xx | No | Return immediately |
| 5xx, Timeout, Connection | Yes | Exponential backoff (1→2→4→max 30s), 3-5 attempts, jitter |
| Rate limit (429) | Yes | After Retry-After |

## Rules

- One handler for the entire application (middleware)
- Inherit from `AppException`, not bare `Exception`
- Fail Fast: guard clauses, Pydantic at boundaries
- Stack trace only in dev (DEBUG=True)

## Prohibitions (blocker)

`except: pass` | `except Exception` without logging | try/except in every controller | returning None instead of raising an exception

Full version: see [reference.md](reference.md)
