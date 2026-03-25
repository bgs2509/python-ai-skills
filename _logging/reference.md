# Centralized Logging

> **Centralized** configuration — a single module `core/logging.py` (SSoT, DRY). Every module uses the unified configuration, not its own. From logs alone, an AI agent can reconstruct the full call stack of any request.

---

## Log-Driven Design — 11 Principles

| # | Principle | Essence |
|---|-----------|---------|
| 1 | **Log levels** | DEBUG — debugging, INFO — normal flow, WARNING — potential issues, ERROR — requires attention, CRITICAL — system is non-operational. |
| 2 | **Cross-cutting identification** | request_id (unique operation ID), correlation_id (client ID, does not change), user_id (after authentication). All logs contain request_id. |
| 3 | **JSON format** | In production, all logs are in JSON. Parsed automatically. |
| 4 | **Decision logging** | At business logic branching points, record: decision (ACCEPT/REJECT/RETRY/SKIP/FALLBACK), reason, evaluated_conditions, actual_values. |
| 5 | **State transitions** | On entity state change: entity_type, entity_id, from_state, to_state, reason, valid_next_states. |
| 6 | **Incoming requests** | Middleware automatically logs: method, path, duration_ms, status_code, client_ip, auth_context, error_code. |
| 7 | **Outgoing HTTP calls** | For each external call: service, operation, method, endpoint, duration_ms, status_code, error_type, is_retryable. |
| 8 | **DB operations** | For each operation: operation, table, query_type, duration_ms, found, entity_id. Slow queries — WARNING. |
| 9 | **Startup context** | On application startup: service_name, version, environment, python_version, feature_flags, dependencies. |
| 10 | **ContextVars** | Use contextvars to propagate request_id and user_id across all layers without explicit passing. |
| 11 | **Anti-patterns** | Prohibited: useless logs ("Entering function"), logging large objects in full, logging in loops, duplicating already-logged information. |

---

## AI-Readable Logging

> An AI agent, reading ONLY the logs, fully understands what the program does — which functions are called, in what order, with what parameters and results.

| Principle | Description |
|-----------|-------------|
| **Full log coverage** | Every function, method, and class logs entry and exit. |
| **Function entry** | Function name, input parameters (with secret sanitization), caller (who called). |
| **Function exit** | Result (type + brief description), execution duration, success/failure. |
| **Class lifecycle** | Instance creation, dependency initialization, destruction. |
| **Execution flow** | From logs alone, the full call stack of any request can be reconstructed. |
| **Branching** | Every if/else/match logs which branch was chosen and why (condition + result). |
| **Loops** | Loop start (expected iteration count), completion (actual count), anomalies (0 iterations, too many). |
| **Detail levels** | DEBUG — call tracing, INFO — business events, WARNING/ERROR — issues. |
| **Module context** | Every log entry contains module, class, method — AI can build a call map. |
| **Machine-readable format** | JSON with a fixed field schema. AI parses without guessing. |
| **Correlation** | request_id + span_id for reconstructing the call tree within a single request. |
| **Self-documentation** | Logs replace missing documentation — AI reads logs instead of reading code. |

---

## Structured Logging (structlog)

- Unified configuration in `core/logging.py` (SSoT)
- structlog as the primary library
- JSON format in production, human-readable in development
- Processors: add_log_level, timestamper, StackInfoRenderer
- Integration with stdlib logging for third-party libraries

---

## Correlation ID

- `request_id` — generated at entry (middleware), unique per request
- `correlation_id` — comes from the client (`X-Correlation-ID` header), preserved throughout the chain
- `user_id` — added after authentication
- Storage via `contextvars` — accessible across all layers without explicit passing (DRY)
- In microservices: correlation_id is passed between services via HTTP headers

---

## Sanitization (Security)

Sensitive fields are automatically masked in logs as `***REDACTED***`:

- password, passwd
- token, access_token, refresh_token
- secret, api_key, api_secret
- authorization
- credit_card, card_number
- ssn, social_security

Sanitization is implemented as a structlog processor — in one place (SSoT, DRY).

---

## Centralized Logging by Layer (DRY)

| Layer | How to log | Who logs |
|-------|-----------|----------|
| Incoming HTTP | Middleware (automatically) | RequestLoggingMiddleware |
| Outgoing HTTP | Base HTTP client (automatically) | Single client — see skill `_http` (_http/reference.md) |
| DB operations | Base Repository class (automatically) | BaseRepository |
| Business logic | Explicitly in Application Services | Developer |
| Errors | Centralized handler (automatically) | Exception handler — see skill `_error-handling` (_error-handling/reference.md) |

**Prohibition (DRY)**: do not duplicate logging that is already performed automatically (middleware, base client, handler).

---

## Prohibitions (blocker)

| Anti-pattern | Why it is bad |
|--------------|---------------|
| Useless logs ("Entering function", "Done") | Noise, carry no information |
| Logging large objects in full | Log overflow, slowdown |
| Logging in a loop | N entries instead of one (start + summary) |
| Duplicating already-logged information | Violates DRY |
| Each module configures logging on its own | Violates SSoT |
| `print()` instead of `logger` | Not structured, not parseable |
| Logging sensitive data | Security violation |
