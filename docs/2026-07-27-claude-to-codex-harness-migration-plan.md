# План миграции Claude Code CLI harness → Codex CLI harness

## 1. Контекст

Цель — перенести Claude Code harness в нативные механизмы Codex CLI без запуска Claude-модели.

Архитектура использует функциональное соответствие, поскольку форматы конфигурации и события двух harness различаются.

Claude harness остаётся неизменённым резервом до полной приёмки Codex.

Технологии миграции: Bash, TOML, JSON, Markdown, symlinks, Beads и нативные Codex interfaces.

Основная модель исполнения — `gpt-5.6-sol` с `high`; проектирование и аудит используют `xhigh`.

## 2. Содержание

1. Фиксация исходного состояния и отката
2. Контракт функционального паритета
3. Иерархия инструкций и SSoT
4. Конфигурация, безопасность, подписка и модель
5. Миграция hooks
6. Миграция MCP
7. Миграция skills, workflows и plugins
8. Миграция agents, памяти и сессий
9. Инсталлятор, symlinks и синхронизация
10. Проверка, переключение и откат

## 3. Краткая версия плана

### Этап 1: Фиксация исходного состояния и отката

- **Проблема** — Claude и Codex уже расходятся, а один hook содержит пользовательские изменения.
- **Действие** — Инвентаризировать `~/.claude`, `~/.codex`, `.claude`, `.codex`, symlinks и Git-состояние.
- **Результат** — Получаем проверенную исходную точку и отдельную резервную копию конфигурации.
- **Зависимости** — Этап не имеет зависимостей.
- **Риски** — Резервная копия может захватить credentials. Секретные файлы полностью исключаются.
- **Без этого** — Нельзя отличить ошибку миграции от существующего дрейфа.

### Этап 2: Контракт функционального паритета

- **Проблема** — Требование «работать одинаково» нельзя проверить без измеримых критериев.
- **Действие** — Зафиксировать mapping Claude → Codex внутри отдельной задачи Beads.
- **Результат** — Каждый компонент получает статус: перенос, адаптация, замена или обоснованное исключение.
- **Зависимости** — Требуется завершённый этап 1.
- **Риски** — Буквальное копирование может перенести несовместимые Claude-механизмы.
- **Без этого** — Заявление о полной миграции останется субъективным.

### Этап 3: Иерархия инструкций и SSoT

- **Проблема** — Корневые `AGENTS.md` и `CLAUDE.md` различаются. Глобальный файл превышает стандартный лимит Codex.
- **Действие** — Объединить правила, добавить `project_type: dev` и увеличить `project_doc_max_bytes`.
- **Результат** — Claude и Codex получают одинаковые правила без обрезания контекста.
- **Зависимости** — Требуется mapping этапа 2.
- **Риски** — Дублирование с `developer_instructions` создаст конфликт приоритетов.
- **Без этого** — Codex будет молча игнорировать или обрезать часть правил.

### Этап 4: Конфигурация, безопасность, подписка и модель

- **Проблема** — Сейчас Codex использует `danger-full-access` и `approval_policy = "never"`.
- **Действие** — Перенести shared-настройки в `codex-home/config.toml.template` и включить безопасный режим.
- **Результат** — Codex работает через подписку ChatGPT, без Claude API и второго модельного расхода.
- **Зависимости** — Требуется согласованная иерархия инструкций этапа 3.
- **Риски** — Строгий sandbox может блокировать разрешённую настройку `~/.codex`.
- **Без этого** — Остаётся риск внешней записи, утечки и неконтролируемых действий.

### Этап 5: Миграция hooks

- **Проблема** — Codex не выполняет большинство защитных Claude hooks.
- **Действие** — Адаптировать hooks в `codex-home/hooks.json` и сохранить Beads hooks в `.codex/hooks.json`.
- **Результат** — Возвращаются блокировки, XML-регенерация, RTK и anti-hallucination.
- **Зависимости** — Требуются этапы 3 и 4.
- **Риски** — Глобальные и проектные hooks могут запускаться дважды.
- **Без этого** — Критичные правила останутся только текстовыми рекомендациями.

### Этап 6: Миграция MCP

- **Проблема** — Конфигурация и авторизация MCP отличаются между harness.
- **Действие** — Проверить Context7, Sequential Thinking и GitHub через `codex mcp list`.
- **Результат** — Codex получает нужные интеграции без копирования credentials.
- **Зависимости** — Требуется безопасная конфигурация этапа 4.
- **Риски** — Возможны дублирование GitHub MCP и утечка параметров авторизации.
- **Без этого** — Документация, reasoning и GitHub будут работать иначе.

### Этап 7: Миграция skills, workflows и plugins

