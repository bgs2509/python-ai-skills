# AI deep code analysis — checklist

> Используется агентом на шаге 4 SKILL.md. Цель: найти то, что **детерминированные инструменты в принципе не ловят** — смысловые конфликты, drift между документацией и реализацией, архитектурные нарушения, тонкие баги. Без воды, без догадок, file:line обязательно.

## Входные данные

1. `.full_audit_tmp/results.jsonl` + `excerpts/` — итоги CLI/MCP проверок.
2. `.full_audit_tmp/sentrux/*.json` — Sentrux scan/check_rules/test_gaps/dsm.
3. `docs/superpowers/specs/*-discovery.md` (последний) — бизнес-требования.
4. `docs/superpowers/specs/*-design.md` (последний) — технические решения.
5. `docs/knowledge-graph.xml` — граф модулей.
6. `docs/development-plan.xml` — approved декомпозиция.
7. `src/**/*.py` — собственно код (читать по нужным модулям, не весь сразу).
8. `tests/**/*.py` — тесты.

## Чек-лист (выполнять в порядке)

Использовать TaskCreate, по задаче на каждую категорию. Каждая находка имеет:
- `file:line`
- `severity`: `critical` | `middle` | `minor`
- `evidence`: 1–3 строки кода/spec, цитата
- `why`: почему это проблема (не пересказ кода)
- `fix`: конкретное действие (команда / правка / ADR)

### 1. Spec ↔ code conflicts (critical если меняет поведение)

Сравнить `discovery.md` (FR/NFR) и `design.md` с реализацией:
- FR-N описывает X, а код делает Y или вообще не имеет этого пути
- NFR-N (latency/throughput/retention) — есть ли в коде соответствующий механизм (timeout, batch size, TTL)?
- Допущения spec'а противоречат коду (например spec: "rate-limit 60 req/min", код: без лимита)

### 2. Cross-module logical conflicts (critical/middle)

Поиск **дублирующейся бизнес-логики с расхождением**:
- Один и тот же домен-инвариант реализован в двух местах (валидация, нормализация, хеширование) — сравнить алгоритмы
- Два модуля владеют одним состоянием (например, оба пишут в одну таблицу без чёткого owner'а)
- Циклические импорты/dependency loops (если grace lint не поймал)

Подсказки: `Grep` по ключевым доменным глаголам (normalize, hash, validate, dedupe, score) — есть ли несколько реализаций?

### 3. Architectural drift (middle)

- Модули, появившиеся в `src/`, но отсутствующие в `development-plan.xml` / `knowledge-graph.xml` (cross-check со списком из шага CLI)
- Нарушения слоёв (DDD / hexagonal): infrastructure импортирует domain — ок; domain импортирует infrastructure — нарушение
- Прямой SQL/HTTP в domain-слое в обход repository/gateway

### 4. Test semantic gaps (middle)

CLI ловит «тест упал» и «coverage <X%». ИИ должен ловить:
- Тест есть, но проверяет **не то** — assert'ы на поверхностные свойства (например `assert result is not None` вместо проверки значения)
- Тест замоканен так, что не проверяет реальный invariant модуля
- Edge cases из spec не покрыты ни одним тестом (None, empty, max int, негативные значения, concurrency)
- Бросаются исключения, которые тестируются как «не упало», но не проверяется тип/сообщение

### 5. Security & concurrency anti-patterns (critical)

Не дублировать gitleaks/pip-audit. Искать:
- SQL/shell/HTML injection в обход параметров (f-string в SQL, `subprocess(shell=True)` с user input)
- Race conditions: read-modify-write без блокировки (особенно в counters/state machines)
- Async-блокирующие вызовы (sync IO внутри async без `to_thread`)
- Утечки secrets в логи (logger пишет объект-конфиг с паролем целиком)
- Path traversal: открытие файлов по user-controlled пути без валидации
- Незакрытые ресурсы (file/connection handlers без `with`)

### 6. Doc accuracy (middle/minor)

- README/CLAUDE.md называет команду/файл/энвайр, которого больше нет
- Примеры в docstring выдают другой результат, чем сейчас даёт код
- ADR-NNN отмечен `accepted`, но реализация уже отклоняется от него
- `discovery.md` упоминает модуль, который удалён или переименован

### 7. Operational hygiene (minor)

- Логи без `correlation_id` / без `[BLOCK_NAME]` тэга в критичных ветках
- Magic numbers / hardcoded URLs / duplicated env keys
- TODO/FIXME без даты или Beads-id

## Что НЕ делать

- Не дублировать находки CLI-проверок (если ruff уже сказал — не повторять)
- Не комментировать стиль / переименование переменных без поведенческого риска
- Не «возможно стоит» / «было бы хорошо» — только конкретные дефекты
- Не выдумывать — если нет уверенности, отдельный раздел `Open questions` с явным указанием неопределённости

## Формат вывода

Append в конец `docs/reports/<date>-audit.md`:

```markdown
## AI deep code analysis

_Coverage: <N> findings (critical: <C>, middle: <M>, minor: <Min>)._
_Files inspected: <N>; modules cross-checked: <N>._

### Critical
1. **[Spec↔code] FR-12 not implemented in `src/processor/scorer.py:142`**
   - Evidence: spec — "score must be clamped to [0,1]"; code — `return raw_score` (no clamp).
   - Why: downstream `notifier` assumes 0..1, will misbehave for negative inputs.
   - Fix: add `min(1.0, max(0.0, raw_score))` and unit test for boundary.

### Middle
…

### Minor
…

### Open questions
- `src/ingestor/persistence.py:55` использует `asyncio.gather(..., return_exceptions=False)` — не ясно, преднамеренно ли
  свалить весь батч при первом исключении. Уточнить с автором / в design.md.
```

## Calibration

При первом прогоне на новом проекте — потратить ~5 минут на чтение `discovery.md` целиком и беглый обход `src/` через `Glob` + `Grep` по доменным глаголам. Без этой калибровки секции 1–2 невозможно сделать качественно.


## Required machine-readable output

Directly under `## AI deep code analysis` (BEFORE the `### Critical` / `### Middle` / `### Minor` subsections), emit a fenced JSON block exactly like this:

    ```json
    [
      {"file": "src/foo.py", "line": 42, "severity": "critical", "check_id": "ai-spec-conflict", "rule_id": "fr-5-missing", "message": "FR-5 requires retry but code has no retry path"},
      {"file": "src/bar.py", "line": 88, "severity": "middle",   "check_id": "ai-arch-drift",     "rule_id": "layer-leak",    "message": "domain imports infrastructure adapter"}
    ]
    ```

Rules:
- One object per finding. The human-readable subsections below MUST list the same findings — no findings in subsections that are absent from the JSON block, and vice versa.
- `check_id` MUST start with `ai-` (e.g. `ai-spec-conflict`, `ai-arch-drift`, `ai-test-gap`, `ai-security`, `ai-doc-drift`, `ai-hygiene`).
- `severity` ∈ `critical|middle|minor|open`.
- If no findings: emit `[]` AND the existing empty-sentinel ("No findings after full pass through 7 categories" + "Modules inspected: ...").
