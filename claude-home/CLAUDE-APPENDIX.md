# Global Instructions — Appendix

> Rationale and reference material moved out of `CLAUDE.md` (loaded every session)
> to keep the instruction file lean. Read on demand. Headings mirror `CLAUDE.md`.

## Language

**Почему:** Русский — предпочитаемый язык общения. Английский в коде — industry standard и лучше работает с LLM (training data bias).

## Output Formatting

**Почему:** Claude Code рендерит markdown в моноширинном терминале с ANSI-подсветкой — `**bold**`, `*italic*`, `` `code` `` и fenced code blocks автоматически окрашиваются. Произвольных цветов в markdown нет, поэтому «выделение цветом» = семантическая разметка. Нумерация даёт якоря для ссылок, списки разбивают визуальный шум, пустые строки между абзацами — базовая типографика читаемости.

## Project Classification

**Почему:** GRACE и do-feature создают overhead (13 шагов, XML-артефакты), избыточный для life-проектов без кода.

### 0. Design Before Contract

**Почему:** premature-formalization — классический anti-pattern. Контракт без понимания проблемы потом либо переписывается, либо насильно натягивается на реальность. DDD "Knowledge Crunching" (Evans) и API Design First (Stripe) оба требуют exploration до формализации.

## Workflow Hierarchy (dev-projects only)

**Почему:** `do-feature` физически объединяет Superpowers (процесс), GRACE (структура), Beads (трекинг) — Composite-паттерн, SOTA для multi-framework окружений.

## USER APPROVAL Gates (dev-projects only)

**Почему:** Human-in-the-loop gates защищают от дрейфа в неверную сторону. 3 mandatory — sweet spot. Advisory on deviation — минимум overhead, максимум защиты execution. Исключение легализует фактическую практику (do-autopilot, do-feature --auto-approve) без потери сути правила: агент не решает сам — авто-одобрение всегда следствие явного выбора пользователя + объективной матрицы (аудит 2026-07-02).

## Plan Sizing — Context-Window Budget (dev-projects only)

**Почему:** превышение окна → context-truncation → дрейф плана и тихие ошибки execution. Дробление мельче нужного → overhead на approval-gates × N, drift между под-фазами, fragmented SSoT. Sweet spot — 40–60% окна на под-этап, оставляя запас на iteration logs, tool results и непредвиденные файлы. Кейс 2026-05-01 (Sensedar Phase 12 UI): 6 экранов в одной фазе без UI-scope-cut требовали бы split на 3+ под-фазы; сокращение MVP до 1 экрана позволило оставить монолит.

## Skill Hierarchy

**Почему:** Supervisor-worker pattern (LangGraph, Anthropic agentic patterns) — SOTA для skill composition. Auto-transitions создают скрытые зависимости.

## Documentation SSoT (dev-projects only)

**Почему:** Layered SSoT — industry standard (Linear+Notion, Jira+Confluence). Dual-output md+xml без авто-генерации — anti-pattern из-за drift. Docs-as-code single-source → multi-render — SOTA.

## Commit Convention (dev-projects only)

**Почему:** Conventional Commits — industry standard. Совместимость с release-please, semantic-changelog. MODULE_ID в scope сохраняет GRACE trace для git log.

## Documentation Retrieval Policy

**Почему:** LLM галлюцинируют API для middle-popularity libs (aiogram, SQLAlchemy 2.0 async) после version bump'ов. Just-in-time verification — SOTA anti-hallucination (Anthropic, Cursor docs).

## Anti-Hallucination Protocol (CRITICAL)

**Почему:** Галлюцинация имён артефактов в чате — fundamental LLM failure mode. В отличие от кода, где её ловят pre-commit / tests / USER APPROVAL gates, в свободном диалоге нет automated gate. Кейс 2026-05-11: модель в разговоре про onboarding сочинила переменные `AISW_ONBOARDING_MODE` и `AISW_ONBOARDING_RATE_LIMIT`, которых нет в `.env.example` — пользователь поймал руками. Слой 1 (этот текст) даёт ~60% защиты, слой 3 (Read-first hard rule) — ~95%, слой 2 (Stop hook) — финальная сетка от остаточных случаев. Цена — больше tool-вызовов и медленнее ответ; это приемлемо.

