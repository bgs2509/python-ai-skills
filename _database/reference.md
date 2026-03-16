# Работа с базой данных

> Repository — единственная точка доступа к данным (SSoT, DIP). Бизнес-логика НИКОГДА не обращается к БД напрямую (SoC).

---

## Repository-паттерн

- Интерфейс определяется в Domain (ABC/Protocol) — DIP
- Реализация — в Infrastructure
- Один Repository на одну сущность (SRP)
- Repository возвращает доменные сущности, не ORM-модели
- Базовый Repository с общими операциями (CRUD) — DRY

### Базовый Repository (DRY)

Общие операции определяются один раз в базовом классе:
- `get_by_id(id) -> Entity | None`
- `get_all(filters, pagination) -> list[Entity]`
- `create(entity) -> Entity`
- `update(entity) -> Entity`
- `delete(id) -> None`

Специфичные операции — в конкретных Repository:
- `UserRepository.get_by_email(email) -> User | None`
- `OrderRepository.get_by_status(status) -> list[Order]`

---

## Миграции (Alembic)

- Alembic как единственный инструмент миграций (SSoT)
- Автогенерация: `alembic revision --autogenerate -m "description"`
- Каждая миграция — атомарная, откатываемая (downgrade)
- Именование: `{номер}_{описание}.py`
- Миграции хранятся в git
- Запрет ручного изменения БД в production — только через миграции

---

## Connection Pooling

- Пул соединений настраивается централизованно (SSoT)
- Параметры: pool_size, max_overflow, pool_timeout, pool_recycle
- Закрытие соединений при graceful shutdown
- Мониторинг: количество активных/ожидающих соединений

---

## Параметризованные запросы

- SQL injection — blocker
- Всегда использовать параметризованные запросы (SQLAlchemy bindparams)
- Никакого форматирования строк для SQL
- ORM предпочтительнее raw SQL

---

## Транзакции

- Явные границы транзакций — в Application Service (SoC)
- Repository не управляет транзакциями — это ответственность Application слоя
- Unit of Work паттерн для согласованных операций
- Компенсирующие транзакции для откатов в распределённых системах

---

## N+1 проблема

- Обнаружение: WARNING в логах при > N запросов к одной таблице за один request
- Решение: joinedload (eager loading) или selectinload (subquery)
- Правило: для связей, которые всегда нужны — joinedload, для опциональных — selectinload
- Мониторинг количества запросов на request

---

## Логирование операций с БД (DRY)

Логирование реализуется в базовом Repository — автоматически для всех операций:

| Поле | Описание |
|------|----------|
| operation | create/read/update/delete |
| table | Имя таблицы |
| query_type | SELECT/INSERT/UPDATE/DELETE |
| duration_ms | Время выполнения |
| found | Найдена ли запись (для SELECT) |
| entity_id | ID сущности |

Медленные запросы (> порога) — WARNING.

> Подробнее о формате логирования — см. skill `_logging` (_logging/reference.md).

---

## ORM-модели vs Domain Entities

- ORM-модели — в Infrastructure (привязаны к БД)
- Domain Entities — в Domain (чистая бизнес-логика)
- Маппинг ORM ↔ Entity — в Repository (SoC)
- ORM-модели не проникают выше Infrastructure слоя
