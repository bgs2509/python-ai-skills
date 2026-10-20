---
feature: synonym-glossary
bd_id: python-ai-skills-du5
date: 2026-10-20
status: approved
risk: medium
discovery: docs/superpowers/specs/20261015-synonym-glossary-discovery.md
design: docs/superpowers/specs/20261015-synonym-glossary-design.md
approach: one-module-three-modes
tasks: 17
phases: 5
---

# Per-project synonym glossary: implementation plan (python-ai-skills-du5)

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:executing-plans` (inline). Several steps need the Edit/Write tools on sandbox-protected paths, two steps need the user's per-command sandbox-bypass approval and two steps are user-review stops, so subagent dispatch gains nothing. A worker can take one phase at a time (section "Phases"). Steps use checkbox (`- [ ]`) syntax.

**Goal:** a project keeps a `## Glossary` section in its `AGENTS.md` (or one pointer line to a separate file); one module `claude-home/hooks/glossary.py` delivers it before every answer (`memo`), asks for a one-line correction per forbidden synonym in the last answer (`stop`) and refuses a commit that adds one (`--staged`); both generators create the skeleton; python-ai-skills and ML_Sobes_2026 carry filled glossaries.

**Bead:** `python-ai-skills-du5`.
**Requirements:** [discovery](../specs/20261015-synonym-glossary-discovery.md) (FR-1..FR-15 incl. FR-5a/5b, NFR-1..NFR-9, decisions Q1-Q6).
**Design:** [one-module-three-modes](../specs/20261015-synonym-glossary-design.md) (approved, commit `1fb5e4e`). There are no GRACE contracts in this repository (no `docs/knowledge-graph.xml`): the approved design sections 3 (module map), 4 (contract), 5 (I/O), 7 (tests), 8 (FR-14) and 9 (FR-15) stand in for them, as in `20261015-question-memo-hook-plan.md`. Deviations of detail are listed at the end ("Deviations from the design").

**Architecture:** one Python stdlib module with a pure matcher (`scan_text`) shared by three entry points; wired directly as `python3 '<path>' <mode>` (the form `hook-stats-digest.py` already uses), so no `.sh` launcher; one extra step in the bootstrap pre-commit hook; four text edits (global rule, appendix, two generators) and two sample glossaries.

**Tech stack:** Python 3.11+ stdlib only (`re`, `json`, `subprocess`, `difflib`, `functools`, `dataclasses`, `pathlib`; checked on 3.12.6), pytest + stdlib `subprocess`/`json`, `ruff`, `pre-commit` 4.6.0, `bd`.

## Global constraints (machine facts verified on 2026-10-20)

1. **Sandbox write denial.** The Bash sandbox denies shell writes to `claude-home/hooks/`, `claude-home/CLAUDE.md`, `claude-home/output-styles` and `~/.claude/projects`. Every edit of files there goes through the **Edit / Write tools**, never shell redirects, `sed -i` or `tee`. All other repo files are also edited with Edit (fragile-shell-edit rule). Reading is not restricted. `~/.claude/hooks` is a directory link to `claude-home/hooks`, so `glossary.py` is live in `~/.claude/hooks/` from Task 2 on (no installer step for the module itself).
2. **Git.** Only standalone calls: no `&&`, `|`, `cd`, `-C`, redirects. Stage only the files listed in the step with explicit `git add <files>`. A sandboxed `git status` shows phantom paths (`.bash_profile`, `.bashrc`, `.claude/agents`, `.claude/commands`, `.claude/hooks`, `.claude/launch.json`, `.claude/loop.md`, `.claude/output-styles`, `.claude/routines`, ...): never stage them. Existing noise that is not ours and stays unstaged: `off.err`, `off.json`, `reports/`, `research_notes/` and the modified `.beads/interactions.jsonl`. Commits: Conventional Commits, English, `<type>(glossary): <description>`, pre-commit hooks run (`--no-verify`, `SKIP=` never used). No `git push`. A failing hook means fix the cause.
3. **Temp files** only in `$TMPDIR` (`/tmp/claude-1000` here, shared with other sessions: every scratch directory of this plan is `$TMPDIR/du5-*`). The FR-14 and candidate-count scripts live there and are never committed.
4. **Quality gate before each commit that touches `.py`:** `ruff check` on the changed files (the directory-wide baseline is exactly 1 pre-existing error, F401 in `test_big_read_nudge.py:22`, not ours, not fixed) and the scoped pytest of the step. `make test` runs at the end of each phase. **Baseline measured 2026-10-20: 603 of 603 passed** (473 + 25 + 12 + 76 + 17); the design said 600, the plan uses the measured number and Task 1 re-measures it.
5. **Outside `$PWD` only `*.md` may be edited** (Security rule): `ML_Sobes_2026/glossary.md` and `ML_Sobes_2026/AGENTS.md`. Nothing is edited in `Local_LLM_selection` or `spark-public-bot` (NFR-8). The one-off FR-14 script is not committed. The converted glossary and the pointer edit are written into `ML_Sobes_2026` only **after the user's review** (Task 14 stop). The plan does not commit inside `ML_Sobes_2026`.
6. **Sandbox-bypass calls (user approves each, each its own Bash call with `dangerouslyDisableSandbox: true`):** `make install-symlinks` (Task 10), and one `cp -f` of the converted glossary into `ML_Sobes_2026` (Task 14). Nothing else.
7. **The refresh of the 25 old bootstrap-hook copies in other repositories is prepared as text (Task 17) and run by the user. The plan never runs it.**
8. **Language.** Repository files in English, except text that is Russian by decision: the rule paragraph in `claude-home/CLAUDE.md`, the rationale paragraph in the appendix, the skeleton asset and the glossary entries (they hold the Russian forms they govern). `AGENTS.md` of this repository says "all content in this project is in English"; the glossary section is the one place where Cyrillic forms are the data (flagged in the final report).
9. **Phase sizing** (`~/.claude/CLAUDE-APPENDIX.md` -> "Plan Sizing": one phase fits 40-60 % of the smallest window of the executing model, split on a change of stack, directory or SSoT artifact, do not fragment below about 20 %). Estimate per phase: files read and written, at about 4.45 characters per token, tool results and logs counted double: Phase 1 two files (about 17 KB and 40 KB) = about 25K tokens; Phase 2 six small edits = about 15K; Phase 3 four text files = about 20K; Phase 4 the 112 KB ML_Sobes glossary is never read into the context (a script converts it) = about 15K; Phase 5 = about 8K. Every phase is well below 20 % of the 200K window of the smallest tier, so the five phases are one worker each and are not split further.

## Phases

1. **Phase 1, core module (Tasks 1-7):** `glossary.py` and `test_glossary.py`; Python, one directory, one SSoT artifact. Output: 113 tests green, three modes working from the command line.
2. **Phase 2, integration (Tasks 8-10):** `explanation-terms.py`, `settings.json.template`, `Makefile`, the bootstrap hook, `.pre-commit-config.yaml`; hook wiring and the installer. Output: the hooks run in live sessions and in commits.
3. **Phase 3, rule and generators (Tasks 11-12):** `claude-home/CLAUDE.md`, the appendix, the two generators and the skeleton asset. Text only.
4. **Phase 4, samples (Tasks 13-16):** the glossary of this repository, the one-off conversion of the ML_Sobes_2026 glossary (user review), the conditional commit-gate decision, the bd task for `Local_LLM_selection`.
5. **Phase 5, close (Task 17):** CHANGELOG, full gate, prepared rollout command, inputs for the Finish step.

## File structure

- Create: `claude-home/hooks/glossary.py` (about 390 lines), `claude-home/hooks/test_glossary.py` (126 tests, about 680 lines), `grace-init/assets/glossary-section.md.template`.
- Modify: `claude-home/hooks/explanation-terms.py` (+5 lines), `claude-home/hooks/test_explanation_terms.py` (+1 test), `claude-home/hooks/question-memo-inject.sh` (comment), `claude-home/settings.json.template` (2 handlers), `claude-home/git-template/pre-commit` (1 step), `.pre-commit-config.yaml` (1 local hook), `Makefile` (1 line), `claude-home/CLAUDE.md` (1 paragraph), `claude-home/CLAUDE-APPENDIX.md` (1 rationale paragraph, 1 tree line), `_linters/reference/linters.md` (1 subsection), `_init/SKILL.md`, `grace-init/SKILL.md`, `grace-init/assets/AGENTS.md.template`, `AGENTS.md` (the `## Glossary` section), `CHANGELOG.md`.
- Outside git, `*.md` only: `ML_Sobes_2026/glossary.md` (rewritten by the script), `ML_Sobes_2026/AGENTS.md` (pointer section).
- Commits (one per task; 14 in total, 15 when the conditional Task 15 runs): Task 1 `docs`, Tasks 2-10 `feat`, Task 11 `docs`, Task 12 `feat`, Task 13 `docs`, Task 15 `feat` (conditional), Task 17 `docs`. Tasks 14 and 16 commit nothing.

# Phase 1: core module

## Task 1: Preflight and baseline

**Serves:** evidence baseline (constraint 4).

- [ ] **Step 1:** claim the bead and confirm the tree.

```bash
bd update python-ai-skills-du5 --claim
```

Expected: the issue is already `IN_PROGRESS`, assigned to `bgs2509`; an "already claimed" message is fine.

```bash
git status --short
```

Expected: branch `main`; `?? docs/superpowers/plans/20261015-synonym-glossary-plan.md` and the noise of constraint 2; no modified tracked file except `.beads/interactions.jsonl`.

- [ ] **Step 2:** record the baseline.

```bash
make test
```

Expected: five summary lines whose passed counts sum to `603` (measured 2026-10-20: 473, 25, 12, 76, 17), no failures. Write the five numbers down; Tasks 9-13 add to the first line.

```bash
ruff check claude-home/hooks/
```

Expected: `Found 1 error.` (the pre-existing F401, `test_big_read_nudge.py:22`).

- [ ] **Step 3:** confirm the bd note flags used by Tasks 14-17.

```bash
bd update --help
```

Expected: the help lists `--notes` and `--append-notes`. Use `--append-notes` wherever a later step says "record in bd notes".

- [ ] **Step 4:** commit this plan.

```bash
git add docs/superpowers/plans/20261015-synonym-glossary-plan.md
```

```bash
git commit -m "docs(glossary): add the implementation plan of the project glossary" -m "Task-by-task plan for the approved design. Refs: python-ai-skills-du5"
```

Expected: pre-commit passes (gitleaks; `principles-ssot` runs on `*.md`); one commit with 1 file.


## Task 2: Parser of the `## Glossary` section — RED then GREEN

**Serves:** FR-1 (section, entry line, pointer line); FR-2 (optional definition and source); FR-11 (test file beside the check); FR-6 (exception lines carry a source); FR-10 (plain Markdown, no import); NFR-7 (line regexes); NFR-4 (pointer line).

**Files:** create `claude-home/hooks/test_glossary.py`, `claude-home/hooks/glossary.py` (both with the Write tool).

**Interfaces — produces:** `GlossaryError(ValueError)`; `Group(forms: tuple[str, ...], canonical: str, line: str)`; `Glossary(path: str, groups: tuple[Group, ...], exceptions: tuple[str, ...], lines: tuple[str, ...], pointed: bool)`; `cut_section(text: str, label: str) -> tuple[str, ...] | None`; `parse_section(lines, label) -> (groups, exceptions, pointer | None)`; constants `GLOSSARY_HEADING`, `INSTRUCTION_FILES`, `SECTION_MAX_LINES`, `MEMO_MAX_CHARS`, `GIT_TIMEOUT_S`, `JOURNAL`; regexes `ENTRY_RE`, `FORM_RE`, `POINTER_RE`, `EXCEPTION_RE`, `CYRILLIC`.

**Decision recorded here (design 4.1 vs 3.6):** a section may hold prose and fenced examples; only a *bullet* (`- ` or `* `) must be an entry or an exception line, otherwise it is a contract error. A `Glossary file:` line is a pointer only when it is the whole body of the section. The design text ("every non-blank line must match") would make the generator skeleton of Task 12 fail its own test, because the skeleton carries prose.

- [ ] **Step 1:** write the test file with the Write tool, exactly this content (the header docstring, the helpers and the parser tests; later tasks append to it).

````python
"""Tests for glossary.py — per-project synonym glossary: memo (UserPromptSubmit), stop (Stop), --staged (pre-commit).

A project keeps one `## Glossary` section in its AGENTS.md: one bullet per group of forbidden
synonyms with one canonical term. The memo delivers it before the answer, the Stop mode asks
for a one-line correction per forbidden form, the pre-commit mode refuses a commit that adds
one (bd python-ai-skills-du5). Isolation as in test_explanation_terms.py: a fake HOME and a
temporary git repository per test; fixtures are inline strings.
"""

import json
import subprocess
from pathlib import Path

import pytest

import glossary

HOOK = Path(__file__).resolve().parent / "glossary.py"
REPO = HOOK.parents[2]


def section_of(body):
    return glossary.cut_section("# Project\n\n## Glossary\n\n" + body + "\n", "test")


def parse(body):
    return glossary.parse_section(section_of(body), "test")


@pytest.mark.parametrize(
    ("line", "forms", "canonical"),
    [
        ("- «a», «b», «c d» → **term** — def text (English: x y)", ("a", "b", "c d"), "term"),
        ("- **solo** — only a definition", (), "solo"),
        ("- «реестр», «регистр» → **таблица**", ("реестр", "регистр"), "таблица"),
        ("- «TP (в значении параллелизма)», «амортизированно O(1)» → **x**", ("TP (в значении параллелизма)", "амортизированно O(1)"), "x"),
        ("* «a» → **b** — star bullet (источник: решение 2026-10-20)", ("a",), "b"),
    ],
)
def test_entry_line_parses(line, forms, canonical):
    groups, exceptions, pointer = parse(line)
    assert [(g.forms, g.canonical, g.line) for g in groups] == [(forms, canonical, line)]
    assert (exceptions, pointer) == ((), None)


@pytest.mark.parametrize(
    "line", ["- «x» → канонический без звёздочек", "- Исключение: «форма» без источника", "- просто пункт"]
)
def test_bullet_that_matches_no_form_is_a_contract_error(line):
    with pytest.raises(glossary.GlossaryError, match="matches no glossary form"):
        parse(line)


def test_exception_line_carries_a_source():
    groups, exceptions, _ = parse("- Исключение: «реестр моделей» — источник: model-registry.json")
    assert (groups, exceptions) == ((), ("реестр моделей",))


def test_prose_blank_lines_and_fenced_examples_are_skipped():
    body = "Проза без маркера.\n\n```text\n- «x» → без звёздочек\n```\n\n- «a» → **b**"
    groups, _, pointer = parse(body)
    assert [g.canonical for g in groups] == ["b"] and pointer is None


def test_only_the_example_block_gives_zero_groups():
    assert parse("```text\n- «a» → **b**\n```") == ((), (), None)


def test_section_ends_at_the_next_heading_of_any_level():
    text = "## Glossary\n\n- «a» → **b**\n\n### Exceptions\n\n- «c» → **d**\n"
    groups, _, _ = glossary.parse_section(glossary.cut_section(text, "t"), "t")
    assert [g.canonical for g in groups] == ["b"]


def test_two_glossary_headings_are_a_contract_error():
    with pytest.raises(glossary.GlossaryError, match="more than one"):
        glossary.cut_section("## Glossary\n\n- «a» → **b**\n\n## Glossary\n", "t")


def test_no_heading_means_no_section():
    assert glossary.cut_section("# T\n\n## Other\n\ntext\n", "t") is None


def test_single_pointer_line_is_a_pointer_with_blank_lines_allowed():
    assert parse("\nGlossary file: `glossary.md`\n\n") == ((), (), "glossary.md")


def test_pointer_line_among_prose_is_prose():
    groups, _, pointer = parse("Раздел больше 200 строк — одна строка:\nGlossary file: `glossary.md`")
    assert (groups, pointer) == ((), None)


def test_ml_sobes_form_fixture_of_twelve_rows():
    rows = "\n".join([
        "- «one-hot», «прямое кодирование» → **one-hot кодирование** — Вектор из нулей с единицей (English: one-hot encoding)",
        "- **таблица** — Данные в строках и столбцах (English: table)",
        "- «OOF» → **out-of-fold** — Признак по данным без объекта (English: out-of-fold)",
        "- «K» → **ключ** — Вектор ключа внимания (English: key)",
        "- «TP (в значении параллелизма)» → **тензорный параллелизм** — Разбиение слоя (English: tensor parallelism)",
        "- **precision** — Доля верных среди найденных (English: precision)",
        "- «пересэмплирование», «увеличение миноритарного класса» → **oversampling** — Дублирование (English: oversampling)",
        "- **recall@k** — Полнота в первых k (English: recall at k)",
        "- «амортизированно O(1)» → **амортизированная константа** — Средняя стоимость (English: amortized constant)",
        "- «фича» → **признак** — Столбец данных (English: feature)",
        "- **SMOTE** — Синтетические объекты (English: SMOTE)",
        "- «базовая модель» → **эталонная модель** — Модель для сравнения (English: baseline)",
    ])
    groups, _, _ = parse(rows)
    assert len(groups) == 12
    assert sum(len(g.forms) for g in groups) == 10
````

