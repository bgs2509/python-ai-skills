# Global Instructions

> Cross-tool SSoT for AI coding agents.
> Rationale («Почему») каждого правила и справочные секции — в `CLAUDE-APPENDIX.md` (рядом с этим файлом; читать при сомнении в правиле, в сессию не грузится).
> Discovery paths: `~/.claude/CLAUDE.md` (Claude Code), `~/.claude/AGENTS.md` (symlink), `~/.codex/AGENTS.md` (symlink).

## Language

**Rule:** Always respond to the user in Russian. Code, commit messages, variable names, file paths, YAML/JSON keys — always in English.

**Rule:** Maintain full orthographic correctness (diacritics, accents) for both languages.

## Output Formatting

**Rule:** Нумерованные списки предпочтительнее маркированных, когда у элементов есть порядок, приоритет или на них можно ссылаться («см. п. 3»). Маркированные — только когда порядок действительно не важен.

**Rule:** Маркированный список всегда лучше, чем перечисление через запятую в одну строку. Любое перечисление из 2+ однородных элементов — выносить в список.

**Rule:** Абзацы отделять пустой строкой. Не склеивать разные мысли в один блок текста.

**Rule:** Активно использовать визуальное выделение для цветового подсвечивания в терминале:
1. `**жирный**` — ключевые термины, правила, заголовки пунктов
2. `*курсив*` — акценты, оговорки, мета-комментарии
3. `` `код` `` — идентификаторы, пути, команды, имена файлов/переменных
4. Блоки кода с указанием языка (```` ```bash ````, ```` ```python ````) — для подсветки синтаксиса

**Rule:** Запрет markdown-таблиц в ответах в терминале. В файлах (`*.md`, docs) таблицы разрешены. (Правило самодостаточно; файл стиля `output-styles/no-tables.md` — опциональный дубль для ручного включения, нигде не активирован.)

## Project Classification

**Rule:** Every project MUST declare its type in its root `AGENTS.md` (the single real instruction file; `CLAUDE.md` is a symlink to it, `ln -s AGENTS.md CLAUDE.md`):
- `project_type: dev` — software development (code, tests, infra)
- `project_type: life` — life tracking (Health, Family, Study, Career, Home, Hobby, Budget data entry)

**Rule:** GRACE framework, `do-feature` skill, USER APPROVAL gates, and strict commit conventions apply **only** to `dev` projects. For `life` projects work conversationally without these frameworks.

## Dev-project workflow (dev-projects only)

**Rule (task levels):** Before changing anything in a `dev` project pick the lightest level that fits and announce it in one line: `Level N: <signal>`. On a boundary take the heavier procedure (lower number); mid-task move only to a heavier one (e.g. 2 → 1), never to a lighter one. "Risk" = the criteria in `do-feature` → Flags. "Shipped code" = code a deployed service, an installed tool or a library user runs (in this repo: hooks, scripts).
0. Several shipped features from one draft → `do-autopilot` / `do-multiagent`.
1. Shipped code with risk `medium`/`high`, a new module, or a change to a contract, public API or DB schema → full `do-feature`: `bd create` → Discovery → [APPROVAL] → Brainstorming → [APPROVAL] → GRACE Ask → GRACE Plan → Q&A Contracts → Writing Plans → [APPROVAL] → Execution → Review → Finish → `bd close`. Design is approved before contracts, contracts before code.
2. Shipped code, risk `low`, no contract change, not a bug fix → `do-feature --lite`.
3. A reproducible bug, risk `low`, no contract change → `superpowers:systematic-debugging` → failing test → fix → commit; in a GRACE project through `grace-fix`.
4. No executable code changes (docs, instructions, config, skill text, GRACE XML) → edit → the validator that consumes the file → commit.
5. Throwaway code nothing deploys, installs or imports (one-off script, experiment) → write and run; no tests, review, commit or `bd`. Reused later → level 2.

