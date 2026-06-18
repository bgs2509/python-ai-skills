# Global Instructions

> Cross-tool SSoT for AI coding agents.
> Discovery paths: `~/.claude/CLAUDE.md` (Claude Code), `~/.claude/AGENTS.md` (symlink), `~/.codex/AGENTS.md` (symlink).

## Language

**Rule:** Always respond to the user in Russian. Code, commit messages, variable names, file paths, YAML/JSON keys — always in English.

**Rule:** Maintain full orthographic correctness (diacritics, accents) for both languages.

**Почему:** Русский — предпочитаемый язык общения. Английский в коде — industry standard и лучше работает с LLM (training data bias).

## Output Formatting

**Rule:** Нумерованные списки предпочтительнее маркированных, когда у элементов есть порядок, приоритет или на них можно ссылаться («см. п. 3»). Маркированные — только когда порядок действительно не важен.

**Rule:** Маркированный список всегда лучше, чем перечисление через запятую в одну строку. Любое перечисление из 2+ однородных элементов — выносить в список.

**Rule:** Абзацы отделять пустой строкой. Не склеивать разные мысли в один блок текста.

**Rule:** Активно использовать визуальное выделение для цветового подсвечивания в терминале:
1. `**жирный**` — ключевые термины, правила, заголовки пунктов
2. `*курсив*` — акценты, оговорки, мета-комментарии
3. `` `код` `` — идентификаторы, пути, команды, имена файлов/переменных
4. Блоки кода с указанием языка (```` ```bash ````, ```` ```python ````) — для подсветки синтаксиса

**Rule:** Запрет markdown-таблиц в ответах в терминале остаётся в силе (см. Output Style). В файлах (`*.md`, docs) таблицы разрешены.

**Почему:** Claude Code рендерит markdown в моноширинном терминале с ANSI-подсветкой — `**bold**`, `*italic*`, `` `code` `` и fenced code blocks автоматически окрашиваются. Произвольных цветов в markdown нет, поэтому «выделение цветом» = семантическая разметка. Нумерация даёт якоря для ссылок, списки разбивают визуальный шум, пустые строки между абзацами — базовая типографика читаемости.

## Project Classification

**Rule:** Every project MUST declare its type in its root CLAUDE.md/AGENTS.md:
- `project_type: dev` — software development (code, tests, infra)
- `project_type: life` — life tracking (Health, Family, Study, Career, Home, Hobby, Budget data entry)

**Rule:** GRACE framework, `do-feature` skill, USER APPROVAL gates, and strict commit conventions apply **only** to `dev` projects. For `life` projects work conversationally without these frameworks.

**Почему:** GRACE и do-feature создают overhead (13 шагов, XML-артефакты), избыточный для life-проектов без кода.

## GRACE Core Principles

> Applies only to **dev-type projects**. Life-type projects are exempt.

### 0. Design Before Contract

**Rule:** Before creating or updating a MODULE_CONTRACT, the problem MUST be explored (discovery) and a design decision approved by the user. Contracts formalize decisions — they do not substitute for making them.

**Flow:** Discovery → Brainstorming → USER APPROVAL → Contract → Code.

**Почему:** premature-formalization — классический anti-pattern. Контракт без понимания проблемы потом либо переписывается, либо насильно натягивается на реальность. DDD "Knowledge Crunching" (Evans) и API Design First (Stripe) оба требуют exploration до формализации.

### 1. Never Write Code Without a Contract

**Rule:** After design approval, before generating or editing module code, create or update its MODULE_CONTRACT with PURPOSE, SCOPE, INPUTS, and OUTPUTS.

**Scope:** Applies to **module boundaries** (public API between modules). Internal implementation details inside a module MAY evolve code-first; SSoT for internals is the code itself.

### 2. Semantic Markup Is Load-Bearing Structure

**Rule:** Markers like `# START_BLOCK_<NAME>` and `# END_BLOCK_<NAME>` are navigation anchors, not documentation. They MUST be:
- uniquely named
- paired
- proportionally sized so one block fits inside an LLM working window

### 3. Knowledge Graph Is Always Current

