# AI-инструкция для качественной разработки Python-приложений

> **Назначение**: Подключи этот файл как CLAUDE.md — AI сразу знает все принципы качества.
> **Область**: Python 3.11+, production-ready приложения.
> **Формат**: Принципы и правила. Без примеров кода.

---

## ★ СТРОГО ОБЯЗАТЕЛЬНЫЕ файлы

> **НАРУШЕНИЕ = BLOCKER.** Эти файлы читать ВСЕГДА, без исключений, перед любой работой с кодом.

| Файл | Что содержит |
|------|-------------|
| `development/quality-cascade.md` | 17 принципов качества (DRY, KISS, YAGNI, SOLID, SSoT, Security...) |
| `development/logging.md` | Централизованное логирование, Log-Driven Design, AI-Readable Logging |
| `quality/testing.md` | Тестирование: уровни, покрытие ≥90%, паттерны |

---

## Маршрутная таблица

> Читай дополнительные файлы в зависимости от задачи. Если задача попадает в несколько строк — читай все указанные файлы.

| Задача | Какие файлы читать |
|--------|-------------------|
| Новый проект | `architecture/` (все) + `development/code-standards.md` + `development/naming.md` |
| Пишешь код | `development/code-standards.md` + `development/naming.md` + `development/error-handling.md` |
| Работа с БД | `development/database.md` + `development/error-handling.md` |
| HTTP интеграции | `integrations/http-clients.md` + `integrations/caching.md` |
| Настройка CI | `quality/linters.md` + `quality/ci-cd.md` |
| Ревью кода | `development/quality-cascade.md` + `operations/security.md` + `quality/linters.md` |
| Деплой | `operations/production.md` + `operations/security.md` + `operations/secrets-management.md` + `operations/docker.md` |
| Рефакторинг | `development/quality-cascade.md` + `development/code-standards.md` + `process/completion-report.md` |
| Аудит безопасности | `operations/security.md` + `operations/secrets-management.md` + `quality/linters.md` |
| Управление секретами | `operations/secrets-management.md` + `operations/docker.md` |
| Архитектурное решение | `process/adr.md` — создай ADR |
| Фича завершена | `process/completion-report.md` — напиши отчёт |

---

## Выбор архитектуры

Прочитай базовые гайды `architecture/ddd.md` и `architecture/hexagonal.md`, затем выбери профиль:

| Тип приложения | Файл |
|----------------|------|
| Монолит | `architecture/monolith.md` |
| Микросервисы | `architecture/microservices.md` |

---

## Обязательный workflow

### Verify Before Act (ПЕРЕД каждым изменением кода)

| Действие | Проверка ПЕРЕД выполнением |
|----------|---------------------------|
| Создание файла | Файл НЕ существует |
| Редактирование | Сначала прочитать текущее содержимое |
| Удаление | Проверить все зависимости и ссылки |
| Добавление ссылки | Цель существует |
| Написание кода | Нет похожего кода (DRY) |
| Добавление фичи | Это нужно СЕЙЧАС (YAGNI) |

### Changelog (С КАЖДЫМ изменением)

- Формат: [Keep a Changelog](https://keepachangelog.com/)
- Секции: Added, Changed, Deprecated, Removed, Fixed, Security
- Версионирование: Semantic Versioning (MAJOR.MINOR.PATCH)
- Каждый PR/фича → добавь запись в секцию `Unreleased`
- При релизе → `Unreleased` переименовывается в версию с датой

---

## Полный список файлов

### architecture/
| Файл | Описание |
|------|----------|
| `ddd.md` | Domain-Driven Design: слои, сущности, Value Objects, доменные сервисы |
| `hexagonal.md` | Hexagonal Architecture: порты, адаптеры, направление зависимостей |
| `monolith.md` | Специфика монолитов: модульные границы, shared database |
| `microservices.md` | Специфика микросервисов: изоляция, коммуникация, трейсинг |

### development/
| Файл | Описание |
|------|----------|
| `quality-cascade.md` ★ | 17 принципов качества — применяются ВСЕГДА |
| `code-standards.md` | Типизация, docstrings, импорты, метрики кода |
| `naming.md` | Конвенции именования: Python, сервисы, паттерны |
| `error-handling.md` | Централизованная обработка ошибок, иерархия исключений |
| `logging.md` ★ | Централизованное логирование, structlog, Correlation ID |
| `database.md` | Repository-паттерн, миграции, транзакции, N+1 |

### quality/
| Файл | Описание |
|------|----------|
| `testing.md` ★ | 3 уровня тестов, покрытие ≥90%, фикстуры, моки |
| `linters.md` | Ruff, Mypy, Bandit, pre-commit hooks |
| `ci-cd.md` | Pipeline, порядок проверок, coverage gate |

### operations/
| Файл | Описание |
|------|----------|
| `production.md` | Health checks, graceful shutdown, мониторинг |
| `security.md` | OWASP Top 10, валидация, CORS, rate limiting |
| `secrets-management.md` | Env vars, Pydantic Settings, .env.example |
| `docker.md` | Dockerfile, Compose, security, .dockerignore |

### integrations/
| Файл | Описание |
|------|----------|
| `http-clients.md` | HTTP клиент, retry, timeout, Circuit Breaker |
| `caching.md` | Redis, паттерны кэширования, TTL, инвалидация |

### process/
| Файл | Описание |
|------|----------|
| `adr.md` | Шаблон Architecture Decision Record |
| `completion-report.md` | Шаблон отчёта после завершения фичи |

---

**Версия**: 2.0
**Источник**: AIDD-MVP Generator (~68 принципов, адаптировано для production-ready приложений)
