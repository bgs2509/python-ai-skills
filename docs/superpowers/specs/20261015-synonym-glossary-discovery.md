---
feature: synonym-glossary
bd_id: python-ai-skills-du5
date: 2026-10-15
status: approved
risk: medium
risk_justification: one new check that reads every assistant message (Stop hook) AND the changed lines of every commit (pre-commit) in every project that has a glossary, edits to the global CLAUDE.md, to two generator skills and to the explanation-terms Stop hook, plus a one-off conversion of a 629-row glossary; everything stays advisory (exit 0, no block), reversible and schema-free, but it runs on every project on this machine and uses the one hook shape (Stop) the user has already pushed back on.
evidence: strong
evidence_justification: bd du5 and r1f/r1f.1 read with `bd show`; the global CLAUDE.md sections, both memo hooks, the explanation-terms hook and its tests read in full; prior-art glossary in Local_LLM_selection parsed with the same three regexes vocab.py uses (counts measured), its ending regex probed on 25 inflected and near words, its tests counted; three more neighbouring projects' glossary sections read; the hook journal counted with python3 (151 of 154 records); the hooks and memory pages of code.claude.com fetched 2026-10-15 and quoted; Vale, TBX/termbase and LLM-terminology sources from one web search each (vendor docs and arXiv, not peer-reviewed benchmarks).
open_questions: []
---

# Discovery: per-project synonym glossary that agents check before naming things to the user (python-ai-skills-du5)

## Decisions (user, 2026-10-15, after the first draft of this document)

