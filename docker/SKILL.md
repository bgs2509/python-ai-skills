---
name: docker
description: >
  Контейнеризация Python-приложений (Dockerfile multi-stage, Docker Compose, security hardening,
  health checks, graceful shutdown). Используй при создании Dockerfile, настройке деплоя.
---

# Docker

> Multi-stage build. Минимальный размер, безопасность, кэширование слоёв.

## Dockerfile принципы

| Правило | Описание |
|---------|----------|
| Multi-stage | Builder → Runtime (минимальный образ) |
| Non-root | `adduser --disabled-password appuser` + `USER appuser` |
| Порядок слоёв | Зависимости → Код (кэширование) |
| python:3.11-slim | Не python:3.11 |
| Без dev-зависимостей | Только runtime |

## Security

- `security_opt: no-new-privileges:true`
- `cap_drop: ALL`
- `read_only: true` + tmpfs для /tmp
- Без секретов в image (не COPY .env, не ARG для секретов)

## Docker Compose

- Healthcheck для каждого сервиса
- `depends_on` с `condition: service_healthy`
- Секреты через `environment:` (не build args)

## Production requirements

- Health endpoint `/health` → 200/503
- Graceful shutdown: SIGTERM/SIGINT, 30s timeout
- Конфигурация: Pydantic Settings (Fail Fast при старте)
- Мониторинг: `/metrics` (Prometheus)

Полная конфигурация: см. [reference/docker.md](reference/docker.md)
Production requirements: см. [reference/production.md](reference/production.md)