- **Проблема** — Codex не видит часть Claude skills и использует другой orchestrator.
- **Действие** — Перенести совместимые skills symlinks, адаптировать metadata и преобразовать `commands/pipeline.md`.
- **Результат** — Codex получает одинаковые явные команды и правила автоматического выбора skills.
- **Зависимости** — Требуются этапы 2 и 3.
- **Риски** — Дублирующиеся названия могут запускать разные orchestrator skills.
- **Без этого** — Codex будет выполнять тот же запрос по другому workflow.

### Этап 8: Миграция agents, памяти и сессий

- **Проблема** — В Claude есть шесть agents, а Codex-варианты отсутствуют.
- **Действие** — Преобразовать `agents/*.md` в `codex-home/agents/*.toml`.
- **Результат** — Codex получает аналогичные роли, ограничения и способы делегирования.
- **Зависимости** — Требуются этапы 3, 4 и 7.
- **Риски** — Массовый перенос Claude memories принесёт устаревший контекст.
- **Без этого** — Multi-agent workflows останутся неполными.

### Этап 9: Инсталлятор, symlinks и синхронизация

- **Проблема** — Текущий инсталлятор обслуживает только Claude Code.
- **Действие** — Добавить `scripts/install-codex-symlinks.sh` и новые цели в `Makefile`.
- **Результат** — Harness воспроизводимо устанавливается на новой машине.
- **Зависимости** — Требуется завершение этапов 3–8.
- **Риски** — Инсталлятор может перезаписать `[projects]` и `[hooks.state]`.
- **Без этого** — Ручная установка снова создаст дрейф.

### Этап 10: Проверка, переключение и откат

- **Проблема** — Корректный JSON или TOML не доказывает одинаковое поведение.
- **Действие** — Проверить безопасность, hooks, skills, agents, MCP и session lifecycle.
- **Результат** — Codex становится главным harness только после полной приёмки.
- **Зависимости** — Требуются все предыдущие этапы.
- **Риски** — Небезопасный тест может сам создать побочный эффект.
- **Без этого** — Возможен ложный успех при скрытых функциональных разрывах.

## 4. Полная версия плана

## Этап 1: Фиксация исходного состояния и отката

### Цель этапа

Сохранить проверяемую исходную точку без изменения текущего harness.

### Файлы и каталоги

- Прочитать: `~/.claude/CLAUDE.md`
- Прочитать: `~/.claude/AGENTS.md`
- Прочитать: `~/.claude/settings.json`
- Прочитать: `~/.claude/settings.local.json`
- Прочитать: `~/.codex/AGENTS.md`
- Прочитать: `~/.codex/config.toml`
- Прочитать: `~/.codex/hooks.json`
- Прочитать: `.claude/settings.json`
- Прочитать: `.codex/config.toml`
- Прочитать: `.codex/hooks.json`
- Прочитать: `AGENTS.md`
- Прочитать: `CLAUDE.md`
- Сохранить backup: `~/.codex/backups/2026-07-27-before-harness-migration/`

### Подтверждённая исходная точка

- Claude Code CLI: `2.1.198`.
- Codex CLI: `0.145.0`.
- Ветка `main` опережает `origin/main` на два коммита.
- `claude-home/hooks/regen-xml-on-spec-edit.sh` уже изменён пользователем.
- Этот diff нельзя перезаписывать или восстанавливать из Git.

### Шаги

- [ ] **Шаг 1.1. Создать отдельную Beads-задачу миграции**

  Эта задача не использует `do-feature`.

  Причина: переносится harness, а не программная функция.

- [ ] **Шаг 1.2. Зафиксировать версии CLI**

  ```bash
  claude --version
  codex --version
  ```

  Ожидается вывод установленных версий без запуска моделей.

- [ ] **Шаг 1.3. Зафиксировать Git-состояние**

  ```bash
  git status --short --branch
  git diff -- claude-home/hooks/regen-xml-on-spec-edit.sh
  ```

  Ожидается сохранение существующего пользовательского diff.

- [ ] **Шаг 1.4. Снять inventory symlinks**

  ```bash
  find ~/.claude ~/.codex -maxdepth 3 -type l -print
  readlink -f ~/.claude/CLAUDE.md ~/.claude/AGENTS.md ~/.codex/AGENTS.md
  ```

  Ожидается подтверждение общего глобального SSoT.

- [ ] **Шаг 1.5. Создать безопасный backup**

  Backup включает только конфигурацию, hooks, rules, agents и symlink metadata.

  Полностью исключить:

  - `.env*`;
  - credentials;
  - private keys;
  - auth databases;
  - session transcripts;
  - Claude memory contents.

- [ ] **Шаг 1.6. Проверить восстановимость**

  Сравнить список backup-файлов с inventory.

  Не выполнять фактическое восстановление.

### Gate этапа