**Rule:** Levels 2–4 in a GRACE project run `grace lint` before the commit. Levels 4–5 open no `bd` issue for the edit itself: close the issue the work resolves, file one for leftovers.

**Rule:** USER APPROVAL gates are never skipped on the agent's own initiative. Auto-approval only with explicit user opt-in (`--auto-approve`, an auto-approving orchestrator the user invoked, or a standing `feedback` memory) AND a passing risk × evidence matrix (`do-feature` → Flags); `high`-risk gates stay interactive. Auto-approval never bypasses quality gates, hooks or destructive-operation confirmations.

**Rule:** The full rule text for GRACE principles, Plan Sizing (context-window budget), the Documentation SSoT table and drift resolution, semantic markup, the logging convention and the rules for modifications lives in `~/.claude/CLAUDE-APPENDIX.md` → "Dev-project rules". Read that section before any change to source or test files in a dev project, before planning a phase, and before writing or editing a MODULE_CONTRACT or other GRACE artifacts.

## Skill Hierarchy

**Rule:** Every skill has one role:
- `orchestrator` — may invoke other skills (do-feature, do-autopilot, do-multiagent)
- `worker` — executes a single task, MUST NOT auto-transition (brainstorming, writing-plans, test-driven-development, best-approach/best-rank/best-questions + their engine best-research, grace-plan, grace-execute)
- `utility` — single-purpose helpers (git-commit, git-branch, grace-refresh, grace-ask, best-recommend)

**Rule:** Workers and utilities MUST NOT auto-transition to other skills. Transitions made only by an orchestrator or by the user.

## Commit Convention (dev-projects only)

**Rule:** Conventional Commits with GRACE MODULE_ID as scope:
- Code: `<type>(<MODULE_ID>): <description>` — e.g. `feat(M-VOICE-STT): add Whisper pipeline`
- Meta: `<type>(<short-name>): <description>` — e.g. `docs(readme): add voice section`

**Rule:** Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`. Type is always required.

**Rule:** Commit messages in English. Commit without user confirmation when work is atomic and verified. This rule wins over the Beads block's `Conservative` "do not commit unless asked" default (user decision 2026-08-31; resolution recorded in `python-ai-skills/CLAUDE.md` → "Commit Authority"). It grants nothing for `push` — see Git Push Policy.

## Naming

**Rule:** This section is the single source of naming rules for every project. Each rule has an ID. A project changes a rule only for itself: its own `AGENTS.md` gets a `## Naming overrides` section with lines `<ID>: <project rule>`; a listed ID replaces the global rule in that project, unlisted IDs stay global. Skills and checks that name things read both.

**Rule (N-BRANCH):** Every new git branch name contains `branch` as a separate segment (bounded by the start, the end, `-`, `/` or `_`), so a branch name is never mistaken for a made-up term. Form: `<type>/branch-<slug>` — `<type>` from Commit Convention above, `<slug>` short kebab-case English, e.g. `feat/branch-gigaam-asr`. Claude Code worktrees: pass that form as the worktree name; Claude Code prefixes it with `worktree-`. Existing branches are not renamed (bd `python-ai-skills-31d`).

**Rule (N-DOCS):** Dev-project document names and the `docs/` tree — `CLAUDE-APPENDIX.md` → "File Structure (dev-projects)".

**Rule (N-PY):** Python identifiers — `~/.claude/skills/_code-quality/reference/naming.md`.

## Documentation Retrieval Policy

**Rule:** Use documentation MCP (Context7 via `resolve-library-id` → `query-docs`, or equivalent) for library API verification:
- In Design phase (`do-feature` steps 4, 7) — verify all libraries touched by the design
- In Execution phase — on 4 triggers: (a) first contact with a library in current session, (b) version bump vs design, (c) unknown/unfamiliar method, (d) library error in tests

**Rule:** When following an approved plan with pre-verified APIs — retrieval not required.

## Anti-Hallucination Protocol (CRITICAL)

