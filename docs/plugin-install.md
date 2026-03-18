# Установка плагина python-pipeline

> Пошаговая инструкция для установки локального плагина `python-pipeline` в Claude Code.
> Для обновления уже установленного плагина см. [`docs/plugin-update.md`](plugin-update.md).

---

## Предварительные требования

| Требование | Проверка |
|------------|----------|
| Claude Code CLI установлен | `claude --version` |
| Git установлен | `git --version` |
| Репозиторий `python-ai-skills` склонирован | `ls ~/Henry_Bud_GitHub/python-ai-skills/.claude-plugin/plugin.json` |

---

## Архитектура: плагин vs скиллы

Прежде чем устанавливать — важно понимать, что **плагин и скиллы — разные механизмы**.

### Что даёт плагин (`~/.claude/plugins/`)

Плагин регистрирует **commands** и **agents**:
- `/pipeline` — из `commands/pipeline.md`
- `py-quality`, `py-security`, `py-doc-manager`, `py-test-writer`, `py-supervisor` — из `agents/*.md`

### Что даёт `~/.claude/skills/`

Скиллы (slash-команды `/_docworkflow`, `/_code-quality` и т.д.) регистрируются **отдельно** через симлинки в `~/.claude/skills/`. Без этих симлинков скиллы **не видны** как slash-команды, даже если плагин установлен.

### Полная структура

```
~/.claude/
├── settings.json                 # Глобальные настройки (permissions, hooks, plugins)
├── settings.local.json           # Накопленные разрешения (создаётся автоматически)
├── skills/                       # ⚠️ Симлинки на скиллы (для slash-команд /_*)
│   ├── _docworkflow → ~/Henry_Bud_GitHub/python-ai-skills/_docworkflow/
│   ├── _code-quality → ~/Henry_Bud_GitHub/python-ai-skills/_code-quality/
│   └── ... (15 скиллов)
└── plugins/
    ├── known_marketplaces.json   # Реестр маркетплейсов
    ├── installed_plugins.json    # Метаданные установленных плагинов
    ├── config.json               # Конфигурация
    ├── local/                    # Симлинки на локальные плагины
    │   └── python-pipeline → ~/Henry_Bud_GitHub/python-ai-skills
    ├── cache/                    # Кэш (рабочие файлы, которые Claude Code читает)
    │   └── local-plugins/
    │       └── python-pipeline/
    │           └── 1.2.1/
    │               ├── commands/
    │               ├── agents/
    │               └── ...
    └── marketplaces/
```

**Ключевые моменты:**
- **Плагин** (`plugins/`) → команды (`/pipeline`) и агенты
- **Скиллы** (`skills/`) → slash-команды (`/_docworkflow`, `/_code-quality` и т.д.)
- `cache/` содержит **копию** файлов плагина, привязанную к **версии** из `plugin.json`
- Claude Code читает файлы **только из кэша**, не из исходника напрямую
- **Оба механизма нужны** для полноценной работы

---

## Процедура установки

### Шаг 1. Склонировать репозиторий (если ещё нет)

```bash
cd ~/Henry_Bud_GitHub
git clone <url-репозитория> python-ai-skills
```

Если репозиторий уже есть — убедитесь, что он на актуальной ветке:

```bash
cd ~/Henry_Bud_GitHub/python-ai-skills
git pull
```

### Шаг 2. Зарегистрировать локальный маркетплейс

Локальный маркетплейс — это директория, в которой Claude Code ищет плагины. Нужно добавить `~/.claude/plugins/local` как маркетплейс с именем `local-plugins`:

```bash
claude plugins marketplace add local-plugins --directory ~/.claude/plugins/local
```

**Проверка:** после выполнения в `~/.claude/plugins/known_marketplaces.json` появится запись:

```json
{
  "local-plugins": {
    "source": {
      "source": "directory",
      "path": "/home/USER/.claude/plugins/local"
    }
  }
}
```

