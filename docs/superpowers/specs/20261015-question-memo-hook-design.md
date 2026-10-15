---
feature: question-memo-hook
bd_id: python-ai-skills-r1f.3
date: 2026-10-15
status: draft
risk: medium
risk_justification: one new hook that runs on every user prompt in every project on this machine; advisory only (exit 0, no decision field, about 1.4 KB of text), silent when the section is missing, no contract or schema change. Same as Discovery.
approach: bash-copy
open_questions: []
context7_verified: []
context7_note: no library is involved; the hook is bash + awk + jq (already used by `task-level-inject.sh`), the tests are pytest + stdlib `subprocess`/`json`. Behaviour was probed in this session (prototype in `$TMPDIR`, see 2.3).
requirements: docs/superpowers/specs/20261015-question-memo-hook-discovery.md (FR-1..FR-9 incl. FR-2a, NFR-1..NFR-6, risks 1-10, scope, resolved questions Q1-Q5)
---

# Design: question header, numbers rule and two-score rule delivered by a UserPromptSubmit memo hook (python-ai-skills-r1f.3)

Requirements, hook contract quotes, measurements and risks are in the Discovery spec and are not restated here. This document decides HOW.
Every option below carries the two scores the rule itself prescribes: `X% / Y%`, X = estimated probability that the user chooses the
option (X of all options plus the own-option line sum to 100 %), Y = estimated probability that the option meets FR/NFR without rework.

## 1. Approaches

### 1.1 bash-copy (RECOMMENDED) — 70% / 90%
One new file `claude-home/hooks/question-memo-inject.sh`, a line-for-line sibling of `task-level-inject.sh` (33 lines): one `awk`
cut keyed on the new `## ` heading, one `jq -n` that builds `hookSpecificOutput`, `exit 0` on every path. The `awk` idiom
`'/^## /{inside = /^## <heading>/} inside'` is copied (one line); nothing in `task-level-inject.sh` or its 10 tests changes.
Why the copy and not a shared helper: the duplicated fact is one line; a helper would add a file, a `source` with path resolution,
its own tests and an edit of a shipped hook outside this feature's scope ("Match scope to request"). `principles.md` → KISS lists
"three similar lines replaced by a premature abstraction" as a violation and lets OCP justify an abstraction only for two real
callers; two callers exist, but the abstraction would be longer than the line it removes. Trigger to extract: a third caller
(the glossary delivery, bd `python-ai-skills-du5`). Smallest change meeting FR-3/FR-4/FR-6/NFR-2/NFR-3/NFR-4.

### 1.2 bash-shared-helper — 15% / 80%
`claude-home/hooks/lib/cut-section.sh` with `cut_section <file> <heading>`, sourced by both `task-level-inject.sh` and the new hook.
Pays SSoT for the `awk` line at the price of: a new directory (`hooks/lib/` does not exist; the installer symlinks `hooks/` as a whole,
so no install change, verified by the hooks listing), a `source "$(dirname "$0")/lib/cut-section.sh"` line in each hook, a test for
the helper, and a diff in `task-level-inject.sh` that this feature does not need (FR trace: none). Y is lower because the existing
hook's tests copy the hook file alone into `tmp_path/claude-home/hooks/` (`test_task_level_inject.py:80-97`) — they would break
without also copying `lib/`. Rejected on KISS/YAGNI precedence.

### 1.3 python-hook — 5% / 75%
`question-memo-inject.py` + a `.sh` launcher (pattern `explanation-terms.sh` → `.py`). Python buys nothing here: no regex beyond
`^## `, no transcript parsing, JSON building is one `jq -n`. Costs two files, a `python3 -I` process start per prompt (NFR-2 still met,
but slower than awk + jq), and a second pattern for "cut a section" next to the bash one. Rejected.

### Свой вариант / ни один — 10%
Top X 70 % exceeds the next line (15 %) by 55 percentage points and top Y is 90 % ≥ 80 %: auto-selected under the rule being built.

