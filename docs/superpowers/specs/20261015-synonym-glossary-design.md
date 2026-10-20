---
feature: synonym-glossary
bd_id: python-ai-skills-du5
date: 2026-10-20
status: approved
risk: medium
risk_justification: "one new Python hook module that runs on every user prompt (UserPromptSubmit) and after every answer (Stop) in every project on this machine, plus a step in the bootstrap pre-commit hook that every new repository inherits; advisory in chat (exit 0, no decision field, one line per finding), a gate on commit (exit 1 on findings) only in projects that carry a `## Glossary` section; edits to the global CLAUDE.md, to explanation-terms.py (4 lines), to two generator skills, and a one-off conversion of a 629-row glossary reviewed by the user. Same as Discovery."
approach: one-module-three-modes
open_questions: []
context7_verified: [pre-commit==4.6.0]
context7_note: "Context7 `/pre-commit/pre-commit.com` confirmed `repo: local` hook keys (`entry` carries the arguments, `language`, `files`/`types`, `pass_filenames`, `always_run`, `fail_fast`); the shell-expansion behaviour of `entry` was probed in this session (section 3.5). The hook module is Python 3.12.6 stdlib only (`re`, `json`, `subprocess`, `difflib`, `pathlib`, `datetime`, `os`, `sys`); tests are pytest + stdlib `subprocess`/`json`, as in `test_explanation_terms.py`."
requirements: "docs/superpowers/specs/20261015-synonym-glossary-discovery.md (decisions Q1-Q6, FR-1..FR-15, NFR-1..NFR-9, constraints 1-8, risks 1-12, design points 1-6)"
---

# Design: per-project synonym glossary — one module, three modes (python-ai-skills-du5)

Requirements, hook contract quotes and risks are in the Discovery spec and are not restated here. This document decides HOW. The six
design points of the Discovery ("Design points Step 4 must decide") and the seven open questions of the Step 4 brainstorming were
decided by the user on 2026-10-20; the decisions are stated inline where they apply. Every line reference was read in this session.

## 1. Approaches

### 1.1 one-module-three-modes (CHOSEN) — 50% / 85%
One new file `claude-home/hooks/glossary.py` holds the glossary contract (3 line regexes), the matcher and three sub-commands:
`memo` (UserPromptSubmit), `stop` (Stop) and `--staged` (pre-commit). It is wired directly as Python, the form
`settings.json.template:300-302` already uses for `hook-stats-digest.py`, so no `.sh` launcher is added. The bootstrap pre-commit hook
gets one step before its `exec pre-commit` (`claude-home/git-template/pre-commit:27-35`), `explanation-terms.py` gets the FR-7
precedence in 4 lines, the generators share one template asset. Smallest change that meets FR-1..FR-15 and NFR-1..NFR-9; every file it
touches is traced in section 6.

### 1.2 stop-inside-explanation-terms — 30% / 80%
Same core module, but the Stop scan is hosted in `explanation-terms.py` (one Stop handler, one framing text). Rejected: the coined-term
hook would depend on the glossary module and on its parse errors; its Russian-prose gate (`explanation-terms.py:84-90`, at least 200
letters and 30 % Cyrillic) would also gate glossary findings unless split; the file would carry two responsibilities (SRP). The hooks
documentation states "All matching hooks run in parallel" and "When several hooks return `additionalContext` for the same event, Claude
receives all of the values" (code.claude.com/docs/en/hooks, fetched 2026-10-15), so a second Stop handler costs no extra model turn —
the main argument for 1.2 does not hold.

### 1.3 package-plus-rules-files — 5% / 60%
A `hooks/glossary/` package, a bash memo extension of `question-memo-inject.sh`, per-project `.claude/rules/glossary.md`, a shared
journal module replacing the three `log_block` copies, an installer loop over every repository's hook copy. Rejected: no FR needs a
package, rules files or the journal refactor (KISS/YAGNI precedence in `_code-quality/principles.md`); the installer loop is replaced by
one user-run command (section 3.5). Its one useful piece — the targeted memo — was kept and is part of 1.1 (user decision D5).

### Свой вариант / ни один — 15%

## 2. Decisions carried into this design (user, 2026-10-20)

1. **D1 pointer line**: `Glossary file: \`glossary.md\`` is the single body line of `## Glossary`; the file lives at the project root.
2. **D2 groups without forbidden forms**: kept as `- **term** — definition` lines, parsed, never scanned (208 of 629 ML_Sobes rows).
3. **D3 case and short forms**: Latin forms case-sensitive and literal; Cyrillic forms case-insensitive with case endings; a form of at
   most 2 characters matches only as a whole token; the lookahead includes `[a-z0-9_]` (the prior-art regex matched «OOF» inside
   «OOFS» and «k-fold» inside «k-folds», probed 2026-10-15); the 13 short forms of ML_Sobes are listed for review during FR-14.
4. **D4 pre-commit reach**: a step in the bootstrap template hook plus a documented local-hook entry for repositories that have a
   `.pre-commit-config.yaml` but no template copy; the 22 old template copies are refreshed by one command the plan prepares and the
   user runs — not by the installer.
5. **D5 memo above the cap**: targeted — the `prompt` field is scanned with the same matcher for canonical and forbidden forms and only
   the matching groups are sent, capped at `MEMO_MAX_CHARS`; nothing matched or over the cap → rule + pointer line + counts. Small
   glossaries (section form, at most 200 lines and 8,000 characters) are sent in full.
6. **D6 section boundary**: the section form holds at most 200 lines AND 8,000 characters; above either, the separate-file form.
7. **Samples**: python-ai-skills (section form; seed groups taken from real usage at execution time, not invented) and ML_Sobes_2026
   (separate file, converted by the one-off FR-14 script; the pointer line replaces `ML_Sobes_2026/AGENTS.md:103`).

## 3. Module map

### 3.1 Files
1. NEW `claude-home/hooks/glossary.py` (about 240 lines): constants (section 4.4), `load_glossary(root)` (section 4.1-4.3, lookup
   section 4.5), `scan_text(text, glossary)` (section 4.6), `changed_lines(head, new)` (copied from `vocab.py:215-226`, 12 lines),
   `log_record(detail)` (one journal writer, the `explanation-terms.py:45-59` shape; every hook in this repo carries its own copy —
   `branch-name-check.py:280`, `block-no-verify.sh:29` — consolidation is a separate refactor, LATER), `main(argv)` dispatching
   `memo` / `stop` / `--staged` (section 5). Linked to `~/.claude/hooks/glossary.py` by the existing whole-directory link
   (`scripts/install-claude-symlinks.sh:100`); no installer change.
