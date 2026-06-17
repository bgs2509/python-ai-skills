---
name: project-sync
description: >
  Sync the CURRENT git repository (cwd) across three points: this machine ↔
  GitHub (hub) ↔ gpu-1 VPS. Hybrid topology — code travels through GitHub
  (hub-and-spoke), gitignored artifacts travel via rsync. Bidirectional.
  Report-first: diagnose read-only, show a report, act only after confirmation.
  TRIGGER when: user calls /project-sync, user wants to push/pull the current
  repo across machines, "sync this repo", "sync to gpu-1". For ALL repos on the
  VPS at once use /projects-sync instead. For local-only commits use /smart-commit.
argument-hint: "[--check diagnose only] [--with-artifacts] [--yes skip confirmation]"
---

# /project-sync — Sync the current repository

> Один репо (где стоишь) ↔ GitHub ↔ gpu-1. Гибрид: код через GitHub, артефакты через rsync.

## Топология (зафиксирована)

1. **GitHub = источник правды.** Обе машины (эта и gpu-1) пушат/пуллят только в GitHub. Прямого git-канала машина↔машина нет.
2. **Артефакты** (`data/`, веса, логи — то, что в `.gitignore`) через git не ходят → отдельный `rsync`-канал на gpu-1.
3. **Bidirectional** — gpu-1 равноправная dev-машина.

## Инструмент

Детерминированное ядро — `lib/sync.py` (этого скила). Используй его CLI, не inline-python:

- Диагностика репо → `python3 ~/.claude/skills/project-sync/lib/sync.py diagnose <path>` (JSON: branch, has_remote, dirty_files, ahead, behind, state).

`state` ∈ `up_to_date | behind | ahead | diverged | dirty | no_remote`.

## Алгоритм

1. **Определи репо** — `cwd`. Убедись, что это git-репозиторий (`git rev-parse --git-dir`).
2. **Диагностика (read-only)** — `git fetch --all --prune`, затем CLI `diagnose`. Покажи отчёт пользователю.
3. **Report-first** — выведи: ветка, состояние, ahead/behind, список грязных файлов, есть ли `origin`.
4. **Реши по состоянию** (report-first; при сомнении — спроси с вариантами, confidence и рекомендацией):
   - `up_to_date` → ничего не делать.
   - `behind` → `git pull --ff-only` (безопасный fast-forward; объясни, что это просто перемотка вперёд).
   - `ahead` → `git push`.
   - `diverged` → **СПРОСИТЬ** (истории разошлись). Дай варианты: rebase / merge / разобрать вручную / пропустить, с confidence и рекомендацией. НЕ авто-force.
   - `dirty` → **СПРОСИТЬ** (есть незакоммиченное). Покажи файлы. Варианты: закоммитить (`/smart-commit`) / отложить / пропустить репо.
   - `no_remote` → **создать репо на GitHub** и запушить: `gh repo create --source . --private --remote origin --push` (подтверждение приватности у пользователя).
5. **Синхронизировать gpu-1** — после того как локальная сторона сошлась с GitHub, на gpu-1 для этого репо тоже `git pull --ff-only` из GitHub (через `ssh gpu-1`). Так обе машины сходятся на хабе.
6. **Артефакты** (только при `--with-artifacts` или по запросу) → **СПРОСИТЬ**, какие gitignored-пути синкать, затем `rsync -az` на gpu-1. Сначала покажи `--dry-run`.

## Флаги

- `--check` — только диагностика и отчёт, без действий.
- `--with-artifacts` — предложить rsync gitignored-артефактов после кода.
- `--yes` — пропустить confirmation gate (быстрый путь для заведомо чистого `behind`/`ahead`; не действует на `dirty`/`diverged` — они всегда спрашивают).

## Правила

1. **Report-first** — действие только после показанного отчёта и подтверждения.
2. **Никогда не `--force`** автоматически. Дивергенция → спросить.
3. **User-invoked** — скил не запускается сам; это держит нас в рамках глобального правила «не пушить код авто».
4. **Только текущий репо.** Для всех репо на ВПС → `/projects-sync`.
