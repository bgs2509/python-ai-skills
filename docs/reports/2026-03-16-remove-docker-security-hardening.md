# Completion Report: TASK-005

**Дата:** 2026-03-16
**Задача:** Удалить security hardening из _docker skill

## Что сделано

Удалены правила контейнерной безопасности, которые ломают сервисы с `setuid()`/`setgid()` (nginx, postgres).

## Изменения

| Файл | Что сделано |
|------|-------------|
| `_docker/SKILL.md` | Убран "security hardening" из description, удалены `no-new-privileges`, `cap_drop: ALL`, `read_only: true` |
| `_docker/reference/docker.md` | Удалены строки `No new privileges`, `Drop capabilities`, `Read-only filesystem` из таблицы Security |
| `CLAUDE.md` | Обновлено описание `_docker` в каталоге skill'ов |

## Что осталось в секции Security

- Non-root user (`adduser --disabled-password appuser` + `USER appuser`)
- Без секретов в image (не COPY .env, не ARG для секретов)

## Причина

`no-new-privileges:true` + `cap_drop: ALL` запрещали nginx worker'ам вызывать `setgid()`.
Worker'ы падали при старте → master принимал TCP-соединения, но некому было их обрабатывать → curl зависал.

## Коммиты

- `6032b71` — chore: remove 'security hardening' pattern from _docker skill description
- `5ef759a` — fix: remove no-new-privileges and cap_drop rules from _docker skill