- [ ] **Step 2:** run it and see RED.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q
```

Expected: `1 error`: collection fails with `ModuleNotFoundError: No module named 'glossary'`.

- [ ] **Step 3:** write `claude-home/hooks/glossary.py` with the Write tool, exactly this content (header, constants, data types, `cut_section`, `parse_section`).

````python
#!/usr/bin/env python3
"""Project glossary hook: one canonical term per group of forbidden synonyms (bd python-ai-skills-du5).

A project keeps a `## Glossary` section in its AGENTS.md (or one pointer line to a separate
file): one bullet per group, `- «forbidden», «forbidden» → **canonical** — definition`. One
module, three modes, one matcher:

  memo     UserPromptSubmit: send the glossary (or the groups the prompt touches) before the answer
  stop     Stop: ask for one line `Поправка к термину: «X» → «Y»` per forbidden form in the last answer
  --staged pre-commit: report forbidden forms in the changed lines of staged files, exit 1 on findings

memo and stop are advisory (exit 0 on every path, no `decision`, silent without a glossary);
--staged is a gate (exit 0 / 1 findings / 2 glossary unreadable). Stdlib only.
See ~/.claude/CLAUDE.md -> "Explanation Protocol".
"""
import datetime
import difflib
import functools
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

GLOSSARY_HEADING = "## Glossary"
INSTRUCTION_FILES = ("AGENTS.md", "CLAUDE.md")  # first that is a regular file at the project root
SECTION_MAX_LINES = 200  # section form above this -> separate file
MEMO_MAX_CHARS = 8_000  # a memo carries the section or the touched groups only up to this (hook cap: 10,000)
GIT_TIMEOUT_S = 5  # Stop has 10 s, UserPromptSubmit 3 s
JOURNAL = Path.home() / ".claude" / "hook-stats" / "blocks.jsonl"

ENTRY_RE = re.compile(
    r"^[-*] (?:(?P<forms>«[^»]+»(?:, «[^»]+»)*) → )?\*\*(?P<canonical>[^*]+)\*\*"
    r"(?: — (?P<definition>.*?))?(?: \((?P<kind>источник|English): (?P<source>[^)]+)\))?\s*$"
)
FORM_RE = re.compile(r"«([^»]+)»")
POINTER_RE = re.compile(r"^Glossary file: `([^`]+)`\s*$")
EXCEPTION_RE = re.compile(r"^[-*] Исключение: «([^»]+)» — источник: (\S.*)$")

CYRILLIC = re.compile(r"[а-яёА-ЯЁ]")


class GlossaryError(ValueError):
    """The glossary breaks the contract: a bullet matching no form, two headings, an unreadable pointer."""


@dataclass(frozen=True)
class Group:
    forms: tuple  # forbidden forms, verbatim; empty for a group kept for the memo only
    canonical: str
    line: str


@dataclass(frozen=True)
class Glossary:
    path: str
    groups: tuple
    exceptions: tuple  # phrases in which a forbidden form is legal
    lines: tuple  # the cut section, heading included
    pointed: bool  # the groups come from a separate file


def cut_section(text, label):
    """Lines of the `## Glossary` section, heading to the line before the next `#` line; None without the heading."""
    lines = text.split("\n")
    starts = [i for i, line in enumerate(lines) if line.rstrip() == GLOSSARY_HEADING]
    if not starts:
        return None
    if len(starts) > 1:
        raise GlossaryError(f"{label}: more than one '{GLOSSARY_HEADING}' heading")
    end = next((i for i in range(starts[0] + 1, len(lines)) if lines[i].startswith("#")), len(lines))
    section = lines[starts[0]:end]
    while not section[-1].strip():
        section.pop()
    return tuple(section)


def parse_section(lines, label):
    """(groups, exceptions, pointer) of a cut section.

    Fenced lines and prose are skipped; a bullet that is neither an entry nor an exception raises GlossaryError.
    The pointer is the whole body: one `Glossary file: ...` line and nothing else."""
    body, fenced = [], False
    for number, line in enumerate(lines[1:], 2):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif line.strip() and not fenced:
            body.append((number, line))
    pointer = POINTER_RE.match(body[0][1]) if len(body) == 1 else None
    if pointer:
        return (), (), pointer.group(1)
    groups, exceptions = [], []
    for number, line in body:
        if not line.startswith(("- ", "* ")):
            continue
        exception, entry = EXCEPTION_RE.match(line), ENTRY_RE.match(line)
        if exception:
            exceptions.append(exception.group(1))
        elif entry:
            groups.append(Group(tuple(FORM_RE.findall(entry.group("forms") or "")), entry.group("canonical"), line))
        else:
            raise GlossaryError(f"{label}: section line {number}: bullet matches no glossary form: {line}")
    return tuple(groups), tuple(exceptions), None
````

- [ ] **Step 4:** see GREEN.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q
```

Expected: `17 passed`.

- [ ] **Step 5:** lint.

```bash
ruff check claude-home/hooks/glossary.py claude-home/hooks/test_glossary.py
```

Expected: `All checks passed!`

- [ ] **Step 6:** commit.

```bash
git add claude-home/hooks/glossary.py claude-home/hooks/test_glossary.py
```

```bash
git commit -m "feat(glossary): parse the Glossary section of a project instruction file" -m "Entry, exception and pointer lines; prose and fenced examples are skipped; a malformed bullet is a contract error. Refs: python-ai-skills-du5"
```

Expected: pre-commit passes (`hook-regression-tests` runs `pytest claude-home/hooks/`); one commit with 2 files.


## Task 3: Lookup: `cwd` -> project root -> instruction file -> section -> pointer

**Serves:** FR-4 (`cwd` lookup, heading as cut key, pointer as fallback); FR-10; NFR-4 (absolute pointer = one glossary per domain); NFR-5 (no file, no heading: no glossary).

**Files:** modify `claude-home/hooks/test_glossary.py`, `claude-home/hooks/glossary.py` (Edit tool).

**Interfaces — consumes:** Task 2 (`cut_section`, `parse_section`, `Glossary`, `GlossaryError`, `INSTRUCTION_FILES`, `GIT_TIMEOUT_S`). **Produces:** `git(root, *args) -> CompletedProcess` (bytes, timeout `GIT_TIMEOUT_S`); `project_root(cwd: str) -> Path`; `read_source(root, name: str, staged: bool) -> str | None`; `load_glossary(root, staged: bool = False) -> Glossary | None` (raises `GlossaryError`). Test helpers `sh`, `home`, `make_project`, `GLOSSARY_MD`.

- [ ] **Step 1:** append the lookup tests to `claude-home/hooks/test_glossary.py` (Edit tool; the anchor is the last test of Task 2).

`old_string`:

```text
    assert sum(len(g.forms) for g in groups) == 10
```

`new_string`:

```text
    assert sum(len(g.forms) for g in groups) == 10


def sh(cwd, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def home(tmp_path):
    path = tmp_path / "home"
    (path / ".claude").mkdir(parents=True)
    return path


def make_project(tmp_path, files, git=True):
    root = tmp_path / "project"
    root.mkdir()
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)
    if git:
        sh(root, "init", "-q")
    return root


GLOSSARY_MD = "# Project\n\n## Glossary\n\n- «фича» → **признак** — столбец данных\n- «лог» → **журнал**\n"


def test_lookup_reads_agents_md_at_the_root(tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": GLOSSARY_MD})
    found = glossary.load_glossary(root)
    assert [g.canonical for g in found.groups] == ["признак", "журнал"]
    assert (found.path, found.pointed) == (str(root / "AGENTS.md"), False)


def test_lookup_falls_back_to_claude_md_and_prefers_agents_md(tmp_path):
    only_claude = make_project(tmp_path, {"CLAUDE.md": GLOSSARY_MD})
    assert glossary.load_glossary(only_claude).path == str(only_claude / "CLAUDE.md")
    both = tmp_path / "both"
    both.mkdir()
    (both / "AGENTS.md").write_text("# P\n\nno glossary here\n")
    (both / "CLAUDE.md").write_text(GLOSSARY_MD)
    assert glossary.load_glossary(both) is None  # the first regular file wins, even without a glossary


def test_lookup_skips_a_directory_named_like_an_instruction_file(tmp_path):
    root = make_project(tmp_path, {"AGENTS.md/keep": "x", "CLAUDE.md": GLOSSARY_MD})
    assert glossary.load_glossary(root).path == str(root / "CLAUDE.md")


@pytest.mark.parametrize("files", [{}, {"AGENTS.md": "# P\n\n## Other\n\ntext\n"}])
def test_no_instruction_file_or_no_heading_means_no_glossary(tmp_path, files):
    assert glossary.load_glossary(make_project(tmp_path, files)) is None


def test_relative_pointer_reads_the_pointed_file(tmp_path):
    root = make_project(tmp_path, {
        "AGENTS.md": "# P\n\n## Glossary\n\nGlossary file: `glossary.md`\n",
        "glossary.md": "# G\n\nheader\n\n" + GLOSSARY_MD.split("# Project\n\n")[1] + "\n## Спорные выборы\n\n1. проза\n",
    })
    found = glossary.load_glossary(root)
    assert found.pointed and found.path == str(root / "glossary.md")
    assert [g.canonical for g in found.groups] == ["признак", "журнал"]


def test_absolute_pointer_reaches_another_domain(tmp_path):
    shared = tmp_path / "shared.md"
    shared.write_text(GLOSSARY_MD)
    root = make_project(tmp_path, {"AGENTS.md": f"## Glossary\n\nGlossary file: `{shared}`\n"})
    assert glossary.load_glossary(root).path == str(shared)


@pytest.mark.parametrize(
    ("pointed", "reason"),
    [(None, "unreadable"), ("# G\n\nno heading\n", "no '## Glossary' heading"), ("## Glossary\n\nGlossary file: `x.md`\n", "must not point further")],
)
def test_broken_pointer_is_a_contract_error(tmp_path, pointed, reason):
    files = {"AGENTS.md": "## Glossary\n\nGlossary file: `glossary.md`\n"}
    if pointed is not None:
        files["glossary.md"] = pointed
    with pytest.raises(glossary.GlossaryError, match=reason):
        glossary.load_glossary(make_project(tmp_path, files))


def test_project_root_of_a_subdirectory_is_the_git_root(tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": GLOSSARY_MD, "sub/x.txt": "x"})
    assert glossary.project_root(str(root / "sub")) == root.resolve()


def test_project_root_outside_git_is_the_directory_itself(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    assert glossary.project_root(str(plain)) == plain
```

- [ ] **Step 2:** RED.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q
```

Expected: `12 failed, 17 passed` (the 12 new tests fail with `AttributeError: module 'glossary' has no attribute ...`).

- [ ] **Step 3:** append the lookup code to `claude-home/hooks/glossary.py` (Edit tool).

`old_string`:

```text
    return tuple(groups), tuple(exceptions), None
```

`new_string`:

```text
    return tuple(groups), tuple(exceptions), None


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=GIT_TIMEOUT_S)


def project_root(cwd):
    """The git work tree of cwd, else cwd itself (a worktree resolves to its own root)."""
    try:
        result = git(cwd or ".", "rev-parse", "--show-toplevel")
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.decode().strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return Path(cwd or ".")


def read_source(root, name, staged):
    """Text of a file: from the git index under `staged` (falling back to disk), else from disk; None if unreadable."""
    if staged:
        result = git(root, "show", f":{name}")
        if result.returncode == 0:
            return result.stdout.decode("utf-8", "replace")
    try:
        return (Path(root) / name).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def load_glossary(root, staged=False):
    """The glossary of the project at root; None when it has none; GlossaryError when it is unreadable."""
    for name in INSTRUCTION_FILES:
        text = read_source(root, name, staged)
        if text is not None:
            break
    else:
        return None
    label = str(Path(root) / name)
    section = cut_section(text, label)
    if section is None:
        return None
    groups, exceptions, pointer = parse_section(section, label)
    if pointer is None:
        return Glossary(label, groups, exceptions, section, False)
    target = str(Path(root) / pointer)
    pointed_text = read_source(root, pointer, staged)
    if pointed_text is None:
        raise GlossaryError(f"{label}: pointed file {target} is unreadable")
    section = cut_section(pointed_text, target)
    if section is None:
        raise GlossaryError(f"{target}: no '{GLOSSARY_HEADING}' heading")
    groups, exceptions, again = parse_section(section, target)
    if again:
        raise GlossaryError(f"{target}: a pointed glossary must not point further")
    return Glossary(target, groups, exceptions, section, True)
```

- [ ] **Step 4:** GREEN and lint.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q
```

Expected: `29 passed`.

```bash
ruff check claude-home/hooks/glossary.py claude-home/hooks/test_glossary.py
```

Expected: `All checks passed!`

- [ ] **Step 5:** commit.

```bash
git add claude-home/hooks/glossary.py claude-home/hooks/test_glossary.py
```

```bash
git commit -m "feat(glossary): find the project glossary from the working directory" -m "Git root of cwd, AGENTS.md before CLAUDE.md, one-hop pointer to a relative or absolute file, index or disk source. Refs: python-ai-skills-du5"
```


## Task 4: Matcher: exemptions, case endings, boundaries, `scan_text`

**Serves:** FR-5a and FR-5b (the shared matcher); FR-6 (identifiers, fences, backticks, «», links, English lines, exception phrases); NFR-2 (regex only, stdlib only); FR-3 (governed text = every Cyrillic line).

**Files:** modify `claude-home/hooks/test_glossary.py`, `claude-home/hooks/glossary.py`.

**Interfaces — consumes:** Task 2 (`Glossary`, `Group`, `CYRILLIC`), test helpers `parse`, `section_of`. **Produces:** `word_regex(word)`, `form_regex(form) -> re.Pattern` (cached per form), `governed_lines(text) -> list[str]`, `Finding(line_no: int, form: str, canonical: str)`, `scan_text(text, glossary, only_lines: set[int] | None = None) -> list[Finding]`, `changed_lines(head_text: str | None, new_text: str) -> set[int]`, constants `ENDINGS`, `BOUNDARY_L`, `BOUNDARY_R`, `IDENT_RE`, `TOKEN_EDGES`.

- [ ] **Step 1:** append the matcher tests (Edit tool; they are the probes of design 4.6 as parametrised cases, one exemption per case).

`old_string`:

```text
    assert glossary.project_root(str(plain)) == plain
```

`new_string`:

````text
    assert glossary.project_root(str(plain)) == plain


MATCH_BODY = "\n".join([
    "- «реестр», «регистр» → **таблица**",
    "- «запись» → **строка**",
    "- «OOF» → **out-of-fold**",
    "- «k-fold» → **блочная проверка**",
    "- «TP» → **истинно положительный**",
    "- «K» → **ключ**",
    "- «dev set» → **отложенная выборка**",
    "- «кросс-валидация» → **перекрёстная проверка**",
    "- «валидация» → **проверка**",
    "- «scale_pos_weight» → **вес класса**",
    "- Исключение: «реестр моделей» — источник: model-registry.json",
])


def matcher():
    groups, exceptions, _ = parse(MATCH_BODY)
    return glossary.Glossary("test", groups, exceptions, section_of(MATCH_BODY), False)


def forms_in(text):
    return [f.form for f in glossary.scan_text(text, matcher())]


@pytest.mark.parametrize(
    "text",
    ["Это реестр данных", "Реестр данных", "в реестре", "реестром", "реестры", "о реестрах", "из реестра"],
)
def test_cyrillic_form_matches_case_and_endings(text):
    assert forms_in(text) == ["реестр"]


@pytest.mark.parametrize("text", ["записать данные", "записка автору", "табличный вид", "реестровый номер"])
def test_near_words_do_not_match(text):
    assert forms_in(text) == []


def test_form_with_final_vowel_keeps_its_case_endings():
    assert forms_in("новая запись, две записи, о записях, записью") == ["запись", "запись", "запись", "запись"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("слово OOF здесь", ["OOF"]),
        ("слово OOFS здесь", []),
        ("слово oof здесь", []),
        ("слово k-fold здесь", ["k-fold"]),
        ("слово k-folds здесь", []),
        ("слово K-fold здесь", []),
        ("слово TP здесь", ["TP"]),
        ("слово tp и TPU здесь", []),
        ("слово Q, K, V здесь", ["K"]),
        ("слово K=5 здесь", ["K"]),
        ("слово Ключ здесь", []),
        ("слово dev set здесь", ["dev set"]),
        ("слово dev sets и Dev Set здесь", []),
        ("слово dev   set здесь", ["dev set"]),
    ],
)
def test_latin_forms_are_literal_and_short_ones_whole_token(text, expected):
    assert forms_in(text) == expected


@pytest.mark.parametrize("text", ["слово реестр-сводка здесь", "слово DNS-реестр здесь", "слово реестр_x здесь"])
def test_a_hyphen_or_underscore_is_a_boundary_on_both_sides(text):
    assert forms_in(text) == []


@pytest.mark.parametrize(
    "text",
    [
        "слово `реестр` здесь",
        "слово «реестр» здесь",
        "```\nреестр\n```\nслово здесь",
        "слово [реестр](https://example.org/a) здесь",
        "слово https://example.org/реестр здесь",
        "слово scale_pos_weight здесь",
        "слово registry.jsonl и docs/plan.md здесь",
        "слово camelCase и HTTPServer и reverse-WireGuard здесь",
        "слово H0 здесь",
        "English line with OOF in prose and nothing else",
    ],
)
def test_exempt_spans_are_not_read(text):
    assert forms_in(text) == []


def test_english_line_with_a_forbidden_latin_form_is_silent_and_the_same_form_on_a_cyrillic_line_fires():
    assert forms_in("This line has OOF in English prose.\nА здесь OOF в русской строке.") == ["OOF"]


def test_all_capital_abbreviation_stays_checkable_but_an_identifier_does_not():
    assert forms_in("слово OOF здесь и OOF_x там") == ["OOF"]


def test_exception_phrase_overlapping_a_form_drops_the_finding():
    assert forms_in("слово реестр моделей здесь") == []
    assert forms_in("слово реестр здесь и реестр моделей там") == ["реестр"]


def test_the_longest_form_wins_over_a_form_inside_it():
    assert forms_in("слово кросс-валидация здесь") == ["кросс-валидация"]
    assert forms_in("слово валидация здесь") == ["валидация"]


def test_findings_carry_line_number_form_and_canonical_in_text_order():
    found = glossary.scan_text("первая строка\nслово регистр и запись", matcher())
    assert found == [glossary.Finding(2, "регистр", "таблица"), glossary.Finding(2, "запись", "строка")]


def test_only_lines_limits_the_report():
    text = "слово реестр\nслово регистр"
    assert [f.line_no for f in glossary.scan_text(text, matcher(), only_lines={2})] == [2]


def test_changed_lines_marks_replaced_and_inserted_lines_only():
    assert glossary.changed_lines("a\nb\nc", "a\nB\nc\nd") == {2, 4}
    assert glossary.changed_lines(None, "a\nb") == {1, 2}
````

- [ ] **Step 2:** RED.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q
```

Expected: `46 failed, 29 passed` (the 46 new tests fail with `AttributeError`).

- [ ] **Step 3:** append the matcher code to `claude-home/hooks/glossary.py`.

`old_string`:

```text
    return Glossary(target, groups, exceptions, section, True)
```

`new_string`:

````text
    return Glossary(target, groups, exceptions, section, True)


ENDINGS = r"(?:а|я|у|ю|е|ы|и|о|ом|ем|ём|ой|ей|ов|ев|ам|ям|ами|ями|ах|ях|ью|ь|й)?"
BOUNDARY_L = r"(?<![а-яёА-ЯЁA-Za-z0-9_-])"
BOUNDARY_R = r"(?![а-яёА-ЯЁA-Za-z0-9_-])"
IDENT_RE = re.compile(
    r"[A-Za-z0-9_./-]*(?:[_/]|[0-9]|\.[A-Za-z])[A-Za-z0-9_./-]*"  # _ / digit inner dot: scale_pos_weight, docs/plan.md, H0
    r"|(?=[A-Za-z-]*[a-z])[A-Za-z][A-Za-z-]*[A-Z][A-Za-z-]*"  # a capital after the first letter and a lowercase one: camelCase
)
TOKEN_EDGES = ".,;:!?()[]{}\"'«»*—–"


def word_regex(word):
    """A Cyrillic word: stem plus case endings; a Latin word: literal."""
    if CYRILLIC.search(word):
        stem = word[:-1] if word[-1] in "аяоеиыуюэёьй" else word
        return re.escape(stem) + ENDINGS
    return re.escape(word)


@functools.lru_cache(maxsize=None)
def form_regex(form):
    """One form: words joined by any blanks; Cyrillic forms ignore case, Latin forms are literal."""
    body = r"\s+".join(word_regex(w) for w in form.split())
    return re.compile(BOUNDARY_L + body + BOUNDARY_R, re.IGNORECASE if CYRILLIC.search(form) else 0)


def blank(match):
    return re.sub(r"[^\n]", " ", match.group())


def blank_ident(match):
    core = match.group().strip(TOKEN_EDGES)
    return blank(match) if core and IDENT_RE.fullmatch(core) else match.group()


def governed_lines(text):
    """The lines of text with every exempt span replaced by spaces (offsets and line numbers survive)."""
    out, fenced = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out.append(" " * len(line))
        else:
            out.append(" " * len(line) if fenced else line)
    text = "\n".join(out)
    for exempt in (r"`[^`\n]*`", r"«[^»\n]*»", r"\[[^\]\n]*\]\([^)\n]*\)", r"https?://\S+"):
        text = re.sub(exempt, blank, text)
    return re.sub(r"\S+", blank_ident, text).split("\n")


@dataclass(frozen=True)
class Finding:
    line_no: int
    form: str
    canonical: str


def scan_text(text, glossary, only_lines=None):
    """Forbidden forms of the glossary in text, outside the exempt spans, on Cyrillic lines only.

    only_lines: 1-based line numbers to report (None: all). A form inside a longer form's match,
    or overlapping an exception phrase, is not reported."""
    pairs = [(form, group.canonical) for group in glossary.groups for form in group.forms]
    findings = []
    for line_no, line in enumerate(governed_lines(text), 1):
        if (only_lines is not None and line_no not in only_lines) or not CYRILLIC.search(line):
            continue
        excused = [m.span() for phrase in glossary.exceptions for m in form_regex(phrase).finditer(line)]
        found = [
            (m.start(), m.end(), form, canonical)
            for form, canonical in pairs
            for m in form_regex(form).finditer(line)
            if not any(m.start() < end and start < m.end() for start, end in excused)
        ]
        kept = []
        for start, end, form, canonical in sorted(found, key=lambda f: f[0] - f[1]):  # longest first, stable
            if not any(k[0] <= start and end <= k[1] for k in kept):
                kept.append((start, end, form, canonical))
        findings += [Finding(line_no, form, canonical) for _, _, form, canonical in sorted(kept)]
    return findings


def changed_lines(head_text, new_text):
    """1-based numbers of the lines of new_text that differ from head_text; head_text None: every line is new."""
    new_lines = new_text.split("\n")
    if head_text is None:
        return set(range(1, len(new_lines) + 1))
    matcher = difflib.SequenceMatcher(None, head_text.split("\n"), new_lines, autojunk=False)
    changed = set()
    for tag, _, _, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "insert"):
            changed.update(range(j1 + 1, j2 + 1))
    return changed
````

- [ ] **Step 4:** GREEN and lint.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q
```

Expected: `75 passed`.

```bash
ruff check claude-home/hooks/glossary.py claude-home/hooks/test_glossary.py
```

Expected: `All checks passed!`

- [ ] **Step 5:** commit.

```bash
git add claude-home/hooks/glossary.py claude-home/hooks/test_glossary.py
```

```bash
git commit -m "feat(glossary): match forbidden forms with case endings and exemptions" -m "Symmetric hyphen boundary, whole-token short forms, longest form wins, identifier shapes and quoted spans are not read. Refs: python-ai-skills-du5"
```


## Task 5: Mode `memo` (UserPromptSubmit)

**Serves:** FR-3 (the glossary reaches the answer); FR-4 (live sessions, `cwd`); NFR-1 (three memo forms under the 10,000-character cap); NFR-3 (advisory: exit 0, no `decision`, nothing on stderr); NFR-5 (silence without a glossary, no journal noise).

**Files:** modify `claude-home/hooks/test_glossary.py`, `claude-home/hooks/glossary.py`.

**Interfaces — consumes:** Tasks 2-4. **Produces:** `log_record(detail: dict) -> None` (never raises; JSONL record with `ts`, `hook: "glossary"`, `cwd`, `**detail`); `emit(event, context)`; `memo_context(glossary, prompt) -> str` (whole section, else touched groups, else pointer text); `read_event() -> dict | None`; `run_memo(data) -> int`; `HOOKS` dict; `main(argv) -> int`; test helpers `run_mode`, `memo`, `context_of`, `silent`, `groups_section`.

- [ ] **Step 1:** append the memo tests.

`old_string`:

```text
    assert glossary.changed_lines(None, "a\nb") == {1, 2}
```

`new_string`:

```text
    assert glossary.changed_lines(None, "a\nb") == {1, 2}


def run_mode(mode, payload, home, cwd=None):
    return subprocess.run(
        ["python3", str(HOOK), mode],
        input=payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False),
        capture_output=True,
        text=True,
        timeout=30,
        cwd=cwd,
        env={"PATH": "/usr/bin:/bin", "HOME": str(home)},
    )


def memo(home, root, prompt="привет", **extra):
    return run_mode("memo", {"hook_event_name": "UserPromptSubmit", "prompt": prompt, "cwd": str(root), **extra}, home)


def context_of(result, event):
    assert result.returncode == 0 and result.stderr == ""
    out = json.loads(result.stdout)
    assert "decision" not in out and out["hookSpecificOutput"]["hookEventName"] == event
    return out["hookSpecificOutput"]["additionalContext"]


def silent(result):
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def groups_section(count, prefix="термин"):
    return "".join(f"- «{prefix}{i}» → **канон{i}** — определение {i}\n" for i in range(count))


def test_memo_sends_the_whole_section_of_a_small_glossary(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": GLOSSARY_MD + "\n## Другое\n\nSTAYS-OUT\n"})
    context = context_of(memo(home, root), "UserPromptSubmit")
    assert "- «фича» → **признак** — столбец данных" in context and "STAYS-OUT" not in context
    assert str(root / "AGENTS.md") in context and "only the canonical terms" in context


def test_memo_resolves_a_subdirectory_to_the_project_root(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": GLOSSARY_MD, "sub/x.txt": "x"})
    assert "«фича»" in context_of(memo(home, root / "sub"), "UserPromptSubmit")


def test_memo_reads_claude_md_when_it_is_the_instruction_file(home, tmp_path):
    root = make_project(tmp_path, {"CLAUDE.md": GLOSSARY_MD})
    assert "«фича»" in context_of(memo(home, root), "UserPromptSubmit")


def test_memo_of_a_pointed_glossary_sends_only_the_touched_groups_in_file_order(home, tmp_path):
    root = make_project(tmp_path, {
        "AGENTS.md": "## Glossary\n\nGlossary file: `glossary.md`\n",
        "glossary.md": "## Glossary\n\n" + groups_section(30),
    })
    context = context_of(memo(home, root, prompt="что значит канон7 и термин3?"), "UserPromptSubmit")
    sent = [line for line in context.splitlines() if line.startswith("- ")]
    assert sent == ["- «термин3» → **канон3** — определение 3", "- «термин7» → **канон7** — определение 7"]
    assert "2 of 30 groups" in context


def test_memo_of_a_pointed_glossary_with_nothing_touched_sends_the_pointer(home, tmp_path):
    root = make_project(tmp_path, {
        "AGENTS.md": "## Glossary\n\nGlossary file: `glossary.md`\n",
        "glossary.md": "## Glossary\n\n" + groups_section(30),
    })
    context = context_of(memo(home, root, prompt="совсем другая тема"), "UserPromptSubmit")
    assert "30 groups" in context and "- «" not in context and "glossary.md" in context


@pytest.mark.parametrize(
    "section",
    [groups_section(201), "".join(f"- «т{i}» → **к{i}** — {'д' * 100}\n" for i in range(80))],
    ids=["201 lines", "over 8,000 characters"],
)
def test_memo_of_an_oversized_section_falls_back_to_the_pointer(home, tmp_path, section):
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\n" + section})
    context = context_of(memo(home, root, prompt="совсем другая тема"), "UserPromptSubmit")
    assert "groups," in context and "- «" not in context


def test_memo_caps_the_touched_groups_at_the_character_limit(home, tmp_path):
    section = "".join(f"- «слово» → **канон{i}** — {'д' * 200}\n" for i in range(60))
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\nGlossary file: `g.md`\n", "g.md": "## Glossary\n\n" + section})
    context = context_of(memo(home, root, prompt="слово"), "UserPromptSubmit")
    assert len(context) <= glossary.MEMO_MAX_CHARS + 400 and "groups touched" in context


@pytest.mark.parametrize("payload", ["", "not json", "[]", "42"])
def test_memo_malformed_input_is_silent(home, tmp_path, payload):
    root = make_project(tmp_path, {"AGENTS.md": GLOSSARY_MD})
    silent(run_mode("memo", payload, home, cwd=root))


def test_memo_without_a_glossary_is_silent_and_writes_no_journal(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": "# P\n\nno glossary\n"})
    silent(memo(home, root))
    assert not (home / ".claude" / "hook-stats").exists()


def test_memo_without_git_or_instruction_file_is_silent(home, tmp_path):
    silent(memo(home, make_project(tmp_path, {}, git=False)))


def test_memo_with_a_broken_pointer_is_silent_and_journals_the_error(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\nGlossary file: `absent.md`\n"})
    silent(memo(home, root))
    record = json.loads((home / ".claude" / "hook-stats" / "blocks.jsonl").read_text().splitlines()[-1])
    assert (record["hook"], record["mode"]) == ("glossary", "memo") and "unreadable" in record["error"]


def test_unknown_mode_is_a_usage_error(home):
    result = run_mode("bogus", {}, home)
    assert result.returncode == 2 and "usage" in result.stderr
```

- [ ] **Step 2:** RED.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q
```

Expected: `10 failed, 81 passed` (the 6 silence tests pass vacuously, because the module has no `main` yet and prints nothing; the 10 tests that expect output fail).

- [ ] **Step 3:** append the journal, memo and entry-point code.

`old_string`:

```text
    return changed
```

`new_string`:

```text
    return changed


def log_record(detail):
    """Append one JSONL record to the hook journal (the explanation-terms.py shape); never raises."""
    try:
        JOURNAL.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        record = {"ts": stamp, "hook": "glossary", "cwd": os.getcwd(), **detail}
        with open(JOURNAL, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def emit(event, context):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": context}}, ensure_ascii=False))


def memo_context(glossary, prompt):
    """The text a memo sends: the whole section, else the groups the prompt touches, else a pointer."""
    section = "\n".join(glossary.lines)
    if not glossary.pointed and len(glossary.lines) <= SECTION_MAX_LINES and len(section) <= MEMO_MAX_CHARS:
        return f"Project glossary from {glossary.path} (the only copy); use only the canonical terms in this answer:\n\n{section}"
    picked, total = [], 0
    for group in glossary.groups:
        if any(form_regex(term).search(prompt) for term in (group.canonical, *group.forms)):
            total += len(group.line) + 1
            if total > MEMO_MAX_CHARS:
                break
            picked.append(group.line)
    if picked:
        return (
            f"Project glossary {glossary.path}: {len(picked)} of {len(glossary.groups)} groups touched by this prompt "
            "(the file has the rest); use only the canonical terms:\n\n" + "\n".join(picked)
        )
    return (
        f"Project glossary: {glossary.path}, {len(glossary.groups)} groups, {len(glossary.lines)} lines. "
        "Read it before naming a thing; use only its canonical terms in this answer."
    )


def read_event():
    """The hook input: a JSON object, else None."""
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def run_memo(data):
    glossary = load_glossary(project_root(data.get("cwd") or ""))
    if glossary:
        emit("UserPromptSubmit", memo_context(glossary, data.get("prompt") or ""))
    return 0


HOOKS = {"memo": run_memo}


def main(argv):
    mode = argv[1] if len(argv) > 1 else ""
    if mode not in HOOKS:
        print("usage: glossary.py memo | stop | --staged", file=sys.stderr)
        return 2
    try:
        data = read_event()
        return HOOKS[mode](data) if data is not None else 0
    except Exception as exc:  # advisory hooks never fail a turn; the journal keeps the cause
        log_record({"mode": mode, "error": f"{type(exc).__name__}: {exc}"})
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4:** GREEN and lint.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q
```

Expected: `91 passed`.

```bash
ruff check claude-home/hooks/glossary.py claude-home/hooks/test_glossary.py
```

Expected: `All checks passed!`

- [ ] **Step 5:** commit.

```bash
git add claude-home/hooks/glossary.py claude-home/hooks/test_glossary.py
```

```bash
git commit -m "feat(glossary): add the memo mode that sends the glossary before the answer" -m "Whole section up to 200 lines and 8,000 characters, otherwise the groups the prompt touches, otherwise a pointer; silent without a glossary. Refs: python-ai-skills-du5"
```


## Task 6: Mode `stop` (Stop)

**Serves:** FR-5a (one line per finding, never blocks); NFR-3 (exit 0 on every path, no `decision`); NFR-6 (journal record, `hook` = `glossary`); NFR-5.

**Files:** modify `claude-home/hooks/test_glossary.py`, `claude-home/hooks/glossary.py`.

**Interfaces — consumes:** Tasks 2-5 (`scan_text`, `emit`, `log_record`, `HOOKS`). **Produces:** `stop_context(glossary, findings) -> str` (distinct forms, first occurrence order); `run_stop(data) -> int`; `HOOKS["stop"]`; test helpers `stop`, `project` fixture, `FORMS_BODY`, `LONG_RU`.

- [ ] **Step 1:** append the stop tests.

`old_string`:

```text
    assert result.returncode == 2 and "usage" in result.stderr
```

`new_string`:

```text
    assert result.returncode == 2 and "usage" in result.stderr


FORMS_BODY = "- «кросс-валидация» → **перекрёстная проверка**\n- «фича» → **признак**\n- «лог» → **журнал**\n"
LONG_RU = "Это сообщение написано по-русски, чтобы строка считалась русской. "


def stop(home, root, message, **extra):
    return run_mode("stop", {"hook_event_name": "Stop", "last_assistant_message": message, "cwd": str(root), **extra}, home)


@pytest.fixture
def project(tmp_path):
    return make_project(tmp_path, {"AGENTS.md": "## Glossary\n\n" + FORMS_BODY})


def test_stop_asks_for_one_line_per_forbidden_form_without_blocking(home, project):
    context = context_of(stop(home, project, LONG_RU + "Нужна кросс-валидация и ещё одна фича."), "Stop")
    assert "«кросс-валидация» → «перекрёстная проверка»" in context and "«фича» → «признак»" in context
    assert "Поправка к термину: «<form>» → «<canonical>»" in context and "ALREADY READ" in context


def test_stop_lists_each_distinct_form_once_in_order_of_first_occurrence(home, project):
    context = context_of(stop(home, project, LONG_RU + "Фича, потом лог, потом снова фича.\nИ ещё одна фича."), "Stop")
    listed = context.split("project glossary: ", 1)[1].split(".\n", 1)[0]
    assert listed == "«фича» → «признак», «лог» → «журнал»"


def test_stop_is_silent_when_the_message_uses_canonical_terms_only(home, project):
    silent(stop(home, project, LONG_RU + "Здесь только признак и журнал."))


def test_stop_is_silent_when_a_stop_hook_is_already_continuing(home, project):
    silent(stop(home, project, LONG_RU + "Фича.", stop_hook_active=True))


@pytest.mark.parametrize("payload", ["", "not json", "[]", "42"])
def test_stop_malformed_input_is_silent(home, project, payload):
    silent(run_mode("stop", payload, home, cwd=project))


def test_stop_without_a_glossary_is_silent_and_writes_no_journal(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": "# P\n\nplain\n"})
    silent(stop(home, root, LONG_RU + "Фича."))
    assert not (home / ".claude" / "hook-stats").exists()


def test_stop_journals_the_findings_under_the_glossary_hook_name(home, project):
    stop(home, project, LONG_RU + "Фича и лог.")
    record = json.loads((home / ".claude" / "hook-stats" / "blocks.jsonl").read_text().splitlines()[-1])
    assert (record["hook"], record["mode"], record["cwd"]) == ("glossary", "stop", str(project))
    assert record["findings"] == [["фича", "признак"], ["лог", "журнал"]]
    assert record["glossary"] == str(project / "AGENTS.md") and record["ts"].endswith("+00:00")


def test_stop_still_answers_when_the_journal_cannot_be_written(home, project):
    (home / ".claude").rmdir()
    (home / ".claude").write_text("a file where the journal directory should be")
    assert "«фича» → «признак»" in context_of(stop(home, project, LONG_RU + "Фича."), "Stop")


def test_stop_with_a_broken_pointer_is_silent(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\nGlossary file: `absent.md`\n"})
    silent(stop(home, root, LONG_RU + "Фича."))
```

- [ ] **Step 2:** RED.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q
```

Expected: `12 failed, 91 passed`.

- [ ] **Step 3:** add the stop code before the `HOOKS` line and register the mode.

`old_string`:

```text
HOOKS = {"memo": run_memo}
```

`new_string`:

```text
def stop_context(glossary, findings):
    """The one-line correction request for the distinct forbidden forms of the last message."""
    forms = {}
    for finding in findings:
        forms.setdefault(finding.form, finding.canonical)
    listed = ", ".join(f"«{form}» → «{canonical}»" for form, canonical in forms.items())
    return (
        f"GLOSSARY {glossary.path}: these forms in your last message are forbidden synonyms of the project glossary: {listed}.\n\n"
        "The user has ALREADY READ that message. Do NOT repeat, rewrite or quote it; no paragraphs, no apology. "
        "Reply with exactly one line per form and nothing else:\n"
        "  Поправка к термину: «<form>» → «<canonical>»\n"
        "See ~/.claude/CLAUDE.md -> 'Explanation Protocol'."
    )


def run_stop(data):
    glossary = None if data.get("stop_hook_active") else load_glossary(project_root(data.get("cwd") or ""))
    findings = scan_text(data.get("last_assistant_message") or "", glossary) if glossary else []
    if findings:
        log_record({"cwd": data.get("cwd") or "", "mode": "stop", "glossary": glossary.path, "findings": [[f.form, f.canonical] for f in findings]})
        emit("Stop", stop_context(glossary, findings))
    return 0


HOOKS = {"memo": run_memo, "stop": run_stop}
```

- [ ] **Step 4:** GREEN and lint.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q
```

Expected: `103 passed`.

```bash
ruff check claude-home/hooks/glossary.py claude-home/hooks/test_glossary.py
```

Expected: `All checks passed!`

- [ ] **Step 5:** commit.

```bash
git add claude-home/hooks/glossary.py claude-home/hooks/test_glossary.py
```

```bash
git commit -m "feat(glossary): add the stop mode that asks one correction line per forbidden form" -m "No decision field, no rewrite request; findings are journaled in blocks.jsonl under hook glossary. Refs: python-ai-skills-du5"
```


## Task 7: Mode `--staged` (pre-commit)

**Serves:** FR-5b (`<path>:<line>: «form» → «canonical»`, exit 0 / 1 / 2); FR-6; NFR-2 (changed lines only, one `git show` per staged path); NFR-3 (the commit gate); NFR-5 (silence without a glossary); NFR-6; NFR-4 (absolute pointer under `--staged`).

**Files:** modify `claude-home/hooks/test_glossary.py`, `claude-home/hooks/glossary.py`.

**Interfaces — consumes:** Tasks 2-6 (`load_glossary(root, staged=True)`, `scan_text(..., only_lines)`, `changed_lines`, `git`, `project_root`, `log_record`). **Produces:** `run_staged() -> int`; the `--staged` branch of `main`; test helpers `staged`, `committed` fixture.

**Decision point for the user (Task 14):** the test `test_staged_checks_the_glossary_file_itself_for_foreign_forbidden_forms` encodes the design as approved (a definition that uses another group's forbidden form is a finding). The conversion of the ML_Sobes glossary measured in Task 14 shows 327 such findings in its own definitions; if the user chooses to exempt entry lines, Task 15 replaces that test and adds 3 lines.

- [ ] **Step 1:** append the staged tests.

`old_string`:

```text
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\nGlossary file: `absent.md`\n"})
    silent(stop(home, root, LONG_RU + "Фича."))
```

`new_string`:

```text
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\nGlossary file: `absent.md`\n"})
    silent(stop(home, root, LONG_RU + "Фича."))


def staged(home, root):
    return subprocess.run(
        ["python3", str(HOOK), "--staged"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=root,
        env={"PATH": "/usr/bin:/bin", "HOME": str(home)},
    )


@pytest.fixture
def committed(tmp_path):
    """A project whose HEAD holds the glossary and a notes file with one old forbidden form."""
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\n" + FORMS_BODY, "notes.md": "Старая фича в тексте.\nВторая строка.\n"})
    sh(root, "add", "-A")
    sh(root, "commit", "-q", "-m", "init")
    return root


def test_staged_reports_only_the_new_forbidden_line_and_exits_1(home, committed):
    (committed / "notes.md").write_text("Старая фича в тексте.\nВторая строка.\nНовый лог добавлен.\n")
    sh(committed, "add", "notes.md")
    result = staged(home, committed)
    assert (result.returncode, result.stdout, result.stderr) == (1, "notes.md:3: «лог» → «журнал»\n", "")
    record = json.loads((home / ".claude" / "hook-stats" / "blocks.jsonl").read_text().splitlines()[-1])
    assert (record["hook"], record["mode"], record["findings"]) == ("glossary", "staged", [["notes.md", 3, "лог", "журнал"]])


def test_staged_without_a_new_forbidden_form_passes_silently(home, committed):
    (committed / "notes.md").write_text("Старая фича в тексте.\nВторая строка изменена.\n")
    sh(committed, "add", "notes.md")
    result = staged(home, committed)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def test_staged_new_file_is_scanned_in_full(home, committed):
    (committed / "new.md").write_text("Строка раз.\nЛог тут.\n")
    sh(committed, "add", "new.md")
    assert staged(home, committed).stdout == "new.md:2: «лог» → «журнал»\n"


def test_staged_binary_file_is_skipped(home, committed):
    (committed / "blob.bin").write_bytes(b"\x00\xff\xfe" + "фича".encode())
    sh(committed, "add", "blob.bin")
    assert staged(home, committed).returncode == 0


def test_staged_reads_the_glossary_from_the_index_not_the_working_tree(home, committed):
    (committed / "AGENTS.md").write_text("## Glossary\n\n" + FORMS_BODY + "- «шина» → **канал**\n")  # edited, not staged
    (committed / "bus.md").write_text("Слово шина тут.\n")
    sh(committed, "add", "bus.md")
    assert staged(home, committed).returncode == 0


def test_staged_without_a_glossary_exits_0_silently(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": "# P\n\nplain\n", "a.md": "Фича.\n"})
    sh(root, "add", "-A")
    result = staged(home, root)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    assert not (home / ".claude" / "hook-stats").exists()


def test_staged_contract_error_exits_2_with_the_reason(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\n- «x» → без звёздочек\n"})
    sh(root, "add", "-A")
    result = staged(home, root)
    assert result.returncode == 2 and result.stdout.startswith("glossary: ") and "matches no glossary form" in result.stdout


def test_staged_broken_pointer_exits_2(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\nGlossary file: `absent.md`\n"})
    sh(root, "add", "-A")
    assert staged(home, root).returncode == 2


def test_staged_checks_the_glossary_file_itself_for_foreign_forbidden_forms(home, tmp_path):
    body = "- «лог» → **журнал** — то же, что фича\n- «фича» → **признак**\n"
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\n" + body})
    sh(root, "add", "-A")
    assert staged(home, root).stdout == "AGENTS.md:3: «фича» → «признак»\n"


def test_staged_follows_an_absolute_pointer_outside_the_repository(home, tmp_path):
    shared = tmp_path / "shared.md"
    shared.write_text("## Glossary\n\n" + FORMS_BODY)
    root = make_project(tmp_path, {"AGENTS.md": f"## Glossary\n\nGlossary file: `{shared}`\n", "a.md": "Новая фича.\n"})
    sh(root, "add", "-A")
    assert staged(home, root).stdout == "a.md:1: «фича» → «признак»\n"
```

- [ ] **Step 2:** RED.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q
```

Expected: `9 failed, 104 passed` (the test for a broken pointer passes vacuously: the unknown mode already exits 2).

- [ ] **Step 3:** add `run_staged` before the `HOOKS` line and the `--staged` branch to `main`.

`old_string`:

```text
HOOKS = {"memo": run_memo, "stop": run_stop}
```

`new_string`:

```text
def run_staged():
    """pre-commit: forbidden forms in the changed lines of the staged files; exit 0 clean, 1 findings, 2 glossary unreadable."""
    root = project_root(os.getcwd())
    try:
        glossary = load_glossary(root, staged=True)
    except GlossaryError as exc:
        print(f"glossary: {exc}")
        return 2
    if glossary is None:
        return 0
    names = git(root, "diff", "--cached", "--name-only", "--diff-filter=AM", "-z").stdout.decode().split("\0")
    found = []
    for name in filter(None, names):
        staged = git(root, "show", f":{name}")
        if staged.returncode != 0 or b"\0" in staged.stdout:
            continue
        try:
            new_text = staged.stdout.decode("utf-8")
        except UnicodeDecodeError:
            continue
        head = git(root, "show", f"HEAD:{name}")
        old_text = head.stdout.decode("utf-8", "replace") if head.returncode == 0 else None
        for f in scan_text(new_text, glossary, changed_lines(old_text, new_text)):
            found.append((name, f))
            print(f"{name}:{f.line_no}: «{f.form}» → «{f.canonical}»")
    if found:
        log_record({"mode": "staged", "glossary": glossary.path, "findings": [[n, f.line_no, f.form, f.canonical] for n, f in found]})
    return 1 if found else 0


HOOKS = {"memo": run_memo, "stop": run_stop}
```

`old_string`:

```text
    if mode not in HOOKS:
```

`new_string`:

```text
    if mode == "--staged":
        return run_staged()
    if mode not in HOOKS:
```

- [ ] **Step 4:** GREEN and lint.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q
```

Expected: `113 passed`.

```bash
ruff check claude-home/hooks/glossary.py claude-home/hooks/test_glossary.py
```

Expected: `All checks passed!`

- [ ] **Step 5:** check the three modes from the command line against this repository (no glossary yet: all silent).

```bash
echo '{"prompt":"x","cwd":"/home/bgs/ai-steward/Gena_Beeline_Local/python-ai-skills"}' | python3 claude-home/hooks/glossary.py memo; echo "exit=$?"
python3 claude-home/hooks/glossary.py --staged; echo "exit=$?"
python3 claude-home/hooks/glossary.py bogus; echo "exit=$?"
```

Expected: `exit=0`, `exit=0`, then `usage: glossary.py memo | stop | --staged` and `exit=2`; nothing else printed.

- [ ] **Step 6:** commit.

```bash
git add claude-home/hooks/glossary.py claude-home/hooks/test_glossary.py
```

```bash
git commit -m "feat(glossary): add the staged mode that refuses a commit adding a forbidden form" -m "Changed lines of staged text files only; the glossary is read from the index; exit 1 with findings, 2 when the glossary is unreadable. Refs: python-ai-skills-du5"
```


# Phase 2: integration

## Task 8: FR-7: the coined-term hook leaves glossary-forbidden Latin forms to the glossary hook

**Serves:** FR-7; FR-11 (test beside each check).

**Files:** modify `claude-home/hooks/glossary.py`, `claude-home/hooks/test_glossary.py`, `claude-home/hooks/explanation-terms.py`, `claude-home/hooks/test_explanation_terms.py` (Edit tool).

**Interfaces — consumes:** `load_glossary`, `project_root`, `CYRILLIC`. **Produces:** `forbidden_latin_forms(cwd: str) -> set[str]` (forbidden forms without a Cyrillic letter, verbatim; empty without a glossary; may raise `GlossaryError`).

**Why the test differs from the design's example (design 7.F):** `explanation-terms.py` only treats hyphenated Latin compounds and single lowercase-start backticked words as candidates; an all-capital abbreviation such as `OOF` is never a candidate, so the design's example would pass without any change. The evidence corpus holds `<cwd>/AGENTS.md` and the files of the repository; a form is *not* real for it only when the glossary lives outside both (an absolute pointer to another domain's file, NFR-4). That is the case the test builds: without the filter the coined-term hook asks about `drift-guard` while `glossary.py stop` already reports it with its canonical term, so the user would get two framings for one word.

- [ ] **Step 1:** append the unit tests of `forbidden_latin_forms` to `claude-home/hooks/test_glossary.py`.

`old_string`:

```text
    assert staged(home, root).stdout == "a.md:1: «фича» → «признак»\n"
```

`new_string`:

```text
    assert staged(home, root).stdout == "a.md:1: «фича» → «признак»\n"


def test_forbidden_latin_forms_are_the_forms_without_a_cyrillic_letter(tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\n- «OOF», «фича», «k-fold» → **x**\n"})
    assert glossary.forbidden_latin_forms(str(root)) == {"OOF", "k-fold"}


def test_forbidden_latin_forms_without_a_glossary_is_empty(tmp_path):
    assert glossary.forbidden_latin_forms(str(make_project(tmp_path, {}))) == set()


def test_stop_reports_the_latin_form_the_coined_term_hook_leaves_out(home, tmp_path):
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\n- «drift-guard» → **сверка отрисовки**\n"})
    context = context_of(stop(home, root, LONG_RU + "Проверка drift-guard здесь."), "Stop")
    assert "«drift-guard» → «сверка отрисовки»" in context
```

- [ ] **Step 2:** append the coined-term test to `claude-home/hooks/test_explanation_terms.py`.

`old_string`:

```text
    result = run(home, workdir, message, [], tmp_path)
    silent(result)
```

`new_string`:

```text
    result = run(home, workdir, message, [], tmp_path)
    silent(result)


def test_a_form_the_project_glossary_forbids_is_left_to_the_glossary_hook(home, workdir, tmp_path):
    # The glossary sits in a file outside the repository, so no evidence marks `drift-guard` as real;
    # the coined-term hook must not ask about a word that glossary.py already reports with its canonical term.
    shared = tmp_path / "shared-glossary.md"
    shared.write_text("## Glossary\n\n- «drift-guard» → **сверка отрисовки**\n")
    (workdir / "AGENTS.md").write_text(f"## Glossary\n\nGlossary file: `{shared}`\n")
    subprocess.run(["git", "init", "-q"], cwd=workdir, check=True)
    result = run(home, workdir, PROSE + "Проверка drift-guard здесь.", [], tmp_path)
    silent(result)
```

- [ ] **Step 3:** RED.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py claude-home/hooks/test_explanation_terms.py -q
```

Expected: `3 failed, 130 passed`: the two unit tests fail with `AttributeError: ... 'forbidden_latin_forms'`, the coined-term test fails because the hook asks about `drift-guard`.

- [ ] **Step 4:** add `forbidden_latin_forms` to `claude-home/hooks/glossary.py`.

`old_string`:

```text
def log_record(detail):
```

`new_string`:

```text
def forbidden_latin_forms(cwd):
    """Forbidden forms without a Cyrillic letter, verbatim; empty when the project has no glossary."""
    found = load_glossary(project_root(cwd))
    return {form for group in found.groups for form in group.forms if not CYRILLIC.search(form)} if found else set()


def log_record(detail):
```

- [ ] **Step 5:** add the import and the filter to `claude-home/hooks/explanation-terms.py` (two Edit calls).

`old_string`:

```text
import subprocess
import sys
```

`new_string`:

```text
import subprocess
import sys

import glossary
```

`old_string`:

```text
    candidates = collect_candidates(text)
    if not candidates:
```

`new_string`:

```text
    candidates = collect_candidates(text)
    try:
        candidates -= glossary.forbidden_latin_forms(data.get("cwd") or "")
    except Exception:  # a glossary problem never silences the coined-term check
        pass
    if not candidates:
```

- [ ] **Step 6:** GREEN and lint.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py claude-home/hooks/test_explanation_terms.py -q
```

Expected: `133 passed` (116 + 17).

```bash
ruff check claude-home/hooks/glossary.py claude-home/hooks/test_glossary.py claude-home/hooks/explanation-terms.py claude-home/hooks/test_explanation_terms.py
```

Expected: `All checks passed!`

- [ ] **Step 7:** commit.

```bash
git add claude-home/hooks/glossary.py claude-home/hooks/test_glossary.py claude-home/hooks/explanation-terms.py claude-home/hooks/test_explanation_terms.py
```

```bash
git commit -m "feat(glossary): leave glossary-forbidden Latin forms to the glossary hook" -m "forbidden_latin_forms is subtracted from the coined-term candidates; a glossary problem never silences the coined-term check. Refs: python-ai-skills-du5"
```


## Task 9: Wiring: settings template, Makefile, test, memo-hook comment

**Serves:** FR-4 (live delivery); FR-5a (Stop handler); FR-11 (Makefile entry, wiring test); NFR-2 (timeouts: Stop 10 s, UserPromptSubmit 3 s).

**Files:** modify `claude-home/hooks/test_glossary.py`, `Makefile`, `claude-home/settings.json.template`, `claude-home/hooks/question-memo-inject.sh` (comment only; its tests are untouched).

**Interfaces — produces:** the `Stop` handler `python3 '{{CLAUDE_HOME}}/hooks/glossary.py' stop` (timeout 10) and the fourth `UserPromptSubmit` handler `... memo` (timeout 3).

- [ ] **Step 1:** append the wiring test.

`old_string`:

```text
    assert "«drift-guard» → «сверка отрисовки»" in context
```

`new_string`:

```text
    assert "«drift-guard» → «сверка отрисовки»" in context


def test_settings_template_wires_both_modes():
    hooks = json.loads((REPO / "claude-home" / "settings.json.template").read_text(encoding="utf-8"))["hooks"]
    commands = {event: [h["command"] for group in groups for h in group["hooks"]] for event, groups in hooks.items()}
    assert "python3 '{{CLAUDE_HOME}}/hooks/glossary.py' stop" in commands["Stop"]
    assert "python3 '{{CLAUDE_HOME}}/hooks/glossary.py' memo" in commands["UserPromptSubmit"]
```

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q -k settings_template
```

Expected: `1 failed, 116 deselected`.

- [ ] **Step 2:** Makefile: add the test file to `test:` (Edit tool; the continuation lines are one TAB followed by 19 spaces; the new line starts the same way).

`old_string`:

```text
claude-home/hooks/test_question_memo_inject.py \
```

`new_string`:

```text
claude-home/hooks/test_question_memo_inject.py \
	                   claude-home/hooks/test_glossary.py \
```

```bash
cat -A Makefile | sed -n 22,30p
```

Expected: the four lines start with `^I` and 19 spaces and end with `\$`; `claude-home/hooks/test_glossary.py \$` follows the `test_question_memo_inject.py` line.

- [ ] **Step 3:** template: the `Stop` handler (Edit tool).

`old_string`:

```text
            "command": "'{{CLAUDE_HOME}}/hooks/explanation-terms.sh'",
            "timeout": 10
          }
```

`new_string`:

```text
            "command": "'{{CLAUDE_HOME}}/hooks/explanation-terms.sh'",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "python3 '{{CLAUDE_HOME}}/hooks/glossary.py' stop",
            "timeout": 10
          }
```

- [ ] **Step 4:** template: the `UserPromptSubmit` handler.

`old_string`:

```text
            "command": "'{{CLAUDE_HOME}}/hooks/question-memo-inject.sh'",
            "timeout": 3
          }
```

`new_string`:

```text
            "command": "'{{CLAUDE_HOME}}/hooks/question-memo-inject.sh'",
            "timeout": 3
          },
          {
            "type": "command",
            "command": "python3 '{{CLAUDE_HOME}}/hooks/glossary.py' memo",
            "timeout": 3
          }
```

- [ ] **Step 5:** the memo hook's reserved-slot comment now names the sibling handler (Edit tool, text only).

`old_string`:

```text
# it would make the model write a second message. A per-project glossary delivery
# (bd python-ai-skills-du5) may reuse this hook later; it is not built.
```

`new_string`:

```text
# it would make the model write a second message. The per-project glossary delivery
# (bd python-ai-skills-du5) is `glossary.py memo`, a sibling handler, not this hook.
```

- [ ] **Step 6:** verify.

```bash
python3 -m json.tool claude-home/settings.json.template > /dev/null
```

Expected: exit 0, no output.

```bash
jq '[.hooks.Stop[0].hooks | length, (.hooks.UserPromptSubmit[0].hooks | length)]' claude-home/settings.json.template
```

Expected: `[2, 4]`.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py claude-home/hooks/test_question_memo_inject.py scripts/test_install_claude_symlinks.py -q
```

Expected: all passed (117 + 12 + the installer suite; `test_every_hook_path_is_one_shell_word` passes because `claude-home/hooks/glossary.py` exists).

- [ ] **Step 7:** gate and commit.

```bash
make test
```

Expected: sum of the five passed counts `721` (603 baseline + 117 glossary tests + 1 coined-term test), no failures.

```bash
git add claude-home/hooks/test_glossary.py Makefile claude-home/settings.json.template claude-home/hooks/question-memo-inject.sh
```

```bash
git commit -m "feat(glossary): wire the glossary hook into Stop and UserPromptSubmit" -m "Direct python3 handlers in the settings template, test file listed in make test; takes effect after make install-symlinks (Task 10). Refs: python-ai-skills-du5"
```


## Task 10: Pre-commit: bootstrap-hook step, local-hook entry, documentation, installer re-run

**Serves:** FR-5b (the commit gate reaches every repository); NFR-3 (gate: exit 1 refuses the commit); FR-11 (functional test of the bootstrap hook); design 3.5 (delivery to other projects).

**Files:** modify `claude-home/hooks/test_glossary.py`, `claude-home/git-template/pre-commit`, `.pre-commit-config.yaml`, `_linters/reference/linters.md`.

**Facts (design 3.5, probed 2026-10-15, re-checked 2026-10-20):** pre-commit does not expand `~` or `$HOME` in `entry`, hence `bash -c`; the installer copies the template into `~/.git-template` and refreshes this checkout's `.git/hooks/pre-commit` (`scripts/install-claude-symlinks.sh:189-218`) but not other repositories.

- [ ] **Step 1:** append the bootstrap-hook tests and the two structural guards.

`old_string`:

```text
    assert "python3 '{{CLAUDE_HOME}}/hooks/glossary.py' memo" in commands["UserPromptSubmit"]
```

`new_string`:

```text
    assert "python3 '{{CLAUDE_HOME}}/hooks/glossary.py' memo" in commands["UserPromptSubmit"]


TEMPLATE_HOOK = REPO / "claude-home" / "git-template" / "pre-commit"


def run_template_hook(home, root):
    (home / ".claude" / "hooks").mkdir(parents=True)
    (home / ".claude" / "hooks" / "glossary.py").symlink_to(HOOK)
    return subprocess.run(
        ["bash", str(TEMPLATE_HOOK)],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=root,
        env={"PATH": "/usr/bin:/bin", "HOME": str(home)},
    )


def test_bootstrap_hook_refuses_a_commit_with_a_new_forbidden_form(home, committed):
    (committed / "notes.md").write_text("Старая фича в тексте.\nВторая строка.\nНовый лог добавлен.\n")
    sh(committed, "add", "notes.md")
    result = run_template_hook(home, committed)
    assert result.returncode == 1
    assert "notes.md:3: «лог» → «журнал»" in result.stdout and "glossary check failed" in result.stderr


def test_bootstrap_hook_lets_a_clean_commit_through(home, committed):
    (committed / "notes.md").write_text("Старая фича в тексте.\nВторая строка изменена.\n")
    sh(committed, "add", "notes.md")
    assert run_template_hook(home, committed).returncode == 0


def test_bootstrap_hook_runs_the_glossary_step_before_the_framework_delegation():
    text = TEMPLATE_HOOK.read_text(encoding="utf-8")
    assert 0 < text.index("glossary.py") < text.index("exec pre-commit")


def test_repository_config_declares_the_glossary_check():
    config = (REPO / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert "id: glossary-check" in config and 'glossary.py" --staged' in config
```

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q -k 'bootstrap or repository_config'
```

Expected: `3 failed, 1 passed, 117 deselected` (the clean-commit test passes vacuously).

- [ ] **Step 2:** bootstrap hook: the glossary step before the framework delegation (Edit tool on `claude-home/git-template/pre-commit`).

`old_string`:

```text
# Run pre-commit framework if config exists and tool available
```

`new_string`:

```text
# Project glossary (bd python-ai-skills-du5): forbidden synonyms in the changed lines of the
# staged files. Exit 0 at once when the repository has no `## Glossary` section.
GLOSSARY_CHECK="$HOME/.claude/hooks/glossary.py"
if [ -f "$GLOSSARY_CHECK" ] && ! python3 "$GLOSSARY_CHECK" --staged; then
  echo "pre-commit (template): glossary check failed — commit refused" >&2
  exit 1
fi

# Run pre-commit framework if config exists and tool available
```

- [ ] **Step 3:** this repository's config: the live example of the local-hook form.

`old_string`:

```text
        files: ^claude-home/scripts/
        pass_filenames: false
```

`new_string`:

```text
        files: ^claude-home/scripts/
        pass_filenames: false

      # Project glossary (bd python-ai-skills-du5): forbidden synonyms in the changed lines of the
      # staged files. The bootstrap hook (claude-home/git-template/pre-commit) runs the same check
      # first, so a commit here runs it twice; this entry is the documented form for a repository
      # that has a config but no copy of the bootstrap hook (_linters/reference/linters.md).
      - id: glossary-check
        name: glossary (forbidden synonyms in changed lines)
        entry: bash -c 'exec python3 "$HOME/.claude/hooks/glossary.py" --staged'
        language: system
        pass_filenames: false
        always_run: true
```

- [ ] **Step 4:** document the local-hook form (Edit tool on `_linters/reference/linters.md`).

`old_string`:

```text
### Docker: Dockerfile Linting
```

`new_string`:

````text
### Project glossary (forbidden synonyms)

A project with a `## Glossary` section in its `AGENTS.md` checks the changed lines of every commit against it
(bd `python-ai-skills-du5`). A repository created from `~/.git-template` already runs the check from the bootstrap
hook. A repository that has a `.pre-commit-config.yaml` but no copy of the bootstrap hook declares it as a local hook;
the machine needs `make install-symlinks` first, because the entry runs `~/.claude/hooks/glossary.py`. pre-commit does
not expand `~` or `$HOME` in `entry`, hence `bash -c`:

```yaml
- repo: local
  hooks:
    - id: glossary-check
      name: glossary (forbidden synonyms in changed lines)
      entry: bash -c 'exec python3 "$HOME/.claude/hooks/glossary.py" --staged'
      language: system
      pass_filenames: false
      always_run: true
```

The check exits 0 clean (and in a project without the section), 1 with findings, 2 when the glossary is unreadable.

### Docker: Dockerfile Linting
````

- [ ] **Step 5:** GREEN, YAML, the framework route.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q
```

Expected: `4 passed, 117 deselected` here, and the whole file `121 passed`.

```bash
python3 -c "import yaml; print(len(yaml.safe_load(open('.pre-commit-config.yaml'))['repos'][0]['hooks']))"
```

Expected: `7`.

```bash
pre-commit run glossary-check --all-files
```

Expected: `glossary (forbidden synonyms in changed lines)....Passed` (the repository has no glossary yet, the hook is silent).

- [ ] **Step 6:** install: re-render `~/.claude/settings.json` and refresh the two copies of the bootstrap hook — Bash call with `dangerouslyDisableSandbox: true`, its own call, the user approves it (it writes into `~/.claude` and `~/.git-template`; idempotent).

```bash
make install-symlinks
```

Expected: the installer ends without error and prints `updated .../.git/hooks/pre-commit`.

- [ ] **Step 7:** verify the live result (read-only).

```bash
jq '[.hooks.Stop[0].hooks | length, (.hooks.UserPromptSubmit[0].hooks | length)]' ~/.claude/settings.json
```

Expected: `[2, 4]`.

```bash
cmp claude-home/git-template/pre-commit .git/hooks/pre-commit
```

Expected: no output, exit 0 (byte-identical).

```bash
cmp claude-home/git-template/pre-commit ~/.git-template/hooks/pre-commit
```

Expected: no output, exit 0.

- [ ] **Step 8:** gate and commit (from now on every commit of this repository runs the glossary check twice, silently while `AGENTS.md` has no glossary).

```bash
make test
```

Expected: sum `725` (603 + 121 + 1), no failures.

```bash
git add claude-home/hooks/test_glossary.py claude-home/git-template/pre-commit .pre-commit-config.yaml _linters/reference/linters.md
```

```bash
git commit -m "feat(glossary): run the glossary check from the bootstrap pre-commit hook" -m "Template step before the framework delegation, local-hook entry as the live example and in linters.md, functional tests of the template step. Refs: python-ai-skills-du5"
```


# Phase 3: rule and generators

## Task 11: Global rule paragraph and appendix rationale

**Serves:** FR-3 (the rule that makes agents use only canonical terms); FR-9 (rule named once, no restatement of the one-designation rule, no global layer); FR-1 (N-DOCS line for `glossary.md`); NFR-4 (one rule text).

**Files:** modify `claude-home/hooks/test_glossary.py`, `claude-home/CLAUDE.md`, `claude-home/CLAUDE-APPENDIX.md` (Edit tool).

**Design note:** the design wrote the pointer line inside single backticks (`` `Glossary file: `glossary.md`` ``), which renders broken; a double-backtick code span is used.

- [ ] **Step 1:** append the guard test.

`old_string`:

```text
    assert "id: glossary-check" in config and 'glossary.py" --staged' in config
```

`new_string`:

```text
    assert "id: glossary-check" in config and 'glossary.py" --staged' in config


def test_global_instructions_name_the_glossary_mechanism_once():
    text = (REPO / "claude-home" / "CLAUDE.md").read_text(encoding="utf-8")
    assert text.count("`## Glossary`") == 1 and text.count("glossary.py") == 1
```

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q -k global_instructions
```

Expected: `1 failed, 121 deselected`.

- [ ] **Step 2:** `claude-home/CLAUDE.md`: the rule paragraph after the hook-level rule of Explanation Protocol.

`old_string`:

```text
— тот остаётся на дисциплине.

**Разобранные примеры**
```

`new_string`:

```text
— тот остаётся на дисциплине.

**Rule (глоссарий проекта):** у проекта есть раздел `## Glossary` в `AGENTS.md` — по одной строке на группу синонимов: «запрещённые формы» → **канонический термин**, при необходимости определение и источник. В тексте для пользователя (чат, документы, задачи bd, CHANGELOG, отчёты, строки и комментарии кода, HTML) употребляется только канонический термин; идентификаторы кода, текст в обратных кавычках и в «кавычках» не проверяются. Раздел больше 200 строк или 8 000 знаков живёт в `glossary.md` в корне проекта, а в разделе остаётся одна строка ``Glossary file: `glossary.md` ``. Хук `~/.claude/hooks/glossary.py` доставляет словарь перед ответом (UserPromptSubmit: раздел целиком или только группы, задетые вопросом), проверяет последний ответ (Stop: одна строка `Поправка к термину: «X» → «Y»` на находку, без блокировки) и изменённые строки коммита (`--staged`, отказ в коммите). Проект без раздела — тишина. Один словарь на предметную область: второй проект той же области ставит строку-указатель на файл первого.

**Разобранные примеры**
```

- [ ] **Step 3:** `claude-home/CLAUDE-APPENDIX.md`: the rationale paragraph in `## Explanation Protocol`.

`old_string`:

```text
здесь тот же принцип для терминов.

## First-Contact Protocol
```

`new_string`:

```text
здесь тот же принцип для терминов.

**Почему (глоссарий проекта, bd `python-ai-skills-du5`):** правило «одно явление — одно обозначение» выше — дисциплина без данных: в каждой сессии обозначение выбирается заново, и две сессии выбирают разное. Глоссарий — файл, который модель читает до ответа, а проверка читает после. Проверок две, потому что у каждой свой предел: хук Stop видит последнее сообщение, но не файлы; проверка при коммите видит файлы, но не чат. В чате проверка совещательная (одна строка на находку, без блокировки): блокировка заставляла модель переписывать уже прочитанный ответ (bd `python-ai-skills-r1f.1`); при коммите — обязательная, как `vocab-check` в `Local_LLM_selection`. Раздел лежит внутри `AGENTS.md`, а не в отдельном файле с `@`-импортом: Codex читает `AGENTS.md` как один файл и импорты не раскрывает. Словарь больше 200 строк выносится в файл, потому что документация памяти Claude Code советует держать файл короче 200 строк; в разделе остаётся одна строка-указатель. Перед ответом хук отправляет раздел целиком до 8 000 знаков (предел вывода одного хука — 10 000), выше — только группы, задетые вопросом.

## First-Contact Protocol
```

- [ ] **Step 4:** `claude-home/CLAUDE-APPENDIX.md`: the N-DOCS line in the file tree of `## File Structure (dev-projects)`.

`old_string`:

````text
  operational-packets.xml                # static GRACE schema
```
````

`new_string`:

````text
  operational-packets.xml                # static GRACE schema
glossary.md                            # separate-file glossary (section form over 200 lines or 8,000 characters): project root, not under docs/
```
````

- [ ] **Step 5:** verify: the guard, the principles guard (the paragraph must not restate a code principle) and the memo guard.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py claude-home/hooks/test_principles_ssot.py claude-home/hooks/test_question_memo_inject.py -q
```

Expected: all passed (122 + the two other files).

```bash
wc -c claude-home/CLAUDE.md
```

Expected: about `41,900` bytes (40,682 before; the Codex chain cap of 32 KiB was already exceeded and the earlier Codex check of `20261015-question-memo-hook-plan.md` Task 6 found no truncation of the sections that matter; nothing is measured again here).

- [ ] **Step 6:** commit.

```bash
git add claude-home/hooks/test_glossary.py claude-home/CLAUDE.md claude-home/CLAUDE-APPENDIX.md
```

```bash
git commit -m "docs(glossary): add the project glossary rule to the global instructions" -m "One rule paragraph in Explanation Protocol, rationale and N-DOCS tree line in the appendix; guard test counts the names once. Refs: python-ai-skills-du5"
```


## Task 12: Generator skeleton: one asset, two generators

**Serves:** FR-8 (both generators create the skeleton from one template); FR-2 (the skeleton shows the optional fields); Constraint 6 of the discovery (same skeleton from two mechanisms).

**Files:** create `grace-init/assets/glossary-section.md.template` (Write tool); modify `claude-home/hooks/test_glossary.py`, `grace-init/assets/AGENTS.md.template`, `grace-init/SKILL.md`, `_init/SKILL.md`.

**Why the text is in two files:** `grace-init` renders `assets/AGENTS.md.template` and says "never hardcode template content inline"; `_init` inlines its own short `AGENTS.md` and so points at the asset. The asset is the SSoT; the copy inside `AGENTS.md.template` is guarded by a test (`test_grace_agents_template_carries_the_asset_verbatim`).

- [ ] **Step 1:** append the generator tests.

`old_string`:

```text
    assert text.count("`## Glossary`") == 1 and text.count("glossary.py") == 1
```

`new_string`:

```text
    assert text.count("`## Glossary`") == 1 and text.count("glossary.py") == 1


ASSET = REPO / "grace-init" / "assets" / "glossary-section.md.template"


def test_asset_skeleton_has_no_groups_and_no_contract_errors():
    text = ASSET.read_text(encoding="utf-8")
    assert glossary.parse_section(glossary.cut_section(text, "asset"), "asset") == ((), (), None)


def test_both_generators_reference_the_asset():
    for rel in ("_init/SKILL.md", "grace-init/SKILL.md"):
        assert "glossary-section.md.template" in (REPO / rel).read_text(encoding="utf-8"), rel


def test_grace_agents_template_carries_the_asset_verbatim():
    template = (REPO / "grace-init" / "assets" / "AGENTS.md.template").read_text(encoding="utf-8")
    assert ASSET.read_text(encoding="utf-8").strip() in template
```

- [ ] **Step 2:** RED.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q -k 'asset or generators or agents_template'
```

Expected: `3 failed, 122 deselected` (the skeleton test fails with `FileNotFoundError`: the asset does not exist yet).

- [ ] **Step 3:** create the asset with the Write tool, exactly this content (the example lines sit in a fenced block because the parser skips fenced lines; the last line is prose here, not a pointer).

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

- [ ] **Step 4:** `grace-init/assets/AGENTS.md.template`: append the asset text after `## Rules for Modifications`.

`old_string`:

```text
6. Never remove semantic markup anchors unless the structure is intentionally replaced with better anchors.
```

`new_string`:

````text
6. Never remove semantic markup anchors unless the structure is intentionally replaced with better anchors.

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

- [ ] **Step 5:** `grace-init/SKILL.md`: one row in the template table.

`old_string`:

```text
| `assets/AGENTS.md.template`              | `AGENTS.md` (project root) + `CLAUDE.md -> AGENTS.md` symlink |
```

`new_string`:

```text
| `assets/AGENTS.md.template`              | `AGENTS.md` (project root) + `CLAUDE.md -> AGENTS.md` symlink |
| `assets/glossary-section.md.template`    | the `## Glossary` skeleton, already appended to `assets/AGENTS.md.template` (one text, a test keeps the two equal) |
```

- [ ] **Step 6:** `_init/SKILL.md`: one sentence before the symlink instruction.

`old_string`:

```text
Then `ln -s AGENTS.md CLAUDE.md`.
```

`new_string`:

```text
Append `grace-init/assets/glossary-section.md.template` verbatim to `AGENTS.md` (the `## Glossary` skeleton; one template for both generators). Then `ln -s AGENTS.md CLAUDE.md`.
```

- [ ] **Step 7:** GREEN, gate, commit.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py claude-home/hooks/test_principles_ssot.py -q
```

Expected: all passed (125 in the first file).

```bash
make test
```

Expected: sum `729` (603 + 125 + 1), no failures.

```bash
git add claude-home/hooks/test_glossary.py grace-init/assets/glossary-section.md.template grace-init/assets/AGENTS.md.template grace-init/SKILL.md _init/SKILL.md
```

```bash
git commit -m "feat(glossary): create the Glossary skeleton in _init and grace-init" -m "One template asset; grace-init appends it to its AGENTS.md template, _init points at it; a test keeps the two copies equal. Refs: python-ai-skills-du5"
```


# Phase 4: samples

## Task 13: Sample 1: the glossary of python-ai-skills (section form, groups from real usage)

**Serves:** FR-12 (first sample, section form); FR-1; FR-2; FR-3; NFR-7 (section well under 200 lines and 8,000 characters).

**Files:** create `$TMPDIR/du5-count/count_forms.py` (not committed); modify `claude-home/hooks/test_glossary.py`, `AGENTS.md`.

**Selection rule (design 11.3: rule and counts, not a hand-picked list):** candidates are the groups the design listed (observed in this repository's prose and journal). A candidate group is **kept** when at least two designations of the same thing each occur **at least 3 times as whole words** (the matcher of `glossary.py`, case endings included) in the assistant text of this project's session transcripts: that is the evidence that the repository mixes them. A group with a designation at 0 occurrences is dropped. The **canonical** designation is the one with more whole-word occurrences in the tracked `*.md` files (documents the user approved); when the two counts differ by less than 2 to 1 the **user decides**. A candidate designation that is a plural of another (`логи` of `лог`) is not listed separately: the endings of the form already cover it.

- [ ] **Step 1:** write the counting script with the Write tool to `$TMPDIR/du5-count/count_forms.py` (outside the repository, not committed).

```python
#!/usr/bin/env python3
"""One-off (bd python-ai-skills-du5): whole-word counts of candidate glossary forms in the assistant text of this project's sessions.