> **Примечание:** этот шаг выполняется **один раз**. При установке последующих локальных плагинов маркетплейс уже будет зарегистрирован.

### Шаг 3. Создать симлинк на плагин

Создать символическую ссылку из `~/.claude/plugins/local/` на корень репозитория:

```bash
mkdir -p ~/.claude/plugins/local
ln -s ~/Henry_Bud_GitHub/python-ai-skills ~/.claude/plugins/local/python-pipeline
```

**Важно:** имя симлинка (`python-pipeline`) должно совпадать с полем `name` в `.claude-plugin/plugin.json`.

**Проверка:**

```bash
ls -la ~/.claude/plugins/local/python-pipeline
# Ожидаемый вывод:
# python-pipeline -> /home/USER/Henry_Bud_GitHub/python-ai-skills
```

### Шаг 4. Создать симлинки скиллов

> **⚠️ Без этого шага скиллы `/_docworkflow`, `/_code-quality` и т.д. НЕ будут видны как slash-команды.**

```bash
mkdir -p ~/.claude/skills

for skill in _adr _architecture _caching _code-quality _database _docker _docworkflow _error-handling _http _init _linters _logging _report _security _testing; do
  ln -s ~/Henry_Bud_GitHub/python-ai-skills/${skill}/ ~/.claude/skills/${skill}
done
```

**Проверка:**

```bash
ls -la ~/.claude/skills/
# Должно быть 15 симлинков, каждый указывает на соответствующую директорию в python-ai-skills
```

Claude Code ищет скиллы в `~/.claude/skills/` и регистрирует каждую папку с `SKILL.md` как slash-команду.

### Шаг 5. Установить плагин

```bash
claude plugins install python-pipeline@local-plugins
```

Эта команда:
1. Находит `python-pipeline` в маркетплейсе `local-plugins`
2. Читает `.claude-plugin/plugin.json` из исходника
3. Копирует файлы плагина в `~/.claude/plugins/cache/local-plugins/python-pipeline/<version>/`
4. Записывает метаданные в `~/.claude/plugins/installed_plugins.json`

**Ожидаемый вывод:**

```
✔ Installed python-pipeline@local-plugins (version 1.2.0)
```

### Шаг 6. Перезапустить Claude Code

```bash
# Выйти из текущей сессии
exit
# Запустить заново
claude
```

Claude Code загружает плагины при старте. Без перезапуска новый плагин не будет виден.

### Шаг 7. Проверить установку

В новой сессии Claude Code:

```bash
claude plugins list
```

Плагин `python-pipeline@local-plugins` должен быть в списке с актуальной версией.

Дополнительная проверка — вызвать команду плагина и скилл:

```
/pipeline          # Команда из плагина (commands/)
/_docworkflow      # Скилл из ~/.claude/skills/
```

Оба должны распознаваться. Если `/pipeline` работает, а `/_docworkflow` — нет, значит пропущен шаг 4 (симлинки скиллов).

---

## Установка с нуля (все команды)

Для быстрой установки на чистой системе — все шаги одним блоком:

```bash
# 1. Склонировать репозиторий
cd ~/Henry_Bud_GitHub
git clone <url-репозитория> python-ai-skills

# 2. Зарегистрировать локальный маркетплейс
claude plugins marketplace add local-plugins --directory ~/.claude/plugins/local

# 3. Создать симлинк плагина
mkdir -p ~/.claude/plugins/local
ln -s ~/Henry_Bud_GitHub/python-ai-skills ~/.claude/plugins/local/python-pipeline

# 4. Создать симлинки скиллов
mkdir -p ~/.claude/skills
for skill in _adr _architecture _caching _code-quality _database _docker _docworkflow _error-handling _http _init _linters _logging _report _security _testing; do
  ln -s ~/Henry_Bud_GitHub/python-ai-skills/${skill}/ ~/.claude/skills/${skill}
done

# 5. Установить плагин
claude plugins install python-pipeline@local-plugins

# 6. Перезапустить Claude Code
```

---

## Выбор scope: user vs project