Secondary axes decided inside 1.1 (each with the same scoring, all above the auto-select threshold):
- Framing line: English, names the file and "the only copy", like `task-level-inject.sh:30` — 70% / 90% (Russian framing 15 %,
  no framing 5 %, own 10 %). The section itself is Russian; the framing only tells the model where the SSoT is.
- Heading name `## Questions and Numbers` — 70% / 90% (Russian «Вопросы и числа» 15 %, `## Question Protocol` 5 %, own 10 %).
  Every `## ` heading of the file is English (21 headings, l.7-292; only First-Contact Protocol has a Russian tail); the existing
  pointer form in the profile is "глобальный CLAUDE.md → Explanation Protocol" (`Gena_Beeline_Local/CLAUDE.md:18`); grep over the repo
  finds no existing use of the string, so the awk key is unique.
- Pointer form in skills, profile and memory: `глобальный CLAUDE.md → Questions and Numbers` (heading, no path, no rule text) —
  70% / 90% (path form `~/.claude/CLAUDE.md → …` 20 %, own 10 %). Matches the precedent above and `best-research/SKILL.md:99`
  ("глобальное правило Output Formatting").
- stdin handling (FR-3 says "prints nothing when … stdin is malformed"): consume stdin and require a JSON object
  (`jq -e 'type == "object"'`) — 60% / 90%; require `.hook_event_name == "UserPromptSubmit"` 25 % / 80 % (would also go silent if a
  harness version omits the field — a silent-failure mode nobody notices, risk 1 of the Discovery); ignore stdin entirely
  5 % / 60 % (contradicts the approved FR-3 wording and leaves the harness writing into a closed pipe on long pasted prompts); own 10 %.
  Probed: empty, `not json`, `[]`, `42` → exit 4/5/1/1 from jq, hook silent, exit 0; `{}` and `{"prompt":"x"}` → delivered.

## 2. Recommended approach in detail

### 2.1 The new section of `claude-home/CLAUDE.md` (FR-1, FR-2, FR-2a, NFR-1, NFR-5)
Inserted after the Output Formatting section (after l.27, before `## Project Classification` at l.29), one blank line on each side.
Measured on the draft file: **1,234 characters (`wc -m`), 10 lines, 2,112 bytes** — the hook cap is 10,000 characters (Discovery quote),
so the memo is 8 times below it; NFR-1 target (< 2,000 characters, ≤ ~20 lines) met. Rendered as `additionalContext` with the framing
line: 1,363 characters. Verbatim text:

```md
## Questions and Numbers

**Rule (шапка вопроса):** каждый вопрос пользователю открывают три строки, затем сам вопрос:
1. **План:** все задачи по порядку (1–3 строки).
2. **Сейчас:** какая задача и какой её шаг или вопрос из скольких.
3. **Цель вопроса:** что решает ответ.

**Rule (числа):** у каждого числа есть единица измерения. У каждого процента названы база («N из M») и точка сравнения (с чем сравниваем). Действует в чате и в любом тексте для пользователя — отчёт, задача в трекере, CHANGELOG, документация — на любом языке.

**Rule (две оценки варианта):** каждый вариант в любой рекомендации (все `best-*`, открытые вопросы do-feature, любой другой вопрос с вариантами) несёт две оценки в форме `X% / Y%`: X — вероятность того, что пользователь выберет этот вариант; Y — вероятность того, что вариант выполнит критерии приёмки задачи без переделки. Значения X всех вариантов плюс строка «Свой вариант / ни один — N%» в сумме дают 100 %; значения Y независимы. Автоматический выбор — только когда X лучшего варианта превышает X следующей строки (строка «Свой вариант» тоже конкурент) не менее чем на 20 процентных пунктов — разность значений X, не относительный прирост — И Y лучшего не ниже 80 %. Во всех остальных случаях, а также в точках утверждения пользователем (USER APPROVAL) — вопрос пользователю.
```

