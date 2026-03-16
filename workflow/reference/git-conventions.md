# Git Conventions

> Правила оформления коммитов и работы с git.

---

## Формат коммит-сообщения

```
TASK-NNN: <type>: <description>
```

### Типы (type)

| Тип | Когда |
|-----|-------|
| `feat` | Новая функциональность |
| `fix` | Исправление бага |
| `refactor` | Рефакторинг без изменения поведения |
| `docs` | Изменения в документации |
| `test` | Добавление или изменение тестов |
| `ci` | Изменения CI/CD |
| `chore` | Прочее (зависимости, конфиги) |

### Примеры

```
TASK-001: feat: add user authentication via JWT
TASK-003: fix: handle timeout in HTTP client
TASK-007: docs: add backlog and workflow process
TASK-012: refactor: extract validation to separate module
```

---

## Правила

| Правило | Описание |
|---------|----------|
| Язык | Английский |
| Task ID | Обязателен в начале сообщения |
| Заголовок | Первая строка ≤ 72 символа — краткое "что сделано" |
| Императив | Использовать повелительное наклонение: "add", не "added" |
| Тело | **ОБЯЗАТЕЛЬНО**. Через пустую строку после заголовка. Подробное описание: что изменено, зачем, какие файлы затронуты, какие решения приняты |

---

## Тело коммита (description)

> **Цель:** по `git log` можно восстановить полную историю развития проекта без чтения кода.

Тело коммита должно отвечать на вопросы:

1. **Что сделано** — какие конкретные изменения внесены (файлы, модули, функции)
2. **Зачем** — какую проблему решает, какая задача из backlog
3. **Как** — ключевые решения и подход (не весь код, а суть)
4. **Что затронуто** — список изменённых/созданных/удалённых файлов с пояснением

### Атомарность коммитов

- Коммит должен быть **маленьким** — минимальное количество файлов, одно логическое изменение
- Если задача затрагивает много файлов — разбивать на несколько коммитов по логическим группам
- Каждый коммит должен оставлять проект в рабочем состоянии
- Один коммит = одна мысль, которую можно понять из `git log`

Примеры разбиения большой задачи:
```
TASK-007: docs: add workflow and backlog process
TASK-007: docs: add planning format and git conventions
TASK-007: docs: update ADR and completion report templates with Task ID
TASK-007: docs: add CHANGELOG.md and update routing table
```

### Формат тела

```
TASK-NNN: <type>: <краткий заголовок>

<Подробное описание: что, зачем, как>

Изменения:
- <файл/модуль>: <что сделано и зачем>
- <файл/модуль>: <что сделано и зачем>
```

### Пример

```
TASK-007: docs: add mandatory documentation pipeline

Add 6-step documentation pipeline that every task must follow:
backlog → planning → ADR → changelog → completion report → commit.

Introduce TASK-NNN / PLAN-NNN / ADR-NNN numbering system
with cross-references between all artifacts.
Extract planning format from global CLAUDE.md into process/planning.md (DRY).

Изменения:
- process/workflow.md: сквозной пайплайн 6 этапов с чеклистом
- process/backlog.md: шаблон задачи с нумерацией TASK-NNN
- process/planning.md: формат плана (вынесен из ~/.claude/CLAUDE.md)
- process/git-conventions.md: формат коммитов с Task ID
- CHANGELOG.md: создан в корне проекта
- process/adr.md: добавлено поле Task ID
- process/completion-report.md: добавлен блок Task (ID, план, ADR)
- CLAUDE.md: добавлен workflow в маршрутную таблицу
```