- Все исходные компоненты перечислены.
- Текущий Git diff сохранён.
- Backup не содержит запрещённых файлов.
- Команды не запускали Claude-модель.

### Коммит

На этом этапе код и tracked-файлы не изменяются.

Коммит не требуется.

## Этап 2: Контракт функционального паритета

### Цель этапа

Превратить требование «работать одинаково» в измеримый acceptance contract.

### Артефакт

Mapping хранится в Beads-задаче миграции.

Отдельный markdown backlog не создаётся.

### Определение 100% паритета

Каждый активный Claude-компонент должен иметь:

- нативный Codex-эквивалент;
- адаптер;
- функциональную замену;
- обоснованное исключение.

Идентичные ответы моделей не входят в критерий.

Claude и Codex используют разные модели и runtime.

### Шаги

- [ ] **Шаг 2.1. Создать перечень зон**

  Обязательные зоны:

  - глобальные инструкции;
  - проектные инструкции;
  - permissions;
  - sandbox;
  - hooks;
  - MCP;
  - skills;
  - workflows;
  - slash-команды;
  - plugins;
  - subagents;
  - memories;
  - session lifecycle;
  - symlinks;
  - модель;
  - reasoning effort;
  - авторизация;
  - multi-machine consistency.

- [ ] **Шаг 2.2. Классифицировать каждый компонент**

  Допустимые статусы:

  - `direct`;
  - `adapt`;
  - `replace`;
  - `exclude`.

- [ ] **Шаг 2.3. Добавить проверку к каждому компоненту**

  Каждая строка mapping должна содержать:

  - Claude source;
  - Codex target;
  - способ переноса;
  - риск;
  - verification command;
  - rollback action;
  - текущий статус.

- [ ] **Шаг 2.4. Зафиксировать порядок приоритетов**

  При конфликте использовать порядок:

  1. Безопасность.
  2. Пользовательские инструкции.
  3. Project SSoT.
  4. Hook enforcement.
  5. Workflow parity.
  6. Удобство.

- [ ] **Шаг 2.5. Проверить исключения**

  Отключённый Claude plugin можно исключить.

  Исключение должно сохранять его неактивное состояние.

### Gate этапа

- Нет активных элементов со статусом `unmapped`.
- Каждому критичному правилу соответствует проверка.
- Secrets и memories не входят в автоматический перенос.
- Отключённые plugins явно отмечены.

### Коммит

Mapping хранится в Beads.

Tracked-файлы не изменяются.

## Этап 3: Иерархия инструкций и SSoT

### Цель этапа

Создать общую иерархию правил без дублирования и обрезания контекста.

### Файлы

- Изменить: `AGENTS.md`
- Заменить symlink: `CLAUDE.md`
- Изменить: `claude-home/CLAUDE.md`
- Изменить: `.codex/config.toml`
- Позднее обновить: `codex-home/config.toml.template`

### Целевая иерархия

Глобальный SSoT:

```text
~/.claude/CLAUDE.md -> repository/claude-home/CLAUDE.md
~/.claude/AGENTS.md -> ~/.claude/CLAUDE.md
~/.codex/AGENTS.md  -> ~/.claude/CLAUDE.md
```

Проектный SSoT:

```text
repository/AGENTS.md
repository/CLAUDE.md -> repository/AGENTS.md
```

### Шаги

- [ ] **Шаг 3.1. Сравнить проектные инструкции**

  ```bash
  diff -u AGENTS.md CLAUDE.md
  ```

  Ожидается подтверждение текущего дрейфа.

- [ ] **Шаг 3.2. Объединить уникальные правила**

  `AGENTS.md` становится проектным SSoT.

  Управляемые Beads-маркеры сохраняются.

- [ ] **Шаг 3.3. Добавить тип проекта**

  Добавить в начало project metadata:

  ```yaml
  project_type: dev
  ```

- [ ] **Шаг 3.4. Удалить дублирующиеся Beads-блоки**

  Сохранить один актуальный managed block.

  Не изменять его внутренние markers вручную.

- [ ] **Шаг 3.5. Связать Claude project file**

  Заменить `CLAUDE.md` symlink на `AGENTS.md`.

  Перед заменой сохранить содержимое через Git.

- [ ] **Шаг 3.6. Увеличить лимит инструкций**

  Глобальный файл уже содержит `35 789` байт.

  Установить:

  ```toml
  project_doc_max_bytes = 65536
  ```

- [ ] **Шаг 3.7. Дедуплицировать `developer_instructions`**

  В Codex-specific слое оставить:

  - имена нативных инструментов;
  - особенности approvals;
  - особенности hooks;
  - правила Codex agents;
  - особенности plugin discovery.

  Общие правила остаются в `claude-home/CLAUDE.md`.

