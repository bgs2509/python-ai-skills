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

---

# Moved rule text (from CLAUDE.md, 2026-10-13)

> These rules still apply. They were moved out of the always-loaded `CLAUDE.md` to cut per-request context (bd `python-ai-skills-8of.3`, `docs/superpowers/specs/20261013-global-instructions-discovery.md`). Each section is the verbatim former text.

## Dev-project rules

### GRACE Core Principles

> Applies only to **dev-type projects**. Life-type projects are exempt.

#### 0. Design Before Contract

**Rule:** Before creating or updating a MODULE_CONTRACT, the problem MUST be explored (discovery) and a design decision approved by the user. Contracts formalize decisions — they do not substitute for making them.

**Flow:** Discovery → Brainstorming → USER APPROVAL → Contract → Code.

#### 1. Never Write Code Without a Contract

**Rule:** After design approval, before generating or editing module code, create or update its MODULE_CONTRACT with PURPOSE, SCOPE, INPUTS, and OUTPUTS.

**Scope:** Applies to **module boundaries** (public API between modules). Internal implementation details inside a module MAY evolve code-first; SSoT for internals is the code itself.

#### 2. Semantic Markup Is Load-Bearing Structure

**Rule:** Markers like `# START_BLOCK_<NAME>` and `# END_BLOCK_<NAME>` are navigation anchors, not documentation. They MUST be:
- uniquely named
- paired
- proportionally sized so one block fits inside an LLM working window

#### 3. Knowledge Graph Is Always Current

**Rule:** `docs/knowledge-graph.xml` is the project map. When you add a module, move a module, rename exports, or add dependencies, run `grace-refresh` so future agents can navigate deterministically.

#### 4. Verification Is a First-Class Artifact

**Rule:** Testing, traces, and log anchors are designed before large execution waves. `docs/verification-plan.xml` is part of the architecture, not an afterthought. Logs are evidence. Tests are executable contracts.

#### 5. Top-Down Synthesis

**Rule:** Code generation follows:
`Discovery → RequirementsAnalysis → Brainstorming → TechnologyStack → DevelopmentPlan → VerificationPlan → Code + Tests`

Never jump straight to code when requirements, architecture, or verification intent are still unclear.

### Workflow Hierarchy (dev-projects only)

**Rule:** For any new feature, bugfix, or significant change in a `dev` project — invoke `do-feature` skill as the **single entry point**. It orchestrates Discovery → Brainstorming → GRACE Plan → Writing Plans → Execution → Review → Finish.

**Flow:** `bd create` → Discovery → [APPROVAL] → Brainstorming → [APPROVAL] → GRACE Ask → GRACE Plan → Q&A Contracts → Writing Plans → [APPROVAL] → Execution → Review → Finish → `bd close`.

### USER APPROVAL Gates (dev-projects only)

**Meta:** Agents have freedom in **HOW** to implement, but not in **WHAT** to build. Contracts, plans, graph references, verification requirements, and USER APPROVAL gates define the allowed space.

**Rule:** Three mandatory gates in `do-feature`:
- After Discovery (step 3) — approve FR/NFR/scope
- After Brainstorming (step 5) — approve design
- After Writing Plans (step 10) — approve implementation plan

**Rule:** One advisory gate during Execution (step 11): if any step deviates from the approved plan, prompt "deviation detected, approve?" before continuing.

**Rule:** Gates MUST NOT be skipped by the agent's own initiative.

**Rule (auto-approval exception):** Gates MAY be auto-approved ONLY when BOTH hold:
1. Explicit user opt-in: a `--auto-approve` flag, an auto-approving orchestrator the user invoked (`do-autopilot`, `do-multiagent`), or a standing `feedback` memory.
2. The gate artifact passes the risk × evidence matrix defined in `do-feature` (`## Flags`).

`high`-risk gates always remain interactive regardless of opt-in. Auto-approval never bypasses hard quality gates, pre-commit hooks, or destructive-operation confirmations.

### Plan Sizing — Context-Window Budget (dev-projects only)

