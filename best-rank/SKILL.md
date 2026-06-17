---
name: best-rank
description: >
  Re-audit an existing set of options already in context through the best-research
  engine — validate each again, surface unstated intent and blind spots, add
  missing best-practice options, then score every option 0–100% as its probability
  of acceptance and rank from highest to lowest. Thin wrapper over best-research —
  its specialization is taking a ready list and ranking by %.
  TRIGGER when: user calls /best-rank, there is already a list of options /
  approaches / variants in context and the user wants a second-pass audit +
  probability ranking.
  SKIP when: no option list exists yet — generate from scratch via /best-approach;
  resolving a set of questions — use /best-questions.
argument-hint: "[опционально: на чём сфокусироваться при переоценке]"
---

# /best-rank — Ре-аудит и ранжирование готового списка

> Уже есть список вариантов в контексте? Перепроверю каждый движком `best-research`, добавлю упущенные best-practice решения, проставлю каждому вероятность принятия 0–100% и отранжирую.

## Вход

Аргумент (опционально) — на что сделать акцент при переоценке («с упором на скорость внедрения», «учти что life-проект»). Если списка вариантов в контексте **нет** — это работа для `/best-approach`; скажи об этом и предложи его.

## Что делает (тонкая обёртка)

1. **Собери существующие варианты** — выпиши явным списком ВСЕ варианты из контекста с источником каждого («предложен ассистентом», «предложен юзером», «из brainstorming»). Ничего не теряй и не сливай молча.
2. **Прогони набор через движок `best-research`** — следуй его спецификации (`~/.claude/skills/best-research/SKILL.md`): исследование (код + Context7 + WebSearch + CLAUDE.md) → мета-анализ → 17 принципов качества → добавление упущенных best-practice вариантов (пометка «[добавлено]»). Это **переиспользование общего ядра по ссылке**, не передача управления.
3. **Оцени и отранжируй по %** — каждому варианту (исходному + добавленному) процент вероятности принятия 0–100% (по формату `best-recommend`), сортировка по % убыв. *(Отличие от `best-approach`, где сортировка простое → сложное.)*

## Правила специфичные для best-rank

1. **Не терять варианты** — каждый вариант из контекста попадает в рейтинг, даже с низким % и причиной «почему нет».
2. **Осмысленный разброс** — проценты различимы; близкие варианты назвать близкими явно, не подгонять.
3. **Сортировка** — по % убыв (от фаворита к аутсайдеру).
4. **Нет списка в контексте** — не выдумывать: сказать, что это кейс для `/best-approach`.

Всё остальное (обязательность исследования, Context7, объективность, мета-анализ, СТОП) — по спецификации `best-research`.

## Формат вывода

```text
## Аудит вариантов: {краткое описание задачи}

### Что выяснилось при переоценке
- Настоящая цель / Хотел но не сформулировал / Ошибочные предположения / Слепые зоны

### Рейтинг (от высшего % к низшему)
**1. {Название} — 85%** [исходный | добавлено]
{Описание}
✅ Усиливает: ... ❌ Нарушает/риски: ... 🚩 Red flags: ...
Почему 85%: {1–2 предложения, источник}

**2. {Название} — 60%** ...

## 💡 Рекомендация
{блок по формату /best-recommend}
```

## После выбора пользователя

1. Подтверди выбор кратко.
2. **Вызван из orchestrator workflow** → верни findings + рейтинг вызывающему. НЕ переходить к другим workflow.
3. **Вызван standalone:** Dev → вернуть управление активному workflow; Life → можно реализовывать.
4. Просит скомбинировать — пересчитай % для гибрида.

## Роль в семье best-*

- `best-rank` = **research / audit tool** (ревизия готового списка + рейтинг по вероятности).
- НЕ управляет workflow transitions, НЕ вызывает process-skills.
- Отличие: `best-rank` берёт **готовый список**; `best-approach` строит **с нуля**; `best-questions` ведёт по **вопросам**.
- Движок разбора — `best-research`; формат рекомендации — `best-recommend`.
