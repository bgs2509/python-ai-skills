---
name: _docker
description: >
  Python application containerization (Dockerfile multi-stage, Docker Compose,
  health checks, graceful shutdown). Use when creating Dockerfiles or configuring deployment.
---

# Docker

> Multi-stage build. Minimal size, security, layer caching.

## Dockerfile Principles

| Rule | Description |
|------|-------------|
| Multi-stage | Builder → Runtime (minimal image) |
| Non-root | `adduser --disabled-password appuser` + `USER appuser` |
| Layer order | Dependencies → Code (caching) |
| python:3.11-slim | Not python:3.11 |
| No dev dependencies | Runtime only |

## Security

- Non-root user: `adduser --disabled-password appuser` + `USER appuser`
- No secrets in image (no COPY .env, no ARG for secrets)

## Docker Compose

- Healthcheck for every service
- `depends_on` with `condition: service_healthy`
- Secrets via `environment:` (not build args)

## Production Requirements

- Health endpoint `/health` → 200/503
- Graceful shutdown: SIGTERM/SIGINT, 30s timeout
- Configuration: Pydantic Settings (Fail Fast at startup)
- Monitoring: `/metrics` (Prometheus)

Full configuration: see [reference/docker.md](reference/docker.md)
Production requirements: see [reference/production.md](reference/production.md)
