---
name: best-approach
description: >
  Generate solution approaches from scratch for a task, then analyze and compare
  them through the best-research engine, recommend with confidence %, and wait
  for the user's choice. Thin wrapper over best-research — its only specialization
  is generating the candidate options from nothing.
  TRIGGER when: user calls /best-approach, user has a task but no option list yet
  and wants approaches compared from scratch.
  SKIP when: a list of options already exists in context — re-rank it via
  /best-rank; resolving a set of clarifying questions — use /best-questions.
argument-hint: "[описание задачи или промпт]"
---

# /best-approach — Генерация подходов с нуля

> Есть задача, но нет списка вариантов? Сгенерирую подходы с нуля, разберу движком `best-research`, дам рекомендацию, жду выбора.

## Вход

Аргумент — описание задачи. Если не передан — спроси: «Какую задачу разбираем?».

## Что делает (тонкая обёртка)

1. **Сгенерируй варианты с нуля.** Это единственная специализация этого скила: для задачи без готового списка предложи реалистичные подходы (адекватно сложности: простая → 2–3, средняя → 3–4, сложная → 4–5).
2. **Передай сгенерированный набор в движок `best-research`** — следуй его спецификации (`~/.claude/skills/best-research/SKILL.md`): исследование контекста (код + Context7 + WebSearch + CLAUDE.md) → мета-анализ → 17 принципов качества → pros/cons → рекомендация по формату `best-recommend`. Это **переиспользование общего ядра по ссылке**, не передача управления другому workflow.
3. **Сортировка вариантов — от простого к сложному** (по сложности реализации). *(Отличие от `best-rank`, где сортировка по % убыв.)*

## Правила специфичные для best-approach

1. **Сортировка** — всегда простое → сложное.
2. **Существующий код** — перед предложением варианта проверить, нет ли уже готового решения (DRY).
3. **СТОП перед действием** — не реализовывать ни один вариант до явного выбора.

Всё остальное (обязательность исследования, Context7, объективность, формат вывода, СТОП) — по спецификации `best-research`.

## После выбора пользователя

1. Подтверди выбор кратко.
2. **Вызван из orchestrator workflow** (do-feature, Discovery) → верни findings вызывающему skill'у. НЕ переходить к другим workflow.
3. **Вызван standalone:**
   - **Dev-проект** → вернуть управление активному workflow проекта, не реализовывать напрямую.
   - **Не dev-проект** (Life) → приступать к реализации выбранного варианта.
4. Просит скомбинировать варианты — адаптируйся.

## Роль в семье best-*

- `best-approach` = **research tool** (генерация подходов с нуля + разбор движком).
- НЕ управляет workflow transitions, НЕ вызывает process-skills.
- Отличие: `best-approach` строит варианты **с нуля**; `best-rank` берёт **готовый список** и ранжирует с %; `best-questions` ведёт по **набору вопросов**.
- Движок разбора — `best-research`; формат рекомендации — `best-recommend`.
