---
name: _init
description: >
  Инициализация нового Python-проекта для Claude Code. Создаёт CLAUDE.md, CHANGELOG.md,
  структуру docs/. Вызывай при старте нового проекта.
disable-model-invocation: true
---

# Инициализация проекта

> Настройка нового Python-проекта для работы с Claude Code и python-ai-skills.

## Обязательные вопросы пользователю

Перед созданием файлов задай эти вопросы:

1. **Название проекта** — как называется проект?
2. **Тип архитектуры** — монолит или микросервисы?
3. **Фреймворк** — FastAPI, Django, CLI, библиотека?
4. **База данных** — PostgreSQL, SQLite, без БД?
5. **Кэш** — Redis, без кэша?
6. **Описание** — 1-2 предложения: что делает проект?

## Создаваемые файлы

### 1. CLAUDE.md (в корне проекта)

```markdown
# {Название проекта}

## Описание
{Описание из ответа пользователя}

## Архитектура
- Тип: {монолит/микросервисы}
- Фреймворк: {FastAPI/Django/...}
- БД: {PostgreSQL/SQLite/нет}
- Кэш: {Redis/нет}

## Стандарты
Этот проект следует стандартам python-ai-skills (глобальные skill'ы).
```

### 2. CHANGELOG.md

```markdown
# Changelog

Формат: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Версионирование: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Инициализация проекта
```

### 3. Структура docs/

```
docs/
├── backlog/     # Задачи (TASK-NNN)
├── plans/       # Планы реализации
├── adr/         # Архитектурные решения
└── reports/     # Отчёты о выполнении
```

### 4. .claude/settings.local.json (если не существует)

```json
{
  "permissions": {
    "allow": []
  }
}
```

## После создания

Сообщи пользователю:
- Какие файлы созданы
- Какие skill'ы доступны глобально (перечисли основные)
- Как вызвать skill: `/_code-quality`, `/_adr` и т.д.