**Rule:** При создании любого плана реализации (`do-feature` Writing Plans, GRACE phases, roadmap) фаза/под-этап ДОЛЖНА укладываться в **одно контекстное окно активной модели** со всеми файлами, документами, тестами и логами, которые потребуются для её выполнения и верификации.

**Rule:** Если оценка scope (файлы × средний размер + контракты + тесты + логи + plan.md) превышает ~60% эффективного окна модели — фаза дробится на под-этапы (`Phase-N.a`, `Phase-N.b`, …) до выполнения требования.

**Rule:** Граница раскола проводится по смене *стека / директории / правил / SSoT-артефакта*, а не по числу файлов. Один под-этап = один связный набор файлов с общими импортами, общим тест-фикстурным окружением и общим набором правил.

**Rule:** Если под-этапы получаются мельче ~20% окна и между ними сильная логическая связь — объединить обратно (KISS, anti-fragmentation). Цель — **fit, не fragment**.

**Rule:** Бюджет окна оценивать по *эффективному* размеру (с учётом system prompt, skills, MCP tools, истории) — не по номинальному размеру окна активной модели: номинал никогда не бывает свободен целиком.

**Rule (какое именно окно считать):** окна ярусов различаются в разы, и фазу планирует одна модель, а исполняет другая. Считать по **наименьшему** окну среди тех моделей, которые будут фазу исполнять и верифицировать, а не по окну модели, пишущей план. Номиналы — в `claude-home/model-registry.json` (`context_tokens`): 1M у большинства ярусов, 200K у `cheap`=haiku, 122 880 у локального `qwen38`. Практический пересчёт для оценки объёма: **~4,45 знака на токен** на связном английском тексте (замер 2026-09-22, `docs/research/model-passports-2026-09.md`).

### Documentation SSoT (dev-projects only)

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

### Semantic Markup Reference

> Полный справочник шаблонов разметки (MODULE_CONTRACT, MODULE_MAP, CONTRACT, BLOCK, CHANGE_SUMMARY) вынесен в `CLAUDE-APPENDIX.md` — читать перед написанием контрактов.

### Logging and Trace Convention

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

### File Structure (dev-projects)

> Дерево каталогов `docs/` для dev-проектов — в `CLAUDE-APPENDIX.md`; SSoT-таблица зон — выше в «Documentation SSoT».

### Rules for Modifications

1. Before editing any file: read its MODULE_CONTRACT.
2. After editing source or test files: update MODULE_MAP in-header.
3. After adding or removing modules: run `grace-refresh` to update `docs/knowledge-graph.xml`.
4. After changing test files, commands, or log markers: run `grace-refresh --verify` to update `docs/verification-plan.xml`.
5. After editing `discovery.md` or `design.md` frontmatter: pre-commit hook regenerates parent XML (`requirements.xml` / `technology.xml`).

## Model Routing — full text

**Meta:** The Anthropic quota is the scarce pool and must be spent on judgement, not on bulk reading. Savings come from **where intermediate reading happens**: a delegate that reads 40 files and returns a 2-page digest costs the Anthropic pool only the digest.

**Rule:** Route work to the cheapest pool that can do it correctly:
1. **Anthropic** (scarce) — architecture decisions, `/best-*` analysis, instruction/schema design, subtle debugging, and **verification of every other pool's output**.
2. **Z.ai GLM** via the `claude-glm` shell function (`~/.bashrc`, added 2026-08-17) — reconnaissance, inventories, grep/log sweeps, web research, bulk mechanical edits, draft docs/tests from a finished spec, independent corpus annotation.
3. **Local gateway** (DGX Spark `spark-1`: `qwen38-27b`, `gemma-4-26b`, `bge-m3`) — **costs no tokens at all**, only machine time, and is the only channel where code never leaves own infrastructure. But it is the slowest and narrowest channel: measured 80 s on a trivial prompt, 190 s at ~65k context, and it refuses anything past its 122,880-token window (2026-09-22, `docs/research/model-passports-2026-09.md`). Use it for **queued background work nobody waits on** — corpus annotation, batch scoring, overnight sweeps. Never put it inside a loop or on a step a human is waiting for: ten in-loop calls cost 13-32 minutes of pure latency.
4. **Codex** (`codex exec -m ...`) — second independent voice where annotator agreement is measured.

