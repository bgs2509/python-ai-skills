# Обработка ошибок

> **Централизованная** обработка — единый exception handler (SSoT, DRY). Исключения определяются в одном месте. Дублирование try/except блоков — blocker.

---

## Иерархия исключений (SSoT)

Все исключения определяются в `core/exceptions.py`:

```
AppException (базовый)
├── DomainError
│   ├── EntityNotFoundError
│   ├── BusinessRuleViolationError
│   └── InvalidStateError
├── InfrastructureError
│   ├── DatabaseError
│   ├── ExternalServiceError
│   └── CacheError
├── ValidationError
│   ├── InputValidationError
│   └── SchemaValidationError
├── AuthenticationError
└── AuthorizationError
```

**Правила (SRP)**:
- Каждое исключение — один тип ошибки
- Исключение содержит: error_code, message, details (опционально)
- Наследование от `AppException` — никаких голых `Exception`

---

## Централизованный exception handler (DRY)

- Один handler для всего приложения — в middleware или app-level
- Преобразование исключений в стандартизированный HTTP-ответ
- Дублирование try/except в контроллерах — blocker

### Стандартизированный формат ответа

```json
{
    "error": {
        "code": "ENTITY_NOT_FOUND",
        "message": "User with id 123 not found",
        "request_id": "req-abc-123"
    }
}
```

### Маппинг исключений на HTTP-коды

| Исключение | HTTP код |
|------------|----------|
| `InputValidationError` | 400 |
| `AuthenticationError` | 401 |
| `AuthorizationError` | 403 |
| `EntityNotFoundError` | 404 |
| `BusinessRuleViolationError` | 409/422 |
| `ExternalServiceError` | 502 |
| Неизвестное исключение | 500 |

---

## Fail Fast

- Валидация на входе — guard clauses вместо глубокой вложенности
- Pydantic для валидации на границах системы (API, конфигурация)
- Невалидные данные не должны проникать в бизнес-логику
- Сообщения об ошибках — понятные, с контекстом

---

## Stack Trace

- В production (DEBUG=False): только error_code + message
- В development (DEBUG=True): полный stack trace
- Stack trace НИКОГДА не отдаётся клиенту в production

---

## Retry-стратегии

| Тип ошибки | Retryable? | Стратегия |
|------------|-----------|-----------|
| 4xx (клиентская) | Нет | Вернуть ошибку сразу |
| 5xx (серверная) | Да | Exponential backoff |
| Timeout | Да | Retry с увеличенным timeout |
| Connection error | Да | Retry с backoff |
| Rate limit (429) | Да | Retry после Retry-After |

- Exponential backoff: 1s → 2s → 4s → max 30s
- Максимум 3-5 попыток
- Jitter для предотвращения thundering herd

---

## Запреты (blocker)

| Антипаттерн | Почему плохо |
|-------------|-------------|
| `except: pass` | Тихое проглатывание ошибок — невозможно диагностировать |
| `except Exception` без логирования | Ошибка теряется |
| try/except в каждом контроллере | Дублирование (DRY) — используй централизованный handler |
| Возврат None вместо исключения | Скрытая ошибка, NullPointerException позже |
| Строковые ошибки вместо типизированных | Невозможно обработать программно |
| Логирование + проброс одной ошибки дважды | Дублирование в логах (DRY) |
