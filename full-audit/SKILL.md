---
name: full-audit
description: >
  Read-only, deterministic full audit of code AND documentation in a dev-project.
  Aggregates exit codes / JSON from project tooling (make lint, mypy, pytest --cov,
  grace lint, pre-commit, gitleaks, sentrux, bd doctor, radon, vulture, pip-audit,
  SSoT-drift checks) into a single markdown report under docs/reports/. AI is used
  ONLY for residual semantic gaps after objective metrics are collected.
  TRIGGER: user invokes /full-audit (or asks "сделай полный аудит кода и документации").
  SKIP: life-projects (no project_type=dev), no pyproject.toml/Makefile detected.
argument-hint: "[--ai] [--quick] [--no-tests] [--cli-only|--no-ai] [--no-sentrux] [--no-trends] [--out=docs/reports/YYYYMMDD-audit.md]"
---

# /full-audit — Full deterministic code+docs audit

> **Apply only to dev-projects.** Refuse with a clear message in life-projects (no `project_type: dev` in CLAUDE.md, no `pyproject.toml`).

## Принципы

1. **Detеrministic-first, AI-second.** Сначала CLI/MCP/exit codes (объективные метрики), затем AI deep analysis для того, что инструменты в принципе не ловят (cross-module conflicts, spec↔code mismatch, тонкие security/concurrency баги).

1a. **Finding-level granularity.** Каждая check'а emits findings в нормализованном виде `{check_id, file, line, severity, rule_id, message_raw}`. Это позволяет diff'ать findings между прогонами через стабильные fingerprint (`sha1(check_id + file + line_bucket + canonical_message)`).

1b. **Trend detection is read-only.** Skill сравнивает текущий набор findings с историей `docs/reports/.audit-history.jsonl` и репортит три категории: **sticky** (повторение ≥ 3 раз подряд), **oscillating** (циклическое появление-исчезновение), **cross-breaking pairs** (A исчезает + B появляется в том же модуле, повторяется ≥ 2 раз). Никаких auto-fix'ов — только секция `## Trends` в отчёте.

## Флаги управления AI-стадией (важно — читать внимательно)

Skill различает **три режима**:

| Флаг           | AI deep analysis | Enforcement |
|----------------|------------------|-------------|
| `--ai`         | **обязателен**   | **HARD GATE**: после AI-стадии запускается `lib/check_ai_section.py`; если в отчёте нет валидной секции `## AI deep code analysis` — skill exit 1. Никакие отговорки («pipeline чистый», «недавно был аудит», «low-effort run») не принимаются. |
| (без флага)    | рекомендован     | soft — агент может пропустить с явным обоснованием. Используется только для черновых прогонов. |
| `--cli-only` / `--no-ai` | пропущен | разрешённый явный skip; `check_ai_section.py` не запускается. |

**Правило:** при сомнении — всегда запускать с `--ai`. Без флага агент склонен экономить.
2. **Read-only.** Никаких `--fix`, никаких коммитов, никаких записей в код. Skill пишет только в `docs/reports/<date>-audit.md` и временные файлы в `.full_audit_tmp/`.
3. **Idempotent.** Повторный запуск перезаписывает отчёт того же дня. Старые отчёты не трогает.
4. **No bypass.** Если у проекта есть `make total-test` / pre-commit hooks — запускаются как есть, без `--no-verify`/`SKIP=`.
5. **No-skip, no-reuse — ABSOLUTE RULE.**
   - **Все CLI checks (1–19, 21) и все MCP-проверки (20a–20e) обязательны на каждом запуске.** Они образуют ground truth аудита.
   - **Запрещено переиспользовать `.full_audit_tmp/results.jsonl` от предыдущего прогона.** Каждый `/full-audit` начинается с `rm -rf .full_audit_tmp/` и полным повторным запуском `lib/run.sh` + sentrux MCP suite. Старый отчёт не является источником данных — это анти-паттерн «перепечатывания» вместо аудита.
   - **Если инструмент не установлен — это HARD FAIL, не SKIPPED.** Skill завершается exit 1 с инструкцией поставить (`uv tool install <tool>` / `pip install pre-commit gitleaks` / `npm i -g …`). Статус `SKIPPED` допустим **только** для одного класса случаев: явный пользовательский opt-out флагом (`--no-tests`, `--no-sentrux`). Опций «тихо пропустить из-за отсутствия» больше нет.
   - **Флаги `--quick` и `--no-tests` — opt-out, не default.** Без них pipeline идёт на полную, включая integration-тесты, pip-audit и `make total-test`. Quick-режим помечается в Summary отдельной плашкой `⚠ PARTIAL RUN — <skipped>` чтобы reviewer видел, что аудит неполный.