Usage: count_forms.py <transcripts dir> <hooks dir> <repo root>; candidates are listed below as (term, term, ...) pairs.
Counts whole words with the matcher of glossary.py, in assistant text of the sessions and in the tracked *.md files."""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[2])
import glossary  # noqa: E402

CANDIDATES = [
    ("реестр моделей", "регистр моделей", "таблица моделей"),
    ("журнал", "лог"),
    ("хук", "перехватчик"),
    ("символическая ссылка", "симлинк"),
    ("подагент", "субагент", "сабагент"),
]


def assistant_texts(directory):
    for path in sorted(Path(directory).glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("type") != "assistant":
                continue
            for block in (event.get("message") or {}).get("content") or []:
                if isinstance(block, dict) and block.get("type") == "text":
                    yield block["text"]


def tracked_docs(root):
    names = subprocess.run(["git", "ls-files", "-z", "*.md"], cwd=root, capture_output=True, text=True).stdout.split("\0")
    return [(Path(root) / n).read_text(encoding="utf-8", errors="replace") for n in names if n]


def main():
    sessions, docs = list(assistant_texts(sys.argv[1])), tracked_docs(sys.argv[3])
    print(f"assistant text blocks: {len(sessions)}; tracked *.md files: {len(docs)}")
    for terms in CANDIDATES:
        cells = []
        for term in terms:
            rx = glossary.form_regex(term)
            cells.append(f"{term}: sessions {sum(len(rx.findall(t)) for t in sessions)}, docs {sum(len(rx.findall(t)) for t in docs)}")
        print("; ".join(cells))


main()
```

- [ ] **Step 2:** run it.

```bash
python3 $TMPDIR/du5-count/count_forms.py /home/bgs/.claude/projects/-home-bgs-ai-steward-Gena-Beeline-Local-python-ai-skills /home/bgs/ai-steward/Gena_Beeline_Local/python-ai-skills/claude-home/hooks /home/bgs/ai-steward/Gena_Beeline_Local/python-ai-skills
```

Expected: one line per candidate group. Measured 2026-10-20 (1,069 assistant text blocks, 188 tracked `*.md`): `реестр моделей` sessions 5 / docs 1, `регистр моделей` 0 / 0, `таблица моделей` 0 / 0 (dropped: nothing mixed); `журнал` 218 / 41, `лог` 9 / 8 (kept, canonical `журнал`: 41 to 8); `хук` 571 / 18, `перехватчик` 0 / 1 (dropped); `символическая ссылка` 4 / 1, `симлинк` 84 / 1 (kept, tie in the documents: user decides); `подагент` 75 / 3, `субагент` 174 / 5, `сабагент` 0 / 1 (kept, 3 to 5 in the documents: user decides). Use the numbers of the run, not these.

- [ ] **Step 3:** USER STOP — ask the user (global question header: plan, current task and step, goal of the question). Show the counts. Ask, for each kept group whose documents' counts differ by less than 2 to 1, which designation is canonical. With the 2026-10-20 counts: group `симлинк` / `символическая ссылка` and group `подагент` / `субагент`. Offer both orientations of each line with the two scores `X% / Y%` per the global rule. Do not choose for the user.

- [ ] **Step 4:** append the guard test (RED).

`old_string`:

```text
    assert ASSET.read_text(encoding="utf-8").strip() in template
```

`new_string`:

```text
    assert ASSET.read_text(encoding="utf-8").strip() in template


def test_this_repository_glossary_fits_the_section_form():
    found = glossary.load_glossary(REPO)
    assert found is not None and not found.pointed and len(found.groups) >= 1
    assert len(found.lines) <= glossary.SECTION_MAX_LINES and len("\n".join(found.lines)) <= glossary.MEMO_MAX_CHARS
```

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q -k this_repository_glossary
```

Expected: `1 failed, 125 deselected` (`AssertionError`: `AGENTS.md` has no glossary).

- [ ] **Step 5:** write the section into `AGENTS.md` (Edit tool; it goes before `## Non-Interactive Shell Commands`, outside the managed Beads blocks). The text below is the orientation `лог` -> `журнал`, `симлинк` -> `символическая ссылка`, `субагент`/`сабагент` -> `подагент`; swap the canonical and the forbidden form of a group where the user chose the other orientation. The two alternative lines are: `- «символическая ссылка» → симлинк — файл, указывающий на другой путь; `make install-symlinks` создаёт такие ссылки в `~/.claude` (источник: подсчёт употреблений, bd python-ai-skills-du5)` and `- «подагент», «сабагент» → субагент — агент, которого основной агент запускает инструментом `Agent` (источник: подсчёт употреблений, bd python-ai-skills-du5)`. A group the user rejects is deleted from the section (at least one group must remain; if none remains, stop and ask).

`old_string`:

```text
**Version**: 3.7

## Non-Interactive Shell Commands
```

`new_string`:

```text
**Version**: 3.7

## Glossary

- «лог» → **журнал** — файл записей о событиях, например `~/.claude/hook-stats/blocks.jsonl` (источник: подсчёт употреблений, bd python-ai-skills-du5)
- «симлинк» → **символическая ссылка** — файл, указывающий на другой путь; `make install-symlinks` создаёт такие ссылки в `~/.claude` (источник: подсчёт употреблений, bd python-ai-skills-du5)
- «субагент», «сабагент» → **подагент** — агент, которого основной агент запускает инструментом `Agent` (источник: подсчёт употреблений, bd python-ai-skills-du5)

## Non-Interactive Shell Commands
```

- [ ] **Step 6:** GREEN and the three modes against the real section.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q
```

Expected: `126 passed`.

```bash
echo '{"prompt":"x","cwd":"/home/bgs/ai-steward/Gena_Beeline_Local/python-ai-skills"}' | python3 claude-home/hooks/glossary.py memo | jq -r .hookSpecificOutput.additionalContext
```

Expected: the framing line, a blank line, then the whole `## Glossary` section (3 groups).

```bash
echo '{"hook_event_name":"Stop","cwd":"/home/bgs/ai-steward/Gena_Beeline_Local/python-ai-skills","last_assistant_message":"Это сообщение написано по-русски. Нужен симлинк и лог."}' | python3 claude-home/hooks/glossary.py stop | jq -r .hookSpecificOutput.additionalContext
```

Expected: one framing text listing `«симлинк» → «символическая ссылка», «лог» → «журнал»` (with the user's orientations) and the one-line form.

- [ ] **Step 7:** dry run of the commit gate on the real section: stage `AGENTS.md` and run the staged mode.

```bash
git add AGENTS.md
```

```bash
python3 claude-home/hooks/glossary.py --staged; echo "exit=$?"
```

Expected: no findings, `exit=0` (the entry lines are quoted in «», the definitions use no forbidden form). **If it prints findings, fix the definition text, not the check.**

- [ ] **Step 8:** record the counts in bd notes (they go into the CHANGELOG entry of Task 17).

```bash
bd update python-ai-skills-du5 --append-notes "Task 13 counts (whole words, assistant text of this project's sessions / tracked *.md): <paste the lines printed in Step 2>; decisions: <canonical choices of the user>"
```

Expected: the note is saved (the angle-bracket parts are the observed values, they cannot exist before Steps 2-3).

- [ ] **Step 9:** commit.

```bash
git add claude-home/hooks/test_glossary.py AGENTS.md
```

```bash
git commit -m "docs(glossary): add the glossary of python-ai-skills" -m "Groups chosen by the counting rule recorded in bd notes; guard test on the real section. Refs: python-ai-skills-du5"
```

Expected: both hook runs of pre-commit (template step and framework hook) pass; the commit has 2 files. From now on the memo and Stop modes are active in this repository.


## Task 14: FR-14: convert `ML_Sobes_2026/glossary.md` (one-off script, user review before writing)

**Serves:** FR-14; NFR-9 (629 in / 629 out, every synonym kept, counted); FR-12 (second sample, separate file + pointer); FR-10; NFR-1 and NFR-2 (timing on the largest glossary); NFR-8 (`Local_LLM_selection` stays silent).

**Files:** create `$TMPDIR/du5-fr14/convert_glossary.py` (not committed); write `ML_Sobes_2026/glossary.md` and edit `ML_Sobes_2026/AGENTS.md` only after Step 5. Nothing in this repository changes.

**Measured on 2026-10-20 (the design's input facts re-checked):** 629 term rows in 19 `## ` sections, 567 synonym forms, 208 rows without synonyms, the `## Спорные выборы` section. Two figures of design 4.3 differ from the measurement and are shown to the user: the forms the check can never match are **14** with the design's own identifier rule (`class_weight`, `scale_pos_weight`, `bfloat16`, `ColBERT`, `CoT`, `H0`, `LambdaRank`, `wait_for`, `ProcessPool`, `ThreadPool`, `async/await`, `CancelledError`, `zero_grad`, `no_grad`), not 6 (a camelCase or digit rule blanks them); forms with a qualifier are **4**, not 6.

- [ ] **Step 1:** write the script with the Write tool to `$TMPDIR/du5-fr14/convert_glossary.py`.

```python
#!/usr/bin/env python3
"""One-off FR-14 conversion (bd python-ai-skills-du5): ML_Sobes_2026/glossary.md table form -> `## Glossary` entry form.

