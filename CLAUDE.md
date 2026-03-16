# python-ai-skills — Claude Code Skills

> Коллекция skill'ов для качественной разработки Python 3.11+ приложений.
> Каждый skill — папка с `SKILL.md` (краткая версия) + `reference.md` (полная версия).

---

## Каталог skill'ов

| Skill | Вызов | Описание |
|-------|-------|----------|
| quality-cascade | `/quality-cascade` | 17 принципов качества (DRY, KISS, YAGNI, SOLID) |
| error-handling | `/error-handling` | Иерархия исключений, HTTP-маппинг, retry |
| security | `/security` | OWASP Top 10, валидация, секреты |
| logging | `/logging` | Structured logging, Correlation ID, санитизация |
| testing | `/testing` | 3 уровня тестов, покрытие ≥90%, pytest |
| database | `/database` | Repository-паттерн, миграции, транзакции |
| architecture | `/architecture` | DDD, Hexagonal, монолит vs микросервисы |
| linters | `/linters` | Ruff, Mypy, Bandit, pre-commit, CI pipeline |
| docker | `/docker` | Dockerfile, Compose, security, production |
| http-clients | `/http-clients` | httpx, timeout, retry, Circuit Breaker |
| caching | `/caching` | Redis, TTL, инвалидация, graceful degradation |
| workflow | `/workflow` | Пайплайн документации: backlog → commit |
| create-adr | `/create-adr` | Генератор Architecture Decision Record |
| completion-report | `/completion-report` | Генератор отчёта о завершении фичи |
| init-project | `/init-project` | Инициализация нового проекта |

---

## Когда какой skill использовать

| Задача | Skill'ы |
|--------|---------|
| Пишешь код | quality-cascade, error-handling |
| Ревью кода | quality-cascade, security, linters |
| Работа с БД | database, error-handling |
| HTTP интеграции | http-clients, caching |
| Настройка CI | linters |
| Деплой | docker, security |
| Тестирование | testing |
| Новый проект | init-project, architecture |
| Архитектурное решение | architecture, create-adr |
| Фича завершена | completion-report, workflow |
| Начало задачи | workflow |

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

**Версия**: 3.0