**Rule (structural constraint):** Subagents spawned via the Agent tool ALWAYS run on Anthropic models — the model parameter accepts Anthropic tiers only. To delegate to GLM, shell out instead:
```bash
bash -ic "claude-glm -p --model opus --allowedTools Read Grep Glob Bash < task.txt" > out.md
```
Working precedent: `Sensedar-Spark/scripts/run_markup_queue.sh`. That hand-written form is the fallback for one-off experiments; for ordinary delegation prefer `model-run.sh` (rule below), which builds the same command from the registry and records the attempt.

**Rule (tier mapping is NOT identity):** `claude-glm` remaps tiers — `--model fable` → `glm-5.3[1m]`, `--model opus` → **`glm-5.3-flash`**, `--model sonnet`/`--model haiku` → `glm-4.7`. Asking for "opus" under `claude-glm` gets Flash. Pick deliberately. Three consequences worth knowing before writing a delegate: `glm-5.3` has only `low`/`high`/`max` efforts (no `medium`, no `xhigh`) and **cannot disable reasoning**; `glm-4.7`'s window is ~205k, not 1M; and under `claude-glm` the four **claude.ai connectors** (Claude Docs, Gmail, Google Calendar, Google Drive) are disabled because the Z.ai key outranks the claude.ai login — all seven local MCP servers, including `context7`, keep working (verified via `claude mcp list`, 2026-09-22).

**Rule (choosing WHICH model, not which pool):** the pool rules above say where work belongs; the concrete model, its launch flags, its timeout and its fallback order live in **`~/.claude/model-registry.json`** (repo: `claude-home/model-registry.json`) under six roles — `planner`, `executor`, `researcher` (web research with sources), `reviewer` (do-feature Step 12 code review, ADR-003), `batch`, and the reference-only `orchestrator`. Do not restate model names, efforts or timeouts in a skill, a prompt or this file: the registry is their single home, and a copy will drift from it.

