---
name: explain
description: >
  Multi-dimensional explanation generator: explains a concept, theory, term, document,
  project, codebase, difference pair or LLM output for a chosen audience, with a fixed
  term register and source grounding. Eight axes (search source, object, audience,
  detail, register, structure, language, sources) plus presets; full explanations follow
  a per-object anatomy matrix (five for concept/document, four for project plus an auto
  "done this time" section for artifacts, five for codebase); difference questions get
  a three-section structure; bare term questions get a brief three-block decode; a lost
  user gets rescue mode with the object taken from the dialog. Extends the global
  Explanation Protocol.
  TRIGGER when: user calls /explain (Pi: /skill:explain); asks to explain something
  «как джуну / ребёнку / сеньору / бизнесу», «начиная с базы / с нуля», «простыми словами»;
  asks a bare term question — «что такое X», «что значит X», «что означает X», «расшифруй X»,
  «объясни X», «explain X» — auto brief mode; asks a difference question — «чем отличается X
  от Y», «в чём разница между X и Y» — auto difference mode; asks «как работает / как устроен X»;
  asks to walk through a project or code — «прочитай проект… и объясни», «разбери X»,
  «объясни, что ты сделал»; is lost mid-task — «ничего не понимаю», «запутался» + explain
  intent — rescue mode (object from the dialog, no clarifying question); wants controlled
  detail, decoded terms or a fixed vocabulary.
  SKIP when: short factual answer or work report; recommendation delivery (best-recommend);
  comparing concrete data instances (vacancies, bank statements, recruiters) — data
  analysis, not explanation; «какой вариант лучше / что тут бест практис» → best-approach;
  «исправь / почини / почему падает» about concrete code or tests → debugging;
  «сделай отчёт» → report; web-research task wording («Find on the internet: what is…»);
  plain in-answer explanation covered by the global Explanation Protocol.
argument-hint: "[что объяснить и для кого; --preset child|junior|senior|business, --audience, --detail full|partial|none, --search auto|local|web|none, --structure five|difference|summary-first|direct|brief, --lang ru|en, --no-sources]"
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
| `structure` — порядок изложения | `five` (матрица анатомий: фиксированный набор разделов своего типа объекта, `reference.md` § 1.6) · `difference` (Суть → Ключевые различия → Когда что выбрать) · `summary-first` (TL;DR, потом разделы) · `direct` (сразу на целевом уровне) · `brief` (краткий: расшифровка → что это → зачем) | `five`; «что такое X» → `brief`; «чем отличается X от Y» → `difference` |
| `lang` — язык объяснения | `ru` · `en` (глоссарий терминов всё равно двуязычный) | `ru` |
| `sources` — grounding | `on` (web-факт → URL; код → `file:line`; вывод LLM → цитата; библиотека → Context7/официальная документация) · `off` (`--no-sources`) | `on` |

## Пресеты

| Пресет | audience | detail | structure | Особенности |
|--------|----------|--------|-----------|-------------|
| `child` | child | full | five | Короткие предложения, аббревиатур нет вовсе |
| `junior` (по умолчанию) | junior | full | five | — |
| `senior` | senior | none | direct | — |
| `business` | nontech | full | five | Только термины из реестра, определения бытовым языком |

Пресет задаёт оси по умолчанию; любая ось переопределяется флагом аргумента или естественным языком («объясни как ребёнку» → preset `child`).

## Правила

1. **Без вопросов по осям.** Не хватает оси — берём значение по умолчанию или из пресета, не спрашиваем. Объект не передан — один вопрос: «Что объясняем?».
2. **Строка режима.** Первая строка ответа: `Режим: объект=… · кому=… · детализация=… · поиск=… · структура=… · язык=… · источники=…` — пользователь видит режим и может сменить любую ось.
3. **Реестр терминов (всегда).** До письма зафиксировать реестр: термин → одно определение. В тексте — только формы из реестра; синонимная замена на ходу запрещена («функция» не превращается в «метод»/«процедуру»); новый необходимый термин — сначала в реестр с определением, потом в текст. Проектные запрещённые формы проверяет глоссарий-хук (`claude-home/hooks/glossary.py`) — скилл их не дублирует.
4. **База — глобальный Explanation Protocol** (global CLAUDE.md): обычное русское слово вместо термина, термин только при необходимости, запрет образов и метафор. Скилл добавляет поверх: уровни детализации, реестр, режим.
5. **Гипотезы — флагом.** Не уверен в факте — пометить «предположительно, нужно проверить», не выдавать за факт.
6. **Самопроверка перед выдачей** — чек-лист в `reference.md`.
7. **Автоматический выбор структуры.** «Что такое X / что значит X / объясни X» без иных уточнений → `brief`: расшифровка аббревиатуры обязательна, «что это» и «зачем» — по 1–3 предложения, без вопросов. «Чем отличается X от Y» без иных уточнений → `difference` в краткой форме (суть → 1–2 различия → когда что). Во всех остальных случаях полное объяснение → `five` — матрица анатомий своего типа объекта (`reference.md` § 1.6). `llm-output`, `web-result` и `text` разбираются процедурой фрагментов (§ 1.2) — разделы к ним не применяются. Явный `--structure` сильнее автоопределения.
8. **Приглашение сменить режим.** После строки режима — одно короткое приглашение: «другая аудитория или уровень — скажи»; повторять в каждом ответе не нужно.
9. **Число — только с единицей измерения.** Цифра без единицы («50» без того, что это: проценты, миллисекунды, запросы) — ошибка ответа; процент без базы («N из M») и точки сравнения — ошибка. Опора: global CLAUDE.md → Questions and Numbers (правило чисел); скилл делает его операционным для объяснений.
10. **Rescue-режим.** «Ничего не понимаю / запутался / не понимаю» + фраза намерения («объясни», «с базы», «с нуля», «начиная с базы») → объект берётся из текущего диалога, вопрос «Что объясняем?» не задаётся; `detail=full`, аудитория `junior` (если не указана), анатомия своего типа объекта.

Полная спецификация осей, процедура для `llm-output`, шаблоны по аудиториям и чек-лист — `reference.md`.