**Rule:** НИКОГДА не упоминать в ответе пользователю конкретное имя файла, переменной, функции, env-ключа, CLI-флага, метода библиотеки, поля БД, API endpoint, конфигурационного параметра, sub-команды БЕЗ предварительной верификации в текущей сессии одним из источников:
1. `Read` / `Grep` / `Glob` по реальному файлу проекта.
2. `<tool> --help` / `--schema` / manpage для CLI.
3. `context7 query-docs` для библиотеки/фреймворка.
4. Прямая цитата из сообщения пользователя в этой же сессии.
5. Содержимое уже выполненного tool result в этой сессии.

**Rule:** Если факт НЕ верифицирован — формулировать ЯВНО как гипотезу: «*возможно стоит добавить X*», «*предположительно есть Y*», «*типично в таких системах используется Z, но нужно проверить*». Запрещены утверждения «в файле есть Y», «переменная Z делает W», «есть команда `/foo`», «можно настроить через `BAR_BAZ`» без verified evidence.

**Rule:** Tooling-уровень (hard rule): любой вопрос пользователя про «что есть в файле / проекте / конфиге X», «какие переменные/команды/опции у Y», «как настроено Z» — **обязательное first action**: `Read(X)` или `Grep`. Текстовый ответ генерируется ТОЛЬКО после получения tool result. Никаких ответов «из памяти про проект» или «по аналогии с похожими проектами».

**Rule:** Скорость ответа НИКОГДА не приоритетнее точности. При сомнении — STOP, прочитать источник, потом отвечать. Нарушение этого правила — критический defect, эквивалент unverified subagent claim.

## Explanation Protocol (CRITICAL)

**TRIGGER:** ответ объясняет, как что-то работает, почему так устроено, в чём разница между понятиями, или разбирает незнакомую пользователю тему. Любая область — код, ML, поэзия, воспитание детей.
**SKIP:** отчёт о выполненной работе, список файлов, короткий фактический ответ.

**Rule:** Называть явление обычным русским словом. «Во время индексирования», а не `index-time`. «Тестирование», а не «прогон». Вводить термин ТОЛЬКО если обычного русского слова не существует ИЛИ термин нужен пользователю для дела (встретится в документации, прозвучит на собеседовании) — и тогда сразу с русским эквивалентом: `search-time` — во время поиска.

**Rule:** ЗАПРЕЩЕНО обозначать величину или явление **образом** — метафорой, переносным смыслом, словом из чужой предметной области. «Урожайность полосы», «здоровье конвейера», «аппетит модели», «дыхание системы» — это украшения, а не термины: читатель вынужден угадывать, что за ними стоит, и каждый угадает своё. Писать буквально: «сколько текста снимает эта полоса», «сколько проверок конвейер проходит», «сколько памяти занимает модель».

**Rule:** Проверка на образ, применять к каждому существительному, которое обозначает величину: если по прямому значению слово принадлежит другой области — сельскому хозяйству, медицине, войне, спорту, погоде, телесности — а в источниках предметной области в этом значении не встречается, то это образ. Заменить описанием того, что измеряется.

**Rule:** Тяга к яркому слову — сама по себе признак. Если при письме хочется сказать «выразительнее», это момент, когда надо остановиться и написать, что именно имеется в виду. Скучная точная фраза всегда лучше живой неточной.

**Rule (граница):** Правило не запрещает образы, УЖЕ принятые в предметной области и подтверждаемые её источниками. «Клапан», «дребезг», «шум» в проекте Sensedar — законные обозначения, потому что они введены его же документами и там определены. Незаконно изобретать новый образ самому.

**Rule:** Одно явление — одно обозначение на весь ответ и всю сессию. Выбрать обозначение при первом упоминании и дальше повторять его дословно. Повторять одно и то же слово — правильно. Заменять синонимом ради разнообразия — дефект, даже если синоним точнее звучит.

**Rule:** Каждый термин проверяется отдельно и по дословной форме. Если один термин пары подтверждён в источнике, второй НЕ считается подтверждённым по симметрии. Нет дословной формы в источнике — писать обычными русскими словами.

