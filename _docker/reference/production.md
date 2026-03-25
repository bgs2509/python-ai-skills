# Production Requirements

> Requirements for a production-ready application. Configuration via Pydantic Settings (SSoT).

---

## Health Checks

- Endpoint `/health` returns HTTP 200 when healthy, 503 when there are issues
- Checks connectivity to DB, Redis, external dependencies
- Response format: `{"status": "healthy", "checks": {"database": "ok", "redis": "ok"}}`
- Used by the orchestrator for restarts (see skill `_docker` (_docker/reference/docker.md))

---

## Graceful Shutdown

- Handling SIGTERM and SIGINT signals
- Completing current HTTP requests before stopping
- Closing DB and cache connections
- Timeout for shutdown (30 seconds)
- Logging the start and completion of shutdown (see skill `_logging` (_logging/reference.md))

---

## Configuration Management (SSoT)

- All settings via Pydantic Settings (single configuration point)
- All secrets via environment variables (see skill `_security` (_security/reference/secrets-management.md))
- Configuration validation at startup (Fail Fast): required fields without defaults
- Default values only for optional parameters
- dev/staging/prod separation via the `ENVIRONMENT` variable

---

## Error Handling

- Centralized exception handling (see skill `_error-handling` (_error-handling/reference.md) — DRY)
- Standardized error format: `{error: {code, message, request_id}}`
- Stack trace only in dev (settings.DEBUG)
- All unhandled exceptions are logged

---

## Monitoring

- Request metrics: count, latency (p50, p95, p99), errors
- Business logic metrics (custom counters)
- `/metrics` endpoint (Prometheus-compatible)
- Alerts on critical errors

---

## Startup Context

On application startup, log (INFO):
- service_name, version
- environment (dev/staging/prod)
- python_version
- feature_flags
- dependencies (versions)

> Logging format — see skill `_logging` (_logging/reference.md).

---

## Performance Metrics

| Metric | Threshold |
|--------|-----------|
| API response time | < 500ms (p95) |
| Availability | 99% |
