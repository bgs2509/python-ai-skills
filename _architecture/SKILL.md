---
name: _architecture
description: >
  Архитектура Python-приложений: DDD (слои, сущности, Value Objects), Hexagonal (порты, адаптеры).
  Выбор между монолитом и микросервисами. Используй при проектировании структуры проекта.
---

# Архитектура приложений

> Domain-Driven Design + Hexagonal Architecture. Domain — единственный источник бизнес-правил (SSoT).

## Слои и зависимости

```
api/ → application/ → domain/ ← infrastructure/
```

| Слой | Зависит от | Содержит |
|------|-----------|----------|
| Domain | Ничего | Сущности, Value Objects, доменные сервисы, интерфейсы |
| Application | Domain | Use Cases, Application Services, DTO |
| API | Application | Контроллеры, middleware, HTTP-схемы |
| Infrastructure | Domain | Репозитории, HTTP-клиенты, БД, кэш |

**DIP**: Domain определяет интерфейсы → Infrastructure реализует.

## Ключевые концепции

- **Entities**: уникальная идентичность, содержат поведение (не анемичные модели)
- **Value Objects**: immutable, самовалидирующиеся (Money, Email, Address)
- **Доменные сервисы**: логика между несколькими сущностями, stateless
- **Ports & Adapters**: входящие (Use Case) и исходящие (Repository) порты
- **DI**: связывание в точке входа (main.py / dependencies.py)

## Выбор: монолит vs микросервисы

| Критерий | Монолит | Микросервисы |
|----------|---------|-------------|
| Команда | 1-5 человек | 5+ человек |
| Стадия | Начальная | Зрелая |
| Масштабирование | Единое | Независимое |
| Деплой | Простой | Сложный |

Подробнее:
- DDD (слои, сущности, Bounded Contexts): [reference/ddd.md](reference/ddd.md)
- Hexagonal (порты, адаптеры, структура): [reference/hexagonal.md](reference/hexagonal.md)
- Монолит: [reference/monolith.md](reference/monolith.md)
- Микросервисы: [reference/microservices.md](reference/microservices.md)
