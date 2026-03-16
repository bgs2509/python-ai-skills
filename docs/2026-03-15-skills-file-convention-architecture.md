# Вариант C: Файловая конвенция SKILL.md + reference.md

**Дата:** 2026-03-15
**Контекст:** Выбор архитектуры для переиспользования стандартов python-ai-skills в 10-20+ проектах через Claude Code Skills.
**Статус:** РЕАЛИЗОВАНО 2026-03-16 (15 skill'ов, 26 reference-файлов, symlinks в ~/.claude/skills/, гибридные триггеры).

## Суть подхода

Репозиторий `python-ai-skills` — это **коллекция skill'ов**. Каждая директория в нём — готовый skill с конвенцией: `SKILL.md` содержит краткую версию (L0+L1), `reference.md` — полную (L2). Claude загружает `SKILL.md` при вызове, а `reference.md` читает через инструмент `Read` **только когда нужны детали**. Никакого дополнительного кода, серверов или зависимостей.

```
~/python-ai-skills/                    # Git-репо = коллекция skill'ов (15 skill'ов)
├── quality-cascade/
│   ├── SKILL.md                       # Краткие принципы (~50 строк, context: fork)
│   └── reference/                     # Несколько reference-файлов
│       ├── quality-cascade.md
│       ├── code-standards.md
│       └── naming.md
├── error-handling/
│   ├── SKILL.md
│   └── reference.md                   # Один reference-файл
└── ...

~/.claude/skills/                      # Symlinks → python-ai-skills (15 шт.)
├── quality-cascade → ~/python-ai-skills/quality-cascade
├── error-handling → ~/python-ai-skills/error-handling
└── ...
```

---

## Как работает загрузка (3 фазы)

### Фаза 1: Метаданные (старт сессии)

При начале сессии Claude загружает **только `name` и `description`** каждого skill'а.

- Стоимость: ~100 токенов на skill
- 15 skill'ов (реализовано) = ~1,500 токенов (пренебрежимо)
- 50 skill'ов = ~5,000 токенов (всё ещё мало)
- Бюджет: 2% контекстного окна (можно переопределить через `SLASH_COMMAND_TOOL_CHAR_BUDGET`)

Claude видит **что доступно**, но не загружает содержимое.

**Источник:** [Skills — Where skills live](https://code.claude.com/docs/en/skills.md#where-skills-live)

### Фаза 2: SKILL.md (при вызове)

Когда skill вызван (вручную `/quality-review` или автоматически по description), Claude читает полный `SKILL.md` с диска.

- Стоимость: 300-5,000 токенов (зависит от размера)
- Рекомендация: до 500 строк
- Перечитывается каждый раз (нет кеша между вызовами)
- Изменения в файле видны мгновенно (live reload)

### Фаза 3: Поддерживающие файлы (по требованию)

Если `SKILL.md` ссылается на `reference.md`, Claude читает его через `Read` **только если задача требует деталей**.

- Стоимость: 0 токенов пока не прочитан
- Claude решает сам — нужен ли reference.md для текущей задачи
- Файл читается через Read tool, **не дублируется** в каждом сообщении контекста (в отличие от MCP-ответов)

**Это ключевое преимущество Варианта C:** reference.md прочитан через Read = одноразовая загрузка. MCP-ответ = включается в историю и пересылается в каждом сообщении.

**Источник:** [Skills — Add supporting files](https://code.claude.com/docs/en/skills.md#add-supporting-files)

---

## Структура skill'а

### Минимальный пример

```yaml
# ~/python-ai-skills/quality-cascade/SKILL.md
---
name: quality-cascade
description: 17 принципов качества Python-кода. Используй при ревью, рефакторинге и написании нового кода.
---

## Принципы (краткая версия)

1. **DRY** — нет дублирования логики
2. **SRP** — один класс/функция = одна ответственность
3. **LoD** — не лезь в чужие внутренности (a.b.c.d — плохо)
4. **KISS** — простое решение лучше сложного
5. **Fail Fast** — валидация на входе, guard clauses
...

**Красные флаги:** except pass, god class >300 строк, magic numbers

Полный текст с примерами и антипаттернами: см. [reference.md](reference.md)
```

### reference.md

```markdown
# Quality Cascade — полная версия

## Принцип 1: DRY

### Описание
...

### Примеры нарушений
...

### Как исправить
...

## Принцип 2: SRP
...
```

### Реализованные варианты структуры

**Один reference-файл** (полная версия = один файл):
```
error-handling/
├── SKILL.md              # Краткая версия (~40 строк)
└── reference.md          # Полная версия (~110 строк)
```

**Папка reference/** (несколько тематических файлов):
```
architecture/
├── SKILL.md              # DDD + Hexagonal кратко
└── reference/
    ├── ddd.md            # Слои, сущности, Value Objects
    ├── hexagonal.md      # Порты, адаптеры, DI
    ├── monolith.md       # Специфика монолитов
    └── microservices.md  # Специфика микросервисов
```

**Без reference** (шаблон/генератор целиком в SKILL.md):
```
init-project/
└── SKILL.md              # Интерактивная инициализация с вопросами
```

**Источник:** [Best practices — Pattern 2: Domain-organized](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#pattern-1-high-level-guide-with-references)

---

## Поведение description — как Claude выбирает skills

Description — **единственное** что определяет автозагрузку. Claude использует **семантическое сопоставление** (не regex, не ключевые слова) через свою языковую модель.

### Правила хорошего description

```yaml
# ✅ Хорошо — конкретно, с триггерами
description: >
  17 принципов качества Python-кода (DRY, SRP, LoD, KISS).
  Используй при ревью кода, рефакторинге, написании новых модулей.

# ❌ Плохо — слишком абстрактно
description: Помогает с качеством кода
```

### Что включать в description

1. **ЧТО делает** — "17 принципов качества Python-кода"
2. **КОГДА использовать** — "при ревью, рефакторинге, написании нового кода"
3. **Ключевые слова** — "DRY, SRP, LoD, KISS" (помогают семантическому матчингу)
4. **TRIGGER-условия** (для авто-вызова) — "TRIGGER когда: выбор между технологиями, пользователь сравнивает варианты"

### Паттерн TRIGGER в description

Для skill'ов, которые должны срабатывать автоматически, в description добавляется блок TRIGGER:

```yaml
description: >
  Создание ADR. Шаблон с контекстом, альтернативами, решением.
  TRIGGER когда: выбор между технологиями/библиотеками, выбор архитектурного паттерна,
  пользователь сравнивает варианты.
```

Это не гарантирует автоматический вызов, но значительно повышает вероятность. Если авто-вызов не сработал, workflow напоминает вызвать skill вручную.

**Реализовано для:** create-adr, completion-report.

### Ограничения

- Максимум 1,024 символа
- Нельзя XML-теги
- Писать от третьего лица ("Проверяет код...", не "Я проверяю...")

**Источник:** [Best practices — Writing effective descriptions](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#writing-effective-descriptions)

---

## Расход токенов — детальный расчёт

### Базовые размеры

| Компонент | Строк | Токенов |
|-----------|-------|---------|
| Description (1 skill) | 2-3 | ~100 |
| SKILL.md body (краткая версия) | 30-50 | ~300-500 |
| reference.md (полная версия) | 150-500 | ~1,500-5,000 |

### Сценарий: 15 skill'ов (реализовано), сессия 20 сообщений

**Ревью кода (5 запросов) — нужны 3 skill'а с деталями:**
- Descriptions всех 15: ~1,500 токенов (загружены всегда)
- SKILL.md × 3: 900-1,500 токенов
- reference.md × 1-3: 1,500-5,000 токенов (Claude решает сколько нужно)
- **Итого: 3,400-7,500 токенов на запрос**

**Написание кода (10 запросов) — фоновый контекст, детали не нужны:**
- Descriptions: ~1,500 токенов
- SKILL.md × 0-2 (автозагрузка): 0-600 токенов
- reference.md: не читается
- **Итого: 1,000-1,600 токенов на запрос**

**Простые вопросы (5 запросов) — skills не нужны:**
- Descriptions: ~1,500 токенов
- Остальное: 0
- **Итого: 1,000 токенов на запрос**

### Сравнение с другими вариантами

| Метрика | Без тиеринга | Вариант C | MCP (A/B/D) |
|---------|-------------|-----------|-------------|
| Среднее за сессию | ~100,000 | ~34,000 | ~46,000 |
| Экономия | — | **66%** | 54% |
| Мусорные токены | 40-60% | 10-20% | 10-20% |

**Почему C экономнее MCP:** reference.md прочитан через Read = данные в одном сообщении. MCP-ответ = включается в tool_result и **пересылается в каждом последующем запросе** пока не будет сжат.

---

## Сильные стороны

### 1. Ноль кода, ноль зависимостей

Никакого MCP-сервера, embedding-провайдера, базы данных. Только .md файлы в `~/python-ai-skills/` + symlinks в `~/.claude/skills/`. Работает на любой машине с Claude Code.

### 2. Лучшая экономия токенов (-66%)

Парадоксально, самый простой вариант экономит больше всех. Причина: `reference.md` читается через `Read` tool и не дублируется в истории сообщений, в отличие от MCP-ответов.

### 3. Live reload

Изменил `SKILL.md` или `reference.md` — Claude видит изменения при следующем вызове. Не нужно перезапускать сервер, переиндексировать базу, перезагружать сессию.

### 4. Git-версионирование

Все skill'ы — обычные .md файлы. Можно хранить в git, делать PR, откатывать, отслеживать историю изменений.

### 5. Прозрачность

Видно что Claude загрузил — каждый Read tool call отображается в чате. В отличие от автозагрузки `user-invocable: false`, где непонятно что и когда подгрузилось.

### 6. Быстрый старт

Время на создание: ~1 сессия Claude Code (15 skill'ов + 26 reference файлов, включая миграцию из плоской структуры). Для сравнения: MCP-варианты = 4-6 часов, OpenViking = 5-7 часов.

### 7. Масштабируемость описаний

При 15 skill'ах (реализовано) описания = ~1,500 токенов (<1% контекста). При 100 skill'ах = ~10,000 токенов (~2%). Система работает до 100+ skill'ов без деградации.

---

## Слабые стороны

### 1. Нет семантического поиска

Claude выбирает skill только по description (семантическое сопоставление LLM). При 30+ skill'ах с похожими описаниями Claude может выбрать не тот skill или пропустить нужный.

**Митигация:** Писать максимально специфичные description с ключевыми словами-триггерами. Избегать пересекающихся описаний.

### 2. Нет гарантии что reference.md будет/не будет прочитан

Claude **сам решает** нужен ли reference.md. Это может привести к:
- **Перерасходу:** Claude читает reference.md когда хватило бы SKILL.md
- **Недозагрузке:** Claude не читает reference.md когда детали нужны

**Митигация:** Чёткие указания в SKILL.md: "Для ревью кода ОБЯЗАТЕЛЬНО прочитай reference.md. Для написания нового кода — достаточно принципов выше."

### 3. Ручное разделение на L0/L1/L2

Нужно вручную решить что идёт в SKILL.md (краткая версия), а что в reference.md (полная). Для 15 skill'ов из python-ai-skills (26 файлов) это было сделано за одну сессию Claude Code.

**Статус:** Выполнено 2026-03-16. Обновлять инкрементально при добавлении новых skill'ов.

### 4. Нет памяти между сессиями (для skills)

Skills не запоминают что работало, а что нет. Каждая сессия начинается с нуля.

**Митигация:** Claude Code имеет собственную систему memory (`~/.claude/projects/*/memory/`). Это не связано со skills, но покрывает потребность в памяти.

### 5. Нет автоматического профилирования по типу проекта

Skill не знает, что проект — монолит или микросервис. Нужно либо:
- Явно вызывать `/quality-review-monolith`
- Либо полагаться на CLAUDE.md проекта (где указан тип архитектуры)

**Митигация:** В CLAUDE.md проекта указывать тип архитектуры. Skill может содержать инструкцию: "Прочитай CLAUDE.md проекта, найди тип архитектуры, применяй соответствующие правила."

### 6. Запись в python-ai-skills из другого проекта требует исключения в политике $PWD

Для создания/редактирования skill'ов из целевого проекта (где накоплен контекст) нужно разрешить запись в `~/python-ai-skills/` — это исключение из политики LOCAL-ONLY.

**Решение:** В глобальном `~/.claude/CLAUDE.md` добавлено whitelist-исключение (РЕАЛИЗОВАНО 2026-03-16):

```markdown
##### Исключения для записи вне $PWD

Запись вне $PWD разрешена ТОЛЬКО:
- Путь: `~/Henry_Bud_GitHub/python-ai-skills/**`
- Операции: создание и редактирование .md файлов
- Запрещено: удаление, переименование, запись не-.md файлов
- Этот список ФИНАЛЬНЫЙ — новые исключения добавлять только после явного запроса пользователя
```

Это не "размывание" политики, а осознанное решение: `python-ai-skills` — это инфраструктура skill'ов (аналог `.gitconfig`), а не "чужой проект".

### 7. Claude может автозагрузить ненужный skill (или не загрузить нужный)

Если description слишком широкий — ложные срабатывания. Если слишком узкий — Claude не вызовет автоматически когда нужно.

**Митигация (подавление авто-вызова):**
- `disable-model-invocation: true` — только ручной вызов (реализовано: init-project)
- Узкие, специфичные description

**Митигация (усиление авто-вызова):**
- TRIGGER-условия в description с конкретными ситуациями (реализовано: create-adr, completion-report)
- Fallback через workflow: напоминание вызвать вручную перед коммитом

---

## Приоритеты skill'ов

При конфликте имён (один skill на нескольких уровнях):

| Приоритет | Уровень | Путь |
|-----------|---------|------|
| 1 (высший) | Enterprise | Управляется админом |
| 2 | Personal | `~/.claude/skills/<name>/SKILL.md` |
| 3 | Project | `.claude/skills/<name>/SKILL.md` |
| 4 (низший) | Plugin | `<plugin>/skills/<name>/SKILL.md` |

Проектный skill может **переопределить** глобальный с тем же именем. Это позволяет иметь глобальный `quality-cascade` и проектный `quality-cascade` с дополнениями.

**Источник:** [Skills — Where skills live](https://code.claude.com/docs/en/skills.md#where-skills-live)

---

## Динамический контент (!`command`)

Skills поддерживают preprocessing — выполнение shell-команд **до** отправки Claude:

```yaml
---
name: project-stats
description: Статистика текущего проекта
---

## Текущее состояние
- Файлов Python: !`find . -name "*.py" | wc -l`
- Строк кода: !`find . -name "*.py" -exec wc -l {} + | tail -1`
- Последний коммит: !`git log --oneline -1`
```

Claude получает **результат**, не команду. Полезно для skill'ов, которые должны знать состояние проекта.

**Источник:** [Skills — Inject dynamic context](https://code.claude.com/docs/en/skills.md#inject-dynamic-context)

---

## context: fork + reference файлы

При использовании `context: fork` skill запускается в изолированном subagent контексте. **Реализовано** в skill `quality-cascade`:

```yaml
---
name: quality-cascade
description: >
  17 принципов качества Python-кода (DRY, KISS, YAGNI, SOLID, SSoT, LoD, Fail Fast).
  Используй при ревью кода, рефакторинге, написании новых модулей.
  Проверяет code-standards и naming conventions.
context: fork
agent: Explore
---

# Quality Cascade — 17 принципов качества
...
Полные принципы: см. [reference/quality-cascade.md](reference/quality-cascade.md)
```

Subagent **может** читать reference файлы через Read — поддерживающие файлы работают нормально в forked контексте.

**Источник:** [Skills — Run skills in a subagent](https://code.claude.com/docs/en/skills.md#run-skills-in-a-subagent)

---

## Структура python-ai-skills

Репозиторий `~/python-ai-skills/` — единый источник истины для всех skill'ов. Деплой в `~/.claude/skills/` через symlinks.

```
~/python-ai-skills/                    # Git-репо (источник истины) — РЕАЛИЗОВАНО 2026-03-16
├── quality-cascade/                   # context: fork, agent: Explore
│   ├── SKILL.md                       # 17 принципов — краткий чек-лист
│   └── reference/
│       ├── quality-cascade.md         # Полные принципы с антипаттернами
│       ├── code-standards.md          # Типизация, docstrings, метрики
│       └── naming.md                  # Конвенции именования
│
├── error-handling/
│   ├── SKILL.md                       # Иерархия исключений, retry
│   └── reference.md                   # Полный маппинг HTTP ↔ исключения
│
├── security/
│   ├── SKILL.md                       # OWASP Top 10 + обязательные правила
│   └── reference/
│       ├── security.md                # Полные правила безопасности
│       └── secrets-management.md      # Pydantic Settings, .env.example, ротация
│
├── logging/
│   ├── SKILL.md                       # Log-Driven Design, ключевые принципы
│   └── reference.md                   # AI-Readable Logging, structlog конфиг
│
├── testing/
│   ├── SKILL.md                       # 3 уровня тестов, покрытие ≥90%
│   └── reference.md                   # AAA-паттерн, фикстуры, моки
│
├── database/
│   ├── SKILL.md                       # Repository-паттерн, ключевые правила
│   └── reference.md                   # Alembic, транзакции, N+1, connection pooling
│
├── architecture/
│   ├── SKILL.md                       # DDD + Hexagonal, выбор монолит/микросервисы
│   └── reference/
│       ├── ddd.md                     # Слои, сущности, Value Objects
│       ├── hexagonal.md               # Порты, адаптеры, DI
│       ├── monolith.md                # Модульные границы, shared database
│       └── microservices.md           # Изоляция, коммуникация, трейсинг
│
├── linters/
│   ├── SKILL.md                       # Ruff, Mypy, Bandit, pre-commit
│   └── reference/
│       ├── linters.md                 # Полная конфигурация инструментов
│       └── ci-cd.md                   # CI pipeline, coverage gate
│
├── docker/
│   ├── SKILL.md                       # Multi-stage, security, health checks
│   └── reference/
│       ├── docker.md                  # Dockerfile, Compose, .dockerignore
│       └── production.md              # Graceful shutdown, мониторинг
│
├── http-clients/
│   ├── SKILL.md                       # httpx, timeout, Circuit Breaker
│   └── reference.md                   # Retry, логирование, обработка ошибок
│
├── caching/
│   ├── SKILL.md                       # Redis, TTL, graceful degradation
│   └── reference.md                   # Паттерны, инвалидация, именование
│
├── workflow/
│   ├── SKILL.md                       # Пайплайн 6 этапов, чеклист
│   └── reference/
│       ├── workflow.md                # Полный пайплайн документации
│       ├── backlog.md                 # Шаблон задачи TASK-NNN
│       ├── planning.md                # Формат планов
│       └── git-conventions.md         # Формат коммитов
│
├── create-adr/                        # Гибридный триггер: авто + ручной
│   ├── SKILL.md                       # Шаблон ADR, правила создания
│   └── reference.md                   # Полный шаблон и статусы
│
├── completion-report/                 # Гибридный триггер: авто + ручной
│   ├── SKILL.md                       # Шаблон отчёта, правила
│   └── reference.md                   # Полный шаблон с метриками
│
├── init-project/
│   └── SKILL.md                       # Интерактивная инициализация (disable-model-invocation)
│
├── docs/
│   └── 2026-03-15-skills-file-convention-architecture.md
│
├── CLAUDE.md                          # Каталог skill'ов + workflow (v3.0)
└── CHANGELOG.md

~/.claude/skills/                      # Symlinks (деплой) — СОЗДАНО 2026-03-16
├── quality-cascade → ~/python-ai-skills/quality-cascade
├── error-handling → ~/python-ai-skills/error-handling
├── security → ~/python-ai-skills/security
├── logging → ~/python-ai-skills/logging
├── testing → ~/python-ai-skills/testing
├── database → ~/python-ai-skills/database
├── architecture → ~/python-ai-skills/architecture
├── linters → ~/python-ai-skills/linters
├── docker → ~/python-ai-skills/docker
├── http-clients → ~/python-ai-skills/http-clients
├── caching → ~/python-ai-skills/caching
├── workflow → ~/python-ai-skills/workflow
├── create-adr → ~/python-ai-skills/create-adr
├── completion-report → ~/python-ai-skills/completion-report
└── init-project → ~/python-ai-skills/init-project
```

### Деплой symlinks

Symlinks создаются вручную (без скрипта). При добавлении нового skill'а — одна команда:

```bash
# Создание всех symlinks (один раз)
mkdir -p ~/.claude/skills
for skill_dir in ~/Henry_Bud_GitHub/python-ai-skills/*/; do
    [ -f "$skill_dir/SKILL.md" ] && ln -sfn "$skill_dir" "$HOME/.claude/skills/$(basename "$skill_dir")"
done

# Добавление нового skill'а
ln -sfn ~/Henry_Bud_GitHub/python-ai-skills/new-skill ~/.claude/skills/new-skill
```

**Статус:** 15 symlinks создано 2026-03-16.

---

## Cross-project workflow: создание skill'ов из целевого проекта

### Проблема

Контекст для нового skill'а накапливается в целевом проекте (например, `claude_bot`), но skill'ы живут в `~/python-ai-skills/`. Без исключения в политике $PWD невозможно записать skill из целевого проекта.

### Решение

В глобальном `~/.claude/CLAUDE.md` добавлено whitelist-исключение для `~/python-ai-skills/`. Это позволяет из любого проекта:

1. **Создать новый skill** — когда в процессе работы выявлен переиспользуемый паттерн
2. **Обновить существующий skill** — когда в целевом проекте найден лучший подход
3. **Добавить reference-материалы** — когда накоплены примеры

### Workflow

```
Проект claude_bot                     ~/python-ai-skills/
┌─────────────────────┐                ┌─────────────────────┐
│ Работаешь над кодом │                │                     │
│ Выявляешь паттерн   │ ── запись ──→  │ error-handling/     │
│ Контекст на месте   │                │   SKILL.md (новый)  │
│                     │                │   reference.md      │
└─────────────────────┘                └─────────────────────┘
                                              │
                                         symlink в
                                       ~/.claude/skills/
                                              │
                                              ▼
                                       Доступен во ВСЕХ
                                       проектах мгновенно
```

### Рекомендации по workflow

- **Создавай skill когда паттерн подтверждён** — не после первого использования, а когда он повторился 2-3 раза
- **Начинай с SKILL.md** — краткая версия (30-50 строк). Reference.md добавишь позже, когда накопятся примеры
- **Коммить в python-ai-skills отдельно** — не забывай, что запись в чужой репо не создаёт коммит автоматически. После сессии зайди в `~/python-ai-skills/` и закоммить изменения

---

## Когда переходить на другой вариант

| Сигнал | Действие |
|--------|----------|
| Claude часто загружает не тот skill | Уточнить descriptions. Если не помогает → MCP с поиском (Вариант B) |
| Skill'ов стало 30+ | Рассмотреть MCP с FTS5 (Вариант B) |
| Claude всегда читает reference.md | Значит SKILL.md недостаточно информативен — расширить краткую версию |
| Claude никогда не читает reference.md | Значит reference.md избыточен — можно убрать |
| Нужна память между сессиями (для skills) | Использовать Claude Code memory или рассмотреть OpenViking |
| Стоимость токенов критична | Вариант A (MCP тиеринг) — даёт явный контроль L0/L1/L2 |

---

## Решения при реализации (2026-03-16)

Документ ниже фиксирует ключевые решения, принятые при реализации. Исходный план выше сохранён для контекста.

### Отличия от исходного плана

| Аспект | План | Реализация | Причина |
|--------|------|-----------|---------|
| Количество skill'ов | 8 (упомянуто "10 core") | **15** | Все 26 исходных файлов покрыты через группировку |
| Исходные файлы | Не определено | Перемещены в reference (git mv) | Вариант D — SSoT, нет дублирования |
| CLAUDE.md | Не упомянут | Каталог skill'ов + workflow (v3.0) | Вариант B — точка входа + навигация |
| deploy-skills.sh | Скрипт в репо | Ручные symlinks | KISS — 15 команд один раз |
| security/reference/ | auth.md, injection.md, validation.md | security.md + secrets-management.md | Файлы из плана не существовали |
| context: fork | Описан, не применён | quality-cascade | Единственный skill для глубокого ревью |
| init-project | Пустой placeholder | Интерактивный с вопросами | Стандартизация настройки проектов |
| process/ файлы | 2 файла (adr, completion-report) | 6 файлов → 3 skill'а + workflow | workflow.md, backlog.md, planning.md, git-conventions.md добавлены |
| Триггерная модель | Отложено | Гибрид: авто (TRIGGER в description) + ручной fallback (workflow) | Баланс: не забудешь, но и без ложных срабатываний |

### Дополнительные skill'ы (не в плане)

| Skill | Источник | Почему добавлен |
|-------|---------|----------------|
| database | development/database.md | Самостоятельная тема: Repository, миграции, N+1 |
| architecture | architecture/*.md (4 файла) | Фундаментальные паттерны: DDD, Hexagonal, монолит/микросервисы |
| linters | quality/linters.md + ci-cd.md | Самый большой файл (221 строка), CI pipeline |
| docker | operations/docker.md + production.md | Контейнеризация + production requirements |
| http-clients | integrations/http-clients.md | HTTP клиент, Circuit Breaker — самостоятельная тема |
| caching | integrations/caching.md | Redis, TTL — самостоятельная тема |
| workflow | process/*.md (4 файла) | Пайплайн документации: 6 этапов |

### Структура reference-файлов

Два варианта в зависимости от количества reference-файлов:

- **Один файл** → `reference.md` (error-handling, logging, testing, database, http-clients, caching, create-adr, completion-report)
- **Несколько файлов** → `reference/` папка (quality-cascade, security, architecture, linters, docker, workflow)

### Триггерная модель create-adr и completion-report (решено 2026-03-16)

**Модель: гибрид (авто + ручной fallback)**

- Оба skill'а **не имеют** `disable-model-invocation` — Claude может вызвать их автоматически
- Description содержит конкретные TRIGGER-условия для автоматического срабатывания
- Если автотриггер не сработал — workflow SKILL.md напоминает вызвать их вручную перед коммитом
- create-adr: триггер на выбор технологий, архитектурных паттернов, сравнение вариантов
- completion-report: триггер на завершение фичи, готовность к коммиту

---

## Источники

- [Claude Code — Extend Claude with skills](https://code.claude.com/docs/en/skills.md)
- [Claude API — Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Claude Code — Manage costs effectively](https://code.claude.com/docs/en/costs.md)
- [Claude Code — Features overview](https://code.claude.com/docs/en/features-overview.md)
