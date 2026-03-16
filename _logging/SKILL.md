---
name: _logging
description: >
  Централизованное логирование Python (structlog, JSON, Log-Driven Design 11 принципов,
  AI-Readable Logging, Correlation ID, санитизация). Используй при настройке логирования, добавлении логов.
---

# Централизованное логирование

> Единая конфигурация в `core/logging.py` (SSoT). structlog + JSON в production.

## Log-Driven Design — ключевые принципы

1. **Уровни**: DEBUG (отладка), INFO (нормальный ход), WARNING (проблемы), ERROR (внимание), CRITICAL (система неработоспособна)
2. **Сквозная идентификация**: request_id + correlation_id + user_id во всех логах
3. **JSON в production**: парсятся автоматически
4. **Логирование решений**: decision (ACCEPT/REJECT/RETRY), reason, conditions
5. **Переходы состояний**: entity, from_state → to_state, reason
6. **ContextVars**: request_id/user_id через все слои без явной передачи

## Централизованное логирование по слоям

| Слой | Кто логирует |
|------|-------------|
| Входящие HTTP | RequestLoggingMiddleware (автоматически) |
| Исходящие HTTP | Базовый HTTP-клиент (автоматически) |
| БД | BaseRepository (автоматически) |
| Бизнес-логика | Application Services (явно) |
| Ошибки | Exception handler (автоматически) |

## Санитизация

Автоматическая маскировка `***REDACTED***`: password, token, secret, api_key, authorization, credit_card, ssn.

## Запреты (blocker)

- `print()` вместо `logger`
- Бесполезные логи ("Entering function")
- Логирование больших объектов целиком
- Логирование в цикле (N записей вместо одной)
- Каждый модуль настраивает логирование по-своему
- Логирование секретов

Полная версия (AI-Readable Logging, structlog конфиг): см. [reference.md](reference.md)
