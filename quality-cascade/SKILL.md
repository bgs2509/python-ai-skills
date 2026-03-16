---
name: quality-cascade
description: >
  17 принципов качества Python-кода (DRY, KISS, YAGNI, SOLID, SSoT, LoD, Fail Fast).
  Используй при ревью кода, рефакторинге, написании новых модулей.
  Проверяет code-standards и naming conventions.
context: fork
agent: Explore
---

# Quality Cascade — 17 принципов качества

> Все 17 принципов применяются ВСЕГДА. Нарушение любого — blocker.

## Базовые (1-7)

1. **DRY** — нет дублирования логики. Общая логика — в переиспользуемых модулях.
2. **KISS** — простые решения. Функция ≤50 строк, вложенность ≤4, цикломатическая сложность <10.
3. **YAGNI** — только необходимое. Никакого кода "на будущее".
4. **SoC** — разделяй ответственности. Бизнес-логика отдельно от I/O.
5. **SSoT** — каждый тип данных определён в одном месте.
6. **CoC** — следуй конвенциям проекта.
7. **Security** — безопасность на всех уровнях.

## SOLID (8-12)

8. **SRP** — одна функция = одна задача. Класс ≤500 строк.
9. **OCP** — открыт для расширения, закрыт для модификации.
10. **LSP** — подтипы заменяют родительские типы без нарушений.
11. **ISP** — маленькие специфичные интерфейсы.
12. **DIP** — зависимость от абстракций, инжекция зависимостей.

## Дополнительные (13-17)

13. **LoD** — минимальная связанность, нет цепочек `a.b.c.d`.
14. **Fail Fast** — валидируй на входе, guard clauses.
15. **Explicit > Implicit** — type hints, именованные константы.
16. **Composition > Inheritance** — наследование глубиной ≤2-3.
17. **Testability** — зависимости инжектируются, нет глобального состояния.

## Красные флаги

`except: pass` | God class >500 строк | magic numbers | copy-paste | `*args/**kwargs` без необходимости

## Централизация (SSoT + DRY)

| Аспект | Где |
|--------|-----|
| Конфигурация | `core/config.py` (Pydantic Settings) |
| Логирование | `core/logging.py` (structlog) |
| Обработка ошибок | `core/exceptions.py` + единый handler |
| DI | `api/dependencies.py` |
| Валидация | Pydantic-схемы на границах |

Полные принципы с примерами: см. [reference/quality-cascade.md](reference/quality-cascade.md)
Стандарты кода: см. [reference/code-standards.md](reference/code-standards.md)
Именование: см. [reference/naming.md](reference/naming.md)