## Output

Один файл: `docs/reports/$(date -I)-audit.md` (или `--out=…`).

Формат:
```
# Full audit — <repo> — <date>

## Summary
| # | Check                  | Status   | Metric              |
|---|------------------------|----------|---------------------|
| 1 | ruff check             | ✓ PASS   | 0 issues            |
| 2 | ruff format            | ✗ FAIL   | 3 files unformatted |
| 3 | mypy (strict on shared)| ⚠ WARN   | 12 errors           |
…

Total: <N pass> / <M total>, <K critical>, <L warnings>

## Details
### 1. ruff check — PASS
<command>: uv run ruff check .
<exit>: 0
<excerpt>: All checks passed!

### 2. ruff format — FAIL
…
```

В конце — раздел **AI deep code analysis** (если не `--cli-only` / `--no-ai`): Claude по чек-листу из `lib/ai_review_prompt.md` находит то, что детерминированные проверки не ловят — конфликты между модулями, расхождения spec↔code, архитектурный drift, тонкие security/concurrency дефекты, semantic gaps в тестах. Каждая находка имеет `file:line`, `severity`, `evidence`, `why`, `fix`.

## Pipeline (фиксированный порядок)

Запускать через `bash ~/.claude/skills/full-audit/lib/run.sh [--quick] [--no-tests]`. Он сам определяет, какие инструменты доступны.

| # | Группа       | Команда                                                       | Источник истины                       |
|---|--------------|---------------------------------------------------------------|---------------------------------------|
| 1 | lint         | `uv run ruff check . --output-format=json`                    | exit + JSON                           |
| 2 | lint         | `uv run ruff format --check .`                                | exit + stderr                         |
| 3 | types        | `uv run mypy src --no-error-summary`                          | exit + stdout                         |
| 4 | secrets      | `uv run pre-commit run gitleaks --all-files` (или `gitleaks detect`) | exit                                  |
| 5 | secrets-fs   | grep policy: `*.env`, `*.pem`, `*.key`, `id_rsa*` outside `.env.example`/`tests/test.env` | поиск через `git ls-files`            |
| 6 | tests        | `uv run pytest tests/unit -q --cov=src --cov-report=json:.full_audit_tmp/cov.json` | exit + cov.json                       |
| 7 | tests-int    | `uv run pytest tests/integration -q` (если `--quick` — skip) | exit                                  |
| 8 | grace        | `grace lint --format=json`                                    | exit + JSON                           |
| 9 | grace        | `grace status`                                                | stdout                                |
| 10| docs-ssot    | `python lib/check_ssot.py` — md/xml drift, knowledge-graph vs `git ls-files src/**/*.py` | self-test                              |
| 11| docs-anchors | grep `START_BLOCK_*`/`END_BLOCK_*` пары, paired & unique      | self-test                              |
| 12| docs-contracts| `python lib/check_contracts.py` — каждый `src/**/*.py` (кроме `__init__.py`, alembic/versions) имеет `START_MODULE_CONTRACT` | self-test                              |
| 13| beads        | `bd doctor`, `bd preflight`, `bd stale`, `bd orphans`         | exit + stdout                         |
| 14| complexity   | `uvx radon cc src -n C -a` (если доступен `uvx`)             | stdout (CC > C = warn)                |
| 15| complexity   | `uvx radon mi src -n B`                                       | stdout                                |
| 16| dead-code    | `uvx vulture src --min-confidence 80`                         | exit + stdout                         |
| 17| docstrings   | `uvx interrogate src -q -f 70`                                | exit                                   |
| 18| deps-audit   | `uvx pip-audit -r <(uv export --no-dev)` или `uv export \| uvx pip-audit -r /dev/stdin` | exit + JSON                           |
| 19| deps-pinned  | `python lib/check_pins.py` — все runtime зависимости через `==` | self-test                              |
| 20a| sentrux     | `mcp__sentrux__scan` (полный архитектурный скан)                       | JSON в `.full_audit_tmp/sentrux/scan.json`        |
| 20b| sentrux     | `mcp__sentrux__check_rules` (проверка project rules)                   | JSON в `.full_audit_tmp/sentrux/check_rules.json` |
| 20c| sentrux     | `mcp__sentrux__test_gaps` (модули без тестов)                          | JSON в `.full_audit_tmp/sentrux/test_gaps.json`   |
| 20d| sentrux     | `mcp__sentrux__dsm` (dependency structure matrix — циклы/слои)         | JSON в `.full_audit_tmp/sentrux/dsm.json`         |
| 20e| sentrux     | `mcp__sentrux__git_stats` (churn / hotspot модулей)                    | JSON в `.full_audit_tmp/sentrux/git_stats.json`   |
| 21| project      | `make total-test` (если есть и не `--quick`) — финальный e2e gate | exit                                   |
| 22| trends       | `aggregate_findings.py` + `history_store.py append` (best-effort)        | `.audit-history.jsonl` (append-only)  |

