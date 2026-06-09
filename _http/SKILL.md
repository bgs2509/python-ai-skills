---
name: _http
description: >
  Python HTTP clients (httpx AsyncClient, timeout, retry, Circuit Breaker,
  centralized logging).
  TRIGGER when: integrating an external API, configuring an httpx client,
  timeout/retry/circuit-breaker on transport, client-side request logging.
  SKIP when: server-side endpoint error mapping (use _error-handling),
  caching responses (use _caching), database access (use _database).
---

# HTTP Clients

> Single base HTTP client (DRY, SSoT). All outgoing calls go through it.

## httpx AsyncClient

- One instance per application lifetime
- Connection pooling
- Specific clients inherit from the base client

## Timeout (required)

| Parameter | Recommendation |
|-----------|---------------|
| connect | 5s |
| read | 30s |
| write | 10s |
| pool | 10s |

No timeout — blocker.

## Retry

Retryable: 5xx, Timeout, Connection error, 429 (after Retry-After).
Non-retryable: 4xx.
Strategy: Exponential backoff + jitter, 3-5 attempts.

## Circuit Breaker

| State | Description |
|-------|-------------|
| Closed | Normal operation |
| Open | Error threshold exceeded → fallback |
| Half-Open | Probe request |

## Centralized Logging (automatic)

service, operation, method, endpoint, duration_ms, status_code, error_type, is_retryable.

Full version: see [reference.md](reference.md)