- [ ] **Шаг 3.8. Устранить зависимость от `@RTK.md`**

  Обязательные RTK-правила перенести в глобальный SSoT.

  Подробную tool-specific механику оставить в отдельном Codex skill.

- [ ] **Шаг 3.9. Проверить загрузку инструкций**

  Запустить Codex:

  - из корня;
  - из вложенной папки;
  - после resume;
  - после compact.

  Codex должен одинаково определять язык, безопасность и project type.

### Gate этапа

- `AGENTS.md` является единственным project SSoT.
- `CLAUDE.md` указывает на `AGENTS.md`.
- `project_type: dev` присутствует.
- Codex не обрезает глобальные инструкции.
- Общие правила отсутствуют в `developer_instructions`.

### Коммит

```bash
git add AGENTS.md CLAUDE.md claude-home/CLAUDE.md .codex/config.toml
git commit -m "docs(harness): unify Claude and Codex instructions"
```

Git push не выполнять.

## Этап 4: Конфигурация, безопасность, подписка и модель

### Цель этапа

Заменить опасный Codex runtime безопасной конфигурацией с подписочной авторизацией.

### Файлы

- Создать: `codex-home/config.toml.template`
- Изменить: `.codex/config.toml`
- Позднее обновить: `~/.codex/config.toml`
- Создать: `codex-home/rules/default.rules`

### Целевая основа

```toml
model = "gpt-5.6-sol"
model_reasoning_effort = "high"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
project_doc_max_bytes = 65536
```

### Защитные слои

1. Sandbox ограничивает запись текущим проектом.
2. Approvals защищают внешние изменения.
3. PreToolUse hook блокирует запрещённые пути и команды.
4. Command rules обеспечивают дополнительную защиту.

Command rules не являются единственным enforcement-слоем.

### Шаги

- [ ] **Шаг 4.1. Создать shared template**

  Перенести только общие значения.

  Не переносить machine-specific project trust.

- [ ] **Шаг 4.2. Сначала применить project override**

  Безопасные значения сначала проверяются в `.codex/config.toml`.

  Глобальный `~/.codex/config.toml` пока не изменяется.

- [ ] **Шаг 4.3. Настроить sandbox**

  Разрешить запись внутри текущего проекта.

  Внешняя запись должна требовать отдельного approval.

- [ ] **Шаг 4.4. Настроить approvals**

  Запрещено использовать `approval_policy = "never"`.

  Запрещено оставлять `danger-full-access` постоянным режимом.

- [ ] **Шаг 4.5. Добавить command rules**

  Правила должны:

  - блокировать bypass проверок;
  - запрашивать approval перед Git push;
  - блокировать широкие destructive-команды;
  - блокировать удалённые модификации.

- [ ] **Шаг 4.6. Не использовать Beta permission profiles**

  Они не входят в первый production cutover.

  Их исследование выполняется отдельной задачей.

- [ ] **Шаг 4.7. Проверить подписочную авторизацию**

  Codex должен использовать ChatGPT subscription.

  API-биллинг не используется.

  Claude CLI и Claude API не запускаются.

- [ ] **Шаг 4.8. Провести строгую проверку**

  ```bash
  codex --strict-config
  codex doctor --json
  codex features list
  ```

  Ожидается корректная конфигурация без критичных ошибок.

### Gate этапа

- `workspace-write` активен.
- `on-request` активен.
- Подписочная авторизация подтверждена.
- Claude runtime не вызывается.
- `codex --strict-config` проходит.
- `codex doctor --json` не раскрывает credentials.

### Коммит

```bash
git add .codex/config.toml codex-home/config.toml.template codex-home/rules/default.rules
git commit -m "chore(harness): add safe Codex configuration"
```

Git push не выполнять.

## Этап 5: Миграция hooks

### Цель этапа

Восстановить защитное и workflow-поведение Claude через Codex command hooks.

### Файлы

- Создать: `codex-home/hooks.json`
- Изменить: `.codex/hooks.json`
- Адаптировать: `claude-home/hooks/block-no-verify.sh`
- Адаптировать: `claude-home/hooks/rtk-rewrite.sh`
- Повторно использовать: `claude-home/hooks/rtk-announce.sh`
- Адаптировать: `claude-home/hooks/regen-xml-on-spec-edit.sh`
- Адаптировать: `claude-home/hooks/anti-hallucination.sh`
- Добавить shared guard: `claude-home/hooks/local-only-guard.sh`

### Разделение ответственности

`codex-home/hooks.json` отвечает за:

- безопасность;
- RTK;
- XML;
- anti-hallucination;
- общие напоминания.

`.codex/hooks.json` отвечает за:

- Beads SessionStart;
- Beads PreCompact;
- Beads PostCompact;
- project lifecycle.

### Шаги