Wording notes: `**Rule (<name>):**` follows the Naming section (`**Rule (N-BRANCH):**`, l.76) rather than the bare `**Rule:**` of
Output Formatting, so the three rules can be cited by name. No backticked single Latin word appears (Discovery risk 6: the
`explanation-terms` Stop hook); `X% / Y%` and `best-*` contain `/` or `*` and the file is tracked, so they count as real either way.
"20 процентных пунктов — разность значений X, не относительный прирост" makes points vs percent unambiguous (bd r1f.3 note:
"assumption: points, not relative %"). Nothing in the section names the hook or the file: that text would be re-sent on every prompt
for no gain; it lives in the appendix (2.2) and the hook header comment.

### 2.2 `claude-home/CLAUDE-APPENDIX.md` paragraph
The appendix mirrors the section order with one `**Почему:**` paragraph per heading (l.6-14 verified). Insert after the Output
Formatting paragraph (l.12), before `## Project Classification` (l.14):

```md
## Questions and Numbers

**Почему:** вопрос приходит пользователю посреди длинной работы, часто после паузы: без строк «План / Сейчас / Цель вопроса» он восстанавливает контекст по переписке. Число без единицы и процент без базы («18 %» вместо «3 из 17») нельзя ни проверить, ни сравнить. Две оценки варианта разделяют два вопроса, которые прежний «процент уверенности» сливал в один: выберет ли пользователь (X — распределение одного выбора, поэтому сумма 100 %) и сработает ли вариант (Y — независимые вероятности). Строка «Свой вариант / ни один» внутри 100 % не позволяет раздать всю сумму только перечисленным вариантам. Порог автоматический выбора (разрыв по X не менее 20 процентных пунктов И Y не ниже 80 %) заменяет прежнее «выше 80 % уверенности» из профиля пользователя и авто-памяти (решения пользователя 2026-10-15, bd `python-ai-skills-r1f`, `python-ai-skills-ao1`). Доставка: раздел читается при старте сессии и повторяется перед каждым ответом хуком `hooks/question-memo-inject.sh` (UserPromptSubmit), потому что CLAUDE.md сессия читает только при старте (python-ai-skills/CLAUDE.md → «Live immediately has one exception»). Проверка после ответа (Stop) отвергнута: она заставляет модель писать второе сообщение (bd `python-ai-skills-r1f.1`).
```

### 2.3 The hook `claude-home/hooks/question-memo-inject.sh` (FR-3, NFR-2, NFR-3, NFR-4)
- Name: `question-memo-inject.sh` (siblings: `task-level-inject.sh`, `principles-inject.sh`); test `test_question_memo_inject.py`.
- Env override: `QUESTION_MEMO_FILE` (precedents `TASK_LEVELS_FILE`, `PRINCIPLES_FILE`); default `$(dirname "$0")/../CLAUDE.md`
  (installed layout `<claude home>/hooks/<hook>` next to `<claude home>/CLAUDE.md`, `task-level-inject.sh:13-14,20`).
- stdin: consumed and required to be a JSON object (1.1 axis); nothing else is read — UserPromptSubmit has no matcher and the memo
  does not depend on the prompt text. No opt-out variable (Discovery scope OUT; `DELEGATION_NUDGE=off` is the precedent if needed later).
- Output: `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "<framing>\n\n<section>"}}`, no
  `decision`, no `systemMessage`, nothing on stderr (`2>/dev/null` on jq and awk as in the pattern).
- Framing line: `Rules for questions, numbers and option scores from <file> (the only copy). Apply them to this answer:` followed by
  a blank line and the section.
- Exit codes: 0 on every path (NFR-3). Silent paths: stdin not a JSON object; file missing, unreadable or a directory; section absent.
- Header comment states the contract like `task-level-inject.sh:1-16` (why a hook: CLAUDE.md read only at session start; glossary
  extension bd du5 noted as future, not built).
- Body (prototype run in `$TMPDIR` in this session against a copy of the real `claude-home/CLAUDE.md` with the section inserted:
  0.012 s wall time, exit 0, 1,363-character context, the previous and the next section not leaked):