**Rule:** `docs/knowledge-graph.xml` is the project map. When you add a module, move a module, rename exports, or add dependencies, run `grace-refresh` so future agents can navigate deterministically.

### 4. Verification Is a First-Class Artifact

**Rule:** Testing, traces, and log anchors are designed before large execution waves. `docs/verification-plan.xml` is part of the architecture, not an afterthought. Logs are evidence. Tests are executable contracts.

### 5. Top-Down Synthesis

**Rule:** Code generation follows:
`Discovery → RequirementsAnalysis → Brainstorming → TechnologyStack → DevelopmentPlan → VerificationPlan → Code + Tests`

Never jump straight to code when requirements, architecture, or verification intent are still unclear.

## Workflow Hierarchy (dev-projects only)

**Rule:** For any new feature, bugfix, or significant change in a `dev` project — invoke `do-feature` skill as the **single entry point**. It orchestrates Discovery → Brainstorming → GRACE Plan → Writing Plans → Execution → Review → Finish.

**Flow:** `bd create` → Discovery → [APPROVAL] → Brainstorming → [APPROVAL] → GRACE Ask → GRACE Plan → Q&A Contracts → Writing Plans → [APPROVAL] → Execution → Review → Finish → `bd close`.

**Почему:** `do-feature` физически объединяет Superpowers (процесс), GRACE (структура), Beads (трекинг) — Composite-паттерн, SOTA для multi-framework окружений.

## USER APPROVAL Gates (dev-projects only)

**Meta:** Agents have freedom in **HOW** to implement, but not in **WHAT** to build. Contracts, plans, graph references, verification requirements, and USER APPROVAL gates define the allowed space.

**Rule:** Three mandatory gates in `do-feature`:
- After Discovery (step 3) — approve FR/NFR/scope
- After Brainstorming (step 5) — approve design
- After Writing Plans (step 10) — approve implementation plan

**Rule:** One advisory gate during Execution (step 11): if any step deviates from the approved plan, prompt "deviation detected, approve?" before continuing.

**Rule:** Gates MUST NOT be skipped.

**Почему:** Human-in-the-loop gates защищают от дрейфа в неверную сторону. 3 mandatory — sweet spot. Advisory on deviation — минимум overhead, максимум защиты execution.

## Plan Sizing — Context-Window Budget (dev-projects only)

**Rule:** При создании любого плана реализации (`do-feature` Writing Plans, GRACE phases, roadmap) фаза/под-этап ДОЛЖНА укладываться в **одно контекстное окно активной модели** со всеми файлами, документами, тестами и логами, которые потребуются для её выполнения и верификации.

**Rule:** Если оценка scope (файлы × средний размер + контракты + тесты + логи + plan.md) превышает ~60% эффективного окна модели — фаза дробится на под-этапы (`Phase-N.a`, `Phase-N.b`, …) до выполнения требования.

**Rule:** Граница раскола проводится по смене *стека / директории / правил / SSoT-артефакта*, а не по числу файлов. Один под-этап = один связный набор файлов с общими импортами, общим тест-фикстурным окружением и общим набором правил.

**Rule:** Если под-этапы получаются мельче ~20% окна и между ними сильная логическая связь — объединить обратно (KISS, anti-fragmentation). Цель — **fit, не fragment**.

**Rule:** Бюджет окна оценивать по *эффективному* размеру (с учётом system prompt, skills, MCP tools, истории) — не по номинальному (200k для Opus 4.7 ≠ 200k свободно).

**Почему:** превышение окна → context-truncation → дрейф плана и тихие ошибки execution. Дробление мельче нужного → overhead на approval-gates × N, drift между под-фазами, fragmented SSoT. Sweet spot — 40–60% окна на под-этап, оставляя запас на iteration logs, tool results и непредвиденные файлы. Кейс 2026-05-01 (Sensedar Phase 12 UI): 6 экранов в одной фазе без UI-scope-cut требовали бы split на 3+ под-фазы; сокращение MVP до 1 экрана позволило оставить монолит.

## Skill Hierarchy

**Rule:** Every skill has one role:
- `orchestrator` — may invoke other skills (do-feature)
- `worker` — executes a single task, MUST NOT auto-transition (brainstorming, writing-plans, test-driven-development, questions-answers, best, grace-plan, grace-execute)
- `utility` — single-purpose helpers (smart-commit, grace-refresh, grace-ask)

