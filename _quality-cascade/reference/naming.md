# Конвенции именования

> Единообразие важнее личных предпочтений (CoC). Имена должны быть явными и описательными (Explicit > Implicit).

---

## Python

| Элемент | Стиль | Пример |
|---------|-------|--------|
| Модуль/файл | snake_case | `user_service.py` |
| Класс | PascalCase | `UserService`, `OrderRepository` |
| Функция/метод | snake_case | `get_user_by_id()` |
| Переменная | snake_case | `user_name`, `is_active` |
| Константа | UPPER_SNAKE | `MAX_RETRIES`, `DEFAULT_PAGE_SIZE` |
| Приватный | _prefix | `_internal_method()` |
| Исключение | PascalCase + Error | `NotFoundError`, `ValidationError` |
| Pydantic-схема | PascalCase | `UserCreate`, `UserResponse` |
| DTO | PascalCase + DTO | `CreateUserDTO`, `UserDTO` |

---

## Паттерны именования по слоям

| Слой | Паттерн | Пример |
|------|---------|--------|
| Domain Entity | Существительное | `User`, `Order`, `Payment` |
| Value Object | Концепт | `Money`, `Email`, `DateRange` |
| Repository | Entity + Repository | `UserRepository`, `OrderRepository` |
| Application Service | Действие + Service | `UserService`, `PaymentService` |
| Use Case | Глагол + Существительное | `CreateUser`, `ProcessPayment` |
| API Router | Множественное число | `/users`, `/orders` |
| Middleware | Назначение + Middleware | `RequestLoggingMiddleware` |

---

## Именование сервисов (микросервисы)

- По Bounded Context: `user-service`, `order-service`
- Формат: kebab-case для имён сервисов
- Docker: `{context}-api`, `{context}-data`
- Переменные окружения: `{CONTEXT}_API_URL`

---

## Антипаттерны

| Плохо | Хорошо | Почему |
|-------|--------|--------|
| `data`, `info`, `temp` | `user_data`, `order_info` | Неинформативно (Explicit) |
| `do_stuff()` | `send_notification()` | Не описывает действие |
| `Manager`, `Handler` (без контекста) | `UserService`, `PaymentProcessor` | Слишком общее |
| `utils.py` (свалка) | Конкретные модули по назначению | Нарушает SRP |
| `process()` | `validate_order()` | Скрывает намерение |
