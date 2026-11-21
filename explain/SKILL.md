---
name: explain
description: >
  Multi-dimensional explanation generator: explains a concept, theory, term, document,
  project, codebase or LLM output at a controlled level of detail for a chosen audience.
  Eight explicit axes (search source, object, audience, term decoding, term register,
  structure, language, source grounding) plus named presets, so every explanation has a
  stated, reproducible mode instead of silent defaults. Extends the global Explanation
  Protocol; does not replace it.
  TRIGGER when: user calls /explain; asks to explain something «как джуну / ребёнку /
  сеньору / бизнесу»; wants a concept, document, project, codebase or LLM output
  explained with controlled detail, decoded terms or a fixed vocabulary.
  SKIP when: short factual answer or work report; recommendation delivery (best-recommend);
  a plain in-answer explanation already covered by the global Explanation Protocol.
argument-hint: "[что объяснить и для кого; --preset child|junior|senior|business, --audience, --detail full|partial|none, --search auto|local|web|none, --structure layers|summary-first|direct, --lang ru|en, --no-sources]"
---

# /explain — Многомерное объяснение

> Объяснить объект (концепцию, документ, проект, кодовую базу, вывод LLM) для выбранной аудитории с контролируемой детализацией. Режим объяснения фиксирован восемью осями и печатается первой строкой ответа — объяснение воспроизводимо и не «плывёт».

## Оси (8)

| Ось | Значения | По умолчанию |
|-----|----------|--------------|
| `search` — откуда брать материал | `none` (объект уже в контексте) · `local` (компьютер: репозиторий, файлы, bd memories) · `web` (интернет) · `auto` | `auto` |
| `object` — что объясняем | `concept` (концепция, теория, термин, название) · `document` (конкретный документ) · `project` (содержание проекта) · `codebase` (код или модуль) · `llm-output` (вывод другой LLM) · `web-result` (результаты веб-поиска) · `text` (произвольный текст) | из запроса |
| `audience` — кому | `child` · `novice` (новичок в теме) · `junior` · `senior` · `nontech` (не связан с программированием) · `mixed` (пишем по самому неподготовленному) | `junior` |
| `detail` — расшифровка терминов | `full` (каждый термин при первом употреблении: расшифровка аббревиатуры + значение в скобках + ≥1 предложение смысла) · `partial` (только термины вне базового набора аудитории) · `none` | по аудитории |
| `register` — реестр терминов | всегда включён; значения не выбираются — см. правило ниже | on |
| `structure` — порядок изложения | `layers` (суть в 3 предложениях → база → слои деталей) · `summary-first` (TL;DR, потом разделы) · `direct` (сразу на целевом уровне) | `layers` |
| `lang` — язык объяснения | `ru` · `en` (глоссарий терминов всё равно двуязычный) | `ru` |
| `sources` — grounding | `on` (web-факт → URL; код → `file:line`; вывод LLM → цитата; библиотека → Context7/официальная документация) · `off` (`--no-sources`) | `on` |

## Пресеты

| Пресет | audience | detail | structure | Особенности |
|--------|----------|--------|-----------|-------------|
| `child` | child | full | layers | Короткие предложения, аббревиатур нет вовсе |
| `junior` (по умолчанию) | junior | full | layers | — |
| `senior` | senior | none | direct | — |
| `business` | nontech | full | layers | Только термины из реестра, определения бытовым языком |

Пресет задаёт оси по умолчанию; любая ось переопределяется флагом аргумента или естественным языком («объясни как ребёнку» → preset `child`).

## Правила

1. **Без вопросов по осям.** Не хватает оси — берём значение по умолчанию или из пресета, не спрашиваем. Объект не передан — один вопрос: «Что объясняем?».
2. **Строка режима.** Первая строка ответа: `Режим: объект=… · кому=… · детализация=… · поиск=… · структура=… · язык=… · источники=…` — пользователь видит режим и может сменить любую ось.
3. **Реестр терминов (всегда).** До письма зафиксировать реестр: термин → одно определение. В тексте — только формы из реестра; синонимная замена на ходу запрещена («функция» не превращается в «метод»/«процедуру»); новый необходимый термин — сначала в реестр с определением, потом в текст. Проектные запрещённые формы проверяет глоссарий-хук (`claude-home/hooks/glossary.py`) — скилл их не дублирует.
4. **База — глобальный Explanation Protocol** (global CLAUDE.md): обычное русское слово вместо термина, термин только при необходимости, запрет образов и метафор. Скилл добавляет поверх: уровни детализации, реестр, режим.
5. **Гипотезы — флагом.** Не уверен в факте — пометить «предположительно, нужно проверить», не выдавать за факт.
6. **Самопроверка перед выдачей** — чек-лист в `reference.md`.

Полная спецификация осей, процедура для `llm-output`, шаблоны по аудиториям и чек-лист — `reference.md`.