Плагин можно установить в двух scope'ах:

| Scope | Флаг | Действие | Когда использовать |
|-------|------|----------|-------------------|
| `user` | (по умолчанию) | Доступен во всех проектах | Общие skill'ы для разработки |
| `project` | `--scope project` | Только для текущего проекта | Проектоспецифичные правила |

```bash
# Установка для конкретного проекта
claude plugins install python-pipeline@local-plugins --scope project
```

`python-pipeline` рекомендуется устанавливать в scope `user`, так как skill'ы применимы к любому Python-проекту.

---

## Структура плагина

Плагин определяется файлом `.claude-plugin/plugin.json` в корне репозитория:

```json
{
  "name": "python-pipeline",
  "version": "1.2.0",
  "description": "Python development pipeline — orchestrates 9 phases, 15 skills, 5 agents via Agent Teams",
  "author": { "name": "bgs" }
}
```

| Поле | Описание |
|------|----------|
| `name` | Уникальное имя плагина. Должно совпадать с именем симлинка |
| `version` | Версия в формате SemVer. Используется для кэширования |
| `description` | Описание (отображается в `plugins list`) |
| `author` | Информация об авторе |

---

## Частые ошибки и решения

### Ошибка 1: `Plugin "python-pipeline" not found`

**Симптом:**
```
Error: Plugin "python-pipeline" not found
```

**Причины и решения:**

| Причина | Решение |
|---------|---------|
| Не указан суффикс маркетплейса | Использовать `python-pipeline@local-plugins` |
| Маркетплейс `local-plugins` не зарегистрирован | Выполнить шаг 2 (регистрация маркетплейса) |
| Симлинк не создан или указывает не туда | Проверить: `ls -la ~/.claude/plugins/local/python-pipeline` |
| Имя симлинка не совпадает с `name` в `plugin.json` | Пересоздать симлинк с правильным именем |

**Диагностика:**

```bash
# Проверить маркетплейс
cat ~/.claude/plugins/known_marketplaces.json | grep local-plugins

# Проверить симлинк
ls -la ~/.claude/plugins/local/

# Проверить plugin.json
cat ~/.claude/plugins/local/python-pipeline/.claude-plugin/plugin.json
```

---

### Ошибка 2: `Marketplace "local-plugins" not found`

**Симптом:**
```
Error: Marketplace "local-plugins" not found
```

**Причина:** локальный маркетплейс не зарегистрирован.

**Решение:**

```bash
claude plugins marketplace add local-plugins --directory ~/.claude/plugins/local
```

---

### Ошибка 3: Симлинк сломан (dangling symlink)

**Симптом:** `ls -la` показывает симлинк красным цветом, или команда установки не находит `plugin.json`.

**Причина:** репозиторий перемещён или удалён.

**Решение:**

```bash
# Удалить старый симлинк
rm ~/.claude/plugins/local/python-pipeline

# Создать новый с правильным путём
ln -s /актуальный/путь/к/python-ai-skills ~/.claude/plugins/local/python-pipeline

# Проверить
ls -la ~/.claude/plugins/local/python-pipeline
cat ~/.claude/plugins/local/python-pipeline/.claude-plugin/plugin.json
```

---

### Ошибка 4: `Unknown skill: _docworkflow` (скиллы не видны как slash-команды)

**Симптом:**
```
› Unknown skill: _docworkflow
```

Плагин установлен, `/pipeline` работает, но `/_docworkflow`, `/_code-quality` и другие скиллы с префиксом `_` не распознаются.

**Причина:** отсутствует директория `~/.claude/skills/` с симлинками на скиллы. Плагин регистрирует только commands (`/pipeline`) и agents, а скиллы — **отдельный механизм** через `~/.claude/skills/`.

**Решение:**

```bash
mkdir -p ~/.claude/skills

for skill in _adr _architecture _caching _code-quality _database _docker _docworkflow _error-handling _http _init _linters _logging _report _security _testing; do
  ln -s ~/Henry_Bud_GitHub/python-ai-skills/${skill}/ ~/.claude/skills/${skill}
done

# Перезапустить Claude Code
```

