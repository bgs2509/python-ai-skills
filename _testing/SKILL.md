---
name: _testing
description: >
  Тестирование Python (pytest, 3 уровня тестов, покрытие ≥90%, AAA-паттерн,
  фикстуры, моки, Testcontainers). Используй при написании тестов, настройке test infrastructure.
---

# Тестирование

> Зависимости инжектируются (DIP), глобального состояния нет (Testability).

## Три уровня

| Уровень | Что | Где | Зависимости |
|---------|-----|-----|-------------|
| Unit | Изолированная логика | `tests/unit/` | Моки |
| Integration | Взаимодействие | `tests/integration/` | Testcontainers |
| E2E | Полные сценарии | `tests/e2e/` | Реальная инфраструктура |

## Покрытие: ≥90%

`pytest --cov=src --cov-fail-under=90`

## Паттерн: Arrange-Act-Assert

Каждый тест — три блока: подготовка → действие → проверка.

## Именование

`test_{что}_{сценарий}_{результат}` — например `test_create_user_duplicate_email_raises_error`

## Ключевые правила

- Фикстуры в `conftest.py` каждого уровня (DRY)
- Фабрики в `tests/factories.py` (SSoT для тестовых данных)
- Моки — только для внешних зависимостей
- `@pytest.mark.parametrize` для нескольких вариантов
- Testcontainers: PostgreSQL, Redis на session scope

## Обязательно покрывать

Application Services, Domain Entities, Repositories, API endpoints, валидация, exception handler

## Антипаттерны (blocker)

Тест без assert | зависимость от порядка | внешние сервисы | слишком много моков

Полная версия: см. [reference.md](reference.md)