1. **Q1 governed text = (c):** chat prose, every text written for the user (docs, bd issue text, CHANGELOG, reports) AND code
   strings, comments and HTML. Code **identifiers** stay exempt (Language rule, `claude-home/CLAUDE.md:9`: identifiers in English);
   the file check skips identifiers and quoted forbidden forms (the glossary's own lines, verbatim quotes).
2. **Q2 check location = both:** a Stop hook on `last_assistant_message` that asks one line per finding in the form
   `Поправка к термину: «X» → «Y»` and journals to `blocks.jsonl` (the `explanation-terms` shape), AND a pre-commit check on the
   changed lines of files.
3. **Q3 global layer = LATER:** per-project glossaries only; a group is promoted to a global layer once it repeats in 3 projects.
4. **Q4 carrier:** a `## Glossary` section inside the project `AGENTS.md`; when the glossary exceeds 200 lines, a separate file plus
   one pointer line in `AGENTS.md`.
5. **Q5 entry fields:** forbidden forms → canonical term; definition and source optional (auto-selected by the threshold of the global
   CLAUDE.md → Questions and Numbers; the user may revise at Step 3).
6. **Q6 existing glossary projects:** `ML_Sobes_2026/glossary.md` (four-column table `Основной термин | English | Синонимы (не
   употреблять) | Кратко`, 629 rows → stays a separate file with a pointer, per Q4) is converted inside du5 by a one-off script after
   Step 4 and becomes the second sample project. `Local_LLM_selection` (its `vocab.py` parses the current headings, 44 tests; its
   section «Никогда не общее слово — всегда точное» has qualification semantics that do not fit forbidden → canonical) and the
   `spark-public-bot` pointer go to a separate bd task executed inside `Local_LLM_selection` (global Security rule: from this
   repository only `*.md` files outside `$PWD` may be edited).

Finding recorded, out of scope: `Local_LLM_selection/AGENTS.md` (5,926 bytes) and `Local_LLM_selection/CLAUDE.md` (29,735 bytes)
are two separate regular files, not a symlink (ls 2026-10-15), against the Project Classification rule "`CLAUDE.md` is a symlink
to it" (`claude-home/CLAUDE.md:42`); `ML_Sobes_2026/CLAUDE.md -> AGENTS.md` is a symlink as required. The separate bd task for
`Local_LLM_selection` must decide which file carries its glossary before converting anything.

## Intent

### Literal request (bd `python-ai-skills-du5`, description and acceptance criteria)

Claude Code "keeps mixing synonyms and inventing new terms, e.g. calling the same thing 'table', 'register', 'registry',
'sector'". Each project needs "a glossary of synonym groups with one canonical term per group; in conversation with the user the
agent always checks the glossary and uses only the canonical term". Acceptance: (1) a glossary file exists in a sample project;
(2) a session in that project uses only canonical terms from it; (3) a check (hook or validator) flags a forbidden synonym in an
assistant message; (4) generators create the file for new projects. The description lists the open design points: file name and
location, how it is loaded (AGENTS.md import vs separate file), format (canonical term + forbidden synonyms + definition + source),
how agents consult it (instruction vs hook check on the final message), bootstrap for existing projects (`_init` / `grace-init`).

### Real goal

The user reads answers across 90 project directories (40 of them with an `AGENTS.md`, 40 with a `CLAUDE.md`; counted 2026-10-15
in `~/ai-steward/Gena_Beeline_Local`) and pays a comprehension cost each time one thing gets a new name. The global rule already
exists as discipline: "Одно явление — одно обозначение на весь ответ и всю сессию ... Заменять синонимом ради разнообразия —
дефект" (`claude-home/CLAUDE.md:131`). What is missing is the **data** that rule needs: a per-project list that says which
designation is the one. Without the list every session picks a designation afresh, and two sessions pick two. The glossary turns
a discipline rule into a file a model can read before answering and a check can read after.

### Unstated assumptions (made explicit)

1. The glossary governs **Russian prose** to the user. The complaint words are Russian in practice (the prior-art lists are
   Cyrillic: «запись», «служба», «разборщик»); code identifiers, commit messages and YAML keys stay English by the Language rule
   (`claude-home/CLAUDE.md:9`). `spark-public-bot/AGENTS.md:68-70` already states the split: "Русский словарь правит русский
   текст ... Комментарии в коде пишутся по-английски."
2. "Per project" means **per domain**. `spark-public-bot/AGENTS.md:43-46` does not copy the glossary of `Local_LLM_selection`;
   it points at it by absolute path: "Он лежит в `.../Local_LLM_selection/CLAUDE.md`, раздел 1, и здесь не дублируется —
   дубликат разошёлся бы с оригиналом." One domain, two repositories, one glossary.
3. The user's four example words are **generic**, not domain words. Groups such as «таблица / реестр / регистр» recur in many
   projects, which argues for a global layer (decided LATER in Q3: promoted once a group repeats in 3 projects) that per-project
   glossaries extend or override — the shape the Naming section
   already defines: "its own `AGENTS.md` gets a `## Naming overrides` section with lines `<ID>: <project rule>`; a listed ID
   replaces the global rule in that project, unlisted IDs stay global" (`claude-home/CLAUDE.md:85`). No project uses that
   section yet (grep over 40 `AGENTS.md`/`CLAUDE.md` files, 0 hits).
4. "A session uses only canonical terms" is a **model-behaviour** criterion; the research below says prompt-level glossaries are
   followed only partly, so the check (criterion 3) is the real gate, not an optional extra.

### Blind spots

1. **Russian inflection.** A forbidden noun appears in six or more case forms. The prior-art checker handles this with a
   stem-plus-ending regex (`vocab.py:167-178`, `_ENDINGS` of 27 endings). Probe 2026-10-15 on that regex: «таблица», «таблицы»,
   «таблицу», «таблицей», «таблицах», «таблиц» all match (6 of 6); «табличный», «таблично» do not (adjective/adverb, correct);
   «записать», «записка» do not match «запись» (correct); but «таблица-сводка» matches and «DNS-запись» does not, because the
   lookbehind `(?<![а-яёa-z0-9_-])` excludes a hyphen on the left only. Compounds are a known edge in both directions.
2. **Legitimate occurrences of a forbidden word**: a code identifier (`registry.jsonl`), a column name, a quote from a source
   document or from the user, English prose, a bd issue title written earlier. The prior art answers with per-exception sources
   (`vocab.py:67-72`, 3 entries, each with "source of the exception") plus 10 qualification patterns (`vocab.py:74-85`) and a test
   that every exception names its source (`test_vocab.py:118`). Any new check needs at least: skip fenced code, inline backticks,
   quoted spans; and an exception list with a source per line.
3. **Which text is governed** (decided in Q1: the widest option). Chat; docs, bd issue text, CHANGELOG (the Questions-and-Numbers
   rule's scope "в чате и в любом тексте для пользователя", `claude-home/CLAUDE.md:36`); and code strings, comments and HTML, as
   `Local_LLM_selection` does (`vocab.py` scans `DGX_Spark/numbers/*.py` and `speed-tables.html`). Each widening adds false
   positives — hence the identifier and quote exemptions of FR-6.
4. **How the glossary reaches a running session.** `CLAUDE.md`/`AGENTS.md` are read at session start only (code.claude.com/docs/en/memory:
   "Both are loaded at the start of every conversation"; project rule "Live immediately has one exception" in
   `python-ai-skills/CLAUDE.md`). The repo's answer is a `UserPromptSubmit` memo hook that cuts a section at run time
   (`claude-home/hooks/question-memo-inject.sh:24-36`, 36 lines); that hook's header already reserves the slot: "A per-project
   glossary delivery (bd python-ai-skills-du5) may reuse this hook later; it is not built" (`question-memo-inject.sh:10-11`).
   A per-project glossary needs the project path: the UserPromptSubmit input carries `cwd` (docs example, fetched 2026-10-15).
5. **Size varies 20x between projects.** `Local_LLM_selection/CLAUDE.md` holds 29 glossary items; `ML_Sobes_2026/glossary.md`
   holds 629 term rows in 19 tables (667 table lines minus 19 header and 19 separator rows; recounted by the orchestrator, the first draft said 599), 750 lines, 112.4 KB. A hook's
   `additionalContext` is capped at 10,000 characters per hook (r1f.3 discovery quote of the hooks page). Re-sending a whole
   glossary per prompt is possible for the first project and impossible for the second.
6. **Codex has no hooks and expands no imports**: "Codex reads `~/.codex/AGENTS.md` as a single file, expands no `@`-imports"
   (`python-ai-skills/CLAUDE.md` -> Multi-machine consistency) and stops its instruction chain at 32 KiB (r1f.3 discovery risk 7);
   `claude-home/CLAUDE.md` is already 40,682 bytes (wc 2026-10-15). A glossary outside the project `AGENTS.md` text is invisible to
   Codex; a global glossary section in `claude-home/CLAUDE.md` lands after the cap.
7. **Interaction with the existing coined-term hook.** `explanation-terms.py` counts a word as real when it appears in
   `<cwd>/CLAUDE.md` or `<cwd>/AGENTS.md` (`explanation-terms.py:131-133`) or in any file git tracks in the repository
   (`explanation-terms.py:211-226`). Listing a forbidden Latin-script synonym in a glossary file therefore **whitelists** it for
   that hook. The two checks need a precedence rule (glossary "forbidden" beats "found in repo"), or the glossary lines must be
   excluded from the evidence corpus.
8. **Partial compliance even when the glossary is in context.** A localisation team's report (LinkedIn, anecdotal) says that
   after glossary prompts, inline injection and lower temperature "roughly 1 to 2 in every 6 terms still deviated"; the WMT 2025
   Terminology shared task and the Cohere CAT+ report treat terminology adherence as a measured property, with negative glossary
   entries added "because a model that copies every glossary entry would otherwise score well" (arXiv 2609.13916). The glossary
   alone will not satisfy acceptance criterion 2; the check and a journal are what make compliance visible.

## Prior art in the user's own projects (measured 2026-10-15)

1. **`Local_LLM_selection/CLAUDE.md`** (374 lines). Section `# 1. Словарь. Одно понятие — одно слово` (l.15) with subsections
   `## Никогда не общее слово — всегда точное` (l.21), `## Запрещённые слова, добавленные 08.09.2026` (l.144), `## Слова отбора,
   принятые до этого файла` (l.165), `## Запрещённые слова` (l.176), `## Оговорка о старых текстах` (l.203). Entry form
   `N. «forbidden form» → **canonical term**`. Parsed with the checker's own three regexes (`vocab.py:110-112`): 8 generic-noun items
   (10 forms: «ключ», «запись», «порт», «путь», «файл», «конфиг», «слово», «строка», «сервис», «туннель»), 21 forbidden items
   (26 forms), 20 of 21 with a bold replacement, 1 of 21 citing a source or date in its text, 0 of 21 with a definition field.
   The file also records a migration decision: old texts keep forbidden words («размышление» — 172 раза, «шаблон» — 57), "Словарь
   обязателен для нового текста. Сплошная замена по старым документам — отдельная работа" (l.205-212).
2. **`Local_LLM_selection/DGX_Spark/numbers/vocab.py`** (432 lines, v1.1.0). Reads the two headings above (`_FORBIDDEN_HEADING`,
   `_GENERIC_HEADING`, l.61-62), parses items (`_section_lines` l.115, `load_vocabulary` l.136), matches with the ending regex
   (`_ENDINGS` l.167, `_word_regex` l.170, `_form_regex` l.175, `scan_text` l.191), scans code, HTML and the changed lines of
   generated reports (`--staged`, index against HEAD), prints `СЛОВАРЬ <path>:<line>: «form» запрещено → «replacement»`, exits 0/1/2
   (`main` l.379). Wired as pre-commit id `vocab-check`, `entry: python3 DGX_Spark/numbers/vocab.py --staged`
   (`Local_LLM_selection/.pre-commit-config.yaml:10-15`). Tests: `DGX_Spark/numbers/tests/test_vocab.py`, 471 lines, 44 test
   functions, including `test_real_repository_has_no_vocabulary_findings` (l.290) that scans the live repository. **Portability:**
   it imports `model`, `reports`, `statuses` (`vocab.py:45-47`) — project modules; the reusable core (section parsing + ending regex
   + `scan_text`, about 70 lines) is project-free, the other about 360 lines are report plumbing. Lemmatisation is not used; no
   external dependency.
3. **`ML_Sobes_2026/glossary.md`** (750 lines, 112.4 KB): table form `| Основной термин | English | Синонимы (не употреблять) |
   Кратко |`, 629 term rows in 19 tables + a `## Спорные выборы` section (l.729). Rule in `ML_Sobes_2026/AGENTS.md:103`: "употреблять
   **только основной термин** из словаря; синонимы — не употреблять. Перед каждым вопросом, эталоном или объяснением сверяться со
   словарём. Нового понятия в словаре нет — добавить строку". No checker (grep for `glossary` in `*.py`, `*.sh`, `*.yaml` of that
   project: 0 files). It has the definition column the first prior art lacks.
4. **`spark-public-bot/AGENTS.md:43-70`** (`## 2. Словарь`): imports the `Local_LLM_selection` glossary by path, repeats 6 of the
   most frequent terms with "Не «модель», не «запись»" style negatives, and restates the generic-noun ban. Evidence for a shared
   glossary and for reference-not-copy.
5. **`Bio-Chem-Career-2026/AGENTS.md:23-29`** (`## Терминология баллов`): a two-term disambiguation («минимальные баллы» vs
   «проходной балл») with a classification rule "по последствию" — a glossary entry that needs a definition, not only a synonym list.

Four projects, three formats (numbered «» → **bold** list; four-column table; prose list with negatives). Any new format either
parses the first (so `Local_LLM_selection` keeps its checker and its file) or that project is migrated. Decided in Q6: the table
form of `ML_Sobes_2026` is converted inside this feature (FR-14); `Local_LLM_selection` and the `spark-public-bot` pointer wait for
a separate task (FR-15).

## Existing contracts this feature touches

1. **Explanation Protocol** (`claude-home/CLAUDE.md:116-155`): the principle (one designation, l.131; terms checked by verbatim form,
   l.133; source per introduced term, l.143) and the hook-level line (l.153) describing `explanation-terms.sh`. The glossary rule must
   be added, not restated (SSoT rule in Preferences, `claude-home/CLAUDE.md:246`).
2. **Naming** (`claude-home/CLAUDE.md:83-91`): the per-project override contract (l.85) with IDs (`N-BRANCH`, `N-DOCS`, `N-PY`) and the
   line "Skills and checks that name things read both" — the natural home for a glossary rule ID once the global layer exists
   (LATER by Q3).
3. **Questions and Numbers** (`claude-home/CLAUDE.md:29-38`): delivered per prompt by `question-memo-inject.sh`; sets the precedent for
   "rule lives once, hook cuts it at run time" and for the scope wording "в чате и в любом тексте для пользователя" (l.36).
4. **`explanation-terms.py`** (278 lines) + `explanation-terms.sh` (3 lines) + `test_explanation_terms.py` (175 lines, 12 test
   functions): Stop hook, Russian-prose filter (at least 200 letters, Cyrillic share >= 30 %, l.74-90), two candidate shapes — hyphenated
   Latin compounds and single backticked Latin words (l.76-77, 93-115) — evidence corpus = session non-assistant text + instruction
   files + git grep (l.118-226); never blocks, asks one line per word (l.256-268); journals to `~/.claude/hook-stats/blocks.jsonl`
   (l.45-59). Deliberately does not detect Russian jargon: "formally indistinguishable from any other Russian word, so it stays on the
   rule in CLAUDE.md" (l.30-32) — exactly the gap a glossary closes, because the glossary names which Russian words are forbidden.
5. **Hook wiring** (`claude-home/settings.json.template`, parsed 2026-10-15): `Stop` has one handler, `explanation-terms.sh`,
   `timeout: 10` s; `UserPromptSubmit` has three handlers, `timeout: 3` s each (message counter, `git-finish-router.sh`,
   `question-memo-inject.sh`); `SessionStart` two. Hooks are global; per-project hooks would need `.claude/settings.json` in each
   project (hooks docs, "Hook locations" table) — not an option when the file is produced by a generator for every project.
6. **Stop-hook behaviour, official** (code.claude.com/docs/en/hooks, fetched 2026-10-15): `last_assistant_message` "contains the text
   content of Claude's final response"; `hookSpecificOutput.additionalContext` is "Non-error feedback for Claude. The conversation
   continues so Claude can act on it, but unlike `decision: "block"` it is shown in the transcript as hook feedback rather than a hook
   error"; "8-consecutive-continuation cap"; `stop_hook_active` guard. So **any** Stop check produces another model turn — the user's
   objection in r1f: "NO post-hoc Stop check of the header (a Stop check makes the model write a second message)" (r1f.3 discovery,
   constraint 3). The same user accepted the **one-line correction** form for coined words (bd `r1f.1` closed 2026-10-15: "no block,
   one-line correction via Stop additionalContext"). The boundary the user drew: no block, no rewrite, no paragraph; one line per word is
   tolerated. Q2 decided that the synonym check uses exactly that tolerated form (FR-5a), plus a pre-commit check on files (FR-5b).
7. **Memory and imports, official** (code.claude.com/docs/en/memory, fetched 2026-10-15): "CLAUDE.md files can import additional files
   using `@path/to/import` syntax. Imported files are expanded and loaded into context at launch"; "maximum depth of four hops";
   "Import parsing skips Markdown code spans and fenced code blocks"; an import outside the working directory is "external" and needs a
   one-time approval dialog; inside `AGENTS.md` "`@path` imports are expanded"; "target under 200 lines per CLAUDE.md file. Longer files
   consume more context and reduce adherence". Project-rule files in `.claude/rules/` load at launch and may be symlinked.
8. **Generators**: `_init/SKILL.md:26-44` inlines the `AGENTS.md` template (14 lines) and lists the files it creates (`AGENTS.md`,
   `CHANGELOG.md`, `docs/`, `.claude/settings.local.json`); `grace-init/SKILL.md:13-21` maps `assets/AGENTS.md.template` (164 lines) and
   six XML templates to targets, step 3 (l.44-47) creates or verifies `AGENTS.md`. Two generators, two template mechanisms (inline vs
   asset file); a glossary bootstrap touches both.
9. **Test harness**: `Makefile:20-36` lists every hook test file explicitly; `.pre-commit-config.yaml:41-42` `hook-regression-tests`
   runs `pytest claude-home/hooks/` on commits touching hooks; baseline 600 of 600 tests passed (bd du5 pre-dispatch note).
10. **Document names**: `CLAUDE-APPENDIX.md` -> "File Structure (dev-projects)" lists `docs/` only; no name for a glossary file exists
    in N-DOCS today, so the separate-file form of Q4 (glossaries over 200 lines, e.g. `ML_Sobes_2026/glossary.md`) needs a name
    added there.

## Measured evidence of the problem

1. Hook journal `~/.claude/hook-stats/blocks.jsonl` (counted 2026-10-15 with python3): 154 records, 151 of them from
   `explanation-terms`, 2026-08-28 to 2026-10-15, across 57 working directories; 219 distinct flagged words, 223 occurrences. The
   previous session's analysis (bd du5 notes, not re-verified here) classed 37 of the 219 as coined. **The journal measures only
   Latin-script candidates**; Russian synonym switching («таблица» → «реестр») leaves no trace there, so the problem the user names
   has no machine count today. Selection rule for the figure: every record whose `hook` field equals `explanation-terms`.
2. The one project that measured its Russian synonyms by hand found «размышление» 172 times and «шаблон» 57 times in its old texts
   (`Local_LLM_selection/CLAUDE.md:205-207`) — the scale a per-project list reaches once someone counts.

## Best practices with sources

1. **Concept-first term base** (TBX, ISO 30042; vendor docs of Wordbee, RWS Trados, Phrase, web search 2026-10-15): one concept
   carries a preferred term, admitted synonyms and prohibited (forbidden) terms; QA tools flag prohibited terms. Known pitfall
   (ProZ thread): marking deprecated spellings as forbidden flags every segment containing the word, including legitimate ones —
   the same false-positive class as blind spot 2. Phrase users note the lack of a "deprecated" status distinct from "forbidden".
   Lesson: the entry needs a status per synonym (forbidden vs admitted) or at least an exception mechanism.
2. **Vale vocabularies** (docs.vale.sh/keys/vocabularies, vale.sh/docs/checks/substitution): `accept.txt` / `reject.txt`, one word,
   phrase or regular expression per line; accepted terms feed a substitution rule that enforces spelling and casing, rejected terms an
   existence rule that flags every occurrence; substitution rules map a forbidden form to its preferred form. The two-file model is the
   docs-as-code equivalent of forbidden → canonical, and it uses regex for inflection instead of lemmatisation — the same choice as
   `vocab.py`.
3. **LLM terminology adherence** (arXiv 2401.14559; arXiv 2510.17504 WMT 2025 Terminology task; arXiv 2609.13916 Cohere CAT+; JDTL
   2025/2/4): adherence is measured as "did the required term appear", negative entries are needed so that a model copying every
   glossary line does not score well, and prompt injection alone leaves a measurable deviation rate. Lesson for this feature: deliver
   the list before the answer AND check after; keep a journal so the deviation rate is a number.
4. **Repo precedent for delivery**: section cut at run time, `additionalContext`, exit 0 (`task-level-inject.sh:20-33`,
   `question-memo-inject.sh:24-36`); and for a check after the answer: one line per word, journal, no block (`explanation-terms.py:256-273`).

## Functional requirements

- FR-1 A glossary exists per project as a `## Glossary` section of the project `AGENTS.md`: a list of synonym groups, each group with
  exactly one canonical term and one or more forbidden forms; the canonical term is written verbatim as it must appear in prose.
  When the section would exceed 200 lines, the list lives in a separate file and `AGENTS.md` carries one pointer line to it.
  Source: user request (bd du5 description); user decision Q4; official guidance (memory docs "target under 200 lines").
- FR-2 A glossary entry may carry a definition and a source (document, decision date); both are optional. Source: user request
  (bd du5 description "format (canonical term + forbidden synonyms + definition + source)"); user decision Q5.
- FR-3 The agent reads the glossary before answering in that project and uses only canonical terms in the governed text: chat prose,
  every text written for the user (docs, bd issue text, CHANGELOG, reports), and code strings, comments and HTML. Code identifiers are
  exempt. Source: user request (acceptance criterion 2); user decision Q1; existing rules `claude-home/CLAUDE.md:9` (identifiers in
  English) and `:131` (one designation).
- FR-4 The glossary reaches a session that started before the glossary changed, through the hook route the project already uses for
  rules that must reach live sessions; the hook locates the project glossary through `cwd`. Source: existing contract
  (`python-ai-skills/CLAUDE.md` -> "Live immediately has one exception"; `question-memo-inject.sh:10-11` reserved slot); user decision Q4
  (the heading `## Glossary` is the cut key, the pointer line the fallback).
- FR-5a A Stop hook reads `last_assistant_message`, reports every forbidden form found in it (Russian case forms included) and asks for
  exactly one line per finding in the form `Поправка к термину: «X» → «Y»`; it never blocks or rewrites; each finding is journaled.
  Source: user request (acceptance criterion 3); user decision Q2; user decisions r1f / r1f.1 (no block, one line per word);
  measured risk (blind spot 1, inflection).
- FR-5b A pre-commit check scans the changed lines of staged files (prose files and code strings, comments, HTML) for forbidden
  forms, prints `<path>:<line>: «form» → «canonical»` per finding and exits 1 on findings, 0 otherwise, 2 when the glossary cannot be
  read. Source: user decision Q2; existing contract (`vocab.py` `--staged` shape, exit codes 0/1/2, `Local_LLM_selection/.pre-commit-config.yaml:10-15`).
- FR-6 Both checks skip code identifiers, fenced code, inline backticks, quoted spans (the glossary's own lines, verbatim quotes) and
  English prose, and honour an exception list in which every exception names its source. Source: user decision Q1 (identifier and
  quote exemption); existing contract (`vocab.py:67-72`, `test_vocab.py:118`; `explanation-terms.py:93-99` skips code fences and links);
  measured risk (blind spot 2).
- FR-7 A forbidden form listed in the glossary is not counted as "real" by `explanation-terms.py` merely because the glossary file
  contains it. Source: existing contract (`explanation-terms.py:118-149, 211-226`); blind spot 7.
- FR-8 `_init` and `grace-init` create the `## Glossary` skeleton (the entry form and a one-line rule on how to add a group) in the new
  project's `AGENTS.md`; both generators reference one template, not two copies. Source: user request (acceptance criterion 4); user
  decision Q4; existing contract (`grace-init/SKILL.md:23` "Never hardcode template content inline"; SSoT rule).
- FR-9 The global `claude-home/CLAUDE.md` names the glossary mechanism once (the `## Glossary` section, that only canonical terms are
  used, the pointer-file form, the governed text) without restating the one-designation rule of l.131; the appendix carries the
  rationale. No global synonym layer is defined. Source: existing contract (SSoT, `claude-home/CLAUDE.md:246`; appendix convention,
  r1f.3 design 2.2); user decision Q3 (LATER).
- FR-10 Codex sees the same glossary text at session start without a hook, because the section (or the pointer line) is inside
  `AGENTS.md`. Source: existing contract (`python-ai-skills/CLAUDE.md` -> Multi-machine consistency: Codex reads AGENTS.md as a single
  file, no imports); user decision Q4.
- FR-11 Tests beside each check (pytest, same isolation as `test_explanation_terms.py`: fake HOME, synthetic fixtures, a temporary git
  repository; a fixture in the `ML_Sobes_2026` converted form) and Makefile `test` entries. Source: existing contract (`Makefile:20-36`,
  `.pre-commit-config.yaml:41-42`).
- FR-12 Two sample projects carry a filled glossary and are the acceptance fixtures: a project whose glossary fits inside `AGENTS.md`
  (first sample, chosen in Step 4) and `ML_Sobes_2026` (separate file + pointer line). Source: user request (acceptance criterion 1);
  user decision Q6.
- FR-13 CHANGELOG `Unreleased` entry. Source: project `CLAUDE.md` -> Changelog rule.
- FR-14 A one-off script (task level 5: written and run once, not shipped) converts `ML_Sobes_2026/glossary.md` from the four-column
  table (`Основной термин | English | Синонимы (не употреблять) | Кратко`, 629 rows in 19 tables) into the FR-1 entry form: synonyms
  column → forbidden forms, first column → canonical term, `Кратко` → optional definition, `English` kept as part of the definition or
  source; the `## Спорные выборы` section (l.729) is carried over as prose. The converted file stays separate and `ML_Sobes_2026/AGENTS.md:103`
  becomes the pointer line. Source: user decision Q6; existing text `ML_Sobes_2026/AGENTS.md:103`.
- FR-15 A separate bd task is filed for `Local_LLM_selection` (glossary in `CLAUDE.md:15-212`, checker `vocab.py` with 44 tests, the
  qualification semantics of «Никогда не общее слово — всегда точное», the `spark-public-bot/AGENTS.md:43-46` pointer, and the two
  separate `AGENTS.md` / `CLAUDE.md` files); it is executed inside that repository, not from this one. Source: user decision Q6;
  global Security rule (`claude-home/CLAUDE.md` -> Security: outside `$PWD` only `~/ai-steward/**/*.md`).

## Non-functional requirements

- NFR-1 Delivery cost per prompt stays within the memo pattern: the text a hook re-sends is at most the 10,000-character cap and in
  practice a few thousand characters; a glossary above the cap is delivered as a pointer plus the rule, not in full. Source: measured
  risk (blind spot 5: 29 items vs 629 rows); docs cap quoted in the r1f.3 discovery.
- NFR-2 Check runtime within the existing Stop timeout of 10 s for the hook and within the pre-commit budget for the file check
  (changed lines only, never the whole tree); regex only, no lemmatiser, no new dependency. Source: existing contract
  (`settings.json.template` Stop `timeout: 10`; Pre-commit Policy "slow checks belong in CI"; Python Development "no needless
  dependencies"); user decision Q2.
- NFR-3 The Stop hook is advisory only: exit 0 on every path, no `decision: block`, no rewrite request; the one-line form is the
  maximum. The pre-commit check is a gate (exit 1 on findings) like `vocab-check`, never bypassed with `--no-verify`. Source: user
  decisions r1f / r1f.1 and Q2; Pre-commit Policy.
- NFR-4 One copy of the glossary per domain; a second project of the same domain references it, it does not copy it. Source:
  existing precedent `spark-public-bot/AGENTS.md:43-46`; SSoT rule.
- NFR-5 Silence when a project has no glossary: no output, no journal noise, so `life` projects and the 37 projects without one
  (40 with instruction files minus 3 with glossary sections) are untouched. Source: pattern hooks (`question-memo-inject.sh:25-29`
  silent paths); Project Classification rule.
- NFR-6 Every finding is journaled like `explanation-terms` (`blocks.jsonl` record with hook name, cwd, forms), so the deviation
  rate becomes a measurable number per project and month. Source: existing contract (`explanation-terms.py:45-59`,
  `hook-stats-digest.py` SessionStart digest).
- NFR-7 The glossary is plain Markdown a person edits by hand, parsable by at most three line regexes (the `vocab.py` budget); the
  `## Glossary` section stays under 200 lines, above that the separate-file form applies. Source: existing contract
  (`vocab.py:110-112`); official guidance (memory docs "target under 200 lines"); user decision Q4.
- NFR-8 `Local_LLM_selection` is not touched by this feature: its `CLAUDE.md` glossary, `vocab.py` and 44 tests keep their current
  form until the separate bd task (FR-15); the new checks stay silent there because that project has no `## Glossary` section
  (NFR-5). Source: user decision Q6; existing contract (that project's pre-commit `vocab-check`).
- NFR-9 The one-off conversion of `ML_Sobes_2026/glossary.md` is lossless for term rows: 629 canonical terms in, 629 groups out, every
  synonym kept as a forbidden form, verified by a count before and after. Source: user decision Q6; Preferences "Evidence before
  assertions".

## Constraints

1. SSoT: the rule text once in `claude-home/CLAUDE.md`, the glossary once per domain, the template once in the repo.
2. Codex path: text in `AGENTS.md` or nothing (satisfied by Q4: section or pointer line inside `AGENTS.md`); `claude-home/CLAUDE.md`
   is already 40,682 bytes against a 32 KiB chain cap — one more reason Q3 keeps a global layer LATER (hypothesis from r1f.3 risk 7,
   unverified by a Codex run).
3. Claude Code path: `@path` imports expand at launch (depth 4, backticks skipped, external imports need approval); `.claude/rules/`
   files load at launch too; hooks are global and must locate the project glossary through `cwd`.
4. Stop hooks always cost another model turn; the tolerated form is one line per word (r1f.1), nothing longer — chosen in Q2.
5. The checks must be regex-only Russian morphology (prior art, no dependency rule).
6. Two generators with different template mechanisms must produce the same skeleton.
7. No blocking in chat; the pre-commit gate may fail a commit but is never bypassed with `--no-verify` (Pre-commit Policy; Preferences
   "Root-cause over symptom").
8. Security rule: from this repository only `*.md` files outside `$PWD` may be edited — enough for the `ML_Sobes_2026` conversion
   (`glossary.md`, `AGENTS.md`), not for `Local_LLM_selection` (`vocab.py`, tests), hence FR-15.

## Dependencies

1. `claude-home/hooks/explanation-terms.py` (precedence rule FR-7; possibly the host of the new check or its sibling).
2. `claude-home/hooks/question-memo-inject.sh` (delivery slot FR-4) and `claude-home/settings.json.template` (wiring).
3. `claude-home/CLAUDE.md` sections Explanation Protocol and Naming; `claude-home/CLAUDE-APPENDIX.md` rationale paragraph.
4. `_init/SKILL.md` and `grace-init/assets/AGENTS.md.template` (FR-8).
5. `Makefile`, `.pre-commit-config.yaml` (FR-11), `CHANGELOG.md` (FR-13).
6. Sample projects (FR-12): `ML_Sobes_2026` (`glossary.md`, `AGENTS.md:103`) after the FR-14 conversion, plus one project whose
   glossary fits inside `AGENTS.md` (chosen in Step 4). `Local_LLM_selection` is a dependency only of the separate task FR-15.
7. Official docs: hooks (Stop, UserPromptSubmit `cwd`, SessionStart `additionalContext`), memory (imports, AGENTS.md, rules).

## Risks and mitigations

1. False positives from inflection and compounds (probe: «таблица-сводка» matched, «DNS-запись» not) → exception list with sources,
   backtick/code/quote skipping, near-word tests (`test_vocab.py:140` pattern), journal review before widening scope.
2. Second message in chat after a Stop check (accepted in Q2) → NFR-3 one-line form only; `stop_hook_active` guard and the
   8-continuation cap already apply; the journal (NFR-6) shows how often it fires per project so the user can revisit Q2 with a number.
3. Whitelisting conflict with `explanation-terms` (glossary words become "real") → FR-7 precedence; test that a forbidden Latin form
   listed in the glossary is still reported.
4. Glossary growth beyond the memo budget (629 rows exist today) → NFR-1 pointer mode above a cap; the full list stays a file the model
   reads on demand; Q4 fixes the 200-line boundary for the section form.
5. Old sessions never see a new glossary → FR-4 hook delivery via `cwd`; silence without a glossary (NFR-5).
6. Codex blindness → FR-10: the governing text lives in `AGENTS.md`; the global layer is LATER (Q3), so nothing new lands past the
   32 KiB cap in this feature; the cap itself is still to be measured with `codex debug prompt-input` outside the sandbox (LATER, same
   action r1f.3 Q5 planned).
7. Generators create an empty skeleton nobody fills → the skeleton carries the entry form and the add-a-group rule; filling is a
   human/agent act at first contact with a term, as `ML_Sobes_2026/AGENTS.md:103` prescribes ("Нового понятия в словаре нет —
   добавить строку").
8. Format drift across the existing variants → Q6: `ML_Sobes_2026` converted by FR-14 (count-verified, NFR-9); `Local_LLM_selection`
   and `spark-public-bot` deferred to FR-15; `Bio-Chem-Career-2026`'s two-term disambiguation is a definition-bearing entry the FR-2
   optional fields can hold, migration not required.
9. Scope widened to code strings, comments and HTML (Q1) → more false positives on identifiers and quoted forms; FR-6 exemptions
   (identifiers, backticks, fences, quotes) and the exception list with sources; the pre-commit check scans changed lines only
   (NFR-2), so old text never fails a commit — the `Local_LLM_selection/CLAUDE.md:205-212` principle "словарь обязателен для нового
   текста".
10. Compliance not measurable → NFR-6 journal; LATER a transcript scan like `claude-home/scripts/skill-stats.py` for the share of
    answers with a finding (base: answers in projects with a glossary).
11. Conversion of `ML_Sobes_2026/glossary.md` loses rows or merges distinct concepts (its own rule forbids merging, `glossary.md:3`)
    → NFR-9 count check 629 in / 629 out; the script is one-off (level 5), its output reviewed by the user before the pointer line
    replaces `AGENTS.md:103`.
12. `Local_LLM_selection` drifts further from the new form while FR-15 waits, and its two separate `AGENTS.md` / `CLAUDE.md` files
    mean a glossary there is read by Claude Code through `CLAUDE.md` only (memory docs: when a `CLAUDE.md` exists, `AGENTS.md` is not
    read) → recorded in the FR-15 task text; out of scope here.

## Scope

- IN: the `## Glossary` section contract (entry form, optional definition and source, the 200-line boundary and the pointer-line
  form) and its skeleton template; the global rule paragraph in `claude-home/CLAUDE.md` plus the appendix rationale; delivery to live
  sessions (FR-4) within the memo-hook pattern; the Stop hook check (FR-5a) and the pre-commit changed-lines check (FR-5b) with the
  shared exemptions (FR-6), tests and Makefile entries; the precedence rule in `explanation-terms.py` (FR-7); `_init` and `grace-init`
  bootstrap (FR-8); two sample projects (FR-12) including the one-off conversion of `ML_Sobes_2026/glossary.md` and the pointer line in
  its `AGENTS.md` (FR-14); the bd task for `Local_LLM_selection` filed (FR-15); CHANGELOG (FR-13).
- OUT: blocking or rewriting answers; lemmatisation or any new dependency; per-project `.claude/settings.json` hooks; a global
  synonym-group layer; any edit inside `Local_LLM_selection` or `spark-public-bot` (FR-15 executes there, not here); the
  `AGENTS.md` / `CLAUDE.md` split of `Local_LLM_selection` (finding only); migrating old texts of any project (the
  `Local_LLM_selection/CLAUDE.md:205-212` decision stands; changed lines only); editing plugin skills; any push.
- LATER: the global layer once a group repeats in 3 projects (Q3); the `Local_LLM_selection` + `spark-public-bot` task (FR-15); the
  Codex chain-cap measurement; a transcript-based compliance scan; a `/doctor`-style consistency audit of glossaries across projects;
  English-prose glossaries for projects whose chat is English (none found today).

## Design points Step 4 must decide (not decided here)

1. Entry line syntax inside `## Glossary` (the `«forbidden» → **canonical**` list of prior art 1, or a variant that also carries the
   optional definition and source of FR-2) — one syntax for the section form and the separate-file form alike, and the exact shape of
   the pointer line.
2. Whether the Stop check is a new Python module beside `explanation-terms.py` or an extension of it (shared evidence corpus, journal
   and one-line form), and whether the pre-commit check is the same module with a `--staged` entry point (the `vocab.py` core, about
   70 lines, as the starting point) or a second script.
3. How the memo hook finds the glossary from `cwd` (`## Glossary` heading in `AGENTS.md`, then the pointer line) and what it sends above
   the cap (the rule plus the pointer, not the list).
4. The identifier exemption rule for the file check (Latin-script tokens with `_`, digits, camelCase, dotted paths — the
   `explanation-terms.py:14-17` shapes) and how a quoted forbidden form is recognised (backticks, «», fenced blocks, the glossary's own
   lines).
5. Fixture strategy: synthetic glossary in tests, one guard test against each sample project's real file (precedent
   `test_principles_ssot.py`, `test_vocab.py:290`), and the FR-14 conversion verified by the 629-in / 629-out count.
6. Which project is the first (section-form) sample, and the text of the FR-15 bd task for `Local_LLM_selection`.

## Resolved questions

All six open questions were decided by the user on 2026-10-15; the chosen options are listed in "Decisions" at the top of this
document and are the sources of FR-1, FR-2, FR-3, FR-4, FR-5a, FR-5b, FR-6, FR-8, FR-9, FR-10, FR-12, FR-14, FR-15, NFR-2, NFR-3,
NFR-7, NFR-8 and NFR-9. The option lists and recommendations of the first draft are not kept here; they are in the git history of
this file.
