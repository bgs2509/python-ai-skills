# TASK-005: Remove Security Hardening from _docker Skill

## Description

Remove `no-new-privileges`, `cap_drop: ALL`, `read_only: true` rules from the `_docker` skill.

## Reason

`no-new-privileges:true` + `cap_drop: ALL` prevent nginx workers from calling `setgid()`.
Workers crash, master accepts TCP connections, but there is no one to handle them — curl hangs.
Similar issue with postgres and other services using `setuid()`/`setgid()`.

## Acceptance Criteria

- [ ] Removed "security hardening" mention from the skill description
- [ ] Removed `no-new-privileges`, `cap_drop: ALL`, `read_only: true` rules
- [ ] Safe rules remain: non-root user, no secrets in image

## Priority

High — rules break production.
