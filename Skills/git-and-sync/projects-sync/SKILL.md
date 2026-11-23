---
name: projects-sync
description: >
  Sync ALL git repositories discovered on the gpu-1 VPS across three points:
  gpu-1 ↔ GitHub (hub) ↔ this machine. Discovers repos on the remote, then runs
  the same per-repo sync core as /project-sync over each. Report-first and
  user-invoked. TRIGGER when: user calls /projects-sync, user wants to sync
  every repo on the VPS, "sync all repos on gpu-1", bulk cross-machine sync.
  For a SINGLE repo (the current one) use /project-sync instead.
argument-hint: "[discovery-root on gpu-1, default $HOME] [--check] [--with-artifacts] [--yes]"
---

# /projects-sync — Sync all repositories on the VPS

> Все репо, найденные на gpu-1 ↔ GitHub ↔ эта машина. Цикл `/project-sync` по каждому.

## Общий инструмент (SSoT)

Использует то же ядро, что и `/project-sync` — `~/.claude/skills/project-sync/lib/sync.py`. Дублирующей логики нет.

- Discovery репо на ВПС → `python3 ~/.claude/skills/project-sync/lib/sync.py discover gpu-1 <root>` (JSON-список путей репо на gpu-1; `root` — параметр, default `$HOME` на gpu-1).
- Диагностика одного репо → `… diagnose <path>` (см. `/project-sync`).

## Алгоритм

1. **Discovery root** — аргумент скила; если не передан, default = `$HOME` на gpu-1. Покажи пользователю, где будешь искать.
2. **Найди репо на gpu-1** — CLI `discover gpu-1 <root>`. Покажи список и количество. *(gpu-1 в `~/.ssh/config` через ProxyJump vpn-gpu-1.)*
3. **Сопоставь с локальными** — для каждого репо с ВПС определи, есть ли он локально (по origin-URL GitHub или пути).
4. **Обработай каждый репо** (report-first сводкой по всем, затем действия):
   - **Есть и локально** → полный 3-way sync как в `/project-sync`: локальная сторона ↔ GitHub, затем `ssh gpu-1 git -C <path> pull --ff-only`. Состояния `dirty`/`diverged` на любой стороне → **СПРОСИТЬ** (по контракту).
   - **Только на ВПС (VPS-only)** → **GitHub-only**: обеспечить `origin` (если нет — создать репо на GitHub: `ssh gpu-1` + `gh repo create --source <path> --private --remote origin --push`), запушить gpu-1 → GitHub. **Локально не клонировать.**
   - **Только локально (local-only)** → **игнорировать** (discovery-набор = то, что на ВПС; клонов не плодим).
5. **Сводный отчёт** — в конце: сколько синхронизировано, сколько создано на GitHub, сколько пропущено и почему.
6. **Артефакты** (только `--with-artifacts`) → **СПРОСИТЬ** пути, `rsync` с `--dry-run` сначала.

## Политики (зафиксированы)

1. VPS-only репо → GitHub-only (создать origin при отсутствии, push gpu-1→GitHub, без локального клона).
2. Local-only репо → игнорировать.
3. `dirty` → спросить. `diverged` → спросить (rebase/merge/skip, без авто-force).
4. Discovery root → параметр (default `$HOME` gpu-1).

## Флаги

- `--check` — только discovery + диагностика + отчёт, без действий.
- `--with-artifacts` — предложить rsync gitignored-артефактов.
- `--yes` — пропустить gate для заведомо безопасных `behind`/`ahead` (не действует на `dirty`/`diverged`).

## Правила

1. **Report-first** и **user-invoked** — как у `/project-sync`.
2. Никогда не `--force` и не клонировать VPS-only автоматически сверх политики.
3. Для одного репо — `/project-sync`.