**Проверка:**

```bash
ls ~/.claude/skills/
# Должно быть 15 симлинков
```

> **Важно:** это самая частая ошибка при установке на новой машине. Симлинки в `~/.claude/skills/` нужно создавать на каждой машине отдельно — они не переносятся с плагином.

---

### Ошибка 5: Плагин установлен, но `/pipeline` не работает

**Симптом:** `claude plugins list` показывает плагин, но `/pipeline` и другие команды не распознаются.

**Причины и решения:**

| Причина | Решение |
|---------|---------|
| Claude Code не перезапущен после установки | Перезапустить Claude Code |
| Кэш повреждён | Очистить кэш и переустановить (см. ниже) |
| Версия в кэше устаревшая | Выполнить `claude plugins update python-pipeline@local-plugins` |

**Очистка кэша и переустановка:**

```bash
rm -rf ~/.claude/plugins/cache/local-plugins/python-pipeline
claude plugins install python-pipeline@local-plugins
# Перезапустить Claude Code
```

---

### Ошибка 6: `Permission denied` при создании симлинка

**Причина:** нет прав на запись в `~/.claude/plugins/local/`.

**Решение:**

```bash
mkdir -p ~/.claude/plugins/local
# Если всё ещё ошибка:
ls -la ~/.claude/plugins/ | grep local
# Убедиться что директория принадлежит текущему пользователю
```

---

### Ошибка 7: Установлена не та версия

**Симптом:** `claude plugins list` показывает старую версию.

**Причина:** в `.claude-plugin/plugin.json` не обновлена версия, или есть незакоммиченные изменения.

**Решение:**

```bash
# Проверить версию в исходнике
cat ~/Henry_Bud_GitHub/python-ai-skills/.claude-plugin/plugin.json

# Обновить до актуальной версии
claude plugins update python-pipeline@local-plugins

# Перезапустить Claude Code
```

---

### Ошибка 8: `already at the latest version` при первичной установке

**Симптом:**
```
✔ python-pipeline is already at the latest version (1.2.0).
```

**Причина:** плагин уже был установлен ранее (возможно, в другой сессии или другим пользователем).

**Это не ошибка** — плагин установлен и актуален. Достаточно перезапустить Claude Code, если skill'ы не видны.

---

## Удаление плагина

```bash
# Удалить из Claude Code
claude plugins uninstall python-pipeline@local-plugins

# Опционально: удалить симлинк
rm ~/.claude/plugins/local/python-pipeline

# Опционально: очистить кэш
rm -rf ~/.claude/plugins/cache/local-plugins/python-pipeline
```

---

## Диагностика: полная проверка

Если что-то не работает — выполнить все проверки по порядку:

```bash
# 1. Маркетплейс зарегистрирован?
cat ~/.claude/plugins/known_marketplaces.json | python3 -m json.tool

# 2. Симлинк плагина существует и валиден?
ls -la ~/.claude/plugins/local/python-pipeline
cat ~/.claude/plugins/local/python-pipeline/.claude-plugin/plugin.json

# 3. Кэш существует?
ls ~/.claude/plugins/cache/local-plugins/python-pipeline/

# 4. Метаданные корректны?
cat ~/.claude/plugins/installed_plugins.json | python3 -m json.tool

# 5. Версия в кэше совпадает с исходником?
# Исходник:
cat ~/Henry_Bud_GitHub/python-ai-skills/.claude-plugin/plugin.json
# Кэш:
ls ~/.claude/plugins/cache/local-plugins/python-pipeline/

# 6. Симлинки скиллов существуют?
ls -la ~/.claude/skills/
# Должно быть 15 симлинков (_adr, _architecture, ..., _testing)
# Каждый должен указывать на ~/Henry_Bud_GitHub/python-ai-skills/_*/
```

Если какой-то из шагов показывает проблему — вернитесь к соответствующему шагу установки.