Usage: convert_glossary.py <source glossary.md> <output glossary.md> <hooks directory of python-ai-skills>
Writes only <output>; prints the count check and the review lists. Not committed, not shipped."""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, sys.argv[3])  # the hooks directory of python-ai-skills
import glossary  # noqa: E402

DISPUTED = "## Спорные выборы"
HEADER_CELLS = ("Основной термин", "---")


def read_rows(lines):
    rows, groups = [], []
    for line in lines:
        if line.startswith("## ") and not line.startswith(DISPUTED):
            groups.append(line[3:].strip())
        elif line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == 4 and not cells[0].startswith(HEADER_CELLS) and set(cells[0]) != {"-"}:
                rows.append(cells)
    return rows, groups


def main(source, output):
    text = Path(source).read_text(encoding="utf-8")
    lines = text.split("\n")
    disputed_at = next(i for i, line in enumerate(lines) if line.startswith(DISPUTED))
    rows, groups = read_rows(lines[:disputed_at])
    header = lines[:3]  # title, blank line, header paragraph (the project's own rule)
    canon_of = {r[0].lower(): r[0] for r in rows}
    forms_in, forms_out, dropped, entries = 0, 0, [], []
    seen = Counter()
    for canonical, english, synonyms, short in rows:
        forms = [] if synonyms == "—" else synonyms.split(", ")
        forms_in += len(forms)
        kept = [f for f in forms if f.lower() != canonical.lower()]
        dropped += [(canonical, f) for f in forms if f.lower() == canonical.lower()]
        seen.update(kept)
        forms_out += len(kept)
        left = ", ".join(f"«{f}»" for f in kept)
        prefix = f"{left} → " if kept else ""
        entries.append(f"- {prefix}**{canonical}** — {short} (English: {english})")
    body = [
        *header,
        f"{len(groups)} тематических групп исходной таблицы: " + "; ".join(groups) + ".",
        "",
        glossary.GLOSSARY_HEADING,
        "",
        *entries,
        "",
        *lines[disputed_at:],
    ]
    Path(output).write_text("\n".join(body), encoding="utf-8")

    section = glossary.cut_section(Path(output).read_text(encoding="utf-8"), output)
    parsed, _, _ = glossary.parse_section(section, output)
    print(f"rows in: {len(rows)}  entry lines out: {len(entries)}  groups parsed: {len(parsed)}")
    print(f"forms in: {forms_in}  forms out: {forms_out}  dropped self-synonyms: {len(dropped)} {dropped}")
    assert len(rows) == len(entries) == len(parsed) == 629 and forms_in == 567 and forms_out == forms_in - len(dropped)

    all_forms = [f for g in parsed for f in g.forms]
    print("short forms (<= 2 characters, whole-token only):", [f for f in all_forms if len(f) <= 2])
    print("forms the check cannot match (identifier-shaped):",
          [f for f in all_forms if all(glossary.IDENT_RE.fullmatch(w.strip(glossary.TOKEN_EDGES) or "-") for w in f.split())])
    print("forms with a qualifier:", [f for f in all_forms if "(" in f])
    print("forms equal to another row's canonical term:", [(f, canon_of[f.lower()]) for f in all_forms if f.lower() in canon_of])
    print("forms in more than one row:", [f for f, n in seen.items() if n > 1])
    converted = Path(output).read_text(encoding="utf-8")
    hits = glossary.scan_text(converted, glossary.Glossary(output, tuple(parsed), (), section, True))
    print(f"forbidden forms met in the converted file's own definitions: {len(hits)}",
          [(h.line_no, h.form) for h in hits[:10]])


if __name__ == "__main__":
    main(*sys.argv[1:3])
```

- [ ] **Step 2:** run it (it reads the source, writes only `$TMPDIR/du5-fr14/out/glossary.md`, prints the count check and the review lists).

```bash
mkdir -p $TMPDIR/du5-fr14/out
```

```bash
python3 $TMPDIR/du5-fr14/convert_glossary.py /home/bgs/ai-steward/Gena_Beeline_Local/ML_Sobes_2026/glossary.md $TMPDIR/du5-fr14/out/glossary.md /home/bgs/ai-steward/Gena_Beeline_Local/python-ai-skills/claude-home/hooks
```

Expected: measured 2026-10-20: `rows in: 629  entry lines out: 629  groups parsed: 629`; `forms in: 567  forms out: 566  dropped self-synonyms: 1 [('Recall@k', 'recall@k')]`; 13 short forms (`y`, `TN`, `TP`, `FN`, `FP`, `lr`, `Q`, `K`, `V`, `ДИ`, `H0`, `SE`, `GC`); the 14 forms that cannot match; the 4 qualifier forms (`TP (в значении параллелизма)`, `top-k (в значении генерации)`, `цепочка (chain)`, `амортизированно O(1)`); no form equal to another row's canonical term; one form in two rows (`базовая модель`); and `forbidden forms met in the converted file's own definitions: 336` (327 of them inside the entry lines, 9 in the header paragraph and the disputed-choices section). The script asserts 629 / 629 / 567 itself; an `AssertionError` means the source changed since 2026-10-15 — stop and ask.

- [ ] **Step 3:** verify the converted file with the real modes in a scratch project (timing for NFR-1/NFR-2; nothing outside `$TMPDIR` is touched).

```bash
mkdir -p $TMPDIR/du5-fr14/proj
cp -f $TMPDIR/du5-fr14/out/glossary.md $TMPDIR/du5-fr14/proj/glossary.md
printf '## Glossary\n\nGlossary file: `glossary.md`\n' > $TMPDIR/du5-fr14/proj/AGENTS.md
grep -c '^- ' $TMPDIR/du5-fr14/out/glossary.md
```

Expected: `629`.

```bash
( time echo "{\"prompt\":\"Что такое кросс-валидация и k-fold?\",\"cwd\":\"$TMPDIR/du5-fr14/proj\"}" | python3 claude-home/hooks/glossary.py memo | jq -r .hookSpecificOutput.additionalContext ) 2>&1 | tail -12
```

Expected: the targeted framing (`... groups touched by this prompt ...`) with the line `- «кросс-валидация», «k-fold» → **перекрёстная проверка** — ...`; `real` below `3s` (measured 0.66 s).

```bash
echo "{\"hook_event_name\":\"Stop\",\"cwd\":\"$TMPDIR/du5-fr14/proj\",\"last_assistant_message\":\"Это сообщение написано по-русски. Добавь фича в модель.\"}" | python3 claude-home/hooks/glossary.py stop | jq -r .hookSpecificOutput.additionalContext | head -c 400
```

Expected: `GLOSSARY ...: ... «фича» → «признак».` and the one-line form.

- [ ] **Step 4:** USER STOP — review before anything is written into ML_Sobes_2026 (global question header). Show: the count check (629 in / 629 out, 567 forms in, 566 out, the dropped `recall@k`); the 13 short forms (whole-token only; ask whether to keep each — `y`, `K`, `Q`, `V` are one-letter names that also occur as variables); the 14 forms the check cannot match and the 4 qualifier forms; the form `базовая модель` in two rows; and the commit-gate decision D-GATE: after the refresh command, a commit that stages the converted `glossary.md` is scanned in full (every line is new) and the scan reports 336 findings, 327 of them in the entry lines themselves, because definitions use words that other rows forbid (`ответ`, `словарь`, `категория`, ...). Options, each with `X% / Y%`: (A) exempt the glossary's own entry lines from the scan — Task 15, +3 lines of code, the design's choice reversed; (B) keep the design as approved — the user rewrites the 327 definitions before the project's next commit of `glossary.md` (the gate refuses it until then); (C) do not refresh the old hook copy of ML_Sobes_2026 — the memo and Stop modes still work there, the commit gate does not. Record the answer; Task 15 runs only on (A).

- [ ] **Step 5:** after the user's approval: write the converted file — Bash call with `dangerouslyDisableSandbox: true`, its own call (a `.md` file inside `~/ai-steward`, allowed by the Security rule, outside the sandbox's write area).

```bash
cp -f $TMPDIR/du5-fr14/out/glossary.md /home/bgs/ai-steward/Gena_Beeline_Local/ML_Sobes_2026/glossary.md
```

Expected: no output.

```bash
cmp $TMPDIR/du5-fr14/out/glossary.md /home/bgs/ai-steward/Gena_Beeline_Local/ML_Sobes_2026/glossary.md
```

Expected: no output, exit 0.

- [ ] **Step 6:** `ML_Sobes_2026/AGENTS.md`: Read the file first, then two Edit calls — the bullet about the glossary (line 103) is replaced by a pointer section at the end of the file. The rule sentence stays in the header paragraph of `glossary.md` (line 3).

`old_string` (the whole bullet line, one line, followed by its newline), `new_string` empty:

```text
- **Словарь терминов `glossary.md`** (решение пользователя 2026-10-08). Собран из всех терминов банка `bank/`: для каждого понятия — один основной русский термин (по возможности близкий к английскому: «валидационная выборка» — `validation set`), английский перевод и синонимы. В вопросах, эталонных ответах и объяснениях употреблять **только основной термин** из словаря; синонимы — не употреблять. Перед каждым вопросом, эталоном или объяснением сверяться со словарём. Нового понятия в словаре нет — добавить строку в `glossary.md` и дальше употреблять её основной термин.
```

Then append the pointer section at the end of the file:

`old_string`:

```text
- Оценка — коротко: баллы, что прозвучало, что пропущено, эталонный ответ.
```

`new_string`:

```text
- Оценка — коротко: баллы, что прозвучало, что пропущено, эталонный ответ.

## Glossary

Glossary file: `glossary.md`
```

- [ ] **Step 7:** verify in `ML_Sobes_2026` (read-only runs; design 8 step 7) and in `Local_LLM_selection` (NFR-8).

```bash
echo '{"prompt":"Объясни кросс-валидацию","cwd":"/home/bgs/ai-steward/Gena_Beeline_Local/ML_Sobes_2026"}' | python3 claude-home/hooks/glossary.py memo | jq -r .hookSpecificOutput.additionalContext | head -c 600
```

Expected: the targeted form with the `перекрёстная проверка` line.

```bash
echo '{"hook_event_name":"Stop","cwd":"/home/bgs/ai-steward/Gena_Beeline_Local/ML_Sobes_2026","last_assistant_message":"Это сообщение написано по-русски. Добавь фича в модель."}' | python3 claude-home/hooks/glossary.py stop | jq -r .hookSpecificOutput.additionalContext | head -c 300
```

Expected: the one-line request with `«фича» → «признак»`.

```bash
echo '{"prompt":"слово","cwd":"/home/bgs/ai-steward/Gena_Beeline_Local/Local_LLM_selection"}' | python3 claude-home/hooks/glossary.py memo; echo "exit=$?"
```

Expected: empty output, `exit=0` (that project has no `## Glossary` heading).

- [ ] **Step 8:** hand over: the two changed files in `ML_Sobes_2026` are left uncommitted for the user (this plan commits nothing there). Record in bd notes: the user's answers at both stops.

```bash
bd update python-ai-skills-du5 --append-notes "Task 14: ML_Sobes_2026 glossary.md converted (629 in / 629 out, 567 forms in, 566 out) and AGENTS.md pointer written, uncommitted there; D-GATE answer: <A|B|C>."
```

Expected: the note is saved.


## Task 15: CONDITIONAL on D-GATE = A: do not scan the glossary's own entry lines

**Serves:** NFR-3 (the gate must not refuse a glossary that follows its own contract); FR-5b; FR-6.

**Run this task only if the user chose A at the Task 14 stop; otherwise skip it and mark it skipped in the bd notes.**

**Files:** modify `claude-home/hooks/test_glossary.py`, `claude-home/hooks/glossary.py` (Edit tool).

**Behaviour:** `scan_text` does not read a line that is verbatim an entry line of the glossary it checks; every other line of the same file, including the prose around the section, is still scanned. This replaces the design's rule that a definition using another group's forbidden form is a finding (design 5.3 step 2); it removes 327 of 336 findings measured for the ML_Sobes glossary.

- [ ] **Step 1:** replace the test that encodes the design's rule (RED: the replacement fails against the current code).

`old_string`:

```text
def test_staged_checks_the_glossary_file_itself_for_foreign_forbidden_forms(home, tmp_path):
    body = "- «лог» → **журнал** — то же, что фича\n- «фича» → **признак**\n"
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\n" + body})
    sh(root, "add", "-A")
    assert staged(home, root).stdout == "AGENTS.md:3: «фича» → «признак»\n"
```

`new_string`:

```text
def test_staged_does_not_scan_the_glossary_entry_lines_but_scans_the_rest_of_the_file(home, tmp_path):
    body = "- «лог» → **журнал** — то же, что фича\n- «фича» → **признак**\n"
    root = make_project(tmp_path, {"AGENTS.md": "## Glossary\n\n" + body + "\n## Другое\n\nЗдесь лог в прозе.\n"})
    sh(root, "add", "-A")
    assert staged(home, root).stdout == "AGENTS.md:8: «лог» → «журнал»\n"
```

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q -k staged
```

Expected: `1 failed, 9 passed, 116 deselected`.

- [ ] **Step 2:** change the loop of `scan_text`.

`old_string`:

```text
    findings = []
    for line_no, line in enumerate(governed_lines(text), 1):
        if (only_lines is not None and line_no not in only_lines) or not CYRILLIC.search(line):
            continue
```

`new_string`:

```text
    entry_lines = {group.line for group in glossary.groups}
    findings = []
    for line_no, (line, original) in enumerate(zip(governed_lines(text), text.split("\n")), 1):
        if (only_lines is not None and line_no not in only_lines) or not CYRILLIC.search(line) or original in entry_lines:
            continue
```

- [ ] **Step 3:** GREEN, gate, commit.

```bash
python3 -m pytest claude-home/hooks/test_glossary.py -q
```

Expected: `126 passed`.

```bash
ruff check claude-home/hooks/glossary.py claude-home/hooks/test_glossary.py
```

Expected: `All checks passed!`

```bash
git add claude-home/hooks/glossary.py claude-home/hooks/test_glossary.py
```

```bash
git commit -m "feat(glossary): do not scan the glossary entry lines" -m "A definition may use a word another group forbids; the rest of the file is still scanned. Refs: python-ai-skills-du5"
```


## Task 16: FR-15: file the bd task for `Local_LLM_selection`

**Serves:** FR-15; NFR-8 (nothing in that repository is touched).

**Files:** create `$TMPDIR/du5-fr15/description.md` (Write tool, not committed). The task is filed here and executed in `Local_LLM_selection`.

- [ ] **Step 1:** write the description file with the Write tool (the design's section 9 text, line references as in the design; they were read on 2026-10-15 and are re-checked by whoever executes the task).

```text
Convert `CLAUDE.md:15-212` (`# 1. Словарь…`: 29 items — 8 generic nouns with qualification semantics in «Никогда не общее слово — всегда точное», 21 forbidden items with 26 forms, 1 with a source, 0 with definitions) to the python-ai-skills entry form (`- «form» → **canonical** — definition (источник: …)`; exception lines for `VOCAB_EXCEPTIONS` `vocab.py:67-72`; the 10 `QUALIFIED` patterns `vocab.py:74-85` have no equivalent in the contract — decide whether qualification stays a project-local rule inside `vocab.py` or becomes exception lines).

Decide first which file carries it: `AGENTS.md` (5,926 bytes) and `CLAUDE.md` (29,735 bytes) are two regular files (Claude Code reads `CLAUDE.md` only; the global rule `claude-home/CLAUDE.md:42` requires `CLAUDE.md -> AGENTS.md`).

Then either retire `vocab.py`'s section parsing (`_FORBIDDEN_HEADING`/`_GENERIC_HEADING` `vocab.py:61-62`, `_ITEM_RE` `:110`) in favour of `~/.claude/hooks/glossary.py --staged`, keeping its report and template plumbing (about 360 lines) and its 44 tests green, or keep `vocab.py` reading the new form; update `.pre-commit-config.yaml:10-15` (`vocab-check`).

Replace `spark-public-bot/AGENTS.md:43-46` with a `## Glossary` section whose body is `Glossary file: \`/home/bgs/ai-steward/Gena_Beeline_Local/Local_LLM_selection/<file>\`` (keep its 6 local items as entries of its own glossary or of the pointed file — one copy, NFR-4). Old texts stay as they are (`CLAUDE.md:205-212`).

Acceptance: `glossary.py --staged` and `vocab.py --staged` agree on a staged file with one forbidden form; 44 tests pass; `test_real_repository_has_no_vocabulary_findings` (`test_vocab.py:290`) passes.

Depends on python-ai-skills-du5 merged. Source: `docs/superpowers/specs/20261015-synonym-glossary-design.md` section 9; discovery decision Q6, FR-15, NFR-8.
```

- [ ] **Step 2:** file the task.

```bash
bd create "Glossary: migrate the vocabulary of CLAUDE.md to the ## Glossary form and point spark-public-bot at it" -t task -p 3 -l glossary --deps discovered-from:python-ai-skills-du5 --body-file $TMPDIR/du5-fr15/description.md
```

Expected: the new issue id is printed. If `--deps discovered-from:...` is refused, re-run without `--deps` and put the dependency in the description's last paragraph (already there).

```bash
bd show <the printed id>
```

Expected: title, type `task`, priority P3, label `glossary`; the description starts with `Convert CLAUDE.md:15-212`.

Nothing is committed in this task.


# Phase 5: close

## Task 17: CHANGELOG, full gate, rollout command, inputs for the Finish step

**Serves:** FR-13; FR-11; NFR-2 and NFR-3 (final evidence); design 3.5 item 2 (refresh command prepared, not run).

**Files:** modify `CHANGELOG.md` (Edit tool; read lines 1-12 first).

- [ ] **Step 1:** add the entry under `## [Unreleased]` -> `### Added` (first bullet of the section). The counts in the entry are the plan-time values: replace them by the numbers Task 13 Step 2 printed if they differ.

`old_string`:

```text
## [Unreleased]

### Added
```

`new_string`:

```text
## [Unreleased]

### Added
- Per-project synonym glossary (bd `python-ai-skills-du5`): `claude-home/hooks/glossary.py`, one stdlib module with three modes over one matcher. A project keeps a `## Glossary` section in its `AGENTS.md` — one bullet per group, `- «forbidden», «forbidden» → **canonical** — definition (источник: …)`, plus exception lines that carry a source — or, above 200 lines or 8,000 characters, one line ``Glossary file: `glossary.md` `` pointing at a separate file (a relative or an absolute path; one hop). `memo` (`UserPromptSubmit`, timeout 3 s) sends the whole section, or only the groups the prompt touches, or a pointer, at most 8,000 characters; `stop` (`Stop`, timeout 10 s) asks for one line `Поправка к термину: «X» → «Y»` per forbidden form of the last answer, never blocks, and journals to `blocks.jsonl` under `hook` = `glossary`; `--staged` is called from the bootstrap `pre-commit` hook (`claude-home/git-template/pre-commit`) and, as a local hook `glossary-check`, from this repository's `.pre-commit-config.yaml` (a commit here runs it twice; the local-hook form is documented in `_linters/reference/linters.md`), reports forbidden forms in the changed lines of staged text files as `<path>:<line>: «form» → «canonical»` and exits 1 (0 clean, 2 glossary unreadable). Forms match with Russian case endings (Cyrillic forms ignore case, Latin forms are literal, a hyphen or underscore is a boundary on both sides); code identifiers, backticks, «quotes», fenced blocks, links and lines without Cyrillic are not read. Silent in a project without the section. `explanation-terms.py` leaves the forbidden Latin forms of the glossary to this hook. Rule paragraph in `claude-home/CLAUDE.md` -> Explanation Protocol, rationale and `glossary.md` tree line in `CLAUDE-APPENDIX.md`. `grace-init/assets/glossary-section.md.template` is the one skeleton: `grace-init` appends it to its `AGENTS.md` template, `_init` points at it. Samples: the `## Glossary` section of this repository — groups kept by a counting rule (whole words, at least 3 occurrences of each of two designations in the assistant text of this project's session transcripts on 2026-10-20: `журнал` 218 / `лог` 9, `симлинк` 84 / `символическая ссылка` 4, `субагент` 174 / `подагент` 75; canonical forms chosen by the user where the documents' counts differ by less than 2 to 1) — and `ML_Sobes_2026/glossary.md`, converted by a one-off script from 629 table rows (629 in, 629 out; 567 forms in, 566 out, one form equal to its own canonical term dropped) with a pointer section in its `AGENTS.md`. `Local_LLM_selection` is not touched (its migration is a separate bd task). Tests: `claude-home/hooks/test_glossary.py` (126 tests), listed in `make test`; one test added to `test_explanation_terms.py`
```

(If Task 15 ran, add to the entry: "the glossary's own entry lines are not scanned". The counts are the plan-time values; if Task 13 Step 2 printed other numbers, use those.)

- [ ] **Step 2:** full gate.

```bash
make test
```

Expected: sum of the five passed counts `730` (603 + 126 + 1), no failures.

```bash
ruff check claude-home/hooks/
```

Expected: exactly `Found 1 error.` (the pre-existing F401); none from `glossary.py` or `test_glossary.py`.

```bash
python3 -m json.tool claude-home/settings.json.template > /dev/null
```

Expected: exit 0.

```bash
pre-commit run --all-files
```

Expected: every hook `Passed`, including `glossary-check`.

- [ ] **Step 3:** the NFR evidence in one place (quote the outputs in the final report).

```bash
( time echo '{"prompt":"кросс-валидация","cwd":"/home/bgs/ai-steward/Gena_Beeline_Local/ML_Sobes_2026"}' | python3 claude-home/hooks/glossary.py memo >/dev/null ) 2>&1 | grep real
```

Expected: `real` below `3s` (NFR-1/NFR-2; measured 0.66 s on 2026-10-20).

```bash
jq '[.hooks.Stop[0].hooks[].timeout, .hooks.UserPromptSubmit[0].hooks[].timeout]' ~/.claude/settings.json
```

Expected: `[10, 10, 3, 3, 3, 3]` (the two Stop handlers, then the four UserPromptSubmit handlers).

- [ ] **Step 4:** prepare the rollout command as text and keep it in bd notes — the plan never runs it; the user does. The selection rule is the installer's own marker test (`scripts/install-claude-symlinks.sh:211`).

```bash
for h in ~/ai-steward/Gena_Beeline_Local/*/.git/hooks/pre-commit; do
  grep -q 'Bootstrap pre-commit hook installed via ~/.git-template' "$h" \
    && install -m 755 ~/.git-template/hooks/pre-commit "$h" && echo "refreshed $h"
done
```

Expected output when the user runs it: one `refreshed <path>` line per repository that carries the marker (25 on 2026-10-20, this checkout included; the design counted 23 on 2026-10-15). A repository whose hook is a project-specific override is not touched. Repositories without any hook copy and without a config (about 54) are reached only by re-creating the hook with `git init`.

```bash
bd update python-ai-skills-du5 --append-notes "Rollout (user runs, not the agent): refresh of the old bootstrap-hook copies — command in the plan 20261015-synonym-glossary-plan.md Task 17 Step 4."
```

Expected: the note is saved.

- [ ] **Step 5:** commit.

```bash
git add CHANGELOG.md
```

```bash
git commit -m "docs(glossary): add the changelog entry of the project glossary" -m "Counting rule and counts of the sample groups, the conversion check and the rollout note. Refs: python-ai-skills-du5"
```

- [ ] **Step 6:** inputs for Step 12 (Finish) of `do-feature` — collect and return, do not close the bead.

```bash
git log --oneline 1fb5e4e..HEAD
```

Expected: 14 commits after the approved design (`1fb5e4e`), 15 when Task 15 ran: 10 `feat` (Tasks 2-10 and 12) and 4 `docs` (the plan, Tasks 11, 13, 17).

```bash
git diff --stat 1fb5e4e..HEAD
```

Expected: about 20 changed files; none outside the file structure above.

Return to the orchestrator: the commit range `1fb5e4e..HEAD`; the outputs of Task 1 Step 2, Task 10 Step 8, Task 13 Steps 2 and 7, Task 14 Steps 2-3 and 7, Task 17 Step 2; the user's answers at the two stops; the prepared rollout command; the open items (the bd id of Task 16; ML_Sobes_2026 files left uncommitted; the live check that a fresh Claude Code session shows the memo and the Stop line is a user action, as in Task 14 of `20261015-question-memo-hook-plan.md`); closing the bead belongs to the Finish step.


## Deviations from the design

1. **Section contract (design 4.1 vs 3.6 and test G).** The design says every non-blank line of the section must match one of the line regexes, and also that the skeleton, which holds prose, parses to 0 groups and 0 contract errors; the two cannot both hold. Plan: only *bullets* are strict; prose and fenced lines are skipped; a `Glossary file:` line is a pointer only as the whole body (the design's own remark under 3.6 says the same for the skeleton's last line). The design's three contract-error examples are all bullets and stay errors.
2. **Constants.** `SHORT_FORM_CHARS`, `HOOK_CAP_CHARS` and `HOOK_NAME` of design 4.4 are not defined: the first two are never read (the boundary already enforces whole-token matching; the cap is respected by `MEMO_MAX_CHARS`), the third is one literal. Excess-code check: trace test.
3. **Regex cache.** One `lru_cache` per form (`form_regex`), not keyed on the glossary text; same effect, no key to build.
4. **FR-7 test.** `OOF` of design 7.F is not a candidate of `explanation-terms.py`; the plan's test uses a hyphenated form in a glossary outside the repository (Task 8). Verified RED and GREEN in a scratch copy.
5. **Test counts.** Design 7 estimates about 60 tests; the plan has 126 (parametrised cases count one each). The ML_Sobes-form fixture has 12 rows and 10 forms (the design's "9 scannable forms" depended on an unspecified fixture).
6. **Design 4.3 figures.** The forms that can never fire are 14, not 6, and the qualifier forms 4, not 6 (Task 14 shows the lists to the user).
7. **New finding for the user (D-GATE).** 336 findings in the converted ML_Sobes glossary itself, 327 inside entry lines; a conditional Task 15 carries the fix if the user chooses it.
8. **New tests not in the design:** functional tests of the bootstrap hook (a commit with a new forbidden form is refused, a clean one passes), a staged test with an absolute pointer, one for an entry-line directory named like an instruction file.
9. **Refresh count.** 25 repositories carry the bootstrap marker on 2026-10-20 (design: 23 on 2026-10-15).
10. **Task 13 candidates.** Two of the design's five candidate groups fail the counting rule (nothing mixed: `реестр моделей`, `хук`); the canonical form of two others is decided by the user, not by the design's guess.
11. **One installer run (Task 10)** covers Task 9's template and Task 10's hook copy.
12. **Rule paragraph.** Nested backticks of design 3.7 replaced by a double-backtick span.

## Self-review (do-feature reference, Step 9) — executed on the finished plan

**1. Spec coverage.** Every requirement of the Discovery has a task; the `Serves` line of each task names them. Checked by script against the list FR-1..FR-15 (FR-5a, FR-5b separate) and NFR-1..NFR-9:

| Requirement | Tasks | Verification step |
|---|---|---|
| FR-1 | 2, 11, 13 | Task 2 tests (entry, pointer), Task 11 guard, Task 13 guard |
| FR-2 | 2, 12, 13 | Task 2 entry tests, Task 12 asset |
| FR-3 | 4, 5, 11, 13 | Task 5 memo text, Task 11 rule |
| FR-4 | 3, 5, 9 | Task 3 lookup tests, Task 5, Task 9 wiring test |
| FR-5a | 4, 6, 9 | Task 6 tests, Task 9 |
| FR-5b | 4, 7, 10, 15 | Task 7 tests, Task 10 functional tests |
| FR-6 | 2, 4, 7, 15 | Task 4 exemption cases |
| FR-7 | 8 | Task 8 RED/GREEN |
| FR-8 | 12 | Task 12 tests |
| FR-9 | 11 | Task 11 guard (names once), principles guard |
| FR-10 | 2, 3, 14 | Task 2 (no import in the parser), Task 13, Task 14 |
| FR-11 | 2, 8, 9, 10, 17 | Tasks 2-13 tests, Task 9 Makefile line |
| FR-12 | 13, 14 | Task 13 guard, Task 14 commands |
| FR-13 | 17 | Task 17 Step 1 |
| FR-14 | 14 | Task 14 Steps 2-3 (629 / 629 / 567 asserted by the script) |
| FR-15 | 16 | Task 16 `bd show` |
| NFR-1 | 5, 14 | Task 5 tests (cap, three forms), Task 14 Step 3 timing |
| NFR-2 | 4, 7, 9, 14, 17 | Task 14 Step 3, Task 17 Step 3 |
| NFR-3 | 5, 6, 7, 10, 15, 17 | Tasks 5-7 silence and exit-code tests, Task 10 functional tests |
| NFR-4 | 2, 3, 7, 11 | Task 3 absolute pointer, Task 7 absolute pointer under `--staged` |
| NFR-5 | 3, 5, 6, 7 | Tasks 3, 5, 6, 7 silence tests |
| NFR-6 | 6, 7 | Task 6 and Task 7 journal tests |
| NFR-7 | 2, 13 | Task 2 (three line regexes), Task 13 guard (size) |
| NFR-8 | 14, 16 | Task 14 Step 7 (silent in `Local_LLM_selection`) |
| NFR-9 | 14 | Task 14 Step 2 (script assertion) |

Result: 0 requirements without a task, 0 without a verification step.

**2. Placeholder scan.** Searched the plan text for `TBD`, `TODO`, `implement later`, `fill in details`, `similar to task`, `add appropriate`: 0 hits. Every code step carries its complete code, every edit its `old_string` and `new_string`, every command its expected output. The only fill-ins are observed values that cannot exist before an earlier step runs: the counts printed by Task 13 Step 2 in the bd note and the CHANGELOG entry (plan-time values are given), the issue id printed by Task 16, and the user's answers at the two stops. Every code block and every edit of Tasks 2-13 and 15 was replayed on a scratch copy of the repository, and the RED and GREEN counts in this plan are the measured ones (final state: 126 tests in `test_glossary.py`, 17 in `test_explanation_terms.py`). Every `old_string` of an edit of an existing file was checked to occur exactly once.

**3. Type consistency.** Names and signatures used in later tasks are the ones defined in earlier tasks (each task's `Interfaces` block): `load_glossary(root, staged=False)`, `scan_text(text, glossary, only_lines=None)`, `Finding(line_no, form, canonical)`, `memo_context(glossary, prompt)`, `stop_context(glossary, findings)`, `HOOKS`, `forbidden_latin_forms(cwd)`; the test helpers `make_project`, `sh`, `home`, `run_mode`, `context_of`, `silent`, `stop`, `committed`, `staged`, `FORMS_BODY`, `LONG_RU` are defined before their first use. The full file passes 126 tests in the scratch replay, which is the type check.

**4. Reverse traceability** (every top-level name of the final `glossary.py` -> requirement; checked by script against the parsed module, 0 untraced names):

| Name | Requirement |
|---|---|
| `GlossaryError` | FR-5b (exit 2), NFR-5 |
| `Group` | FR-1, FR-2 |
| `Glossary` | FR-1, FR-4 |
| `cut_section` | FR-1 |
| `parse_section` | FR-1, FR-2, FR-6 |
| `git` | FR-4, FR-5b |
| `project_root` | FR-4 |
| `read_source` | FR-4, FR-5b (index first) |
| `load_glossary` | FR-4, NFR-4, NFR-5 |
| `word_regex` | FR-5a |
| `form_regex` | FR-5a, FR-5b |
| `blank` | FR-6 |
| `blank_ident` | FR-6 |
| `governed_lines` | FR-3, FR-6 |
| `Finding` | FR-5a, FR-5b |
| `scan_text` | FR-5a, FR-5b, FR-6 |
| `changed_lines` | FR-5b, NFR-2 |
| `forbidden_latin_forms` | FR-7 |
| `log_record` | NFR-6 |
| `emit` | FR-4, FR-5a |
| `memo_context` | FR-4, NFR-1 |
| `read_event` | NFR-3 |
| `run_memo` | FR-4 |
| `stop_context` | FR-5a |
| `run_stop` | FR-5a |
| `run_staged` | FR-5b |
| `main` | NFR-3 (exit codes) |
| `GLOSSARY_HEADING` | FR-1 |
| `INSTRUCTION_FILES` | FR-4, FR-10 |
| `SECTION_MAX_LINES` | FR-1 (200-line boundary), NFR-7 |
| `MEMO_MAX_CHARS` | NFR-1 |
| `GIT_TIMEOUT_S` | NFR-2 |
| `JOURNAL` | NFR-6 |
| `ENTRY_RE` | FR-1, FR-2, NFR-7 |
| `FORM_RE` | FR-1 (extracts the forms of an entry; not a line regex) |
| `POINTER_RE` | FR-1, NFR-4, NFR-7 |
| `EXCEPTION_RE` | FR-6, NFR-7 |
| `CYRILLIC` | FR-3 (governed lines), FR-7 |
| `ENDINGS` | FR-5a (case endings) |
| `BOUNDARY_L` | FR-5a, FR-6 |
| `BOUNDARY_R` | FR-5a, FR-6 |
| `IDENT_RE` | FR-6 (identifiers) |
| `TOKEN_EDGES` | FR-6 |
| `HOOKS` | FR-4, FR-5a (mode table) |

Configuration keys: the `Stop` handler (timeout 10 s) -> FR-5a, NFR-2; the fourth `UserPromptSubmit` handler (timeout 3 s) -> FR-4, NFR-2; the Makefile line -> FR-11; the `glossary-check` local hook -> FR-5b; the template step -> FR-5b, NFR-3.

**5. Excess-code check** (`~/.claude/skills/_code-quality/principles.md`).
- Deletion test: removing `cut_section`'s two-heading error breaks `test_two_glossary_headings_are_a_contract_error`; removing the `read_source` disk fallback breaks the absolute-pointer test under `--staged`; removing `blank_ident` breaks the identifier cases; removing the longest-form rule breaks `test_the_longest_form_wins_over_a_form_inside_it`; removing `forbidden_latin_forms` breaks the Task 8 tests; removing `log_record` breaks the journal tests. `Glossary.exceptions`, `.lines`, `.pointed` and `Group.line` are each read by a mode (`scan_text`, `memo_context`).
- Trace test: the table above; nothing is untraced. Three constants of the design were dropped because they trace to nothing (deviation 2).
- Boundary test: validation sits at the boundaries only: stdin JSON (`read_event`), the filesystem and git (`read_source`, `project_root`), the glossary file contract (`parse_section`). `run_memo`, `run_stop` and `scan_text` trust their inputs.
- Precedence: KISS and YAGNI applied: no opt-out variable, no journal refactor (`log_record` is one more copy of the journal writer that `explanation-terms.py`, `branch-name-check.py` and `block-no-verify.sh` each carry, design 3.1; consolidation is a separate refactor), no lemmatiser, no global layer, no package. The one conditional addition (Task 15) is justified by a measurement and is the user's call.

**6. Task order respects dependencies.** Parser (2) before lookup (3) before matcher (4, independent of 3 but tested through `parse`) before the modes (5-7); the shared matcher exists before `forbidden_latin_forms` (8); the module is complete and tested before it is wired (9) and before the bootstrap step calls it (10); the installer runs once after both edits (10); the rule text (11) and the skeleton (12) follow the working mechanism they describe; the samples (13, 14) need the live modes and the asset; D-GATE is decided at the Task 14 stop before Task 15; the CHANGELOG (17) needs the Task 13 counts.

**7. Machine constraints encoded.** Edit/Write for protected paths (constraint 1: Tasks 2-9, 11, 12, 15); standalone `git` with explicit `git add` lists (every commit step); `$TMPDIR` scratch (Tasks 13, 14, 16); the sandbox-bypass calls named and limited to two (Tasks 10, 14); the user-review stops (Tasks 13 Step 3, 14 Step 4); the refresh command prepared, never run (Task 17); outside-`$PWD` edits limited to two `*.md` files (Task 14).

## Unverified at plan time

1. The live behaviour of the Stop and `UserPromptSubmit` handlers in a fresh Claude Code session (settings render is tested; the session itself is a user action, the earlier plan's Task 14 precedent).
2. Whether pre-commit's `entry: bash -c '...'` form behaves the same on the other machine (probed here on pre-commit 4.6.0 only).
3. The Codex 32 KiB chain cap after the new `claude-home/CLAUDE.md` paragraph (about 1.1 KB): not re-measured.
4. Line references into `Local_LLM_selection` in the Task 16 text (`vocab.py`, `CLAUDE.md`) were read on 2026-10-15 by the design and are not re-read here.