**Rule:** Слово, обозначающее роль или отношение («автор», «источник», «владелец», «родитель», «клиент», «узел», «запись», «ключ»), употребляется ТОЛЬКО с указанием, **чего именно**: «автор публикации», «источник данных», «родитель события». Голое слово в роли термина запрещено — читатель не обязан догадываться, чего оно автор.

**Rule:** Если такое слово имеет в предметной области техническое значение (колонка таблицы, поле схемы, единица группировки) — назвать это значение при первом употреблении вместе с границами применимости: «автор — значение колонки `author_name`; у публикаций из telegram оно пустое». Слово, выглядящее понятным, понято не будет.

**Rule:** Отглагольное существительное («отключение», «включение», «удаление», «перенос», «сброс») употребляется только с указанием объекта: не «довод за отключение», а «довод за отключение ступени канонизации». Действие без объекта — не мысль, а её обломок.

**Rule:** При выборе конкретного объекта для примера, проверки или замера называть **правило отбора**, а не факт выбора: не «взял одного автора», а «взял автора с наибольшим числом публикаций за 7 суток среди тех, у кого их 15–40 и длина текста 200–3000 знаков». Без правила замер невоспроизводим и его нельзя оспорить.

**Rule:** У введённого термина называть источник: из документации (с указанием какой именно) или общепринятый в отрасли. Не можешь назвать источник — это не термин, а собственная конструкция; описывать словами.

**Rule:** Порядок изложения — от простого к сложному: понятие не появляется в тексте раньше, чем объяснено. Это касается заголовков, списков и поправок к предыдущему ответу наравне с основным текстом.

**Rule (называть сущность, а не роль):** Упоминая участника работы — модель, сценарий, службу, набор данных, — называть **что это конкретно**, а не роль, которую он играет. «Действующий фильтр», «наша модель», «эталон», «сборщик» — это роли: под ними в одном проекте скрываются разные сущности, и читатель подставит не ту. Писать: «обучаемая модель `brand_gbm.npz`, её вердикт в поле `publications.brand_relevant`», «эталон — три разметчика: opus, sonnet, glm». Роль допустима ТОЛЬКО после того, как в этом же ответе названа сущность.

**Rule (роль повторяется при каждом упоминании в новом ответе):** То, что сущность названа в прошлом ответе, не считается: у читателя нет обязанности помнить. В каждом ответе, где роль употребляется впервые, рядом стоит сущность. Дешевле повторить четыре слова, чем дать перепутать две разные вещи.

**Rule (запрет на собственные обозначения для состояний данных):** Состояние записи в базе или файле называется тем, что в ней записано, а не придуманным именем. «Серая зона», «полоса неопределённости», «промежуточный статус» — конструкции; правильно: «поле `brand_relevant` пусто», «оценка между 0,06 и 0,659, вердикт не записан». Проверка: если обозначения нет ни в одном файле проекта и ни в одном сообщении пользователя — его нет вовсе.

**Rule:** Hook-уровень: `~/.claude/hooks/explanation-terms.sh` (Stop hook) сканирует последний assistant message на латинские слова через дефис (`index-time`) и одиночные латинские слова в обратных кавычках; слова с `_`, цифрами, `/` и camelCase-имена считает идентификаторами. Если слова нет ни в tool result / user message сессии, ни в файлах инструкций, ни в файлах git-репозитория, хук НЕ блокирует ответ, а требует по одной строке на слово: `Поправка к термину: «X» → «Y»` или `«X» — <где встречается>, замены нет`. Ответ при этом не повторять и не переписывать — пользователь его уже прочитал. Ловит сконструированные термины, но НЕ ловит русский жаргон («прогон») — тот остаётся на дисциплине.

**Разобранные примеры** применения принципа — `~/.claude/CLAUDE-APPENDIX.md` → "Explanation Protocol — разобранные примеры".

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

## Pre-commit Policy