- [ ] **Шаг 5.1. Зафиксировать Codex hook payload**

  Получить payload через безопасный diagnostic command hook.

  Не использовать payload из другого проекта как спецификацию.

- [ ] **Шаг 5.2. Сопоставить события**

  Требуемый mapping:

  - `SessionStart`;
  - `PreCompact`;
  - `PreToolUse`;
  - `PostToolUse`;
  - `Stop`;
  - `UserPromptSubmit`.

- [ ] **Шаг 5.3. Определить одного владельца Beads events**

  Project hook выполняет Beads lifecycle.

  Global hook не должен повторно запускать `bd prime`.

- [ ] **Шаг 5.4. Адаптировать PreToolUse**

  PreToolUse должен:

  - блокировать `--no-verify`;
  - выполнять RTK rewrite;
  - показывать RTK announcement;
  - блокировать запрещённые paths;
  - блокировать удалённые изменения;
  - напоминать о verifier checks;
  - напоминать о XML first-contact.

- [ ] **Шаг 5.5. Адаптировать PostToolUse**

  XML regeneration запускается только для подходящих spec-файлов.

  Существующий пользовательский diff сохраняется.

- [ ] **Шаг 5.6. Адаптировать Stop**

  Anti-hallucination должен проверять Codex response payload.

  Hook не должен читать секреты или логировать session IDs.

- [ ] **Шаг 5.7. Проверить JSON**

  ```bash
  jq -e empty codex-home/hooks.json .codex/hooks.json
  ```

  Ожидается exit code `0`.

- [ ] **Шаг 5.8. Подтвердить trust**

  Проверить hooks через `/hooks`.

  Доверять только ожидаемым hash.

- [ ] **Шаг 5.9. Проверить однократный запуск**

  Каждый event должен создать ровно одну безопасную diagnostic-запись.

  Diagnostic output не должен содержать sensitive payload.

### Gate этапа

- Все обязательные events покрыты.
- Каждый hook запускается один раз.
- Блокировка не создаёт побочных эффектов.
- XML regeneration работает.
- Anti-hallucination работает на синтетическом сообщении.
- Existing user diff сохранён.

### Коммит

```bash
git add codex-home/hooks.json .codex/hooks.json claude-home/hooks
git commit -m "feat(harness): port Claude hooks to Codex"
```

Git push не выполнять.

## Этап 6: Миграция MCP

### Цель этапа

Сохранить необходимые интеграции без копирования credentials и дублирования серверов.

### Подтверждённый Codex-набор

- Context7.
- Sequential Thinking.
- GitHub через официальный plugin.

Явная project-level Claude MCP-конфигурация не обнаружена.

### Шаги

- [ ] **Шаг 6.1. Зафиксировать текущий список**

  ```bash
  codex mcp list
  codex plugin list
  ```

- [ ] **Шаг 6.2. Проверить Context7**

  Выполнить публичный documentation lookup.

  Проверка не должна изменять внешнее состояние.

- [ ] **Шаг 6.3. Проверить Sequential Thinking**

  Выполнить локальную reasoning-задачу.

  Внешние integrations не используются.

- [ ] **Шаг 6.4. Проверить GitHub**

  Прочитать metadata доступного репозитория.

  Issues, pull requests и branches не изменяются.

- [ ] **Шаг 6.5. Удалить дублирование**

  GitHub plugin остаётся единственным GitHub transport.

  Дополнительный GitHub MCP не добавляется.

- [ ] **Шаг 6.6. Проверить авторизацию**

  Запрещено копировать:

  - credentials;
  - tokens;
  - auth caches;
  - session cookies;
  - secret environment values.

- [ ] **Шаг 6.7. Запустить диагностику**

  ```bash
  codex doctor --json
  ```

  Ожидается redacted output без критичных MCP-ошибок.

### Gate этапа

- Все обязательные MCP отвечают.
- GitHub integration не продублирована.
- Secret values отсутствуют в tracked-файлах.
- Claude runtime не участвует в MCP routing.

### Коммит

Если tracked MCP-конфигурация не менялась, коммит не требуется.

## Этап 7: Миграция skills, workflows и plugins

### Цель этапа

Сохранить Claude workflows через нативное Codex skill discovery.

### Файлы

- Создать: `pipeline/SKILL.md`
- Изменить или добавить: Codex-compatible metadata в переносимых skills
- Обновить: `claude-home/CLAUDE.md`
- Обновить: Codex skill symlinks

### Стратегии переноса

1. Прямой symlink для tool-neutral skill.
2. Codex adapter для Claude-specific metadata.
3. Нативная замена при существующем Codex skill.
4. Исключение только для неактивного компонента.

### Шаги

- [ ] **Шаг 7.1. Сравнить discovery directories**

  Проверить, какие user-scope paths реально использует Codex `0.145.0`.

  Не устанавливать один skill одновременно в несколько discovery paths.