**Rule (delegating by role):** to hand work to another pool, call the runner instead of assembling a command by hand:
```bash
~/.claude/scripts/model-run.sh --role executor --task task.txt --out result.md
```
It picks the first usable model of that role, applies the registry timeout, skips models under an active penalty, distinguishes *unavailable* (quota/5xx/auth → 1-hour penalty on the whole model) from *context overflow* (no penalty — jump to a wider window) and from *slow* (no penalty — slowness is a passport property, not a fault), and appends one facts-only line per attempt to `~/.claude/model-journal.jsonl`. For web research with sources use `--role researcher` (its own 900 s timeout, `roles.<role>.timeout_seconds`, replaces each model's own timeout for that role, longer or shorter). Pass `--expect REGEX` to reject an empty or off-target answer as `check_failed` (never penalised, next model tried); every non-`ok` attempt that actually ran keeps its output under `~/.claude/model-outputs/` (age-pruned), path and size on the journal line. The journal and `~/.claude/model-penalties.json` are machine-local runtime state and are never committed. Call the runner exactly as shown — by path, as its own Bash command, not via `bash …`, not in a pipe or `;`/`&&` chain: only that form matches `sandbox.excludedCommands`, and the runner must write under `~/.claude`, which the Bash sandbox protects with no `allowWrite` exemption (verified 2026-09-24).

**Rule (reading the journal):** `~/.claude/scripts/model-stats.py` is the way to look at it — `--since 24` for the last day, `--json` for machine output. It reports per-model calls, outcome breakdown, median and p90 seconds, active penalties, and **the share of attempts kept off the Anthropic pool** — the one number that says whether delegation is paying for itself. Counted from journal lines only; nothing is scored or estimated.

**Rule (orchestrator is a human choice):** the orchestrator is the main session and is selected by the user at session start via `/model`. A session cannot re-pick its own model from inside itself, so `model-run.sh` never dispatches the `orchestrator` role — that entry is a reference list only.

**Rule:** Prefer a read-only `--allowedTools` set for reconnaissance over `--dangerously-skip-permissions`; when a delegate must write, bound it to an isolated worktree.

**Rule:** Delegation does NOT relax the Trust = 0% rule (see Preferences → subagent artifacts). Run the validator/tests yourself on whatever a cheaper model produced.

**Rule:** Z.ai and Codex pools are finite too (observed: `glm` hitting the Z.ai subscription limit, reset on Beijing time). Spread heavy background work across pools rather than draining one.

## Security — scope of the read-side gate

**Scope of the read-side gate (honest limits, 2026-08-31):** `deny` binds the `Read` tool only, so any allowed command that prints a file walks around it. `cat`, `head`, `tail` and `sudo cat` were removed from the allow list for that reason; `grep`/`rg`/`find`, `ssh * cat` and arbitrary interpreters (`python3 -c "open('.env').read()"`) remain capable and are NOT blocked. Deny patterns must carry a `**/` prefix or an absolute path — a bare `Read(.env)` matches only the cwd root. The `*secret*`/`*_token*` masks from the Rule above are deliberately NOT in the deny list (they false-positive on legit code like `secrets.py`) — they bind agent discipline only. Treat the filename deny-list as a navigation contract for agents; the real gates are file modes (600/700) and the content scanner at commit time. Since 2026-09-24 the Bash sandbox is live on the laptop and `sandbox.credentials` (template) denies sandboxed commands the SSH/GPG dirs, the gh/codex/Claude auth files, the GLM/qwen/secrets env files and `CONTEXT7_API_KEY` — an OS-level read gate for Bash only; commands in `sandbox.excludedCommands` (`git *`, `gh *`, `docker *`, `model-run.sh *`) run outside it — only as a standalone call: a pipe or chain with any other command, a `cd` or `git -C <dir>`, a redirect, `$(...)` or `/usr/bin/git` keeps the whole call sandboxed. The trailing ` *` is load-bearing: a bare `git` matches only `git` with no arguments (sandboxing docs), which kept every git call sandboxed until 2026-10-13; `git` is also excluded from RTK rewriting for the same reason (`RTK.md`).

## Pre-commit — template mechanics

**Rule:** The `~/.git-template` bootstrap hook delegates to the `pre-commit` framework when `.pre-commit-config.yaml` exists, otherwise falls back to a staged `gitleaks` scan. Project-relevant fast checks (ruff check + format-check on staged source files) are added per project — via `.pre-commit-config.yaml` or by extending `.git/hooks/pre-commit`. SSoT of the template hook: `python-ai-skills/claude-home/git-template/pre-commit`.

**Rule:** New dev repos inherit a pre-commit baseline via `~/.git-template` (configured globally). When `git init` or `git clone`, hooks are auto-installed unless the project explicitly overrides.

**Rule:** The template only ever applies to NEW repos, so repos predating it commit unprotected — `python-ai-skills` itself did, for months. When adopting a repo, install the bootstrap hook explicitly (`install-claude-symlinks.sh` does this for its own checkout) and verify with a realistic staged secret. `gitleaks` deliberately ignores well-known documentation placeholders such as the AWS example key, so probing with one makes a working gate look dead.

## Explanation Protocol — разобранные примеры

**Разобранные примеры** (образец применения принципа, НЕ список запрещённых слов — в открытой предметной области такой список составить невозможно):
- «во время индексирования», не `index-time` — дефисной формы нет в документации Elasticsearch, она достроена по аналогии с существующим `search-time`
- «тестирование», «запуск тестов», не «прогон» — обычное русское слово существует
- «сколько текста снимает эта полоса», не «урожайность полосы» — образ из сельского хозяйства, к разбору текста отношения не имеющий; в источниках предметной области в этом значении не встречается