```bash
set -uo pipefail

FILE="${QUESTION_MEMO_FILE:-$(dirname "$0")/../CLAUDE.md}"
jq -e 'type == "object"' >/dev/null 2>&1 || exit 0
[ -f "$FILE" ] && [ -r "$FILE" ] || exit 0

SECTION=$(awk '/^## /{inside = /^## Questions and Numbers/} inside' "$FILE" 2>/dev/null)
[ -n "$SECTION" ] || exit 0

jq -n --arg s "$SECTION" --arg f "$FILE" '{
  hookSpecificOutput: {
    hookEventName: "UserPromptSubmit",
    additionalContext: ("Rules for questions, numbers and option scores from \($f) (the only copy). Apply them to this answer:\n\n" + $s)
  }
}'
exit 0
```

### 2.4 `claude-home/settings.json.template` entry (FR-4)
Third handler in the existing `UserPromptSubmit` group (after `git-finish-router.sh`; the group's `matcher: "*"` stays as is):

```json
{
  "type": "command",
  "command": "'{{CLAUDE_HOME}}/hooks/question-memo-inject.sh'",
  "timeout": 3
}
```

`test_every_hook_path_is_one_shell_word` (`scripts/test_install_claude_symlinks.py:57-64`) and `settings-template-json` cover it with
no new test. After the edit: `make install-symlinks` re-renders the live `settings.json`.

### 2.5 Tests `claude-home/hooks/test_question_memo_inject.py` (FR-6, risk 1, NFR-1)
Same harness as `test_task_level_inject.py` (`bash <hook>`, `env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent",
"QUESTION_MEMO_FILE": …}`, synthetic `DOC` with `PREVIOUS-SECTION` / `NEXT-SECTION` markers around a stub
`## Questions and Numbers` section — the fixture carries a marker string, never the rule text, NFR-4):
1. `test_prompt_gets_the_memo_section` — `{"hook_event_name": "UserPromptSubmit", "prompt": "hi"}` → exit 0, `hookEventName ==
   "UserPromptSubmit"`, marker in `additionalContext`, `"decision" not in out`, framing contains the file path.
2. `test_only_the_memo_section_is_cut` — no `PREVIOUS-SECTION`, `NEXT-SECTION`, `## Project Classification` in the context.
3. `test_missing_file_is_silent`.
4. `test_file_without_the_section_is_silent`.
5. `test_directory_instead_of_file_is_silent` — stdout and stderr both empty.
6. `test_malformed_input_degrades_to_silence` — parametrized `""`, `"not json"`, `"[]"`, `"42"`.
7. `test_default_file_is_next_to_the_hooks_dir` — hook copied to `tmp_path/claude-home/hooks/`, `CLAUDE.md` one level up, no env override.
8. `test_real_claude_md_has_one_memo_section_under_the_cap` — the guard (Q4): reads `REPO / "claude-home" / "CLAUDE.md"` (precedent
   `test_principles_ssot.py` reads the real SSoT file), asserts exactly one line equals `## Questions and Numbers`, and that the cut
   section is ≤ 2,000 characters (`len(str)`, not bytes — the cap is in characters) and ≤ 20 lines (precedent
   `test_ssot_file_stays_short_enough_to_inject`, ≤ 70 lines). Scored: heading + size guard 60% / 90%, heading only 30 % / 85 %,
   own 10 % — auto-selected. Limits are two named constants at the top of the file.
9. `test_hook_stays_silent_on_stderr_for_the_real_file` is NOT added — covered by 5 and 8 together.

### 2.6 Makefile
`test:` target (l.20-34): add `claude-home/hooks/test_question_memo_inject.py \` after the `test_task_level_inject.py` line.
The pre-commit `hook-regression-tests` collects it without a change.

### 2.7 Skill pointers (FR-5, NFR-4) — exact replacement text
Pointer phrase everywhere: `глобальный CLAUDE.md → Questions and Numbers`. No skill repeats the meaning of X or Y, the 100 % rule or
the threshold. Placeholder collision fixed on the way: `X` / `Y` as free placeholders («предположительно X», «Вариант X») would now
read as the scores — renamed to `A` / `B` and `{k}`.

**`best-recommend/SKILL.md`**
- l.5-7 (description): `Confidence expressed as %, explained like to a junior, each % backed by a one-line source, and an honest hypothesis-flag the moment there is doubt.` →
  `Two scores per option, written X% / Y% as defined in the global CLAUDE.md section "Questions and Numbers", explained like to a junior, each score backed by a one-line source, and an honest hypothesis-flag the moment there is doubt.`
- l.17: `> SSoT того, КАК подавать одну рекомендацию: проценты + объяснение как джуну + источник + честный флаг неуверенности.` →
  `> SSoT того, КАК подавать одну рекомендацию: оценки `X% / Y%` + объяснение как джуну + источник + честный флаг неуверенности.`
- l.29: →
  `1. **Две оценки на вариант.** Каждый вариант несёт пару `X% / Y%`; смысл X и Y, сумма 100 % со строкой «Свой вариант / ни один» и порог автоматический выбора заданы в одном месте — глобальный CLAUDE.md → Questions and Numbers; здесь не повторяются. Близкие варианты — назвать близкими явно, не подгонять разброс.`
- l.33: `3. **Источник к каждому проценту.** Каждый % сопровождай` → `3. **Источник к каждой оценке.** Каждую пару `X% / Y%` сопровождай` (rest of the line unchanged).
- l.39-46 (template):
  ```text
  ## 💡 Рекомендация
  **Вариант A — X% / Y%** — {почему основной выбор; источник: <best practice / docs / file:line>}
  **Вариант B — X% / Y%** — {в каких условиях лучше он; источник}
  **Вариант C — X% / Y%** — {edge case; источник}
  **Свой вариант / ни один — N%**

  {Автоматический выбор или вопрос пользователю — по порогу: глобальный CLAUDE.md → Questions and Numbers.}
  {Если есть неуверенность — явный флаг: «предположительно A, требует проверки B».}
  ```
- l.58 (reuse line): →
  `Формат рекомендации — по `/best-recommend`: оценки `X% / Y%` (глобальный CLAUDE.md → Questions and Numbers) + как джуну + источник к каждой оценке + честный флаг гипотезы при сомнении.`

**`best-rank/SKILL.md`**
- l.6-8 (description): `then score every option 0–100% as its probability of acceptance and rank from highest to lowest. Thin wrapper over best-research — its specialization is taking a ready list and ranking by %.` →
  `then give every option the two scores X% / Y% of the global CLAUDE.md section "Questions and Numbers" and rank by X from highest to lowest. Thin wrapper over best-research — its specialization is taking a ready list and ranking by X.`
- l.19: `проставлю каждому вероятность принятия 0–100% и отранжирую.` → `проставлю каждому две оценки `X% / Y%` (глобальный CLAUDE.md → Questions and Numbers) и отранжирую по X.`
- l.29: `3. **Оцени и отранжируй по %** — каждому варианту (исходному + добавленному) процент вероятности принятия 0–100% (по формату `best-recommend`), сортировка по % убыв.` →
  `3. **Оцени и отранжируй по X** — каждому варианту (исходному + добавленному) пара `X% / Y%` по формату `best-recommend`, плюс строка «Свой вариант / ни один — N%»; сортировка по X убыв.`
- l.34: `проценты различимы` → `значения X различимы`; l.35: `по % убыв` → `по X убыв`.
- l.48-54 (output template):
  ```text
  ### Рейтинг (от высшего X к низшему)
  **1. {Название} — X% / Y%** [исходный | добавлено]
  {Описание}
  ✅ Усиливает: ... ❌ Нарушает/риски: ... 🚩 Red flags: ...
  Почему X% / Y%: {1–2 предложения, источник}

  **2. {Название} — X% / Y%** ...
  **Свой вариант / ни один — N%**
  ```
- l.65: `пересчитай % для гибрида` → `пересчитай `X% / Y%` для гибрида`. l.69 and l.72 unchanged ("рейтинг по вероятности" stays true).

**`best-research/SKILL.md`**
- l.7-8 (description): `and rank them with confidence % delivered via the best-recommend format.` →
  `and score them X% / Y% (global CLAUDE.md section "Questions and Numbers") delivered via the best-recommend format.`
- l.20: `дать варианты + % → рекомендовать` → `дать варианты + `X% / Y%` → рекомендовать`.
- l.60: →
  `Подай по формату `/best-recommend`: **оценки `X% / Y%` + объяснение как джуну + источник к каждой оценке + честный флаг гипотезы при сомнении**. Смысл оценок, строка «Свой вариант / ни один» и порог автоматический выбора — глобальный CLAUDE.md → Questions and Numbers; отдельной шкалы нет.`
- l.90: `{блок по формату /best-recommend: % + как джуну + источник + флаг гипотезы}` → `{блок по формату /best-recommend: X% / Y% + как джуну + источник + флаг гипотезы}`.
- l.96: `Pros/Cons и проценты честные` → `Pros/Cons и оценки честные`.

**`best-questions/SKILL.md`**
- l.5 (description): `and STOP after each for the user's choice.` → `and STOP after each for the user's choice unless the auto-select threshold of the global CLAUDE.md section "Questions and Numbers" is met.` (l.6-7 "hard stop after every one" → "hard stop after every one that is not auto-selected").
- l.18: `СТОП после каждого, жду ответ.` → `СТОП после каждого (кроме автоматического выбора по порогу — глобальный CLAUDE.md → Questions and Numbers), жду ответ.`
- l.27: `рекомендация по формату `best-recommend` (проценты)` → `рекомендация по формату `best-recommend` (оценки `X% / Y%`)`.
- l.36-40 (block): line `## Вопрос i/N: {текст вопроса}` is preceded by `{шапка вопроса — глобальный CLAUDE.md → Questions and Numbers}`;
  l.38: `Рекомендация (% по формату best-recommend)` → `Рекомендация (`X% / Y%` по формату best-recommend, со строкой «Свой вариант / ни один»)`.
- l.44: `**СТОП.** Жди ответ. НЕ переходи к следующему вопросу.` →
  `**СТОП** — жди ответ, НЕ переходи к следующему вопросу. Исключение — автоматический выбор по порогу (глобальный CLAUDE.md → Questions and Numbers): показать разбор, пометить выбранный вариант «[выбран автоматически]» и идти дальше.`
- l.47 add after: `- **Автоматический выбор** → записать как решение с пометкой «[выбран автоматически]», к следующему вопросу.`
- l.59: `1. **{Вопрос}** → Вариант X: {решение}` → `1. **{Вопрос}** → Вариант {k}: {решение} [автоматический выбор | выбор пользователя]`.
- l.69: `2. **СТОП после каждого** — жди ответ.` → `2. **СТОП после каждого** — жди ответ; единственное исключение — автоматический выбор по порогу из глобального CLAUDE.md → Questions and Numbers.`
- l.74: `формат варианта, % рекомендация` → `формат варианта, оценки `X% / Y%``.

### 2.8 Profile and auto-memory (FR-9)
- `~/ai-steward/Gena_Beeline_Local/CLAUDE.md:25-26` → one item:
  `3. Автоматический выбор варианта в `/best-questions` и в любой другой рекомендации — только по порогу из глобального CLAUDE.md → Questions and Numbers; своих порогов здесь нет.`
- `~/.claude/projects/-home-bgs-ai-steward-Gena-Beeline-Local-python-ai-skills/memory/best-questions-auto-select-80.md`: keep the file
  name (the index links it) and the frontmatter keys; `description:` → `"Superseded: option auto-select is the X% / Y% rule of the global CLAUDE.md section 'Questions and Numbers'; this memory only points there."`; `modified:` → today; body replaced by:
  `Superseded 2026-10-15 (bd python-ai-skills-r1f.3): the ">80 % confidence" threshold is replaced by the two-score rule written X% / Y% in claude-home/CLAUDE.md → "Questions and Numbers" (loaded at session start and re-sent before every answer by claude-home/hooks/question-memo-inject.sh). Do not apply the old threshold; the profile item 3 points to the same section.`
- `MEMORY.md` index line 6 → `- [best-questions auto-select >80%](best-questions-auto-select-80.md) — superseded: option auto-select is the X% / Y% rule in global CLAUDE.md → Questions and Numbers; the file is a pointer only.`

### 2.9 CHANGELOG `## [Unreleased]` → `### Added` (FR-8), draft
`claude-home/CLAUDE.md`: new `## Questions and Numbers` section (bd `python-ai-skills-r1f.3`, answers `python-ai-skills-ao1`) — every question to the user opens with «План / Сейчас / Цель вопроса»; every number carries a unit and every percentage its base («N из M») and comparison point, in chat and in every text written for the user; every option in a recommendation carries two scores `X% / Y%` (X = probability the user chooses it, X of all options plus «Свой вариант / ни один — N%» sum to 100 %; Y = probability it meets the acceptance criteria without rework), auto-select only at a gap of ≥ 20 percentage points in X over the next line and Y ≥ 80 %. Delivered before every answer by `claude-home/hooks/question-memo-inject.sh` (`UserPromptSubmit`, cuts the section at run time, silent otherwise, 1,234 characters / 10 lines, 0.01 s), wired in `settings.json.template`; Codex gets it through `~/.codex/AGENTS.md`. `best-recommend`, `best-rank`, `best-research`, `best-questions` drop their own percentage meanings (`need not sum to 100`, `probability of acceptance`, the 85/50/20 scale) and point to the section; the profile item 3 and the auto-memory `best-questions-auto-select-80.md` become pointers. Guard test reads the real file (heading present once, ≤ 2,000 characters, ≤ 20 lines). <N> tests, in `make test`.

### 2.10 Verification in Execution (Discovery scope IN)
1. `make test` (baseline 473 of 473) → 473 + new tests; `ruff check claude-home/hooks/` unchanged at the 1 pre-existing error.
2. `python3 -c 'import json; json.load(open("claude-home/settings.json.template"))'` and `make install-symlinks` (re-render), then
   `jq '.hooks.UserPromptSubmit[0].hooks | length' ~/.claude/settings.json` → 3.
3. Live: a fresh `claude --debug` session, type `/best-questions` with one question → the first question starts with «План:» and the
   debug log has the hook's `Hooks: UserPromptSubmit` line (risk 5 hypothesis checked in passing).
4. `codex debug prompt-input` outside the sandbox from this repo (Q5): record whether the new section (about 2 KB into the file) and the
   last section of `claude-home/CLAUDE.md` both appear.
5. `grep -rn 'вероятность принятия\|не обязаны суммироваться\|85–100%' best-*/SKILL.md` → empty (FR-5 evidence).

## 3. Notes for Execution (facts found while designing)
1. This session's Bash sandbox lists `claude-home/hooks`, `claude-home/CLAUDE.md`, `claude-home/output-styles` and `~/.claude/projects`
   under write `denyWithinAllow`. Shell writes (`cat > …`, `sed -i`) into those paths fail inside the sandbox; the Edit/Write tools go
   through the permission system instead and were not probed here. Plan the edits with Edit/Write, not with shell redirects.
2. The memo is injected as a system reminder, so its words count as non-assistant evidence for `explanation-terms` (Discovery risk 6);
   the section itself contains no backticked single Latin word, so nothing in it can trigger a correction line either way.
3. Discovery "Cost of the memo" measured a 753-character / 10-line draft without FR-2a; the FR-2a draft is 1,234 characters / 10 lines
   (2,112 bytes). Token estimate scales to roughly 350-410 tokens per prompt at 3.0-3.5 characters per token; at p90 (15 prompts)
   about 6,000 tokens resident — still about 2.4 % of the 246k-token request size the Discovery cites. The 10,000-character cap is a
   character count, so the byte size above 2,000 is irrelevant to it; the guard test therefore measures `len()` of the decoded text.
4. No fact in the Discovery document was contradicted by this session's checks: line references into the four skills, the template's
   `UserPromptSubmit` group (two handlers, `timeout: 3`), `claude-home/CLAUDE.md` size (351 lines, 38,044 bytes), the Makefile list
   (l.20-34) and the appendix layout all match.