- [ ] **Шаг 7.2. Сопоставить все skills**

  Для каждого skill зафиксировать:

  - shared content;
  - executable `lib/`;
  - Claude-only metadata;
  - Codex target;
  - trigger test.

- [ ] **Шаг 7.3. Разрешить конфликт orchestrators**

  Целевое решение:

  - установить `do-feature` в Codex;
  - сделать его единственным dev-orchestrator;
  - убрать напоминание про `feature-workflow`;
  - не запускать его для harness migration.

- [ ] **Шаг 7.4. Перенести обязательные workflows**

  Особое внимание:

  - `do-feature`;
  - `do-autopilot`;
  - `do-multiagent`;
  - `audit-loop`;
  - `beads-sync`;
  - `git-branch`;
  - `git-commit`;
  - `project-sync`;
  - `projects-sync`.

- [ ] **Шаг 7.5. Дедуплицировать `best-*`**

  Сравнить Claude-набор с Codex skill `best`.

  Оставить один SSoT для каждого поведения.

- [ ] **Шаг 7.6. Преобразовать `pipeline.md`**

  Source:

  ```text
  commands/pipeline.md
  ```

  Target:

  ```text
  pipeline/SKILL.md
  ```

  Проверить:

  - аргументы;
  - shell interpolation;
  - относительные paths;
  - approval gates;
  - явный запуск;
  - автоматический trigger.

- [ ] **Шаг 7.7. Сопоставить plugins**

  Целевое состояние:

  - Superpowers остаётся набором skills;
  - Beads остаётся project skill;
  - Template Bridge переносится выборочно;
  - GitHub plugin остаётся включённым;
  - отключённые Claude plugins не включаются автоматически.

- [ ] **Шаг 7.8. Проверить triggers**

  Каждый обязательный skill проверяется:

  - явным вызовом;
  - подходящим естественным запросом;
  - неподходящим запросом;
  - разрешением symlink;
  - загрузкой executable `lib/`.

### Gate этапа

- Все обязательные skills обнаруживаются.
- Один запрос не запускает два orchestrator skills.
- `pipeline` работает как Codex skill.
- Worker skills не переходят к другим workers самостоятельно.
- Plugins не дублируют MCP и skills.

### Коммит

```bash
git add pipeline claude-home/CLAUDE.md
git commit -m "feat(harness): align Codex skills and workflows"
```

Git push не выполнять.

## Этап 8: Миграция agents, памяти и сессий

### Цель этапа

Перенести шесть Claude roles без массового импорта устаревшей памяти.

### Файлы

- Создать: `codex-home/agents/do-feature-clean.toml`
- Создать: `codex-home/agents/py-doc-manager.toml`
- Создать: `codex-home/agents/py-quality.toml`
- Создать: `codex-home/agents/py-security.toml`
- Создать: `codex-home/agents/py-supervisor.toml`
- Создать: `codex-home/agents/py-test-writer.toml`

### Шаги

- [ ] **Шаг 8.1. Прочитать каждую Claude role**

  Sources:

  - `agents/do-feature-clean.md`;
  - `agents/py-doc-manager.md`;
  - `agents/py-quality.md`;
  - `agents/py-security.md`;
  - `agents/py-supervisor.md`;
  - `agents/py-test-writer.md`.

- [ ] **Шаг 8.2. Создать TOML agents**

  Каждый agent получает:

  - `name`;
  - `description`;
  - `developer_instructions`;
  - безопасный runtime;
  - чёткую область ответственности.

- [ ] **Шаг 8.3. Настроить границы записи**

  - Reviewers работают read-only.
  - Writers пишут только внутри проекта.
  - Security agent не читает secret paths.
  - Supervisor не изменяет файлы самостоятельно.
  - Agents не выполняют Git push.

- [ ] **Шаг 8.4. Сохранить модель наследуемой**

  Agents используют активную Codex-модель.

  Отдельная модель назначается только при доказанной необходимости.

- [ ] **Шаг 8.5. Не импортировать Claude memories**

  Распределить долговечную информацию:

  - правила → `AGENTS.md`;
  - task state → Beads;
  - transient facts → session context.

- [ ] **Шаг 8.6. Оставить Codex memories выключенными**

  Включение memories не входит в первый cutover.

  Это отдельное последующее решение.

- [ ] **Шаг 8.7. Проверить lifecycle**

  Проверить:

  - новую session;
  - resume;
  - fork;
  - compact;
  - возврат agent result;
  - отсутствие persistence transient context.

- [ ] **Шаг 8.8. Проверить шесть ролей**

  Каждой роли дать безопасную read-only задачу.

  Parent проверяет результат объективными командами.

### Gate этапа

