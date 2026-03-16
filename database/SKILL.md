---
name: database
description: >
  Работа с БД в Python (Repository-паттерн, Alembic миграции, транзакции, N+1 проблема,
  connection pooling, ORM vs Domain Entities). Используй при работе с базой данных.
---

# Работа с базой данных

> Repository — единственная точка доступа к данным (SSoT, DIP). Бизнес-логика НИКОГДА не обращается к БД напрямую.

## Repository-паттерн

- Интерфейс в Domain (ABC/Protocol), реализация в Infrastructure (DIP)
- Один Repository на сущность (SRP)
- Возвращает доменные сущности, не ORM-модели
- Базовый Repository: get_by_id, get_all, create, update, delete (DRY)

## Миграции (Alembic)

- Единственный инструмент миграций (SSoT)
- Каждая миграция атомарная, откатываемая
- Запрет ручного изменения БД в production

## Ключевые правила

- **SQL injection — blocker**: только параметризованные запросы
- **Транзакции**: границы в Application Service, не в Repository
- **N+1**: joinedload (eager) или selectinload (subquery)
- **Connection pooling**: централизованно, закрытие при shutdown
- **ORM ↔ Entity маппинг**: в Repository (SoC)

## Логирование (автоматическое в BaseRepository)

operation, table, query_type, duration_ms, found, entity_id. Медленные запросы → WARNING.

Полная версия: см. [reference.md](reference.md)
