# Completion Report: TASK-005

**Date:** 2026-03-16
**Task:** Remove security hardening from _docker skill

## What Was Done

Removed container security rules that broke services using `setuid()`/`setgid()` (nginx, postgres).

## Changes

| File | What was done |
|------|---------------|
| `_docker/SKILL.md` | Removed "security hardening" from description, deleted `no-new-privileges`, `cap_drop: ALL`, `read_only: true` |
| `_docker/reference/docker.md` | Removed `No new privileges`, `Drop capabilities`, `Read-only filesystem` rows from Security table |
| `CLAUDE.md` | Updated `_docker` description in skill catalog |

## What Remains in Security Section

- Non-root user (`adduser --disabled-password appuser` + `USER appuser`)
- No secrets in image (no COPY .env, no ARG for secrets)

## Reason

`no-new-privileges:true` + `cap_drop: ALL` prevented nginx workers from calling `setgid()`.
Workers crashed on startup → master accepted TCP connections, but there was no one to handle them → curl hung.

## Commits

- `6032b71` — chore: remove 'security hardening' pattern from _docker skill description
- `5ef759a` — fix: remove no-new-privileges and cap_drop rules from _docker skill