**Rule:** Workers and utilities MUST NOT auto-transition to other skills. Transitions made only by an orchestrator or by the user.

**Почему:** Supervisor-worker pattern (LangGraph, Anthropic agentic patterns) — SOTA для skill composition. Auto-transitions создают скрытые зависимости.

## Documentation SSoT (dev-projects only)

Each artifact is SSoT for exactly one zone:

| Zone | SSoT | Artifact | Produced by |
|------|------|----------|-------------|
| Business requirements | `discovery.md` frontmatter + `requirements.xml` | Markdown prose + auto-generated XML | do-feature step 2 |
| Technology/stack decisions | `design.md` frontmatter + `technology.xml` | Markdown prose + auto-generated XML | do-feature step 4 |
| Module boundaries (public API) | `MODULE_CONTRACT` headers | In Python source files | grace-plan (step 7) |
| Module internals | Code | Source files themselves | Execution (step 11) |
| Module graph | `knowledge-graph.xml` | Derived from MODULE_CONTRACT | `grace-refresh` |
| Tests + log anchors | `verification-plan.xml` | Derived from tests + code | `grace-refresh --verify` |
| Task decomposition | `development-plan.xml` | Aggregated from plan.md + knowledge-graph + Beads | grace-plan + grace-refresh |
| Execution playbook | `plan.md` | Human-written via `writing-plans` | do-feature step 9 |
| Workflow state (status/queue) | Beads | `bd_id` referenced from XML and plan.md | `bd create/update/close` |

**Drift resolution:**
- Status drift (Beads vs XML) → **Beads wins**
- Structural drift on module boundary → **Contract/XML wins**; code MUST be updated
- Internal code drift → **Code wins**; XML regenerates via `grace-refresh`
- Execution drift (plan.md vs commit) → **Code/commit wins**; plan.md marked "deviated, see commit XYZ"

**Cross-referencing:** `bd_id` is the universal key across `plan.md`, `development-plan.xml`, and Beads.

**Auto-generation:** `discovery.md` frontmatter → `requirements.xml`; `design.md` frontmatter → `technology.xml`. Triggers: pre-commit hook (primary) + AI PostToolUse hook (convenience) + CI check (safety net).

**Почему:** Layered SSoT — industry standard (Linear+Notion, Jira+Confluence). Dual-output md+xml без авто-генерации — anti-pattern из-за drift. Docs-as-code single-source → multi-render — SOTA.

## Semantic Markup Reference

### Module Level
```python
# FILE: path/to/file.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: What this module does - one sentence
#   SCOPE: What operations are included
#   DEPENDS: List of module dependencies
#   LINKS: Knowledge graph references
#   ROLE: Optional: RUNTIME | TEST | BARREL | CONFIG | TYPES | SCRIPT
#   MAP_MODE: Optional: EXPORTS | LOCALS | SUMMARY | NONE
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   exported_function - one-line description
#   ExportedClass - one-line description
# END_MODULE_MAP
```

### Function or Component Level
```python
# START_CONTRACT: function_name
#   PURPOSE: What it does
#   INPUTS: { param_name: Type - description }
#   OUTPUTS: { ReturnType - description }
#   SIDE_EFFECTS: External state changes or "none"
#   LINKS: Related modules/functions
# END_CONTRACT: function_name
```

### Code Block Level
```python
# START_BLOCK_VALIDATE_INPUT
# ... code ...
# END_BLOCK_VALIDATE_INPUT
```

### Change Tracking
```python
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.2.0 - What changed and why
# END_CHANGE_SUMMARY
```

## Logging and Trace Convention

**Rule:** All important logs must point back to semantic blocks:
```python
logger.info(
    f"[ModuleName][functionName][BLOCK_NAME] message",
    extra={
        "correlation_id": correlation_id,
        "stable_field": value,
    },
)
```

**Rules:**
- prefer structured fields over prose-heavy log lines
- redact secrets and high-risk payloads
- treat missing log anchors on critical branches as a verification defect
- update tests when log markers change intentionally

