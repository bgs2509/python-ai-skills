# python-ai-skills — Claude Code Skills

> Коллекция skill'ов для качественной разработки Python 3.11+ приложений.
> Каждый skill — папка с `SKILL.md` (краткая версия) + `reference.md` (полная версия).
> Префикс `_` отличает кастомные skill'ы от встроенных.

---

## Каталог skill'ов

| Skill | Вызов | Описание |
|-------|-------|----------|
| _code-quality | `/_code-quality` | 17 принципов качества (DRY, KISS, YAGNI, SOLID) |
| _error-handling | `/_error-handling` | Иерархия исключений, HTTP-маппинг, retry |
| _security | `/_security` | OWASP Top 10, валидация, секреты |
| _logging | `/_logging` | Structured logging, Correlation ID, санитизация |
| _testing | `/_testing` | 3 уровня тестов, покрытие ≥90%, pytest |
| _database | `/_database` | Repository-паттерн, миграции, транзакции |
| _architecture | `/_architecture` | DDD, Hexagonal, монолит vs микросервисы |
| _linters | `/_linters` | Ruff, Mypy, Bandit, pre-commit, CI pipeline |
| _docker | `/_docker` | Dockerfile, Compose, health checks, production |
| _http | `/_http` | httpx, timeout, retry, Circuit Breaker |
| _caching | `/_caching` | Redis, TTL, инвалидация, graceful degradation |
| _docworkflow | `/_docworkflow` | Пайплайн документации: backlog → commit |
| _adr | `/_adr` | Генератор Architecture Decision Record |
| _report | `/_report` | Генератор отчёта о завершении фичи |
| _init | `/_init` | Инициализация нового проекта |

---

## Когда какой skill использовать

| Задача | Skill'ы |
|--------|---------|
| Пишешь код | _code-quality, _error-handling |
| Ревью кода | _code-quality, _security, _linters |
| Работа с БД | _database, _error-handling |
| HTTP интеграции | _http, _caching |
| Настройка CI | _linters |
| Деплой | _docker, _security |
| Тестирование | _testing |
| Новый проект | _init, _architecture |
| Архитектурное решение | _architecture, _adr |
| Фича завершена | _report, _docworkflow |
| Начало задачи | _docworkflow |

---

## Обязательный workflow

### Verify Before Act (ПЕРЕД каждым изменением кода)

| Действие | Проверка ПЕРЕД выполнением |
|----------|---------------------------|
| Создание файла | Файл НЕ существует |
| Редактирование | Сначала прочитать текущее содержимое |
| Удаление | Проверить все зависимости и ссылки |
| Написание кода | Нет похожего кода (DRY) |
| Добавление фичи | Это нужно СЕЙЧАС (YAGNI) |

### Changelog

- Формат: [Keep a Changelog](https://keepachangelog.com/)
- Секции: Added, Changed, Deprecated, Removed, Fixed, Security
- Каждое изменение → запись в `Unreleased`

---

**Версия**: 3.2
