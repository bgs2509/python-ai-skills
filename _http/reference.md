# HTTP Clients

> A single base HTTP client (DRY, SSoT). All outgoing HTTP calls go through it. Logging and error handling are centralized.

---

## Base HTTP Client (DRY)

- One base class for all HTTP clients
- Built-in logging for every call (DRY — do not duplicate in each client)
- Built-in error handling (DRY — see skill `_error-handling` (_error-handling/reference.md))
- Concrete clients inherit from the base

---

## httpx AsyncClient

- Asynchronous HTTP client (Async-First)
- Connection pooling — connection reuse
- One instance per application lifetime (created at startup, closed at shutdown)

---

## Timeout

Timeouts are set explicitly (Explicit > Implicit):

| Parameter | Purpose | Recommendation |
|-----------|---------|----------------|
| connect | Time to establish a connection | 5s |
| read | Time to receive a response | 30s |
| write | Time to send a request | 10s |
| pool | Time to wait for an available connection | 10s |

Without a timeout — blocker. Infinite waiting = application hang.

---

## Retry

The base HTTP client automatically applies retry strategies.

> Table of retryable/non-retryable errors, backoff parameters — see skill `_error-handling` (_error-handling/reference.md) section "Retry Strategies".

---

## Centralized Logging (DRY)

Every HTTP call is automatically logged by the base client:

| Field | Description |
|-------|-------------|
| service | Name of the called service |
| operation | Operation (get_user, create_order) |
| method | HTTP method (GET, POST, ...) |
| endpoint | URL |
| duration_ms | Execution time |
| status_code | HTTP response code |
| error_type | Error type (if any) |
| is_retryable | Whether it can be retried |

> Logging format — see skill `_logging` (_logging/reference.md).

---

## Centralized Error Handling (DRY)

- HTTP errors are mapped to `ExternalServiceError` (from the `AppException` hierarchy)
- Handling is in the base client, not in each individual call

> Exception hierarchy — see skill `_error-handling` (_error-handling/reference.md).

---

## Circuit Breaker

For critical external dependencies:

| State | Description |
|-------|-------------|
| **Closed** | Normal operation, requests go through |
| **Open** | Error threshold exceeded, requests are not sent (fallback) |
| **Half-Open** | Probe request to check recovery |

- Logging of state transitions (see skill `_logging` (_logging/reference.md) — state transitions)
- Fallback: cached data, default value, or an error with a clear message