- Все шесть agents доступны.
- Reviewers не могут записывать.
- Writers ограничены проектом.
- Claude memories не импортированы.
- Lifecycle не теряет Beads task state.

### Коммит

```bash
git add codex-home/agents
git commit -m "feat(harness): add Codex agent roles"
```

Git push не выполнять.

## Этап 9: Инсталлятор, symlinks и синхронизация

### Цель этапа

Сделать Codex harness воспроизводимым и безопасным для нескольких машин.

### Файлы

- Создать: `scripts/install-codex-symlinks.sh`
- Изменить: `Makefile`
- Использовать: `codex-home/config.toml.template`
- Использовать: `codex-home/hooks.json`
- Использовать: `codex-home/rules/default.rules`
- Использовать: `codex-home/agents/*.toml`

### Целевая структура

```text
codex-home/
├── config.toml.template
├── hooks.json
├── rules/
│   └── default.rules
└── agents/
    ├── do-feature-clean.toml
    ├── py-doc-manager.toml
    ├── py-quality.toml
    ├── py-security.toml
    ├── py-supervisor.toml
    └── py-test-writer.toml
```

### Шаги

- [ ] **Шаг 9.1. Создать idempotent installer**

  Скрипт должен:

  - показывать planned changes;
  - не перезаписывать неожиданные файлы;
  - создавать backup перед заменой;
  - устанавливать отдельные skill symlinks;
  - не заменять system skills;
  - валидировать каждую target;
  - не читать credentials.

- [ ] **Шаг 9.2. Добавить режим проверки**

  Предлагаемый флаг:

  ```bash
  scripts/install-codex-symlinks.sh --check
  ```

  Режим ничего не изменяет.

- [ ] **Шаг 9.3. Сохранить machine-local config**

  Инсталлятор не изменяет автоматически:

  - `[projects]`;
  - `[hooks.state]`;
  - local trust;
  - local MCP authorization;
  - session history.

- [ ] **Шаг 9.4. Добавить managed config block**

  Shared top-level settings обновляются между markers.

  Machine-local TOML sections остаются за пределами блока.

- [ ] **Шаг 9.5. Добавить Makefile targets**

  ```make
  install-codex-symlinks
  check-codex-harness
  ```

  Существующие Claude targets сохраняются.

- [ ] **Шаг 9.6. Проверить shell syntax**

  ```bash
  bash -n scripts/install-codex-symlinks.sh
  ```

  Ожидается exit code `0`.

- [ ] **Шаг 9.7. Проверить dry-run**

  ```bash
  scripts/install-codex-symlinks.sh --check
  ```

  Ожидается список изменений без filesystem mutation.

- [ ] **Шаг 9.8. Проверить фактическую установку**

  После отдельного approval:

  ```bash
  make install-codex-symlinks
  make check-codex-harness
  ```

- [ ] **Шаг 9.9. Сравнить машины**

  Shared-файлы должны совпадать.

  Authentication и trust state должны различаться.

### Gate этапа

- Installer идемпотентен.
- `--check` ничего не меняет.
- Неожиданные файлы не перезаписываются.
- Machine-local TOML sections сохранены.
- System skills не затронуты.

### Коммит

```bash
git add codex-home scripts/install-codex-symlinks.sh Makefile
git commit -m "build(harness): add Codex installation workflow"
```

Git push не выполнять.

## Этап 10: Проверка, переключение и откат

### Цель этапа

Доказать функциональный паритет до переключения основного harness.

### Синтаксические проверки

- [ ] **Шаг 10.1. Проверить JSON**

  ```bash
  jq -e empty codex-home/hooks.json .codex/hooks.json
  ```

- [ ] **Шаг 10.2. Проверить TOML**

  ```bash
  python3.11 -c 'import pathlib, tomllib; tomllib.loads(pathlib.Path("codex-home/config.toml.template").read_text())'
  ```

- [ ] **Шаг 10.3. Проверить Codex config**

  ```bash
  codex --strict-config
  codex doctor --json
  codex features list
  codex mcp list
  codex plugin list
  ```

- [ ] **Шаг 10.4. Проверить symlinks**

  ```bash
  find ~/.codex -maxdepth 3 -type l -print
  ```

### Поведенческие проверки

Использовать только Codex-модель.

Claude-модель для сравнения не запускать.

- [ ] **Шаг 10.5. Проверить instruction hierarchy**

  Проверить запуск:

  - из корня;
  - из вложенной папки;
  - после resume;
  - после compact.

- [ ] **Шаг 10.6. Проверить безопасность**

  Проверить:

  - разрешённое локальное чтение;
  - блокировку внешней записи;
  - блокировку несуществующего secret path;
  - блокировку `--no-verify`;
  - блокировку удалённой модификации.

  Реальные secret-файлы не создаются и не читаются.

