# Тестирование

> Код можно тестировать изолированно (Testability). Зависимости инжектируются (DIP), глобального состояния нет.

---

## Три уровня

| Уровень | Что тестирует | Где | Зависимости |
|---------|---------------|-----|-------------|
| **Unit** | Изолированная логика | `tests/unit/` | Моки |
| **Integration** | Взаимодействие компонентов | `tests/integration/` | Testcontainers (PostgreSQL, Redis) |
| **E2E** | Полные сценарии от API до БД | `tests/e2e/` | Реальная инфраструктура |

---

## Покрытие

- Минимум: ≥90%
- Команда: `pytest --cov=src --cov-fail-under=90`
- CI pipeline: coverage gate — pipeline fails если < 90% (см. `quality/ci-cd.md`)

---

## Именование

Формат: `test_{что}_{сценарий}_{результат}` (общие конвенции именования — см. `development/naming.md`)

Примеры:
- `test_create_user_valid_data_returns_user`
- `test_create_user_duplicate_email_raises_error`
- `test_get_user_not_found_returns_none`

---

## Паттерн: Arrange-Act-Assert

Каждый тест — три чётких блока:
1. **Arrange** — подготовка данных и зависимостей
2. **Act** — выполнение тестируемого действия
3. **Assert** — проверка результата

---

## Фикстуры

- `conftest.py` в каждом уровне (`tests/unit/conftest.py`, `tests/integration/conftest.py`)
- Scope: function (default), module, session — в зависимости от стоимости создания
- Параметризация: `@pytest.mark.parametrize` для тестирования нескольких вариантов
- Общие фикстуры: `tests/conftest.py` (DRY)

---

## Фабрики тестовых данных

- Фабрики в `tests/factories.py` (SSoT для тестовых данных, DRY)
- Создание сущностей с валидными данными по умолчанию
- Переопределение только тех полей, которые важны для теста

---

## Мокирование

- `unittest.mock.AsyncMock` для async зависимостей
- `unittest.mock.patch` для подмены
- Моки — только для внешних зависимостей (DIP позволяет подменять через интерфейс)
- Не мокать внутренние классы и функции — тестируй через публичный интерфейс
- Чрезмерное мокирование — признак плохой архитектуры

---

## Testcontainers

- PostgreSQL: `testcontainers.postgres.PostgresContainer`
- Redis: `testcontainers.redis.RedisContainer`
- Используются в integration тестах
- Контейнер создаётся на session scope, rollback между тестами

---

## Что покрывать обязательно

- Application Services (бизнес-логика)
- Domain Services
- Domain Entities (валидация, бизнес-правила)
- Repositories (CRUD, специфичные запросы)
- API endpoints (status codes, response format)
- Валидация схем (Pydantic)
- Обработка ошибок (все ветки exception handler — см. `development/error-handling.md`)

---

## Что можно исключить

- `__init__.py`
- Конфигурационные файлы
- Абстрактные базовые классы (ABC)
- Простые getters/setters
- Код, сгенерированный Alembic (миграции)

---

## Антипаттерны

| Антипаттерн | Почему плохо |
|-------------|-------------|
| Тест без assert | Ничего не проверяет |
| Тест зависит от порядка выполнения | Нестабильный, ломается при параллельном запуске |
| Тест обращается к внешним сервисам | Нестабильный, зависит от сети |
| Слишком много моков | Тест тестирует моки, не код |
| Один assert на весь файл | Не локализует ошибку |
| Тестовые данные в коде теста (без фабрик) | Дублирование (DRY) |
