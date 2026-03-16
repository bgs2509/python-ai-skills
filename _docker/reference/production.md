# Production Requirements

> Требования для production-ready приложения. Конфигурация через Pydantic Settings (SSoT).

---

## Health Checks

- Endpoint `/health` возвращает HTTP 200 при здоровом состоянии, 503 при проблемах
- Проверка подключения к БД, Redis, внешним зависимостям
- Формат ответа: `{"status": "healthy", "checks": {"database": "ok", "redis": "ok"}}`
- Используется оркестратором для перезапуска (см. skill `_docker` (_docker/reference/docker.md))

---

## Graceful Shutdown

- Обработка сигналов SIGTERM и SIGINT
- Завершение текущих HTTP-запросов перед остановкой
- Закрытие соединений с БД и кэшем
- Таймаут на завершение (30 секунд)
- Логирование начала и завершения shutdown (см. skill `_logging` (_logging/reference.md))

---

## Configuration Management (SSoT)

- Все настройки — через Pydantic Settings (единая точка конфигурации)
- Все секреты — через environment variables (см. skill `_security` (_security/reference/secrets-management.md))
- Валидация конфигурации при старте (Fail Fast): обязательные поля без default
- Значения по умолчанию только для опциональных параметров
- Разделение dev/staging/prod через `ENVIRONMENT` переменную

---

## Error Handling

- Централизованная обработка исключений (см. skill `_error-handling` (_error-handling/reference.md) — DRY)
- Стандартизированный формат ошибок: `{error: {code, message, request_id}}`
- Stack trace только в dev (settings.DEBUG)
- Все необработанные исключения логируются

---

## Мониторинг

- Метрики запросов: count, latency (p50, p95, p99), errors
- Метрики бизнес-логики (custom counters)
- `/metrics` endpoint (Prometheus-совместимый)
- Алерты на критические ошибки

---

## Контекст при старте

При запуске приложения логировать (INFO):
- service_name, version
- environment (dev/staging/prod)
- python_version
- feature_flags
- зависимости (versions)

> Формат логирования — см. skill `_logging` (_logging/reference.md).

---

## Метрики производительности

| Метрика | Порог |
|---------|-------|
| Время отклика API | < 500ms (p95) |
| Доступность | 99% |
