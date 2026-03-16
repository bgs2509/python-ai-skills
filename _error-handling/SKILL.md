---
name: _error-handling
description: >
  Централизованная обработка ошибок Python (AppException иерархия, HTTP-маппинг,
  retry-стратегии, Fail Fast). Используй при написании exception handling, middleware, retry логики.
---

# Обработка ошибок

> Централизованная обработка — единый exception handler (SSoT, DRY). Дублирование try/except — blocker.

## Иерархия исключений

Все в `core/exceptions.py`:

```
AppException (базовый)
├── DomainError (EntityNotFound, BusinessRuleViolation, InvalidState)
├── InfrastructureError (Database, ExternalService, Cache)
├── ValidationError (InputValidation, SchemaValidation)
├── AuthenticationError
└── AuthorizationError
```

## HTTP-маппинг

| Исключение | HTTP |
|------------|------|
| InputValidationError | 400 |
| AuthenticationError | 401 |
| AuthorizationError | 403 |
| EntityNotFoundError | 404 |
| BusinessRuleViolation | 409/422 |
| ExternalServiceError | 502 |
| Неизвестное | 500 |

## Retry-стратегии

| Ошибка | Retry? | Стратегия |
|--------|--------|-----------|
| 4xx | Нет | Вернуть сразу |
| 5xx, Timeout, Connection | Да | Exponential backoff (1→2→4→max 30s), 3-5 попыток, jitter |
| Rate limit (429) | Да | После Retry-After |

## Правила

- Один handler для всего приложения (middleware)
- Наследование от `AppException`, не голых `Exception`
- Fail Fast: guard clauses, Pydantic на границах
- Stack trace только в dev (DEBUG=True)

## Запреты (blocker)

`except: pass` | `except Exception` без логирования | try/except в каждом контроллере | возврат None вместо исключения

Полная версия: см. [reference.md](reference.md)