- [ ] **Шаг 10.7. Проверить hooks**

  Проверить:

  - каждый event запускается один раз;
  - XML regeneration работает на fixture;
  - anti-hallucination блокирует synthetic violation;
  - blocking hook не создаёт side effects.

- [ ] **Шаг 10.8. Проверить skills**

  Проверить:

  - явный вызов `pipeline`;
  - естественный trigger `pipeline`;
  - отсутствие trigger на неподходящем запросе;
  - отсутствие `do-feature` для harness migration;
  - доступность `do-feature` для dev feature.

- [ ] **Шаг 10.9. Проверить agents**

  Проверить:

  - загрузку шести TOML-файлов;
  - read-only reviewers;
  - workspace-only writers;
  - supervisor result verification.

- [ ] **Шаг 10.10. Проверить MCP**

  Проверить:

  - Context7 public lookup;
  - Sequential Thinking local reasoning;
  - GitHub read-only metadata;
  - отсутствие duplicate GitHub server.

### Canary

- [ ] **Шаг 10.11. Выполнить read-only canary**

  Выполнить три read-only задачи в текущем проекте.

- [ ] **Шаг 10.12. Выполнить write canary**

  Создать временную папку внутри project root.

  Выполнить одну безопасную запись и удалить её после проверки.

- [ ] **Шаг 10.13. Выполнить blocking canary**

  Проверить одну внешнюю запись.

  Sandbox должен остановить операцию до side effect.

### Приёмочный gate

Cutover разрешён только при выполнении всех условий:

- нет critical `unmapped`;
- нет secret reads;
- нет unauthorized external writes;
- каждый hook запускается один раз;
- все обязательные skills обнаруживаются;
- все шесть agents загружаются;
- обязательные MCP отвечают;
- Claude runtime не запускается;
- используется ChatGPT subscription;
- `codex doctor --json` не сообщает критичных ошибок;
- существующий пользовательский diff сохранён.

### Финальный аудит

- [ ] **Шаг 10.14. Открыть новый read-only Codex-сеанс**

  Использовать:

  ```text
  model: gpt-5.6-sol
  reasoning: xhigh
  ```

  Аудитор получает:

  - mapping;
  - Git diff;
  - validator outputs;
  - canary results;
  - список исключений.

- [ ] **Шаг 10.15. Объективно проверить audit claims**

  Parent повторно запускает заявленные validators.

  Текстовый отчёт аудитора не считается доказательством.

### Cutover

- [ ] **Шаг 10.16. Установить global Codex symlinks**

  Использовать проверенный installer.

- [ ] **Шаг 10.17. Применить shared config**

  Machine-local sections должны сохраниться.

- [ ] **Шаг 10.18. Подтвердить hook trust**

  Использовать `/hooks`.

- [ ] **Шаг 10.19. Повторить короткий canary**

  Повторить read-only, write и blocking checks.

- [ ] **Шаг 10.20. Закрыть Beads-задачу**

  Задача закрывается только после успешного gate.

- [ ] **Шаг 10.21. Создать финальный commit**

  ```bash
  git add AGENTS.md CLAUDE.md .codex codex-home pipeline scripts Makefile claude-home
  git commit -m "feat(harness): migrate Claude workflow to Codex"
  ```

  Git push не выполнять.

### Rollback

При критичном нарушении:

1. Завершить текущую Codex session.
2. Восстановить предыдущий `config.toml`.
3. Восстановить предыдущие hooks и symlinks.
4. Запустить `codex --strict-config`.
5. Запустить `codex doctor --json`.
6. Вернуться к неизменённому Claude harness.
7. Зафиксировать причину в Beads.
8. Не продолжать cutover до исправления.

Claude harness не удаляется после миграции.

Его удаление требует отдельного решения пользователя.

### Рекомендация по модели

Основная модель:

```text
gpt-5.6-sol
reasoning: high
```

Для проектирования безопасности:

```text
gpt-5.6-sol
reasoning: xhigh
```

Для финального независимого аудита:

```text
gpt-5.6-sol
reasoning: xhigh
```

`ultra` не рекомендуется.

Он автоматически использует subagents и быстрее расходует лимит.

`gpt-5.6-terra` допустима только для механических преобразований после утверждённого mapping.

Для первой миграции проще использовать одну Sol-модель.

### Официальные источники

- [Codex models](https://learn.chatgpt.com/docs/models)
- [Codex pricing](https://learn.chatgpt.com/docs/pricing)
- [Codex configuration](https://learn.chatgpt.com/docs/config-file/config-basic)
- [Codex security](https://learn.chatgpt.com/docs/agent-approvals-security)
- [Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Codex hooks](https://learn.chatgpt.com/docs/hooks)
- [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp)
- [Codex skills](https://learn.chatgpt.com/docs/build-skills)
- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