`--quick` пропускает 7, 14–18, 21 — **только при явном указании пользователем**. Без флага все эти секции обязательны.
`--no-tests` пропускает 6, 7, 21 — только при явном указании.
`--no-sentrux` пропускает 20a–20e — только при явном указании; в обычном прогоне sentrux MCP suite **обязателен**, статус `SKIPPED (MCP not available)` запрещён, отсутствие MCP = exit 1.
`--no-trends` пропускает aggregator+history append (шаг 22) и секцию `## Trends` в отчёте. Используется для bootstrap-прогонов или когда `.audit-history.jsonl` не должен расти. Без флага — trend detection всегда включена (best-effort, никогда не валит pipeline).

## Algorithm (для агента)

Использовать checklist через TaskCreate (по одной задаче на каждый шаг ниже).

1. **Pre-flight.**
   - Прочитать `CLAUDE.md`/`AGENTS.md` корня проекта. Если `project_type: life` — отказать.
   - Проверить наличие `pyproject.toml` + `Makefile`. Если нет — отказать.
   - **Очистить старые артефакты прогона**: `rm -rf .full_audit_tmp/` (НЕ переиспользовать `results.jsonl` от предыдущего запуска — это даст устаревшие данные и превратит аудит в перепечатку отчёта).
   - `mkdir -p docs/reports .full_audit_tmp`.
   - Зафиксировать `git rev-parse HEAD` и `git status --porcelain` в отчёт.
   - **Tool inventory check**: проверить, что доступны все обязательные инструменты — `uv`, `pre-commit`, `gitleaks`, `bd`, `uvx` (для radon/vulture/interrogate/pip-audit), `grace` (если проект GRACE-managed), MCP `mcp__sentrux__*`. Любое отсутствие = HARD FAIL: skill печатает список недостающего и `exit 1` с инструкцией установки. **Запрещено** молча помечать SKIPPED и продолжать.

2. **Run CLI pipeline.** Запустить `bash lib/run.sh <flags>` **на каждом запуске** (никогда не пропускать «потому что есть свежий `results.jsonl`»). Он пишет:
   - `.full_audit_tmp/results.jsonl` — по строке на check (`{id, name, status, exit, metric}`)
   - `.full_audit_tmp/excerpts/<id>.txt` — последние 50 строк каждой команды
   - В конце сам печатает colored brief с classification (CRITICAL/MIDDLE/MINOR) + remediation hints (через `lib/summarize.py`).

3. **Run Sentrux MCP suite — ОБЯЗАТЕЛЬНО** (кроме явного `--no-sentrux` от пользователя).
   Агент запускает **все пять последовательно** и сохраняет JSON в `.full_audit_tmp/sentrux/`:
   - `mcp__sentrux__scan` → `scan.json`
   - `mcp__sentrux__check_rules` → `check_rules.json`
   - `mcp__sentrux__test_gaps` → `test_gaps.json`
   - `mcp__sentrux__dsm` → `dsm.json`
   - `mcp__sentrux__git_stats` → `git_stats.json`

   **Запрет**: Если хоть один MCP-вызов не отработал — это HARD FAIL, не SKIPPED. Skill завершается exit 1 с сообщением «sentrux MCP недоступен — установите/подключите MCP-сервер либо запустите с `--no-sentrux` (получите неполный аудит)». Молчаливое продолжение со `SKIPPED` запрещено.

   Для каждого вызова добавить строку в `results.jsonl` через `python lib/append_result.py <id> <name> <status> <metric>`:
   - status `PASS` если возвращён JSON без `errors`/`violations`
   - status `FAIL` если есть violations критичной категории (security, contract, missing tests on critical path)
   - status `WARN` для остальных нарушений
   - status `SKIPPED` **только** при явном `--no-sentrux`

4. **Render markdown.** `python lib/render.py .full_audit_tmp/results.jsonl > docs/reports/<date>-audit.md`.

