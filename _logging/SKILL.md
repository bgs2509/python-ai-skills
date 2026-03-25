---
name: _logging
description: >
  Centralized Python logging (structlog, JSON, Log-Driven Design 11 principles,
  AI-Readable Logging, Correlation ID, sanitization). Use when configuring logging or adding log statements.
---

# Centralized Logging

> Single configuration in `core/logging.py` (SSoT). structlog + JSON in production.

## Log-Driven Design — Key Principles

1. **Levels**: DEBUG (debugging), INFO (normal flow), WARNING (issues), ERROR (attention needed), CRITICAL (system inoperable)
2. **End-to-end identification**: request_id + correlation_id + user_id in all logs
3. **JSON in production**: automatically parseable
4. **Decision logging**: decision (ACCEPT/REJECT/RETRY), reason, conditions
5. **State transitions**: entity, from_state → to_state, reason
6. **ContextVars**: request_id/user_id propagated across all layers without explicit passing

## Centralized Logging by Layer

| Layer | Who Logs |
|-------|----------|
| Incoming HTTP | RequestLoggingMiddleware (automatic) |
| Outgoing HTTP | Base HTTP client (automatic) |
| Database | BaseRepository (automatic) |
| Business logic | Application Services (explicit) |
| Errors | Exception handler (automatic) |

## Sanitization

Automatic masking `***REDACTED***`: password, token, secret, api_key, authorization, credit_card, ssn.

## Prohibitions (blocker)

- `print()` instead of `logger`
- Useless logs ("Entering function")
- Logging large objects in their entirety
- Logging inside loops (N entries instead of one)
- Each module configuring logging independently
- Logging secrets

Full version (AI-Readable Logging, structlog config): see [reference.md](reference.md)