2. NEW `claude-home/hooks/test_glossary.py` (about 250 lines, section 7).
3. EXTENDED `claude-home/settings.json.template`: second `Stop` handler after `:418-421` — `"command": "python3
   '{{CLAUDE_HOME}}/hooks/glossary.py' stop", "timeout": 10`; fourth `UserPromptSubmit` handler after `:441-444` — `"command":
   "python3 '{{CLAUDE_HOME}}/hooks/glossary.py' memo", "timeout": 3`.
4. EXTENDED `claude-home/git-template/pre-commit`: the glossary step (section 3.5) inserted after the `REPO_ROOT` guard (`:23-24`)
   and before the framework delegation (`:27-35`).
5. EXTENDED `.pre-commit-config.yaml` (this repository): local hook `glossary-check` (section 3.5).
6. EXTENDED `claude-home/hooks/explanation-terms.py` (FR-7, section 3.4): `import glossary` and a 3-line filter in `main()` after
   `collect_candidates` (`:242`).
7. EXTENDED `claude-home/hooks/question-memo-inject.sh:10-11`: the reserved-slot comment becomes "The per-project glossary delivery
   (bd python-ai-skills-du5) is `glossary.py memo`, a sibling handler, not this hook." Text only; its 11 tests are untouched.
8. NEW `grace-init/assets/glossary-section.md.template` (section 3.6); EXTENDED `grace-init/assets/AGENTS.md.template` (the asset's
   text appended after `## Rules for Modifications`, l.157-164) and `grace-init/SKILL.md:13-22` (one table row for the asset);
   EXTENDED `_init/SKILL.md:26-44` (the inline AGENTS.md template gets one line after `## Standards`: "then append
   `grace-init/assets/glossary-section.md.template` verbatim").
9. EXTENDED `claude-home/CLAUDE.md` → `## Explanation Protocol`: one rule paragraph after the hook-level rule (l.153), section 3.7;
   `claude-home/CLAUDE-APPENDIX.md` → `## Explanation Protocol` rationale paragraph (l.62-65) and `## File Structure (dev-projects)`
   (l.138-166): the line `glossary.md  # separate-file glossary (section form over 200 lines or 8,000 characters), project root`
   (N-DOCS, FR-1).
10. EXTENDED `Makefile:22-36`: the line `claude-home/hooks/test_glossary.py \`. No change to `.pre-commit-config.yaml:41-46`
    (`hook-regression-tests` already runs `pytest claude-home/hooks/` on any hook change).
11. EXTENDED `CHANGELOG.md` → `## [Unreleased]` → `### Added` (FR-13).
12. Outside the repository, `*.md` only (Security rule): `ML_Sobes_2026/glossary.md` rewritten by the FR-14 script;
    `ML_Sobes_2026/AGENTS.md:103` replaced by the `## Glossary` heading plus the pointer line (section 8); `AGENTS.md` of this
    repository gets its `## Glossary` section (sample 1).
13. One-off, not committed (task level 5): the FR-14 conversion script in `$TMPDIR` (section 8).

### 3.2 What is reused from existing code
- Section cut by `## ` boundaries: `question-memo-inject.sh:27` (awk) and `branch-name-check.py:255-262` (Python) — the Python form is
  copied (6 lines).
- Project root from `cwd`: `branch-name-check.py:245-254` (`git rev-parse --show-toplevel`, fallback `cwd`, 5 s timeout).
- Fence/link/URL blanking: `explanation-terms.py:93-99`; identifier shapes: `explanation-terms.py:14-17`.
- Inflection regex: `vocab.py:167-177` (`_ENDINGS`, stem rule) with the corrected boundary (D3).
- Changed lines against HEAD: `vocab.py:215-226` (`difflib.SequenceMatcher`, `replace`/`insert` opcodes); glossary read from the
  index under `--staged`: `vocab.py:388-392`.
- Exit codes 0/1/2 and the finding line: `vocab.py:379-429` (`СЛОВАРЬ <path>:<line>: …`), adapted to the FR-5b form.
- One-line correction request, journal, `stop_hook_active` guard: `explanation-terms.py:235, 256-273`.
- Test isolation: `test_explanation_terms.py:61-78` (`env={"PATH": "/usr/bin:/bin", "HOME": <tmp>}`, `cwd` in the payload);
  real-file guard: `test_question_memo_inject.py:128-135`; consumer guard: `test_principles_ssot.py:37-55, 122-124`.

### 3.3 Hook wiring facts
`Stop` has one handler with `timeout: 10` (`settings.json.template:414-424`); `UserPromptSubmit` three handlers with `timeout: 3`
(`:426-446`). The hooks page: `cwd` is a common input field of every event; `additionalContext` is "capped at 10,000 characters" and
"Claude Code measures each string on its own, even when several hooks run for the same event"; `${CLAUDE_PROJECT_DIR}` is "the project
root where the session started" (fixed for the session, so a worktree entered later would keep the old root) — hence `cwd`, not that
variable, locates the glossary.

### 3.4 FR-7 edit in `explanation-terms.py`
After `candidates = collect_candidates(text)` (`:242`):
```python
    try:
        candidates -= glossary.forbidden_latin_forms(data.get("cwd") or "")
    except Exception:  # a glossary problem never silences the coined-term check
        pass
```
`forbidden_latin_forms(cwd)` returns the forbidden forms without Cyrillic letters as a set (verbatim, D3 case-sensitive), empty when
the project has no glossary. A forbidden Latin form is thus never tested against the evidence corpus (`:247-252`, where
`<cwd>/AGENTS.md` and `git grep` would mark it real) — it is reported by `glossary.py stop` with its canonical term instead.

### 3.5 Delivery of the pre-commit check to other projects (D4)
Facts (2026-10-15): 83 git repositories under `~/ai-steward/Gena_Beeline_Local`; 23 carry a copy of the bootstrap hook, 15 have a
`.pre-commit-config.yaml`, 9 both, 54 neither. The installer refreshes the template copy only in `~/.git-template` and in this
checkout (`scripts/install-claude-symlinks.sh:189-218`). pre-commit does not shell-expand `entry` (probed in a temporary repository:
`entry: python3 ~/.claude/hooks/g.py` and `entry: python3 $HOME/.claude/hooks/g.py` both failed with "can't open file
'…/repo/~/.claude/hooks/g.py'"; `entry: bash -c '…' --` passed).

1. Step in `claude-home/git-template/pre-commit`, inserted before line 27 (`set -euo pipefail` is active at `:16`, so the `if !`
   form is used):
```bash
# Project glossary (bd python-ai-skills-du5): forbidden synonyms in the changed lines of the
# staged files. Exit 0 at once when the repository has no `## Glossary` section.
GLOSSARY_CHECK="$HOME/.claude/hooks/glossary.py"
if [ -f "$GLOSSARY_CHECK" ] && ! python3 "$GLOSSARY_CHECK" --staged; then
  echo "pre-commit (template): glossary check failed — commit refused" >&2
  exit 1
fi
```
   Reach: every new repository (`init.templateDir = ~/.git-template`), this checkout (installer `:204-213`), and the other 22 copies
   once refreshed. Exit 2 of the check (glossary unreadable) also refuses the commit — a broken glossary is a configuration error the
   author must fix, the `vocab.py` precedent.
2. Refresh command (prepared by the plan, run by the user; selection rule = the installer's own marker test at `:211`):
```bash
for h in ~/ai-steward/Gena_Beeline_Local/*/.git/hooks/pre-commit; do
  grep -q 'Bootstrap pre-commit hook installed via ~/.git-template' "$h" \
    && install -m 755 ~/.git-template/hooks/pre-commit "$h" && echo "refreshed $h"
done
```
   Expected output: 23 `refreshed` lines (base: the 23 repositories carrying the marker).
3. Local-hook entry for repositories with a config but no template copy (6 of 83 today), added to this repository's
   `.pre-commit-config.yaml` as the live example and to `_linters/reference/linters.md` as the documented form:
```yaml
      - id: glossary-check
        name: glossary (forbidden synonyms in changed lines)
        entry: bash -c 'exec python3 "$HOME/.claude/hooks/glossary.py" --staged'
        language: system
        pass_filenames: false
        always_run: true
```
   In this repository both routes run the same check twice per commit (template step, then the framework hook); the second run reads
   the same index and costs the same 0.1 s order of time — accepted for the example's sake, noted in the CHANGELOG entry.

### 3.6 Generator asset `grace-init/assets/glossary-section.md.template` (FR-8)
````markdown
## Glossary

Одно понятие — одно обозначение (глобальный CLAUDE.md → Explanation Protocol). Одна строка на группу,
формы записи (пример в блоке кода не читается проверкой):

```text
- «запрещённая форма», «ещё форма» → **канонический термин** — определение (источник: документ или дата)
- **термин без синонимов** — определение (English: term)
- Исключение: «форма в законном контексте» — источник: откуда разрешение
```

Нового понятия в словаре нет — добавить строку и дальше употреблять её канонический термин. Раздел больше
200 строк или 8 000 знаков — перенести в `glossary.md` в корне проекта и оставить здесь одну строку:
Glossary file: `glossary.md`
````
The example lines sit inside a fenced block because the parser skips fenced lines inside the section (section 4.1); without the
fence the skeleton would forbid the words «запрещённая форма» in every new project. The last line is prose, not a pointer: the pointer
regex (4.2) anchors at line start and the line starts with "Glossary file:" only when the section body is that single line.
`_init/SKILL.md` and `grace-init/SKILL.md` reference the asset; `test_glossary.py` guards both references (section 7, group G).

### 3.7 `claude-home/CLAUDE.md` paragraph (FR-9), after l.153
```markdown
**Rule (глоссарий проекта):** у проекта есть раздел `## Glossary` в `AGENTS.md` — по одной строке на группу синонимов: «запрещённые формы» → **канонический термин**, при необходимости определение и источник. В тексте для пользователя (чат, документы, задачи bd, CHANGELOG, отчёты, строки и комментарии кода, HTML) употребляется только канонический термин; идентификаторы кода, текст в обратных кавычках и в «кавычках» не проверяются. Раздел больше 200 строк или 8 000 знаков живёт в `glossary.md` в корне проекта, а в разделе остаётся одна строка `Glossary file: `glossary.md``. Хук `~/.claude/hooks/glossary.py` доставляет словарь перед ответом (UserPromptSubmit: раздел целиком или только группы, задетые вопросом), проверяет последний ответ (Stop: одна строка `Поправка к термину: «X» → «Y»` на находку, без блокировки) и изменённые строки коммита (`--staged`, отказ в коммите). Проект без раздела — тишина. Один словарь на предметную область: второй проект той же области ставит строку-указатель на файл первого.
```
The one-designation rule of l.131 is referenced, not restated; the global layer (Q3 LATER) is not mentioned. The appendix paragraph
records the rationale: why a file and not discipline (Discovery "Real goal"), why two checks (blind spot 8), why advisory in chat
(r1f.1), why the pointer form (Codex, 32 KiB chain cap).

## 4. Glossary contract

### 4.1 Section
The section starts at the line `## Glossary` and ends before the next line starting with `#` of any level (the `vocab.py:115-121`
rule, stricter than the `## `-only rule of `question-memo-inject.sh:27`, so a `### Exceptions` sub-heading would end the section — the
contract therefore has no sub-headings; exception lines are entries). Lines inside a fenced block (` ``` ` … ` ``` `) are skipped.
Every other non-blank line must match exactly one of the three regexes below; a line that matches none is a **contract error**
(section 5 says what each mode does with it). At most one `## Glossary` heading per file.

### 4.2 The three line regexes (NFR-7 budget: three)
```python
ENTRY_RE = re.compile(
    r"^[-*] (?:(?P<forms>«[^»]+»(?:, «[^»]+»)*) → )?\*\*(?P<canonical>[^*]+)\*\*"
    r"(?: — (?P<definition>.*?))?(?: \((?P<kind>источник|English): (?P<source>[^)]+)\))?\s*$"
)
FORM_RE = re.compile(r"«([^»]+)»")                    # the vocab.py:111 regex, applied to group "forms"
POINTER_RE = re.compile(r"^Glossary file: `([^`]+)`\s*$")
EXCEPTION_RE = re.compile(r"^[-*] Исключение: «([^»]+)» — источник: (\S.*)$")
```
Verified on 10 sample lines (2026-10-20): an entry with three forms, definition and `English` source parses all five groups; a line
without forms (D2) parses with `forms = None`; a bare `- «реестр», «регистр» → **таблица**` parses; forms containing parentheses
(`«TP (в значении параллелизма)»`, `«амортизированно O(1)»`) parse because forms are delimited by «»; `- «x» → канонический без
звёздочек` and `- Исключение: «форма» без источника` match nothing — contract errors (the `test_vocab.py:118` rule "every exception
names its source" made structural).

Entry semantics:
1. `forms` — forbidden forms, each verbatim as it must not appear (multi-word allowed, separated by `, `); absent → a group with
   no forbidden form (D2): kept for the memo, never scanned.
2. `canonical` — the one designation, written as it must appear in prose (FR-1).
3. `definition` — optional (FR-2), free text up to the source.
4. `(источник: …)` or `(English: …)` — optional (FR-2); `English` is the carrier for the ML_Sobes `English` column (FR-14).
5. Exception line — a verbatim phrase in which a forbidden form is legal, with its source; the matcher drops a finding whose span
   overlaps an exception phrase on the same line (`vocab.py:205-210`); the phrase is matched with the same inflection rule as a form.
6. Pointer line — the only body line of the section (blank lines allowed); the path is relative to the directory of the instruction
   file or absolute (another domain, NFR-4; `spark-public-bot/AGENTS.md:43-46` precedent). The pointed file is parsed by the same
   rules from its own `## Glossary` heading; it must not contain a pointer line (one hop, no chains).

Bullets, not numbers: a numbered list (the `vocab.py:110` form) renumbers on every insert; 629 rows make that a daily cost.
`*` is accepted beside `-` because Markdown editors emit both.

### 4.3 Forms that cannot fire (listed for review in FR-14)
A form that the exemption rules of section 4.6 blank out never fires: identifier-shaped forms (`class_weight`, `scale_pos_weight`,
`wait_for`, `zero_grad`, `no_grad` — `_`; `H0` — digit) — 6 of 567 ML_Sobes forms. They stay in the file as documentation and are
printed by the conversion script under "forms the check cannot match". The 13 forms of at most 2 characters (`y`, `TN`, `TP`, `FN`,
`FP`, `lr`, `Q`, `K`, `V`, `ДИ`, `H0`, `SE`, `GC`) are printed under "short forms, whole-token only" for the user's decision.

### 4.4 Named constants
```python
GLOSSARY_HEADING = "## Glossary"
INSTRUCTION_FILES = ("AGENTS.md", "CLAUDE.md")   # first that exists at the project root
SECTION_MAX_LINES = 200          # D6 / Q4: section form above this -> separate file
MEMO_MAX_CHARS = 8_000           # D5 / D6: full section or targeted groups sent only up to this
HOOK_CAP_CHARS = 10_000          # hooks docs: additionalContext cap per string (not enforced here; MEMO_MAX_CHARS keeps under it)
SHORT_FORM_CHARS = 2             # D3: forms of this length or less match whole tokens only (the boundary already enforces it)
GIT_TIMEOUT_S = 5                # explanation-terms.py:81 precedent; Stop budget is 10 s, UserPromptSubmit 3 s
JOURNAL = Path.home() / ".claude" / "hook-stats" / "blocks.jsonl"
HOOK_NAME = "glossary"
```
Cost figures behind the constants: the ML_Sobes glossary converted is 629 lines of about 120 characters (75,300 characters) — always
over `MEMO_MAX_CHARS`; the question memo today is 1,440 characters (`CHANGELOG.md`, r1f.3 entry); compile of 567 forms 0.47 s and a
scan of a 5,000-character message 0.07 s with one compiled pattern per form (measured 2026-10-15), so the 3 s UserPromptSubmit
budget holds with a margin of 2.4 s even for the largest glossary.

### 4.5 Lookup: `cwd` → project root → instruction file → section → pointer
1. `root = git -C <cwd> rev-parse --show-toplevel` (timeout `GIT_TIMEOUT_S`); on any failure `root = cwd`
   (`branch-name-check.py:245-254`). A worktree under `.claude/worktrees/<name>` resolves to the worktree root, which has its own
   `AGENTS.md` checkout.
2. The first of `root/AGENTS.md`, `root/CLAUDE.md` that is a regular file (a symlink `CLAUDE.md -> AGENTS.md` is the same file; the two
   separate-file projects — `Local_LLM_selection`, `Sinayara-Isuzu` — resolve to `AGENTS.md`, neither has the section, both are silent).
3. Cut `## Glossary` (4.1). No heading → `None` → silence (NFR-5).
4. Section body is one pointer line → read the pointed file, cut its `## Glossary`; unreadable or without heading → contract error.
5. Under `--staged` the instruction file and the pointed file are read from the index (`git show :<path>`), falling back to the working
   tree when the index does not know the path (`vocab.py:388-392`), so the glossary that governs a commit is the one being committed.

### 4.6 Matcher and exemption rules (FR-5a, FR-5b, FR-6)
Blanking, applied to the text before matching, in this order (each step replaces the span with spaces so line numbers and offsets
survive):
1. fenced code blocks (` ``` ` … ` ``` `, multi-line; for `--staged` the state runs over the whole file),
2. inline backticks `` `…` ``,
3. «…» spans — covers the glossary's own entry lines and every verbatim quote (FR-6),
4. Markdown links `[…](…)` and bare URLs (`explanation-terms.py:96-99`),
5. Latin tokens of identifier shape (whitespace-separated, edge punctuation stripped as in `explanation-terms.py:79, 105`):
```python
IDENT_RE = re.compile(
    r"[A-Za-z0-9_./-]*(?:[_/]|[0-9]|\.[A-Za-z])[A-Za-z0-9_./-]*"      # _  /  digit  inner dot: scale_pos_weight, registry.jsonl, docs/plan.md, qwen38-lil-low, H0
    r"|(?=[A-Za-z-]*[a-z])[A-Za-z][A-Za-z-]*[A-Z][A-Za-z-]*"           # mixed case with a capital after the first letter: camelCase, HTTPServer, reverse-WireGuard
)
```
   Verified 2026-10-20: identifiers `scale_pos_weight`, `registry.jsonl`, `camelCase`, `HTTPServer`, `WireGuard`, `reverse-WireGuard`,
   `qwen38-lil-low`, `docs/plan.md`, `H0` are blanked; `k-fold`, `OOF`, `TP`, `SMOTE`, `Dev`, `Recall@k`, `top-k`, `lr` are not —
   all-capital abbreviations stay checkable (`explanation-terms.py:14-17` treats any capital after the first letter as an identifier;
   that rule would hide `OOF`, so the glossary matcher requires a lowercase letter too).
6. A line is governed only if it contains a Cyrillic letter (`[а-яёА-ЯЁ]`) — the English-prose exemption of FR-6, per line. The
   message-level gate of `explanation-terms.py:84-90` is not reused: a short Russian answer with a forbidden word must still be caught.

Form regex (one compiled pattern per form, `functools.lru_cache` keyed on the glossary text):
```python
ENDINGS = r"(?:а|я|у|ю|е|ы|и|о|ом|ем|ём|ой|ей|ов|ев|ам|ям|ами|ями|ах|ях|ью|ь|й)?"   # vocab.py:167
BOUNDARY_L = r"(?<![а-яёА-ЯЁA-Za-z0-9_-])"
BOUNDARY_R = r"(?![а-яёА-ЯЁA-Za-z0-9_-])"

def word_regex(word):          # a word with a Cyrillic letter: stem + endings (vocab.py:170-172); a Latin word: literal
    if CYRILLIC.search(word):
        stem = word[:-1] if word[-1] in "аяоеиыуюэёьй" else word
        return re.escape(stem) + ENDINGS
    return re.escape(word)

def form_regex(form):          # words joined by any blanks (vocab.py:175-177)
    body = r"\s+".join(word_regex(w) for w in form.split())
    flags = re.IGNORECASE if CYRILLIC.search(form) else 0     # D3
    return re.compile(BOUNDARY_L + body + BOUNDARY_R, flags)
```
Verified 2026-10-20: «таблица» finds «Таблица», «таблицы», «таблицей», «таблиц» (4 of 4 case forms) and not «табличный»; «запись»
finds «запись», «записей» and not «записать», «записка»; `OOF` finds `OOF` and not `OOFS` or `oof`; `k-fold` not `k-folds` or
`K-fold`; `TP` not `tp` or `TPU`; `K` finds `K` in «Q, K, V» and in `K=5`, not «Ключ»; `dev set` not `dev sets` or `Dev Set`. The
hyphen is a boundary on both sides, so a compound («таблица-сводка», «DNS-запись») never matches — symmetric and predictable; the
prior art matched one side only (Discovery blind spot 1). A finding is dropped when its span overlaps an exception phrase on the line.
Forms are tried longest first, and a shorter form whose span lies inside a longer form's match on the same line is dropped, so
«кросс-валидация» → «перекрёстная проверка» is one finding, not two («валидация» also being a form).

The matcher is pure (`scan_text(text, glossary) -> list[Finding(line_no, form, canonical)]`), the same function in all three modes.

## 5. The three modes — I/O contracts

Common: `python3 glossary.py <mode>`; stdin JSON for `memo` and `stop`; nothing on stderr on any success path; every exception in
`memo` and `stop` ends in exit 0 with no output (advisory only, NFR-3), after one journal record `{"error": "<class>: <message>"}`
when the journal is writable.

### 5.1 `memo` (UserPromptSubmit; FR-3, FR-4, NFR-1, NFR-5)
Input: `{"hook_event_name": "UserPromptSubmit", "prompt": <str>, "cwd": <str>, …}`. Silence (exit 0, empty stdout): stdin not a JSON
object; no instruction file; no `## Glossary`; contract error (one journal record `{"mode": "memo", "error": …}`).
Output: `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": <text>}}` where `<text>` is one of:
1. **full** — the section is in section form (no pointer line) and its cut text is at most `SECTION_MAX_LINES` lines and
   `MEMO_MAX_CHARS` characters: `"Project glossary from <path> (the only copy); use only the canonical terms in this answer:\n\n" + section`.
2. **targeted** — otherwise: the glossary lines (entries, not exceptions) whose canonical term or any forbidden form the matcher finds
   in `prompt` (canonical terms are matched with the same form regex), in file order, while the running total stays at or under
   `MEMO_MAX_CHARS`; framing: `"Project glossary <path>: <k> of <n> groups touched by this prompt (the file has the rest); use only
   the canonical terms:\n\n" + lines`.
3. **pointer** — nothing matched, or the first matching line alone exceeds the cap: `"Project glossary: <path>, <n> groups, <m> lines.
   Read it before naming a thing; use only its canonical terms in this answer."`.
Measurement (orchestrator, 2026-10-20, simulation over 269 paragraphs of at least 40 characters from `ML_Sobes_2026/bank/**/*.md`
against the converted 629 groups, average group line 120 characters, full list 75,300 characters): matched groups per paragraph
median 2 (262 characters), p90 11 (1,353 characters), maximum 70 (9,499 characters — 1 paragraph of 269 over the 8,000 cap → pointer
mode); 57 of 269 paragraphs matched nothing → pointer mode. Token estimate at 3.0-3.5 characters per token (the
`20261015-question-memo-hook-design.md:272` precedent, an estimate, not a measurement): median about 75-90 tokens, p90 about 390-450,
cap about 2,300-2,700 per prompt.
Not journaled (NFR-6 covers findings, the memo has none). Time budget 3 s: lookup (one `git rev-parse`, about 0.01 s) + parse + up to
567 compiled patterns over the prompt (0.47 s compile + under 0.1 s scan for a 5,000-character prompt).

### 5.2 `stop` (Stop; FR-5a, FR-7, NFR-3, NFR-6)
Input: `{"hook_event_name": "Stop", "stop_hook_active": <bool>, "last_assistant_message": <str>, "cwd": <str>, …}`. Silence: stdin
not a JSON object; `stop_hook_active` true (`explanation-terms.py:235`); no glossary (NFR-5); contract error (journal record); no
finding.
Output (exit 0, no `decision` field):
```json
{"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext":
 "GLOSSARY <path>: these forms in your last message are forbidden synonyms of the project glossary: «кросс-валидация» → «перекрёстная проверка», «фича» → «признак».\n\nThe user has ALREADY READ that message. Do NOT repeat, rewrite or quote it; no paragraphs, no apology. Reply with exactly one line per form and nothing else:\n  Поправка к термину: «<form>» → «<canonical>»\nSee ~/.claude/CLAUDE.md -> 'Explanation Protocol'."}}
```
Distinct forms are listed once each, in order of first occurrence. Journal record (one per invocation with findings):
`{"ts": <ISO UTC seconds>, "hook": "glossary", "cwd": <cwd>, "mode": "stop", "glossary": <path>, "findings": [["кросс-валидация", "перекрёстная проверка"], …]}`
— the `explanation-terms.py:50-54` shape with `hook` = `glossary`, so `hook-stats-digest.py` counts it without change.
No `decision: block`, no rewrite request; both Stop hooks may answer in one continuation (3.3), each with its own one-line form.

### 5.3 `--staged` (pre-commit; FR-5b, FR-6, NFR-2, NFR-3)
No stdin. Root = `git rev-parse --show-toplevel` of the current directory (pre-commit and the bootstrap hook run at the repository
root). Steps:
1. Glossary from the index (4.5 step 5). No section → exit 0, no output. Contract error or unreadable pointer file → one line
   `glossary: <path>: <reason>` on stdout, exit 2.
2. Staged paths: `git diff --cached --name-only --diff-filter=AM -z`. For each: staged text `git show :<path>`; skipped when the
   bytes contain NUL or do not decode as UTF-8 (binary); HEAD text `git show HEAD:<path>`, absent → every line is new
   (`vocab.py:218-219`); `changed_lines` (4.1 reuse) limits `scan_text` to the added or replaced lines — old text never fails a commit
   (`Local_LLM_selection/CLAUDE.md:205-212` principle, Discovery risk 9). The instruction file itself is scanned too: its glossary
   lines are quoted in «», so they are exempt; a definition that uses another group's forbidden form is a real finding.
3. Output per finding `<path>:<line>: «form» → «canonical»` (FR-5b form), stdout only; exit 1 when at least one finding, else 0.
   Journal record `{"mode": "staged", "findings": [[path, line, form, canonical], …]}` with `hook` = `glossary` (NFR-6).
Governed files = every staged text file: prose (`.md`, `.txt`, …), code (strings and comments are Cyrillic lines, Q1), HTML
(Cyrillic text nodes); identifiers never match (4.6 step 5), English lines never match (step 6). Runtime: one `git show` per staged
path, changed lines only (NFR-2); the `vocab.py` run on 44 tests and a whole repository is the precedent that this stays within a
commit-time budget.

## 6. Traceability (FR/NFR → design element)
- FR-1 → 4.1-4.2 (section, entry line, pointer line), 4.4 `SECTION_MAX_LINES`/`MEMO_MAX_CHARS` (D6), 3.1 item 9 N-DOCS line.
- FR-2 → 4.2 groups `definition`, `kind`/`source`.
- FR-3 → 3.7 rule paragraph; 5.1 memo text "use only the canonical terms"; 4.6 governed-text rules (Q1).
- FR-4 → 5.1 `memo` with `cwd` lookup 4.5; heading as cut key, pointer as fallback.
- FR-5a → 5.2 `stop`; FR-5b → 5.3 `--staged`, exit 0/1/2, finding line form.
- FR-6 → 4.6 blanking steps 1-6, exception lines 4.2 item 5 with a source (contract error without one).
- FR-7 → 3.4 `forbidden_latin_forms` filter in `explanation-terms.py`; test group F.
- FR-8 → 3.6 asset, both generators reference it, guard G.
- FR-9 → 3.7 paragraph (no restatement of l.131, no global layer); appendix rationale.
- FR-10 → 4.1: the section or the pointer line is inside `AGENTS.md`, plain Markdown, no `@` import.
- FR-11 → section 7 tests; `Makefile` line; `.pre-commit-config.yaml:41-46` unchanged.
- FR-12 → section 2 item 7 (python-ai-skills section form; ML_Sobes_2026 pointer form); real-file guard H1.
- FR-13 → 3.1 item 11.
- FR-14 → section 8 conversion, 629 in / 629 out check.
- FR-15 → section 9 bd task text.
- NFR-1 → 5.1 three memo forms, `MEMO_MAX_CHARS` 8,000 under the 10,000 cap, measurement.
- NFR-2 → 4.4 timings, 5.3 changed lines only, stdlib only (frontmatter).
- NFR-3 → 5.2 exit 0 everywhere, no `decision`; 5.3 exit 1 as a gate; 3.5 template step refuses the commit.
- NFR-4 → 4.2 item 6 absolute pointer path; 3.7 last sentence.
- NFR-5 → 4.5 step 3 silence; 5.1-5.3 silence paths; test group E.
- NFR-6 → 5.2, 5.3 journal records with `hook` = `glossary`.
- NFR-7 → 4.2 exactly three line regexes; 4.4 `SECTION_MAX_LINES`.
- NFR-8 → 4.5: `Local_LLM_selection` has no `## Glossary` (its headings are `## Запрещённые слова…`, `vocab.py:61-62`), so every
  mode is silent there; nothing in that repository is edited.
- NFR-9 → section 8 step 4 count check.

## 7. Test plan — `claude-home/hooks/test_glossary.py` (FR-11)
Isolation as `test_explanation_terms.py:61-78`: `subprocess.run(["python3", HOOK, mode], env={"PATH": "/usr/bin:/bin", "HOME": tmp})`,
a temporary git repository with `user.name`/`user.email` set, `cwd` in the payload. Fixtures are inline strings; no fixture directory
(none exists under `claude-home/hooks/`). Groups and the requirement each serves:
- A. Parser (FR-1, FR-2, NFR-7): the 10 sample lines of 4.2; a section with a fenced example block (3.6) yields 0 groups; a section with
  blank lines; a file with two `## Glossary` headings → contract error; a section ended by a `#` line of any level.
- B. Matcher (FR-5a, FR-6, D3): the probes of 4.6 as parametrised cases (Cyrillic case forms, near words «записать»/«записка» — the
  `test_vocab.py:140` pattern, `OOF`/`OOFS`, `k-fold`/`k-folds`, `TP`/`tp`, `K` whole token, `dev set`/`dev sets`, compounds on
  both sides); exemptions one per case (fence, backticks, «», link, URL, each identifier shape of 4.6, an English line with a
  forbidden Latin form stays silent, the same form on a Cyrillic line fires); exception phrase overlap; longest-form precedence
  («кросс-валидация» vs «валидация»).
- C. `memo` (FR-4, NFR-1, D5, D6): full form for a 3-group section; targeted form for a pointer-file glossary of 30 groups and a prompt
  touching 2 of them (exactly those 2 lines, file order); pointer form when nothing matches; pointer form when the section is in
  section form but 201 lines or 8,001 characters; `cwd` in a subdirectory resolves to the root; `CLAUDE.md` as the instruction file;
  malformed stdin (`""`, `"not json"`, `"[]"`, `"42"`) → exit 0, empty stdout (the `test_question_memo_inject.py:91-95` set);
  output at most `MEMO_MAX_CHARS` + framing.
- D. `stop` (FR-5a, FR-7, NFR-3, NFR-6): one finding → the one-line form text with «form» → «canonical»; two findings, each listed
  once; no `decision` key; `stop_hook_active` → silence; journal record shape and `hook` = `glossary`; `HOME` unwritable → still
  exit 0 with output.
- E. Silence without a glossary (NFR-5, NFR-8): a repository without the heading, a directory that is not a git repository, a missing
  instruction file, a pointer to a missing file (`memo`/`stop` silent with a journal record; `--staged` exit 2).
- F. FR-7: `explanation-terms.py` run in a repository whose glossary forbids `«OOF» → **out-of-fold**` while a tracked file contains
  `OOF`: the coined-term hook does not list `OOF`; `glossary.py stop` does (added to `test_explanation_terms.py` as one test, the rest
  in `test_glossary.py`).
- G. Generators (FR-8): `_init/SKILL.md` and `grace-init/SKILL.md` contain `glossary-section.md.template`; the asset parses to 0 groups
  and 0 contract errors; `grace-init/assets/AGENTS.md.template` contains the asset text verbatim (`test_principles_ssot.py:122-124`
  shape).
- H. Real files (FR-12, D6): H1 this repository's `AGENTS.md` has exactly one `## Glossary`, at least 1 group, at most
  `SECTION_MAX_LINES` lines and `MEMO_MAX_CHARS` characters, 0 contract errors (`test_question_memo_inject.py:128-135` shape); H2 the
  `settings.json.template` `Stop` and `UserPromptSubmit` groups contain the two `glossary.py` commands; H3 `claude-home/git-template/pre-commit`
  contains the glossary step before the `exec pre-commit` line; H4 `claude-home/CLAUDE.md` names `## Glossary` and `glossary.py`
  exactly once each.
- I. `--staged` (FR-5b, NFR-2, NFR-3): a committed file with a forbidden form on an old line plus a staged change adding one on a new
  line → exactly the new line reported, exit 1; the same with no new forbidden form → exit 0, empty stdout; a staged binary file is
  skipped; the glossary edited in the working tree but not staged → the index version governs; contract error → exit 2 with the
  reason line; the ML_Sobes-form 12-row inline fixture (a `—` row as a no-form group, `«K»`, `«TP (в значении параллелизма)»`,
  `(English: …)` sources) parses to 12 groups and the expected 9 scannable forms.
Expected size about 60 test functions; `make test` baseline 600 of 600 (bd du5 pre-dispatch note) grows accordingly.

## 8. FR-14 — conversion of `ML_Sobes_2026/glossary.md` (task level 5, script in `$TMPDIR`, not committed)
Input facts (2026-10-15): 629 term rows in 19 `## ` sections, every row 4 cells, 0 cells containing `|`, 208 rows with `—` in the
synonyms cell, 347 canonical terms purely Latin, 567 forbidden forms (128 Latin-only), 1 synonym equal to another row's canonical
(`recall@k` under `Recall@k`), 1 synonym in two rows («базовая модель»), 6 forms with a qualifier such as `(в значении …)`, the
`## Спорные выборы` section l.729-750 with 20 numbered prose items, header paragraph l.1-3 with the project's own rule.
Procedure:
1. Read the file; keep the title and the header paragraph (l.1-3) verbatim above a new `## Glossary` heading. The 19 section headings
   cannot stay inside the section (a `#` line ends it, 4.1) and cannot become bold lines (not entries — contract error), so they are
   dropped from the section and listed once in the header paragraph ("19 тематических групп исходной таблицы: …"). Order of entries =
   order of rows.
2. Row → line: `| canonical | english | synonyms | short |` →
   `- «syn1», «syn2» → **canonical** — short (English: english)` when synonyms ≠ `—`, else `- **canonical** — short (English: english)`
   (D2). Synonyms are split on `, `; a synonym equal to the row's canonical (case-insensitive) is dropped with a note; the two cross-row
   cases above are printed for review, not altered.
3. `## Спорные выборы` is copied verbatim after the glossary section (a `## ` heading ends the section, so it is prose outside the
   contract, FR-14).
4. Count check (NFR-9), printed by the script and quoted in the report: rows in = 629; entry lines out = 629; forms in = 567; forms out
   = 567 minus the dropped self-synonyms (expected 0 or 1 — `recall@k` is a different row's canonical, so it stays); then
   `python3 ~/.claude/hooks/glossary.py` parsing the file reports 629 groups, 0 contract errors.
5. Review output for the user before the pointer line is written: the 13 short forms, the 6 forms that cannot fire (4.3), the 6
   qualifier forms, the 2 cross-row cases.
6. `ML_Sobes_2026/AGENTS.md:103` (the «Словарь терминов `glossary.md`» bullet) is replaced by:
```markdown
## Glossary

Glossary file: `glossary.md`
```
   placed as its own section after `## Формат ответов`; the sentence "Перед каждым вопросом, эталоном или объяснением сверяться со
   словарём. Нового понятия в словаре нет — добавить строку" stays in the file's own header paragraph (step 1), so the rule is not lost.
   `ML_Sobes_2026` is a `life` project (its `AGENTS.md`); the memo and Stop modes apply there (NFR-5 only requires silence without a
   glossary), the commit gate applies through its template hook copy after the refresh command of 3.5.
7. Verification in ML_Sobes_2026: `python3 ~/.claude/hooks/glossary.py memo` with a prompt containing «кросс-валидация» returns the
   targeted form with the «перекрёстная проверка» line; `stop` on a message containing «фича» returns the one-line request.

## 9. FR-15 — bd task for `Local_LLM_selection` (filed from here, executed there)
Title: `Glossary: migrate the vocabulary of CLAUDE.md to the ## Glossary form and point spark-public-bot at it`.
Description: Convert `CLAUDE.md:15-212` (`# 1. Словарь…`: 29 items — 8 generic nouns with qualification semantics in «Никогда не общее
слово — всегда точное», 21 forbidden items with 26 forms, 1 with a source, 0 with definitions) to the python-ai-skills entry form
(`- «form» → **canonical** — definition (источник: …)`; exception lines for `VOCAB_EXCEPTIONS` `vocab.py:67-72`; the 10 `QUALIFIED`
patterns `vocab.py:74-85` have no equivalent in the contract — decide whether qualification stays a project-local rule inside
`vocab.py` or becomes exception lines). Decide first which file carries it: `AGENTS.md` (5,926 bytes) and `CLAUDE.md` (29,735 bytes)
are two regular files (Claude Code reads `CLAUDE.md` only; the global rule `claude-home/CLAUDE.md:42` requires `CLAUDE.md -> AGENTS.md`).
Then either retire `vocab.py`'s section parsing (`_FORBIDDEN_HEADING`/`_GENERIC_HEADING` `vocab.py:61-62`, `_ITEM_RE` `:110`) in favour
of `~/.claude/hooks/glossary.py --staged`, keeping its report and template plumbing (about 360 lines) and its 44 tests green, or keep
`vocab.py` reading the new form; update `.pre-commit-config.yaml:10-15` (`vocab-check`). Replace `spark-public-bot/AGENTS.md:43-46` with
a `## Glossary` section whose body is `Glossary file: \`/home/bgs/ai-steward/Gena_Beeline_Local/Local_LLM_selection/<file>\`` (keep
its 6 local items as entries of its own glossary or of the pointed file — one copy, NFR-4). Old texts stay as they are
(`CLAUDE.md:205-212`). Acceptance: `glossary.py --staged` and `vocab.py --staged` agree on a staged file with one forbidden form; 44
tests pass; `test_real_repository_has_no_vocabulary_findings` (`test_vocab.py:290`) passes. Depends on python-ai-skills-du5 merged.

## 10. Risks carried over (Discovery 1-12) and what this design does with them
1. Inflection/compound false positives → symmetric hyphen boundary (4.6), near-word tests (7.B), exception lines with sources, journal
   review via `hook-stats-digest.py`.
2. Second message after Stop → one line per finding, no block (5.2); the journal gives the firing rate per project.
3. Whitelisting by `explanation-terms` → 3.4, test 7.F.
4. Growth beyond the memo budget → targeted memo (5.1) with the measured median 2 groups per paragraph; pointer when over the cap.
5. Old sessions → `memo` on every prompt (5.1).
6. Codex → the text is inside `AGENTS.md` (4.1); nothing added to `claude-home/CLAUDE.md` beyond one paragraph (about 1,100
   characters) — the 32 KiB chain cap stays an unmeasured hypothesis (LATER, Discovery scope).
7. Empty skeletons → the asset carries the add-a-group rule (3.6).
8. Format drift → ML_Sobes converted (8); `Local_LLM_selection` deferred (9).
9. Q1 widening → identifier/quote/fence/English-line exemptions (4.6), changed lines only (5.3).
10. Compliance not measurable → journal records in both checking modes (5.2, 5.3).
11. Conversion loss → count check and review list (8.4-8.5).
12. `Local_LLM_selection` split files → recorded in the FR-15 text (9).
New in this design: (13) a check that runs from the bootstrap hook is invisible to `pre-commit run --all-files` and to `SKIP=`; the
local-hook entry (3.5 item 3) is the documented way to make it visible in a repository's own config. (14) Six ML_Sobes forms can never
fire (4.3) — accepted, listed for the user. (15) Two Stop framings in one continuation when both hooks find something — accepted; both
demand the same one-line form.

## 11. Notes for Execution
1. Shell writes into `claude-home/hooks`, `claude-home/CLAUDE.md` and `~/.claude/projects` fail inside this session's Bash sandbox
   (`denyWithinAllow`); use the Edit/Write tools for those paths (`20261015-question-memo-hook-design.md:266-268` precedent).
2. The memo text is injected as a system reminder, so its words count as non-assistant evidence for `explanation-terms` (`session_corpus`,
   `explanation-terms.py:152-202`); a Latin forbidden form sent by the memo would be whitelisted for the coined-term hook without 3.4 —
   another reason the FR-7 filter sits in `explanation-terms.py`, not in the corpus.
3. The sample section for this repository is written at execution time from forms actually observed in sessions (transcripts under
   `~/.claude/projects/-home-bgs-ai-steward-Gena-Beeline-Local-python-ai-skills/`), per the Explanation Protocol rule on selection
   rules: list the counting rule and the counts in the CHANGELOG entry. Candidate groups seen in this repository's own prose and
   journal: «реестр моделей» (`model-registry.json`) vs «регистр», «таблица»; «журнал» (`blocks.jsonl`, `model-journal.jsonl`) vs
   «лог»; «хук» vs «перехватчик»; «символическая ссылка» vs «симлинк»; «подагент» vs «субагент», «сабагент». These are candidates to
   verify, not the list.
4. Verified this session and not contradicted: `settings.json.template` line numbers (Stop `:414-424`, UserPromptSubmit `:426-446`,
   direct-Python form `:300-302`); `Makefile:20-36`; `.pre-commit-config.yaml:41-46`; bootstrap hook lines `:16, :23-24, :27-35, :36-44`;
   installer `:100, :189-218`; `explanation-terms.py` lines cited; `vocab.py` lines cited; ML_Sobes counts; `python-ai-skills/CLAUDE.md`
   is a symlink to `AGENTS.md` (287 lines).