5. **AI deep code analysis** — запускается **всегда**, кроме случая `--cli-only` / `--no-ai`.

   **При флаге `--ai` стадия обязательна и enforced**. Агент НЕ имеет права её пропустить ни по одной из эвристик:
   - НЕ пропускать «потому что pipeline чистый»
   - НЕ пропускать «потому что недавно был audit»
   - НЕ пропускать «потому что HEAD не менялся» (нет такого правила в skill'е)
   - НЕ пропускать «low-effort run», «и так понятно», «нет смысла»

   Открыть `lib/ai_review_prompt.md` и пройти **все 7 категорий** чек-листа:
   1. Spec ↔ code conflicts (`discovery.md`/`design.md` vs реализация)
   2. Cross-module logical conflicts (дубликаты domain logic, shared state без owner'а)
   3. Architectural drift (слои DDD, модули вне `development-plan.xml`)
   4. Test semantic gaps (тесты есть, но проверяют не то)
   5. Security & concurrency anti-patterns (injection, race conditions, async-блокировки, утечки secrets в логи)
   6. Doc accuracy (примеры в docstring устарели, ADR противоречит коду)
   7. Operational hygiene (correlation_id, magic numbers, TODO без id)

   Каждая находка — `file:line`, `severity` (critical/middle/minor), `evidence` (цитата), `why`, `fix`.
   Append результат в `docs/reports/<date>-audit.md` как раздел `## AI deep code analysis` с подразделами `### Critical / ### Middle / ### Minor / ### Open questions`.

   **Жёсткие правила:**
   - Не дублировать находки CLI/MCP (если ruff/sentrux уже сказали — не повторять).
   - Не выдумывать. Без уверенности → `Open questions` с явной неопределённостью.
   - Без воды («возможно стоит», «было бы хорошо»). Только конкретные дефекты.
   - Минимум для качественного прогона — прочитать последний `discovery.md` целиком и обойти `src/` через `Glob`+`Grep` по доменным глаголам (calibration, ~5 мин).

   **Если по итогам обхода НЕ найдено ни одной находки** — это валидный результат, но нужно зафиксировать его явно:
   ```markdown
   ## AI deep code analysis

   _No findings after full pass through 7 categories._
   _Modules inspected: src/ingestor/persistence.py, src/processor/scorer.py,
    src/notifier/dispatcher.py, src/shared/normalize.py, … (≥3 путей)._
   ```
   Без этой формулировки `check_ai_section.py` упадёт.

5b. **HARD GATE** (только при `--ai`).

   После того как agent дописал секцию `## AI deep code analysis` в отчёт, выполнить:
   ```bash
   python3 ~/.claude/skills/full-audit/lib/check_ai_section.py docs/reports/<date>-audit.md
   ```
   Скрипт проверяет:
   - заголовок `## AI deep code analysis` присутствует;
   - под ним есть **либо** ≥1 находка с file:line под `### Critical/Middle/Minor/Open questions`,
     **либо** explicit empty-sentinel (`No findings after full pass through 7 categories` + `Modules inspected: …` с минимум 3 путями).

   Если check падает (exit 1) — skill завершается с exit 1 и сообщением, что AI-секция не была сделана честно.

6. **AI brief append.** После AI-анализа — пересчитать общий severity и допечатать в stdout краткий блок:
   ```
   AI deep analysis: <C> critical · <M> middle · <Min> minor · <Q> open questions
   See: docs/reports/<date>-audit.md  §AI deep code analysis
   ```

7. **Exit code.**
   - `0` — все обязательные CLI checks PASS, **все** MCP Sentrux вызовы PASS/WARN, **И** нет critical AI findings, **И** (при `--ai`) `check_ai_section.py` прошёл.
   - `1` — есть хоть один FAIL в обязательных CLI checks, **ИЛИ** хоть один отсутствующий обязательный инструмент (CLI или MCP) без явного opt-out флага, **ИЛИ** хоть один critical AI finding, **ИЛИ** (при `--ai`) AI-секция не была сделана / сделана пусто без sentinel'а.
   - `2` — pre-flight отказ (life-project / no pyproject).

   Skill **HARD FAIL** при отсутствии любого обязательного инструмента (CLI 1–19,21 + MCP 20a–20e). SKIPPED допустим **только** при явном opt-out флаге пользователя (`--quick`, `--no-tests`, `--no-sentrux`). «Инструмент не установлен» — это не SKIPPED, это setup defect → exit 1 с сообщением как установить.

8. **Report path.** Печатает `Report: docs/reports/<date>-audit.md` финальной строкой.

## Trend detection

Каждый прогон `/full-audit` записывает свои findings в persistent journal `docs/reports/.audit-history.jsonl` (append-only, одна JSON-строка на occurrence). Когда история содержит ≥ 3 runs, в рендере отчёта появляется секция `## Trends` с тремя подсекциями:

- **Sticky (repeated):** fingerprint присутствует в последних N=3 consecutive runs. Признак — fix не сработал или регулярно ломается обратно.
- **Oscillating (circular type 1):** fingerprint появляется → исчезает → появляется в окне последних K=5 runs (≥ 2 циклов). Признак — лечится симптом, не корень.
- **Cross-breaking pairs (circular type 3):** на границе run X→Y fingerprint A исчез + fingerprint B появился в том же `src/<module>/`, и это повторяется ≥ 2 раз. Признак — общий root cause, A и B надо чинить структурно.

### Storage

- `docs/reports/.audit-history.jsonl` — persistent journal. По умолчанию НЕ в git (см. ниже). Растёт линейно с количеством audit'ов. Manual rotation/archive — на стороне оператора.
- `.full_audit_tmp/findings.jsonl` — per-run normalized store. Эфемерный, перезаписывается каждым `/full-audit`.
- `.full_audit_tmp/sidecars/*.jsonl` — per-self-check sidecar emission. Эфемерные.

### .gitignore рекомендация

Добавь в `.gitignore` проекта:
```
# full-audit history grows commit-by-commit; rotate manually if needed
docs/reports/.audit-history.jsonl
```

Если хочешь хранить shared history (для коммитов между членами команды) — НЕ добавляй в gitignore. Размер контролировать manual rotation.

### Опт-аут

`--no-trends` пропускает шаг aggregator + history append. Используй на bootstrap-прогонах или для исследования без накопления.

### Fingerprint stability

Strict fingerprint `sha1(check_id|file|line_bucket|canonical_message)` стабилен против:
- сдвига строк ±5 (`line_bucket = line // 5`);
- мелких изменений в сообщении (`canonical_message` нормализует числа → `N`, пути → `<path>`, hex-id → `<id>`, lower-case, strip whitespace).

Не стабилен против:
- переименования файла (rename → новый fingerprint).
- Для частичного покрытия rename'ов вычисляется ещё `fingerprint_loose = sha1(check_id|module_top|canonical_message)` — сохраняется в истории как secondary key (детекторы пока его не используют — отложено в будущую итерацию).

### Sentinel rows

Run, выдавший 0 findings, всё равно пишет sentinel-строку в `.audit-history.jsonl` чтобы считаться в `total_runs`. Без sentinel'а чистый codebase никогда бы не накопил 3 runs для срабатывания trend detection.

## Не делает

- Не правит код. Не запускает `--fix`. Не коммитит.
- Не пушит. Не закрывает Beads-issue.
- Не приоритизирует findings — только собирает.
- Не заменяет `audit-loop` (тот — итеративный AI-cross-review с авто-фиксами).

## Когда использовать что

| Хочешь                                   | Skill            |
|------------------------------------------|------------------|
| Снимок здоровья проекта одной командой   | **full-audit**   |
| Итеративные AI-фиксы с rounds + rollback | `audit-loop`     |
| Только pre-commit checks                 | `pre-commit run` |
| Только e2e quality gate                  | `make total-test`|

## Severity calibration для AI findings

Используется при определении общего exit code и при добавлении в brief.

| Severity | Когда применять | Влияние на exit |
|----------|----------------|-----------------|
| **critical** | spec-violation меняющий поведение, security дефект, race condition с потерей данных, утечка secrets в логи, missing path в FR | **exit 1** |
| **middle** | architectural drift, semantic test gap на основном пути, doc accuracy с риском misuse | warning (exit 0) |
| **minor** | doc inaccuracy без риска, hygiene (TODO/magic numbers), стилистика с потенциалом ошибки | info |
| **open question** | агент не уверен, нужно подтверждение автора | info |

## References

- `references/checks.md` — детальное описание каждой проверки и как её интерпретировать.
- `lib/run.sh` — оркестратор CLI pipeline.
- `lib/check_ssot.py`, `lib/check_contracts.py`, `lib/check_pins.py`, `lib/check_anchors.py`, `lib/check_secret_files.py` — self-checks.
- `lib/append_result.py` — добавление Sentrux/MCP результатов в общий JSONL.
- `lib/summarize.py` — colored brief в stdout с classification + advice.
- `lib/render.py` — рендер markdown-отчёта из JSONL.
- `lib/ai_review_prompt.md` — чек-лист AI deep code analysis (7 категорий).
