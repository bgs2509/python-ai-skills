---
name: _workflow
description: >
  Пайплайн обязательной документации: backlog → planning → ADR → changelog →
  completion report → commit. Нумерация TASK/PLAN/ADR. Git conventions.
  Используй при начале новой задачи или перед коммитом.
---

# Пайплайн документации

> Каждая реализованная задача проходит эти этапы.

## 6 этапов

```
1. BACKLOG         → docs/backlog/TASK-NNN-*.md (обязательно)
2. PLANNING (опц.) → docs/plans/PLAN-NNN-*.md
3. ADR (опц.)      → docs/adr/ADR-NNN-*.md
4. CHANGELOG        → CHANGELOG.md секция Unreleased (обязательно)
5. COMPLETION REPORT → docs/reports/{дата}-{фича}.md (обязательно)
6. COMMIT           → TASK-NNN: <type>: <description> (обязательно)
```

## Связность

Task ID (TASK-NNN) проходит через все артефакты: план, ADR, отчёт, коммит.

## Формат коммита

```
TASK-NNN: <type>: <краткий заголовок>

<Подробное описание: что, зачем, как>

Изменения:
- <файл>: <что сделано>
```

Типы: feat, fix, refactor, docs, test, ci, chore.

## Чеклист (перед коммитом)

- [ ] Задача в backlog (TASK-NNN)
- [ ] План в docs/plans/ (если был)
- [ ] ADR в docs/adr/ (если нужен) — если не создан автоматически, вызови `/create-adr`
- [ ] Запись в CHANGELOG.md
- [ ] Completion Report в docs/reports/ — если не создан автоматически, вызови `/completion-report`
- [ ] Коммит с Task ID

> **Напоминание:** create-adr и completion-report могут сработать автоматически по контексту.
> Если этого не произошло — вызови их вручную перед коммитом.

Подробнее:
- Пайплайн: [reference/workflow.md](reference/workflow.md)
- Backlog: [reference/backlog.md](reference/backlog.md)
- Планирование: [reference/planning.md](reference/planning.md)
- Git: [reference/git-conventions.md](reference/git-conventions.md)