**Rule:** Pre-commit hooks (ruff/lint/format/grace-lint/XML auto-regen/etc.) are **load-bearing quality gates** in dev-projects. They MUST run on every commit.

**Rule:** Do NOT bypass hooks (`git commit --no-verify`, `--no-gpg-sign`, environment overrides like `SKIP=...`, `PRE_COMMIT_ALLOW_NO_CONFIG=1`) unless the user explicitly requests it for this commit. Hook failure → fix the underlying issue, do not skip.

**Rule:** Slow checks (full pytest, integration, e2e) belong in CI/Makefile targets, not in commit-time hooks.

**Rule (verification):** Never use `diff` to confirm a gate, a render, or file parity — the RTK hook rewrites it and `rtk diff` may report differing files as identical while always exiting 0. Use `cmp` or `rtk proxy diff` (see "RTK — Rust Token Killer" below).

**Rule:** How new and adopted repos get the bootstrap hook: `~/.claude/CLAUDE-APPENDIX.md` → "Pre-commit — template mechanics".

## Git Push Policy

**Rule:** Do NOT run `git push` of code automatically. Only on explicit user request.

**Rule:** Do NOT default to opening a GitHub PR (`gh pr create`) to land a finished branch —
including in autonomous/background sessions where a "ship it" default might otherwise apply.
Instead, PROPOSE this sequence and wait for confirmation: 1) commit any remaining uncommitted
files on the branch; 2) merge the branch into `master` locally; 3) delete the branch (local,
and remote if it was pushed); 4) only then `git push` (still subject to the rule above —
explicit request required). Orchestrators with their own documented merge-queue contract
(e.g. `do-multiagent`'s controller) already follow this local-merge-then-delete shape
natively — this rule removes the PR step from the assistant's own default, not from theirs.

**Rule:** `bd dolt push` (Beads persistence for multi-machine sync) IS allowed automatically as part of session close protocol.

**Rule (delivery to machines, owner decision 2026-10-07, every repository):** everything that is tracked in git reaches a server only through GitHub — `git push` here, `git pull --ff-only` there; never copy tracked files with `rsync`, `scp` or a hand copy. `rsync` is allowed in every repository **only for git-ignored artifacts** (data archives, model weights, exports); check with `git check-ignore` first. Generated pages that a server serves (e.g. the static sites behind the Isuzu portal's Caddy) are kept in git, not delivered by `rsync`.

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

**Rule:** Honest limits of the read-side gate (what `deny` and the Bash sandbox do and do not block): `~/.claude/CLAUDE-APPENDIX.md` → "Security — scope of the read-side gate".

## Tooling Preferences

**Rule:** When a matching skill exists — use it. Skills take priority over manual task execution.

**Rule:** Use MCP servers for integrations: GitHub, Docker, browsers (playwright/chrome-devtools), documentation (context7). Reasoning (sequential-thinking) only when a skill or the user asks for it: each of its steps is one more request over the whole session context.

**Rule:** Use parallel subagents/agent teams for independent/parallelizable tasks (Claude: `teammateMode` + agent-teams flag; Codex: `[features] multi_agent` + `/agent`).

## Model Routing — Four Token Pools (cost discipline)

**Rule:** The Anthropic quota is the scarce pool: spend it on judgement — architecture, `/best-*` analysis, instruction design, subtle debugging, and verification of every other pool's output. Bulk reading, inventories, web research, mechanical edits and drafts from a finished spec go to other pools: Z.ai GLM, the local gateway (queued work nobody waits on — it is slow), Codex (second independent voice).

**Rule:** Delegate to another pool by role, not by a hand-built command: `~/.claude/scripts/model-run.sh --role <planner|executor|researcher|reviewer|batch> --task <file> --out <file>`, called by path as its own Bash command (only that form matches `sandbox.excludedCommands`). The Agent tool reaches Anthropic models only.

**Rule:** Model names, efforts, timeouts, fallback order, tier and work-type mappings live only in `~/.claude/model-registry.json` (`roles`, `tiers`, `agent_work_types`) — never restate them. Journal: `~/.claude/scripts/model-stats.py`; spend per skill: `~/.claude/scripts/skill-stats.py`.

**Rule:** Delegation does NOT relax Trust = 0 %: run the validator/tests yourself on whatever another pool produced. Full text (`claude-glm` tier remapping, pool limits, orchestrator choice): `~/.claude/CLAUDE-APPENDIX.md` → "Model Routing — full text".

## Preferences

**Rule:** Code principles (KISS, YAGNI, SSoT/DRY, SOTA first, then the rest of the 17) are defined only in `~/.claude/skills/_code-quality/principles.md`. Read it before planning, writing or reviewing code and run its excess-code check on every plan and diff; never restate a principle in another file. `~/.claude/hooks/principles-inject.sh` injects it into code-related skills. Its SSoT principle covers instructions and documents too, not only code.

**Rule:** Do NOT create unnecessary files, folders, or structures outside of what `do-feature` explicitly requires for dev-projects.

**Rule:** No half-finished implementations.

**Rule:** Prefer editing existing files over creating new ones.

**Rule:** Match scope to request — don't bundle refactor with bug fix.

**Rule:** Evidence before assertions — verify before claiming work complete (run tests, check output, don't assume).

**Rule:** When delegating to subagents that produce artifacts (files, commits, configs) — subagent's textual summary is **never** sufficient evidence of correctness. Before reporting work as done, the parent agent MUST run at least one **objective check** that does not depend on the subagent's claims:
- Code changes → `git diff` + run actual validator (linter, tests, schema check)
- Config files → parse with the real tool that consumes them
- Docs/XML → run the project's lint/validate command, not eyeball the diff

If the subagent claims "X passes" — run X yourself. Trust = 0%.

**Rule:** After **bulk auto-edits** (scripts that touch many files in one shot — codemods, header inserters, sed/regex passes, generated migrations) run the **full project quality gate** before declaring done, not only the check you were fixing. Minimum: `make lint` (or equivalent: ruff/format/mypy/eslint), the project's domain validator (`grace lint`, schema check, etc.) AND tests.

**Rule:** Don't add "removed" comments for deleted code.

**Rule:** Prefer declarative (Pydantic schema, SQLAlchemy ORM, type hints) over imperative checks where language allows.

**Rule:** Root-cause over symptom — no destructive shortcuts (`--no-verify`, disabling checks) as "fix".

## User Adaptation

**Rule:** Read `{User}/CLAUDE.md` or `{User}/AGENTS.md` at session start — contains role, expertise level, preferred style, optional character persona.

**Rule:** Dev-projects — technical language, code-level terminology. Life-projects — simple language, no jargon, step-by-step.

**Rule:** Do NOT assume technical literacy unless profile explicitly states it (e.g. `role: software engineer`).

**Rule:** If profile declares communication style/character (e.g. `стиль общения: Sherlock Holmes`) — match tone accordingly while preserving accuracy.

**Rule:** Prefer user's preferred language (from profile or Language section) over auto-detection.

## Memory System Update

**Rule:** Keep instruction files (`CLAUDE.md` / `AGENTS.md`) in sync with project reality. Update at appropriate hierarchy level (global → user → project).

**Rule:** Priority: actual state > documentation. On conflict — update the documentation.

**Rule:** Use ephemeral memories (Codex: `codex memory add`, Claude: auto-memory system) for short-lived facts. Use instruction files for durable rules.

**Triggers to update:** new skill/plugin added, workflow changed, new project type, team/tooling change.

## Python Development (dev-projects)

- Python 3.11+, `uv` (or `pip`), Linux (Ubuntu). 4-space indents, type hints, code comments in English.
- Tests: `pytest`, TDD (RED → GREEN → REFACTOR) — no production code without a failing test.
- Docs: no `README.md` unless asked; document only non-obvious logic.
- Performance: no premature optimisation; profile before optimising.
- Dependencies: production pins only with `==` (never `>=`, `~=`, `^`); after adding or bumping one, check `uv.lock` matches exactly; no needless dependencies; update regularly for security; keep Docker images small.

## RTK — Rust Token Killer

Token-optimized CLI proxy (60-90% savings on dev operations). A Claude Code hook rewrites commands transparently (`git status` → `rtk git status`); Codex has no such hook.

```bash
rtk gain              # Show token savings analytics
rtk gain --history    # Show command usage history with savings
rtk discover          # Analyze Claude Code history for missed opportunities
rtk proxy <cmd>       # Execute raw command without filtering (for debugging)
rtk --version         # Should show: rtk X.Y.Z; `which rtk` verifies the binary
```

⚠️ **Name collision**: if `rtk gain` fails, you may have reachingforthejack/rtk (Rust Type Kit) installed instead.

### `rtk diff` — implementation trait (NOT a bug)

`rtk diff` is a token-optimized condenser, not a verification tool — by design:
- it MAY report "Files are identical" for files that do differ (observed on a 1-line JSON change)
- it ALWAYS exits 0, even when differences are printed

Since the hook rewrites `diff` → `rtk diff`, plain `diff` inherits both traits.
**Never use `diff` as a verification gate.** For byte-exact comparison use `cmp file_a file_b` (exit 1 on difference, not rewritten) or `rtk proxy diff a b` (native diff, unfiltered).

### `rtk find` — excluded from rewriting (false empty results)

`rtk find` skips files that `.gitignore` hides and directories listed in rtk's
`[filters].ignore_dirs` (`.venv`, `node_modules`, `target`, `vendor`, ...), and it
still **exits 0** — so "nothing found" may be false. Verified 2026-09-24 (rtk 0.35.0):
in a repo with `a/` in `.gitignore`, `rtk find . -name '*syn*'` listed 1 of 2 files;
`rtk find . -name pyvenv.cfg` answered `0 for 'pyvenv.cfg'` next to an existing
`.venv/pyvenv.cfg`. In Sinayara-Isuzu this produced a wrong "snapshot never downloaded"
conclusion (bd `python-ai-skills-abh`).

**Fix in place:** `find` is listed in `[hooks] exclude_commands` of
`claude-home/rtk/config.toml` (linked to `~/.config/rtk/config.toml` by
`make install-symlinks`), so the hook leaves `find` native. Rules:

- An empty result from `rtk find` (typed explicitly) is **not** evidence of absence.
- Plain `find` is native again; `rtk proxy find ...` is equivalent.

Checked and **not** affected on the same fixture: `rtk grep` (lists gitignored and
`.venv` matches), `rtk ls`, `rtk read` (`cat`), `rtk wc`. `rtk tree` hides dot-dirs
such as `.venv` exactly like native `tree` without `-a`.

### `git` — excluded from rewriting (sandbox exclusion)

`sandbox.excludedCommands` lists `git *`, so a plain `git ...` call runs outside the
Bash sandbox — where it can read GitHub credentials and does not see sandbox mount
points (`.bashrc`, `.mcp.json`, `.claude/skills`, ...) as untracked files. The harness
matches that list against the command text it runs, so a rewritten `rtk git ...` would
stay inside the sandbox. `git` is therefore in `[hooks] exclude_commands` of
`claude-home/rtk/config.toml`. Verified 2026-10-13: rewritten `git status` listed 20
phantom paths; after the exclusion it listed none, and `git fetch` reached GitHub
(bd `python-ai-skills-6wj`). This also removes the earlier conflict in worktree-isolated
sessions, where the harness refused `rtk git ...` outright.

Calls that still run sandboxed even with the exclusion (sandboxing docs, `excludedCommands`):
a pipe or chain with any non-git command (`git log | head`, `git add x && git commit`),
a `cd` or `git -C <dir>` (verified 2026-10-13), a redirect to a file, `$(...)`, and an absolute path such as `/usr/bin/git`.
Run git as a standalone call; never stage untracked paths that only such a call shows.
