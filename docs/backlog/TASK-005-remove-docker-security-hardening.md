# TASK-005: Удалить security hardening из _docker skill

## Описание

Удалить правила `no-new-privileges`, `cap_drop: ALL`, `read_only: true` из skill'а `_docker`.

## Причина

`no-new-privileges:true` + `cap_drop: ALL` запрещают nginx worker'ам вызывать `setgid()`.
Worker'ы падают, master принимает TCP-соединения, но некому их обрабатывать — curl зависает.
Аналогичная проблема с postgres и другими сервисами, использующими `setuid()`/`setgid()`.

## Критерии готовности

- [ ] Убрано упоминание "security hardening" из описания skill'а
- [ ] Убраны правила `no-new-privileges`, `cap_drop: ALL`, `read_only: true`
- [ ] Остались безопасные правила: non-root user, запрет секретов в image

## Приоритет

Высокий — правила ломают production.