## Explanation Protocol (CRITICAL)

**Почему:** замена понятного слова на жаргон и смена обозначения по ходу текста — два разных дефекта с общим результатом: читатель перестаёт понимать текст и начинает сомневаться в точности всего остального. Причина не в стиле, а в механизме: curse of knowledge (Camerer/Loewenstein/Weber, 1989) плюс отсутствие привязки модели к глоссарию на inference. Отраслевое лекарство — «one term, one concept» (Google developer style guide, Phrase style guide: «do not invent synonyms for key concepts») и «one word, one meaning» (ASD-STE100). Смена слова ради красоты называется elegant variation (Fowler, 1906): в художественном тексте достоинство, в объяснении — дефект, создающий ложные различия между понятиями. Правило Оруэлла (Politics and the English Language, 1946), пятое из шести: «Never use a foreign phrase, a scientific word or a jargon word if you can think of an everyday English equivalent» — здесь применяется к русскому: есть обычное русское слово, значит используется оно. Списки запрещённых слов (termbase forbidden terms, Vale substitution rules) работают только в закрытой предметной области; при разговоре про ML, поэзию и воспитание детей в одних и тех же сессиях контролируется процедура выбора слова, а не словарь. Кейс 2026-08-13: в разговоре про Elasticsearch модель нашла в документации `search-time`, достроила по симметрии `index-time`, которого в документации нет, и подала как существующий термин — пользователь потратил четыре хода, чтобы это вскрыть. Смежное правило — Anti-Hallucination Protocol (имена артефактов); здесь тот же принцип для терминов.

## First-Contact Protocol для незнакомых инструментов и форматов

**Почему:** LLM-склонность к imitation learning из «похожих примеров» без верификации — главный источник subtle schema drift. Иерархия источников превращает молчаливое предположение в явный шаг с verifiable артефактом (output of `--help`, content of skill). Кейс 2026-04-28 (Sensedar GRACE XMLs) — сгенерили `<Phase NUM="...">` вместо `<Phase-N>` потому что взяли схему из соседнего проекта без проверки `grace lint` rules.

## Pre-commit Policy

**Почему:** хук — единственный момент, где defects ловятся ДО публикации. Bypass нормализует «технический долг по умолчанию» (Beck, _Refactoring 2nd_). 4-layer defence (policy + templatedir + Claude PreToolUse hook + workflow preflight) — industry-standard SDLC pattern для multi-tool окружений.

## Git Push Policy

**Почему:** `git push` кода — внешняя необратимая операция, требует approval. `bd dolt push` — системная utility для persistence без внешнего blast radius. 2026-07-08 — ассистент дважды сам открыл `gh pr create --draft` для готовых веток без спроса. Пользователь явно запретил PR как способ доставки по умолчанию и потребовал вместо этого предлагать локальный merge. Это отдельный аспект от правила выше (push только по запросу) — там про МОМЕНТ push, здесь про ВЫБОР стратегии landing.

## Preferences

**Почему:** subagent context isolated, may hallucinate exit codes, may forget to apply part of edits. Only verifier-tool gives ground truth.

**Почему:** bulk edits change formatting and adjacent rules in ways the original task never targeted (extra blank lines, broken imports, indentation drift). Кейс 2026-04-28 (Sensedar): скрипт добавил `MODULE_CONTRACT` в alembic baseline, оставил double blank line — `grace lint` ✅ exit 0, но `ruff format --check` упал. Verified только grace, не make lint — gate был зелёным локально, регрессия проявилась у ревьюера.

**Почему:** do-feature определяет обязательный набор артефактов. Вне него — минимализм. Premature abstraction, scope creep, false completion claims и symptom patching — главные LLM failure modes.

## Memory System Update

**Почему:** docs-as-code с явной hierarchy — SOTA (ThoughtWorks). Divergence creates silent bugs.

## Semantic Markup Reference

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

## File Structure (dev-projects)

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