## File Structure (dev-projects)

```
docs/
  superpowers/
    specs/
      YYYYMMDD-{feature}-discovery.md    # requirements SSoT (→ requirements.xml)
      YYYYMMDD-{feature}-design.md       # tech/stack SSoT (→ technology.xml)
    plans/
      YYYYMMDD-{feature}-plan.md         # execution playbook
  adr/
    ADR-NNN-*.md                         # architectural decisions
  reports/
    YYYYMMDD-{feature}-report.md         # completion reports
  requirements.xml                       # auto-generated
  technology.xml                         # auto-generated
  development-plan.xml                   # aggregated
  verification-plan.xml                  # derived (tests + code)
  knowledge-graph.xml                    # derived (MODULE_CONTRACT)
  operational-packets.xml                # static GRACE schema
```

## Commit Convention (dev-projects only)

**Rule:** Conventional Commits with GRACE MODULE_ID as scope:
- Code: `<type>(<MODULE_ID>): <description>` — e.g. `feat(M-VOICE-STT): add Whisper pipeline`
- Meta: `<type>(<short-name>): <description>` — e.g. `docs(readme): add voice section`

**Rule:** Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`. Type is always required.

**Rule:** Commit messages in English. Commit without user confirmation when work is atomic and verified.

**Почему:** Conventional Commits — industry standard. Совместимость с release-please, semantic-changelog. MODULE_ID в scope сохраняет GRACE trace для git log.

## Documentation Retrieval Policy

**Rule:** Use documentation MCP (Context7 via `resolve-library-id` → `query-docs`, or equivalent) for library API verification:
- In Design phase (`do-feature` steps 4, 7) — verify all libraries touched by the design
- In Execution phase — on 4 triggers: (a) first contact with a library in current session, (b) version bump vs design, (c) unknown/unfamiliar method, (d) library error in tests

**Rule:** When following an approved plan with pre-verified APIs — retrieval not required.

**Почему:** LLM галлюцинируют API для middle-popularity libs (aiogram, SQLAlchemy 2.0 async) после version bump'ов. Just-in-time verification — SOTA anti-hallucination (Anthropic, Cursor docs).

## Anti-Hallucination Protocol (CRITICAL)

**Rule:** НИКОГДА не упоминать в ответе пользователю конкретное имя файла, переменной, функции, env-ключа, CLI-флага, метода библиотеки, поля БД, API endpoint, конфигурационного параметра, sub-команды БЕЗ предварительной верификации в текущей сессии одним из источников:
1. `Read` / `Grep` / `Glob` по реальному файлу проекта.
2. `<tool> --help` / `--schema` / manpage для CLI.
3. `context7 query-docs` для библиотеки/фреймворка.
4. Прямая цитата из сообщения пользователя в этой же сессии.
5. Содержимое уже выполненного tool result в этой сессии.

**Rule:** Если факт НЕ верифицирован — формулировать ЯВНО как гипотезу: «*возможно стоит добавить X*», «*предположительно есть Y*», «*типично в таких системах используется Z, но нужно проверить*». Запрещены утверждения «в файле есть Y», «переменная Z делает W», «есть команда `/foo`», «можно настроить через `BAR_BAZ`» без verified evidence.

**Rule:** Tooling-уровень (hard rule): любой вопрос пользователя про «что есть в файле / проекте / конфиге X», «какие переменные/команды/опции у Y», «как настроено Z» — **обязательное first action**: `Read(X)` или `Grep`. Текстовый ответ генерируется ТОЛЬКО после получения tool result. Никаких ответов «из памяти про проект» или «по аналогии с похожими проектами».

**Rule:** Hook-уровень: `~/.claude/hooks/anti-hallucination.sh` (Stop hook) сканирует последний assistant message на ALL_CAPS-идентификаторы (env-vars, конфиг-ключи) и блокирует завершение turn'а, если идентификатор не встречается ни в одном tool result / user message текущей сессии. Hook — safety net, не замена дисциплины.

**Rule:** Скорость ответа НИКОГДА не приоритетнее точности. При сомнении — STOP, прочитать источник, потом отвечать. Нарушение этого правила — критический defect, эквивалент unverified subagent claim.

**Rule:** Если hook сработал и заблокировал ответ — НЕ обходить (не маскировать токен, не ломать через подбор регулярки). Запустить верификацию (`Read`/`Grep`/`--help`) и переписать ответ с evidence либо явно пометить пункт как «не проверено, гипотеза».

**Почему:** Галлюцинация имён артефактов в чате — fundamental LLM failure mode. В отличие от кода, где её ловят pre-commit / tests / USER APPROVAL gates, в свободном диалоге нет automated gate. Кейс 2026-05-11: модель в разговоре про onboarding сочинила переменные `AISW_ONBOARDING_MODE` и `AISW_ONBOARDING_RATE_LIMIT`, которых нет в `.env.example` — пользователь поймал руками. Слой 1 (этот текст) даёт ~60% защиты, слой 3 (Read-first hard rule) — ~95%, слой 2 (Stop hook) — финальная сетка от остаточных случаев. Цена — больше tool-вызовов и медленнее ответ; это приемлемо.

## First-Contact Protocol для незнакомых инструментов и форматов

**Trigger:** в текущей сессии впервые встречается:
- CLI инструмент / бинарь (например `grace`, `bd`, `dolt`, `alembic`)
- Конфигурационный формат / схема (GRACE XML, Beads JSONL, custom YAML)
- DSL / разметка (semantic markup, project-specific frontmatter)
- Библиотека / фреймворк (триггер также для Documentation Retrieval Policy)

**Rule:** Прежде чем генерировать или валидировать артефакт в этом формате/инструменте, источники проверяются в строгом приоритете. Останавливаться на первом, который дал авторитетный ответ.

1. **Built-in справка инструмента** — `<tool> --help`, `<tool> <subcommand> --help`, `<tool> --schema`, `<tool> --version --verbose`, manpage, `--examples`
2. **Skill для этого инструмента** в `~/.claude/skills/` — skills с префиксом имени инструмента (`grace-*`, `beads:*`), skill `*-explainer` / `*-init` / `*-help`
3. **Официальная документация** — для библиотек: Context7 (`resolve-library-id` → `query-docs`); для CLI/git проектов: WebFetch на `github.com/<owner>/<repo>` README/docs/examples
4. **Issues / changelog инструмента** — для актуальной версии
5. **Похожий проект в файловой системе** — ТОЛЬКО как **последний** источник и ТОЛЬКО после подтверждения что он сам **passes validation** (например `grace lint --failOn errors` exit 0) для **той же major версии инструмента** (`<tool> --version` совпадает)

**Anti-rule:** Запрещено брать схему/формат из «похожего» проекта без прохождения шагов 1–4. Mantra: *another project that has the file is not a spec*.

**Rule:** Если ни один из шагов 1–5 не дал авторитетного ответа — **остановиться и спросить пользователя**, а не генерировать «по аналогии».

**Почему:** LLM-склонность к imitation learning из «похожих примеров» без верификации — главный источник subtle schema drift. Иерархия источников превращает молчаливое предположение в явный шаг с verifiable артефактом (output of `--help`, content of skill). Кейс 2026-04-28 (Sensedar GRACE XMLs) — сгенерили `<Phase NUM="...">` вместо `<Phase-N>` потому что взяли схему из соседнего проекта без проверки `grace lint` rules.

## Pre-commit Policy

**Rule:** Pre-commit hooks (ruff/lint/format/grace-lint/XML auto-regen/etc.) are **load-bearing quality gates** in dev-projects. They MUST run on every commit.

**Rule:** Do NOT bypass hooks (`git commit --no-verify`, `--no-gpg-sign`, environment overrides like `SKIP=...`, `PRE_COMMIT_ALLOW_NO_CONFIG=1`) unless the user explicitly requests it for this commit. Hook failure → fix the underlying issue, do not skip.

**Rule:** Project pre-commit setup defaults to extending the existing `.git/hooks/pre-commit` script with project-relevant fast checks (ruff check + format-check on staged source files). The `pre-commit` framework + `.pre-commit-config.yaml` are also acceptable when the project has no other hooksPath consumers.

**Rule:** Slow checks (full pytest, integration, e2e) belong in CI/Makefile targets, not in commit-time hooks.

**Rule:** New dev repos inherit a pre-commit baseline via `~/.git-template` (configured globally). When `git init` or `git clone`, hooks are auto-installed unless the project explicitly overrides.

**Почему:** хук — единственный момент, где defects ловятся ДО публикации. Bypass нормализует «технический долг по умолчанию» (Beck, _Refactoring 2nd_). 4-layer defence (policy + templatedir + Claude PreToolUse hook + workflow preflight) — industry-standard SDLC pattern для multi-tool окружений.

## Git Push Policy

**Rule:** Do NOT run `git push` of code automatically. Only on explicit user request.

**Rule:** `bd dolt push` (Beads persistence for multi-machine sync) IS allowed automatically as part of session close protocol.

**Почему:** `git push` кода — внешняя необратимая операция, требует approval. `bd dolt push` — системная utility для persistence без внешнего blast radius.

## Security

**Rule:** Do NOT read `.env*`, `*.pem`, `*.key`, `*.ppk`, `id_rsa*`, `credentials.*`, `.aws/credentials`, `.netrc`, `.npmrc`, `*secret*`, `*_token*`.

**Exception:** Placeholder-only fixtures MAY be read, edited, and written. Allowlist:
- `.env.example` (any depth) — env templates
- `.env.*.example` (any depth, e.g. `.env.prod.example`, `.env.test.example`, `.env.dev.example`) — stand-specific env templates
- `tests/test.env`, `tests/**/test.env`, `tests/**/*.testenv` — test fixtures with placeholder credentials only
Real secrets in any of these files = policy violation regardless of name.

**Rule:** Defence-in-depth — filename heuristics are necessary but not sufficient. Dev-projects MUST run a content-scanner (`gitleaks` or `detect-secrets`) as a pre-commit hook AND in CI. Filename allowlist is the navigation contract for agents; content-scan is the actual security gate. New repos inherit gitleaks via `~/.git-template`.

**Rule:** Do NOT modify files outside the current project (`$PWD`), except `~/ai-steward/**/*.md`, `~/.claude/**`, and `~/.codex/**`.

**Rule:** Do NOT log passwords, tokens, API keys, or session IDs.

**Enforcement:** `~/.claude/settings.json` (deny+sandbox) + `~/.codex/config.toml` (deny+sandbox_mode=workspace-write) for read-side; `gitleaks`/`detect-secrets` pre-commit + CI for write-side.

## Tooling Preferences

**Rule:** When a matching skill exists — use it. Skills take priority over manual task execution.

**Rule:** Use MCP servers for integrations: GitHub, Docker, browsers (playwright/chrome-devtools), documentation (context7), reasoning (sequential-thinking).

**Rule:** Use parallel subagents/agent teams for independent/parallelizable tasks (Claude: `teammateMode` + agent-teams flag; Codex: `[features] multi_agent` + `/agent`).

## Preferences

**Rule:** Prefer simple over complex. Three similar lines > premature abstraction.

**Rule:** SSoT (Single Source of Truth): every fact has exactly one authoritative location. Duplication creates drift.

**Rule:** Do NOT create unnecessary files, folders, or structures outside of what `do-feature` explicitly requires for dev-projects.

**Rule:** Don't design for hypothetical future requirements. No half-finished implementations.

**Rule:** Prefer editing existing files over creating new ones.

**Rule:** Match scope to request — don't bundle refactor with bug fix, don't add features not explicitly requested.

**Rule:** Evidence before assertions — verify before claiming work complete (run tests, check output, don't assume).

**Rule:** Fail-Fast — validate at boundaries (user input, external APIs). Trust internal code; don't over-guard.

**Rule:** When delegating to subagents that produce artifacts (files, commits, configs) — subagent's textual summary is **never** sufficient evidence of correctness. Before reporting work as done, the parent agent MUST run at least one **objective check** that does not depend on the subagent's claims:
- Code changes → `git diff` + run actual validator (linter, tests, schema check)
- Config files → parse with the real tool that consumes them
- Docs/XML → run the project's lint/validate command, not eyeball the diff

If the subagent claims "X passes" — run X yourself. Trust = 0%. **Почему:** subagent context isolated, may hallucinate exit codes, may forget to apply part of edits. Only verifier-tool gives ground truth.

**Rule:** After **bulk auto-edits** (scripts that touch many files in one shot — codemods, header inserters, sed/regex passes, generated migrations) run the **full project quality gate** before declaring done, not only the check you were fixing. Minimum: `make lint` (or equivalent: ruff/format/mypy/eslint), the project's domain validator (`grace lint`, schema check, etc.) AND tests. **Почему:** bulk edits change formatting and adjacent rules in ways the original task never targeted (extra blank lines, broken imports, indentation drift). Кейс 2026-04-28 (Sensedar): скрипт добавил `MODULE_CONTRACT` в alembic baseline, оставил double blank line — `grace lint` ✅ exit 0, но `ruff format --check` упал. Verified только grace, не make lint — gate был зелёным локально, регрессия проявилась у ревьюера.

**Rule:** No backwards-compat hacks for internal code — delete unused vars/functions/imports, don't add "removed" comments.

**Rule:** Prefer declarative (Pydantic schema, SQLAlchemy ORM, type hints) over imperative checks where language allows.

**Rule:** Root-cause over symptom — no destructive shortcuts (`--no-verify`, disabling checks) as "fix".

**Почему:** do-feature определяет обязательный набор артефактов. Вне него — минимализм. Premature abstraction, scope creep, false completion claims и symptom patching — главные LLM failure modes.

## User Adaptation

**Rule:** Read `{User}/CLAUDE.md` or `{User}/AGENTS.md` at session start — contains role, expertise level, preferred style, optional character persona.

**Rule:** Dev-projects — technical language, code-level terminology. Life-projects — simple language, no jargon, step-by-step.

**Rule:** Do NOT assume technical literacy unless profile explicitly states it (e.g. `role: software engineer`).

**Rule:** If profile declares communication style/character (e.g. `стиль общения: Sherlock Holmes`) — match tone accordingly while preserving accuracy.

**Rule:** Prefer user's preferred language (from profile or Language section) over auto-detection.

## Rules for Modifications

1. Before editing any file: read its MODULE_CONTRACT.
2. After editing source or test files: update MODULE_MAP in-header.
3. After adding or removing modules: run `grace-refresh` to update `docs/knowledge-graph.xml`.
4. After changing test files, commands, or log markers: run `grace-refresh --verify` to update `docs/verification-plan.xml`.
5. After editing `discovery.md` or `design.md` frontmatter: pre-commit hook regenerates parent XML (`requirements.xml` / `technology.xml`).

## Memory System Update

**Rule:** Keep instruction files (`CLAUDE.md` / `AGENTS.md`) in sync with project reality. Update at appropriate hierarchy level (global → user → project).

**Rule:** Priority: actual state > documentation. On conflict — update the documentation.

**Rule:** Use ephemeral memories (Codex: `codex memory add`, Claude: auto-memory system) for short-lived facts. Use instruction files for durable rules.

**Triggers to update:** new skill/plugin added, workflow changed, new project type, team/tooling change.

**Почему:** docs-as-code с явной hierarchy — SOTA (ThoughtWorks). Divergence creates silent bugs.

## Multi-machine consistency

**Rule:** `~/.claude/CLAUDE.md` is the SSoT instruction file. `~/.claude/AGENTS.md` and `~/.codex/AGENTS.md` are symlinks to it. The SSoT file MUST be identical across machines.

**Rule:** Shared config (`settings.json`, `config.toml`) MUST be identical across machines.

**Rule:** Machine-specific settings live in `~/.claude/settings.local.json` and `~/.codex/config.toml` profiles (not synced).

**Rule:** Secrets (`.credentials.json`, `.env`) — never in git; per-machine only.

**Rule:** Skills with executable `lib/` (Python scripts, bash orchestrators) MAY be symlinked from `~/.codex/skills/<name>` → `~/.claude/skills/<name>` to keep a single SSoT for logic and tests. Skills that are pure instructions (only `SKILL.md`) typically stay as separate per-tool copies. Current symlinked skills: `full-audit`.

@RTK.md
