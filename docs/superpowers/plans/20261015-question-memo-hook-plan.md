---
feature: question-memo-hook
bd_id: python-ai-skills-r1f.3
date: 2026-10-15
status: draft
risk: medium
discovery: docs/superpowers/specs/20261015-question-memo-hook-discovery.md
design: docs/superpowers/specs/20261015-question-memo-hook-design.md
approach: bash-copy
tasks: 14
---

# Question memo hook: implementation plan (python-ai-skills-r1f.3)

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:executing-plans` (inline: several steps need the Edit/Write tools on sandbox-protected paths and one step needs the user's per-command sandbox-bypass approval, so subagent dispatch gains nothing). Steps use checkbox (`- [ ]`) syntax.

**Goal:** a new `## Questions and Numbers` section in `claude-home/CLAUDE.md` (question header, numbers rule, two-score rule `X% / Y%`) is re-sent before every user prompt by a new `UserPromptSubmit` hook; the four `best-*` skills, the user profile and the auto-memory point to the section instead of defining their own percentage; no copy of the rule text exists elsewhere.

**Bead:** `python-ai-skills-r1f.3` (answers `python-ai-skills-ao1`, parent `python-ai-skills-r1f`).
**Requirements:** [discovery](../specs/20261015-question-memo-hook-discovery.md) (FR-1..FR-9 incl. FR-2a, NFR-1..NFR-6, resolved questions Q1-Q5).
**Design:** [bash-copy](../specs/20261015-question-memo-hook-design.md) (implemented as approved; deviations of detail are listed at the end, section "Deviations from the design").

**Architecture:** one bash hook `claude-home/hooks/question-memo-inject.sh`, a line-for-line sibling of `task-level-inject.sh` (`awk` cut of one `## ` section + one `jq -n`, exit 0 on every path); one pytest file beside it; one handler in `settings.json.template`; text edits in `claude-home/CLAUDE.md`, `CLAUDE-APPENDIX.md` and four `SKILL.md` files.

**Tech stack:** bash, awk, jq (already used by `task-level-inject.sh`), pytest + stdlib `subprocess`/`json`, `ruff`, `pre-commit`, `codex` CLI.

## Global constraints (machine facts verified by the orchestrator)

1. **Sandbox write denial.** The Bash sandbox denies writes to `claude-home/hooks/`, `claude-home/CLAUDE.md`, `claude-home/output-styles` and `~/.claude/projects`. Every edit of files there goes through the **Edit / Write tools**, never shell redirects, `sed -i`, `tee` or `chmod` in the sandbox. Other repo files (`Makefile`, `settings.json.template`, `CHANGELOG.md`, `CLAUDE-APPENDIX.md`, `best-*/SKILL.md`) are also edited with Edit (fragile-shell-edit rule), although the sandbox would allow shell there.
2. **Git.** Only as standalone calls: no `&&`, `|`, `cd`, `-C`, redirects. Stage only the files listed in the step with explicit `git add <files>`. Never add phantom paths that a sandboxed `git status` may show (`.bashrc`, `.mcp.json`, `.claude/skills`, ...). Existing untracked noise that is not ours and must stay unstaged: `off.err`, `off.json`, `reports/`, `research_notes/`, and the modified `.beads/interactions.jsonl`, `docs/requirements.xml`, `docs/technology.xml`. Commits: Conventional Commits, English, hooks run (`--no-verify`, `SKIP=` never used). No `git push`.
3. **Temp files** only in `$TMPDIR`. `make install-symlinks` writes into `~/.claude` and re-renders `~/.claude/settings.json` from the template: it **must run with `dangerouslyDisableSandbox: true`** (Task 5), as its own Bash call, with the user's approval of that call. `chmod +x` on the new hook (Task 4) needs the same.
4. **Quality gate before each commit that touches code:** `make test` (baseline **473 of 473 passed** = 355 + 25 + 76 + 17; this plan adds 11 tests, so expect **484 of 484**) and `ruff check <changed .py files>`. Baseline of `ruff check claude-home/hooks/`: exactly 1 pre-existing error, F401 in `test_big_read_nudge.py:22` — **not fixed** (out of scope); the new test file must add none.
5. **Out-of-git files:** the profile `/home/bgs/ai-steward/Gena_Beeline_Local/CLAUDE.md`, the auto-memory file and `MEMORY.md` under `/home/bgs/.claude/projects/-home-bgs-ai-steward-Gena-Beeline-Local-python-ai-skills/memory/` are not in this repository: Task 13 edits them, nothing of them is committed here.
6. **Language:** repository files in English except the rule text, which is Russian by decision (design 2.1); the section text is used **verbatim** from the design as the orchestrator corrected it (coined words replaced: «точки утверждения», «автоматический выбор»).
7. **Command prefix:** each Bash call defines `R=/home/bgs/ai-steward/Gena_Beeline_Local/python-ai-skills` itself (shell state does not persist); all paths below are relative to `$R` unless absolute. Do not `cd`: pytest, make and git run with `$R` as the working directory of the session.

## File structure

- Create: `claude-home/hooks/question-memo-inject.sh` (mode 755), `claude-home/hooks/test_question_memo_inject.py`.
- Modify: `claude-home/CLAUDE.md` (+ section), `claude-home/CLAUDE-APPENDIX.md` (+ rationale paragraph), `claude-home/settings.json.template` (+ third handler), `Makefile` (+ one test file in `test:`), `CHANGELOG.md`, `best-recommend/SKILL.md`, `best-rank/SKILL.md`, `best-research/SKILL.md`, `best-questions/SKILL.md`.
- Modify outside git: profile `CLAUDE.md` item 3, auto-memory `best-questions-auto-select-80.md`, `MEMORY.md` line 6.
- Commit plan (3 commits, justification at the end of Task 7 and Task 12): A `docs` (spec + plan, already approved), B `feat` (section + appendix + hook + tests + Makefile + template + CHANGELOG), C `docs` (skill pointers + CHANGELOG line).

---

## Task 1: Preflight and baseline

**Serves:** NFR evidence baseline (constraint 4).

- [ ] **Step 1: claim the bead and confirm the tree.**

```bash
bd update python-ai-skills-r1f.3 --claim
```

Expected: the issue is already `IN_PROGRESS` and assigned to `bgs2509`; an "already claimed" message is fine.

```bash
git status --short
```

Expected (the snapshot at plan time): `M .beads/interactions.jsonl`, `M docs/requirements.xml`, `M docs/technology.xml`, `?? docs/superpowers/specs/20261015-question-memo-hook-design.md`, `?? docs/superpowers/specs/20261015-question-memo-hook-discovery.md`, `?? docs/superpowers/plans/20261015-question-memo-hook-plan.md`, plus `off.err`, `off.json`, `reports/`, `research_notes/`. Branch `main`.

- [ ] **Step 2: record the baseline.**

```bash
make test
```

Expected: four summary lines, sum of the passed counts `473`, no failures. Write the four numbers down.

```bash
ruff check claude-home/hooks/
```

Expected: `Found 1 error.` (F401, `test_big_read_nudge.py:22`).

- [ ] **Step 3: confirm the bd note syntax** (needed in Tasks 6 and 14).

```bash
bd update --help
```

Expected: the help lists the flag that appends a note (`--notes` or `--append-notes`). Use exactly the flag it lists wherever a later step says "record in bd notes".

- [ ] **Step 4: commit A — the approved Discovery, Design and this plan.**

```bash
git add docs/superpowers/specs/20261015-question-memo-hook-discovery.md docs/superpowers/specs/20261015-question-memo-hook-design.md docs/superpowers/plans/20261015-question-memo-hook-plan.md
```

```bash
git commit -m "docs(question-memo): add discovery, design and plan of the question memo hook" -m "Refs: python-ai-skills-r1f.3"
```

Expected: pre-commit hooks pass (gitleaks, `principles-ssot` skips `docs/`); one commit with 3 files. Why separate: the approved requirements are a record that must not be mixed into the code commit.

---

## Task 2: RED — write the test file

**Serves:** FR-6 (test file), FR-3 (hook contract), FR-1/NFR-1 (guard on the real file, risk 1 of Discovery), NFR-3, NFR-4 (synthetic fixture carries a marker, never the rule text).

**Files:** create `claude-home/hooks/test_question_memo_inject.py`.

- [ ] **Step 1: write the file with the Write tool**, exactly this content.

```python
"""Tests for question-memo-inject.sh — UserPromptSubmit hook that re-sends the memo section.

The rules for question headers, numbers and option scores live in one place: the
"Questions and Numbers" section of the global CLAUDE.md. CLAUDE.md is read only at
session start, so a running session would not learn a changed rule. The hook cuts
that section at run time and injects it before every prompt; a missing file, a
missing section or odd input means silence. The fixture carries a marker, never the
rule text, so the rule has one home (bd python-ai-skills-r1f.3).
"""

import json
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent / "question-memo-inject.sh"
REAL_CLAUDE_MD = Path(__file__).resolve().parents[2] / "claude-home" / "CLAUDE.md"
HEADING = "## Questions and Numbers"
MAX_MEMO_CHARS = 2000  # NFR-1: the cut section stays far below the 10,000-character hook cap
MAX_MEMO_LINES = 20
SECTION = f"{HEADING}\n\n**Rule (stub):** MEMO-MARKER\n"
DOC = "# Global\n\n## Output Formatting\n\nPREVIOUS-SECTION\n\n" + SECTION + "\n## Project Classification\n\nNEXT-SECTION\n"
PROMPT = {"hook_event_name": "UserPromptSubmit", "prompt": "hi"}


@pytest.fixture
def claude_md(tmp_path):
    path = tmp_path / "CLAUDE.md"
    path.write_text(DOC)
    return path


def run(payload, memo_file):
    return subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps(payload) if not isinstance(payload, str) else payload,
        capture_output=True,
        text=True,
        timeout=30,
        env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "QUESTION_MEMO_FILE": str(memo_file)},
    )


def test_prompt_gets_the_memo_section(claude_md):
    result = run(PROMPT, claude_md)
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert out["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "MEMO-MARKER" in out["hookSpecificOutput"]["additionalContext"]
    assert str(claude_md) in out["hookSpecificOutput"]["additionalContext"]
    assert "decision" not in out


def test_only_the_memo_section_is_cut(claude_md):
    context = json.loads(run(PROMPT, claude_md).stdout)["hookSpecificOutput"]["additionalContext"]
    assert "PREVIOUS-SECTION" not in context
    assert "NEXT-SECTION" not in context
    assert "## Project Classification" not in context


def test_missing_file_is_silent(tmp_path):
    result = run(PROMPT, tmp_path / "absent.md")
    assert result.returncode == 0
    assert result.stdout == ""


def test_file_without_the_section_is_silent(tmp_path):
    path = tmp_path / "CLAUDE.md"
    path.write_text("# Global\n\n## Project Classification\n\nafter\n")
    result = run(PROMPT, path)
    assert result.returncode == 0
    assert result.stdout == ""


def test_directory_instead_of_file_is_silent(tmp_path):
    result = run(PROMPT, tmp_path)
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


@pytest.mark.parametrize("payload", ["", "not json", "[]", "42"])
def test_malformed_input_degrades_to_silence(payload, claude_md):
    result = run(payload, claude_md)
    assert result.returncode == 0
    assert result.stdout == ""


def test_default_file_is_next_to_the_hooks_dir(tmp_path):
    # Installed layout: <claude home>/hooks/<hook> and <claude home>/CLAUDE.md;
    # the claude home may differ from $HOME/.claude (installer's CLAUDE_HOME).
    home = tmp_path / "claude-home"
    (home / "hooks").mkdir(parents=True)
    hook = home / "hooks" / HOOK.name
    hook.write_text(HOOK.read_text())
    (home / "CLAUDE.md").write_text(DOC)
    result = subprocess.run(
        ["bash", str(hook)],
        input=json.dumps(PROMPT),
        capture_output=True,
        text=True,
        timeout=30,
        env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent"},
    )
    assert result.returncode == 0
    assert "MEMO-MARKER" in json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


def cut_section(text):
    lines, inside, cut = text.splitlines(), False, []
    for line in lines:
        if line.startswith("## "):
            inside = line.startswith(HEADING)
        if inside:
            cut.append(line)
    return cut


def test_real_claude_md_has_one_memo_section_under_the_cap():
    # Guard (Discovery risk 1): a renamed or moved heading would make the hook silent
    # with nobody noticing; a bloated section would be re-sent before every prompt.
    text = REAL_CLAUDE_MD.read_text(encoding="utf-8")
    assert text.splitlines().count(HEADING) == 1
    cut = cut_section(text)
    assert len("\n".join(cut)) <= MAX_MEMO_CHARS
    assert len(cut) <= MAX_MEMO_LINES
```

- [ ] **Step 2: run it and see RED.**

```bash
python3 -m pytest claude-home/hooks/test_question_memo_inject.py -q
```

Expected: `11 failed`. Reasons: tests 1-7 fail because `bash` cannot open `question-memo-inject.sh` (return code 127, or `FileNotFoundError` in the copy test); the guard fails on `assert 0 == 1` (the heading does not exist yet).

- [ ] **Step 3: lint the test.**

```bash
ruff check claude-home/hooks/test_question_memo_inject.py
```

Expected: `All checks passed!`

---

## Task 3: The section and its rationale — guard test GREEN

**Serves:** FR-1, FR-2, FR-2a, NFR-1, NFR-5 (section), NFR-4 (single home), appendix convention ("Почему" per heading).

**Files:** modify `claude-home/CLAUDE.md`, `claude-home/CLAUDE-APPENDIX.md` (both with the Edit tool).

- [ ] **Step 1: read both files** (the Edit tool requires it): Read `claude-home/CLAUDE.md` lines 25-31 and `claude-home/CLAUDE-APPENDIX.md` lines 1-20.

- [ ] **Step 2: insert the section into `claude-home/CLAUDE.md`** (Edit tool; one blank line on each side; position after Output Formatting, before Project Classification).

`old_string`:

```text
нигде не активирован.)

## Project Classification
```

`new_string`:

````text
нигде не активирован.)

## Questions and Numbers

**Rule (шапка вопроса):** каждый вопрос пользователю открывают три строки, затем сам вопрос:
1. **План:** все задачи по порядку (1–3 строки).
2. **Сейчас:** какая задача и какой её шаг или вопрос из скольких.
3. **Цель вопроса:** что решает ответ.

**Rule (числа):** у каждого числа есть единица измерения. У каждого процента названы база («N из M») и точка сравнения (с чем сравниваем). Действует в чате и в любом тексте для пользователя — отчёт, задача в трекере, CHANGELOG, документация — на любом языке.

**Rule (две оценки варианта):** каждый вариант в любой рекомендации (все `best-*`, открытые вопросы do-feature, любой другой вопрос с вариантами) несёт две оценки в форме `X% / Y%`: X — вероятность того, что пользователь выберет этот вариант; Y — вероятность того, что вариант выполнит критерии приёмки задачи без переделки. Значения X всех вариантов плюс строка «Свой вариант / ни один — N%» в сумме дают 100 %; значения Y независимы. Автоматический выбор — только когда X лучшего варианта превышает X следующей строки (строка «Свой вариант» тоже конкурент) не менее чем на 20 процентных пунктов — разность значений X, не относительный прирост — И Y лучшего не ниже 80 %. Во всех остальных случаях, а также в точках утверждения пользователем (USER APPROVAL) — вопрос пользователю.

## Project Classification
````

- [ ] **Step 3: insert the rationale paragraph into `claude-home/CLAUDE-APPENDIX.md`** (Edit tool; the appendix mirrors the section order; the new heading goes between Output Formatting and Project Classification). Grammar fix against the design text: «Порог автоматического выбора» (genitive).

`old_string`:

```text
## Project Classification

**Почему:** GRACE и do-feature создают overhead
```

`new_string`:

````text
## Questions and Numbers

**Почему:** вопрос приходит пользователю посреди длинной работы, часто после паузы: без строк «План / Сейчас / Цель вопроса» он восстанавливает контекст по переписке. Число без единицы и процент без базы («18 %» вместо «3 из 17») нельзя ни проверить, ни сравнить. Две оценки варианта разделяют два вопроса, которые прежний «процент уверенности» сливал в один: выберет ли пользователь (X — распределение одного выбора, поэтому сумма 100 %) и сработает ли вариант (Y — независимые вероятности). Строка «Свой вариант / ни один» внутри 100 % не позволяет раздать всю сумму только перечисленным вариантам. Порог автоматического выбора (разрыв по X не менее 20 процентных пунктов И Y не ниже 80 %) заменяет прежнее «выше 80 % уверенности» из профиля пользователя и авто-памяти (решения пользователя 2026-10-15, bd `python-ai-skills-r1f`, `python-ai-skills-ao1`). Доставка: раздел читается при старте сессии и повторяется перед каждым ответом хуком `hooks/question-memo-inject.sh` (UserPromptSubmit), потому что CLAUDE.md сессия читает только при старте (python-ai-skills/CLAUDE.md → «Live immediately has one exception»). Проверка после ответа (Stop) отвергнута: она заставляет модель писать второе сообщение (bd `python-ai-skills-r1f.1`).

## Project Classification

**Почему:** GRACE и do-feature создают overhead
````

- [ ] **Step 4: the guard test is GREEN, the rest is still RED.**

```bash
python3 -m pytest claude-home/hooks/test_question_memo_inject.py -q
```

Expected: `1 passed, 10 failed` (the passed one is `test_real_claude_md_has_one_memo_section_under_the_cap`).

- [ ] **Step 5: measure the section (NFR-1 evidence).**

```bash
awk '/^## /{inside = /^## Questions and Numbers/} inside' claude-home/CLAUDE.md | wc -m
```

Expected: about `1250` (design measured 1,234 for the heading-to-last-line text), well below `2000`.

- [ ] **Step 6: the other guards still pass** (the section must not look like a restated principle).

```bash
python3 -m pytest claude-home/hooks/test_principles_ssot.py claude-home/hooks/test_task_level_inject.py -q
```

Expected: all passed, 0 failed.

---

## Task 4: GREEN — the hook

**Serves:** FR-3, NFR-2, NFR-3, NFR-4.

**Files:** create `claude-home/hooks/question-memo-inject.sh`.

- [ ] **Step 1: write the file with the Write tool**, exactly this content.

```bash
#!/bin/bash
# UserPromptSubmit hook: before every answer, re-send the "Questions and Numbers"
# section of the global CLAUDE.md (question header, numbers rule, two-score rule
# X% / Y%) as additionalContext (bd python-ai-skills-r1f.3).
#
# The rules live only in that section; this hook cuts it at run time and keeps no
# copy. CLAUDE.md is read only at session start, so a session older than the rule
# would never learn it — a hook fires in running sessions too (see
# task-level-inject.sh and delegation-pool-nudge.sh). No post-answer (Stop) check:
# it would make the model write a second message. A per-project glossary delivery
# (bd python-ai-skills-du5) may reuse this hook later; it is not built.
#
# Contract:
#   - stdin: JSON object (UserPromptSubmit input); the prompt text is not used
#   - env: QUESTION_MEMO_FILE (default: CLAUDE.md one level above this hook's directory,
#     i.e. <claude home>/CLAUDE.md, whatever CLAUDE_HOME the installer used)
#   - exit 0 always (advisory only; no decision field, nothing on stderr)
#   - stdout: additionalContext JSON when the section is found; empty otherwise
#     (stdin not a JSON object, file missing or unreadable, section absent)

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

- [ ] **Step 2: make it executable — run this Bash call with `dangerouslyDisableSandbox: true`** (the sandbox denies writes under `claude-home/hooks/`; settings run the hook by its path, so the mode bit matters). The user approves the call.

```bash
chmod 755 /home/bgs/ai-steward/Gena_Beeline_Local/python-ai-skills/claude-home/hooks/question-memo-inject.sh
```

```bash
ls -l claude-home/hooks/question-memo-inject.sh
```

Expected: mode `-rwxr-xr-x`.

- [ ] **Step 3: see GREEN.**

```bash
python3 -m pytest claude-home/hooks/test_question_memo_inject.py -q
```

Expected: `11 passed`.

- [ ] **Step 4: NFR-2 / NFR-3 evidence on the real file** (hook against the real `claude-home/CLAUDE.md`, timing, exit code, context size).

```bash
echo '{"hook_event_name":"UserPromptSubmit","prompt":"x"}' | QUESTION_MEMO_FILE=claude-home/CLAUDE.md bash -c 'time claude-home/hooks/question-memo-inject.sh' | jq -r '.hookSpecificOutput.additionalContext | length'
```

Expected: a number between `1300` and `1450` (design: 1,363), the `time` report shows `real` well below `3s` (design: 0.012 s), nothing on stderr. Then:

```bash
echo 'not json' | claude-home/hooks/question-memo-inject.sh; echo "exit=$?"
```

Expected: empty output, `exit=0`.

- [ ] **Step 5: lint.**

```bash
ruff check claude-home/hooks/
```

Expected: still exactly `Found 1 error.` (the pre-existing F401 in `test_big_read_nudge.py:22`); none from `test_question_memo_inject.py`.

---

## Task 5: Wiring — Makefile, template, installer re-render

**Serves:** FR-4 (template handler), FR-6 (Makefile list), NFR-6 (installer keeps the Codex link).

**Files:** modify `Makefile`, `claude-home/settings.json.template`.

- [ ] **Step 1: Makefile — add the test file to `test:`** (Edit tool). Read `Makefile` first. Tabs matter: the continuation lines are one TAB followed by 19 spaces.

`old_string`:

```text
claude-home/hooks/test_task_level_inject.py \
```

`new_string` (the second line starts with a TAB, then 19 spaces):

```text
claude-home/hooks/test_task_level_inject.py \
	                   claude-home/hooks/test_question_memo_inject.py \
```

```bash
cat -A Makefile | sed -n 27,29p
```

Expected: both lines start with `^I` followed by 19 spaces and end with `\$`.

- [ ] **Step 2: template — add the third handler** (Edit tool). Read `claude-home/settings.json.template` lines 410-432 first. Insert after the `git-finish-router.sh` handler, inside the same group (the group's `matcher: "*"` stays).

`old_string`:

```text
            "command": "'{{CLAUDE_HOME}}/hooks/git-finish-router.sh'",
            "timeout": 3
          }
```

`new_string`:

```text
            "command": "'{{CLAUDE_HOME}}/hooks/git-finish-router.sh'",
            "timeout": 3
          },
          {
            "type": "command",
            "command": "'{{CLAUDE_HOME}}/hooks/question-memo-inject.sh'",
            "timeout": 3
          }
```

If the Edit tool reports the `old_string` is not unique, extend it by the following lines (`        ]`, `      }`, `    ]`, `  },`, `  "statusLine": {`) copied exactly from the Read output.

- [ ] **Step 3: template is valid JSON and has 3 handlers.**

```bash
python3 -m json.tool claude-home/settings.json.template > /dev/null
```

Expected: exit 0, no output (redirect to `/dev/null` is allowed).

```bash
jq '.hooks.UserPromptSubmit[0].hooks | length' claude-home/settings.json.template
```

Expected: `3`.

- [ ] **Step 4: installer tests (the one-shell-word test now covers the new path).**

```bash
python3 -m pytest scripts/test_install_claude_symlinks.py -q
```

Expected: all passed (the count equals the baseline of that file; `test_every_hook_path_is_one_shell_word` passes, which needs the hook file to exist).

- [ ] **Step 5: re-render the live settings — Bash call with `dangerouslyDisableSandbox: true`** (it writes `~/.claude/settings.json` and symlinks into `~/.claude`; the user approves this call; idempotent, safe to re-run).

```bash
make install-symlinks
```

Expected: the installer ends without error.

- [ ] **Step 6: verify the live result (read-only).**

```bash
jq '.hooks.UserPromptSubmit[0].hooks | length' ~/.claude/settings.json
```

Expected: `3`.

```bash
echo '{"hook_event_name":"UserPromptSubmit","prompt":"x"}' | ~/.claude/hooks/question-memo-inject.sh | jq -r '.hookSpecificOutput.additionalContext' | head -4
```

Expected: first line `Rules for questions, numbers and option scores from /home/bgs/.claude/hooks/../CLAUDE.md (the only copy). Apply them to this answer:`, then a blank line, then `## Questions and Numbers`. This proves the installed layout (hook symlink next to the CLAUDE.md symlink) cuts the section without an override.

```bash
ls -l ~/.codex/AGENTS.md
```

Expected: a symlink to `.../python-ai-skills/claude-home/CLAUDE.md` (NFR-6: the installer keeps the Codex link).

---

## Task 6: Verification — which sections Codex loads (Discovery Q5, no code change)

**Serves:** NFR-6, scope item "Q5". Result is recorded in bd notes only.

- [ ] **Step 1: find the invocation.**

```bash
codex debug prompt-input --help
```

Expected: usage text for the subcommand (if it fails inside the sandbox with a read-only-filesystem error, re-run it with `dangerouslyDisableSandbox: true`).

- [ ] **Step 2: run it outside the sandbox from this repository — Bash call with `dangerouslyDisableSandbox: true`** (inside the sandbox it failed with `Error: Read-only file system (os error 30)`; the user approves the call). Use the arguments the help of Step 1 lists; the output goes to a file in `$TMPDIR`; if `$TMPDIR` is empty in the unsandboxed shell use `/tmp/claude`.

```bash
codex debug prompt-input > "${TMPDIR:-/tmp/claude}/codex-prompt-input.txt" 2>&1
```

(Add the positional prompt argument only if the help requires one.)

- [ ] **Step 3: read the result (sandboxed, read-only).**

```bash
grep -n '^## ' "$TMPDIR/codex-prompt-input.txt" | head -60
```

```bash
grep -c 'Questions and Numbers' "$TMPDIR/codex-prompt-input.txt"
```

```bash
grep -n '^## ' "$TMPDIR/codex-prompt-input.txt" | tail -5
```

Expected: the list of `## ` headings of `claude-home/CLAUDE.md` that Codex put into its prompt, whether `Questions and Numbers` is among them (count `>= 1`), and the last heading loaded (the file is about 40 KB, above Codex's 32 KiB default chain cap, so a tail truncation is possible; the new section sits about 2 KB into the file and should survive one).

- [ ] **Step 4: record in bd notes** with the flag found in Task 1 Step 3 (example form, replace the bracketed facts with the observed ones):

```bash
bd update python-ai-skills-r1f.3 --notes "Q5 (Codex chain, codex debug prompt-input, 2026-10-15): section 'Questions and Numbers' loaded: <yes|no>; last '## ' heading loaded: <heading>; total '## ' headings loaded: <n> of 22."
```

Expected: the note is saved. **Branch for Task 7:** if the section is `yes`, the CHANGELOG sentence "Codex reads it through `~/.codex/AGENTS.md`" stays; if `no`, replace that sentence with "Codex does not load it (bd `python-ai-skills-r1f.3` notes)" and file a bead: `bd create "Codex chain cap truncates claude-home/CLAUDE.md before Questions and Numbers" -t bug -p 2`.

---

## Task 7: CHANGELOG, quality gate, commit B

**Serves:** FR-8 (CHANGELOG), quality gate (constraint 4).

**Files:** modify `CHANGELOG.md`.

- [ ] **Step 1: add the entry under `## [Unreleased]` → `### Added`** (Edit tool; read the lines 6-16 of `CHANGELOG.md` first; the new bullet goes first in `### Added`).

`old_string`:

```text
### Added
- `claude-home/CLAUDE.md`: new `## Naming` section
```

`new_string`:

````text
### Added
- `claude-home/CLAUDE.md`: new `## Questions and Numbers` section (bd `python-ai-skills-r1f.3`, answers `python-ai-skills-ao1`) — every question to the user opens with «План / Сейчас / Цель вопроса»; every number carries a unit and every percentage its base («N из M») and comparison point, in chat and in every text written for the user; every option in a recommendation carries two scores `X% / Y%` (X = probability the user chooses it, X of all options plus «Свой вариант / ни один — N%» sum to 100 %; Y = probability it meets the acceptance criteria without rework), auto-select only at a gap of at least 20 percentage points in X over the next line and Y of at least 80 %, never at USER APPROVAL gates. Delivered before every answer by `claude-home/hooks/question-memo-inject.sh` (`UserPromptSubmit`, cuts the section at run time, silent otherwise, about 1,250 characters, 0.01 s), wired in `settings.json.template`; Codex reads it through `~/.codex/AGENTS.md`. Rationale paragraph in `CLAUDE-APPENDIX.md`. Guard test reads the real file (heading present once, at most 2,000 characters and 20 lines); 11 tests in `claude-home/hooks/test_question_memo_inject.py`, listed in `make test`
- `claude-home/CLAUDE.md`: new `## Naming` section
````

(The original second bullet continues after the replaced prefix; the Edit replaces only the matched prefix, so the rest of that line stays intact.)

- [ ] **Step 2: full gate.**

```bash
make test
```

Expected: sum of passed counts `484`, no failures (473 baseline + 11).

```bash
ruff check claude-home/hooks/test_question_memo_inject.py
```

Expected: `All checks passed!` (the directory-wide run still shows only the pre-existing F401.)

```bash
python3 -m json.tool claude-home/settings.json.template > /dev/null
```

Expected: exit 0.

- [ ] **Step 3: NFR-4 evidence — the rule text has one home.**

```bash
grep -rln 'точка сравнения' --include=*.md --include=*.sh --include=*.py --include=*.json --include=*.template . --exclude-dir=docs --exclude-dir=.git --exclude-dir=.beads
```

Expected: exactly one path, `./claude-home/CLAUDE.md`. (`docs/` is excluded: the Design quotes the section by necessity.)

- [ ] **Step 4: NFR-5 evidence — no project-specific word in the section.**

```bash
awk '/^## /{inside = /^## Questions and Numbers/} inside' claude-home/CLAUDE.md | grep -c 'python-ai-skills\|Sensedar\|bd \|GRACE'
```

Expected: `0` (grep exits 1 with count 0; that is the passing result).

- [ ] **Step 5: stage and commit B** (explicit files only; the exec bit is part of the `git add` of the hook).

```bash
git add claude-home/CLAUDE.md claude-home/CLAUDE-APPENDIX.md claude-home/hooks/question-memo-inject.sh claude-home/hooks/test_question_memo_inject.py Makefile claude-home/settings.json.template CHANGELOG.md
```

```bash
git ls-files -s claude-home/hooks/question-memo-inject.sh
```

Expected: mode `100755`.

```bash
git commit -m "feat(question-memo): deliver the questions-and-numbers rules before every answer" -m "New CLAUDE.md section Questions and Numbers (question header, numbers rule, two-score rule X% / Y%), re-sent by a UserPromptSubmit hook that cuts it at run time; guard test on the real file. Refs: python-ai-skills-r1f.3"
```

Expected: pre-commit passes (gitleaks, template JSON, settings render tests, hook regression suite, principles-ssot); one commit with 7 files. Justification: the section, the hook that delivers it, the wiring and the tests are one deliverable — the guard test needs the section, the template test needs the hook file — so splitting would leave an intermediate commit with a red gate.

---

## Task 8: `best-recommend/SKILL.md` pointers

**Serves:** FR-5 (`best-recommend`), NFR-4. Read the file first (Edit requirement); six Edit calls, each `old_string` unique in the file. Grammar fix against the design: «порог автоматического выбора».

- [ ] **Step 1: description (lines 5-7).**

`old_string`:

```text
Confidence expressed as %, explained like to a junior, each %
  backed by a one-line source, and an honest hypothesis-flag the moment there is
  doubt.
```

`new_string`:

```text
Two scores per option, written X% / Y% as defined in the
  global CLAUDE.md section "Questions and Numbers", explained like to a junior,
  each score backed by a one-line source, and an honest hypothesis-flag the
  moment there is doubt.
```

- [ ] **Step 2: line 17.**

`old_string`: `проценты + объяснение как джуну + источник + честный флаг неуверенности.`
`new_string`: ``оценки `X% / Y%` + объяснение как джуну + источник + честный флаг неуверенности.``

- [ ] **Step 3: line 29 (the whole numbered item).**

`old_string`: `1. **Проценты уверенности.** Рекомендация выражается в % уверенности на каждый вариант. Проценты — это ранжирование уверенности, не обязаны суммироваться в 100%. Близкие варианты — назвать близкими явно, не подгонять разброс.`

`new_string`: ``1. **Две оценки на вариант.** Каждый вариант несёт пару `X% / Y%`; смысл X и Y, сумма 100 % со строкой «Свой вариант / ни один» и порог автоматического выбора заданы в одном месте — глобальный CLAUDE.md → Questions and Numbers; здесь не повторяются. Близкие варианты — назвать близкими явно, не подгонять разброс.``

- [ ] **Step 4: line 33 (prefix only; the rest of the line stays).**

`old_string`: `3. **Источник к каждому проценту.** Каждый % сопровождай`
`new_string`: ``3. **Источник к каждой оценке.** Каждую пару `X% / Y%` сопровождай``

- [ ] **Step 5: template (lines 41-45).**

`old_string`:

```text
**N% Вариант A** — {почему основной выбор; источник: <best practice / docs / file:line>}
**M% Вариант B** — {в каких условиях лучше он; источник}
**K% Вариант C** — {edge case; источник}

{Если есть неуверенность — явный флаг: «предположительно X, требует проверки Y».}
```

`new_string`:

```text
**Вариант A — X% / Y%** — {почему основной выбор; источник: <best practice / docs / file:line>}
**Вариант B — X% / Y%** — {в каких условиях лучше он; источник}
**Вариант C — X% / Y%** — {edge case; источник}
**Свой вариант / ни один — N%**

{Автоматический выбор или вопрос пользователю — по порогу: глобальный CLAUDE.md → Questions and Numbers.}
{Если есть неуверенность — явный флаг: «предположительно A, требует проверки B».}
```

- [ ] **Step 6: reuse line (58).**

`old_string`: `Формат рекомендации — по `/best-recommend`: проценты + как джуну + источник к каждому % + честный флаг гипотезы при сомнении.`

`new_string`: ``Формат рекомендации — по `/best-recommend`: оценки `X% / Y%` (глобальный CLAUDE.md → Questions and Numbers) + как джуну + источник к каждой оценке + честный флаг гипотезы при сомнении.``

- [ ] **Step 7: the frontmatter still parses.**

```bash
python3 -c "import yaml; t=open('best-recommend/SKILL.md').read().split('---')[1]; print(yaml.safe_load(t)['name'])"
```

Expected: `best-recommend`.

---

## Task 9: `best-rank/SKILL.md` pointers

**Serves:** FR-5 (`best-rank`), Discovery Q2 (user decision: the two-score rule replaces "probability of acceptance"). Read the file first; Edit calls below.

- [ ] **Step 1: description (lines 6-8).**

`old_string`:

```text
missing best-practice options, then score every option 0–100% as its probability
  of acceptance and rank from highest to lowest. Thin wrapper over best-research —
  its specialization is taking a ready list and ranking by %.
```

`new_string`:

```text
missing best-practice options, then give every option the two scores X% / Y% of
  the global CLAUDE.md section "Questions and Numbers" and rank by X from highest
  to lowest. Thin wrapper over best-research — its specialization is taking a
  ready list and ranking by X.
```

- [ ] **Step 2: line 19.**

`old_string`: `проставлю каждому вероятность принятия 0–100% и отранжирую.`
`new_string`: ``проставлю каждому две оценки `X% / Y%` (глобальный CLAUDE.md → Questions and Numbers) и отранжирую по X.``

- [ ] **Step 3: line 29.**

`old_string`: `3. **Оцени и отранжируй по %** — каждому варианту (исходному + добавленному) процент вероятности принятия 0–100% (по формату `best-recommend`), сортировка по % убыв.`

`new_string`: ``3. **Оцени и отранжируй по X** — каждому варианту (исходному + добавленному) пара `X% / Y%` по формату `best-recommend`, плюс строка «Свой вариант / ни один — N%»; сортировка по X убыв.``

- [ ] **Step 4: lines 34 and 35.**

`old_string`: `проценты различимы;` → `new_string`: `значения X различимы;`
`old_string`: `по % убыв (от фаворита к аутсайдеру)` → `new_string`: `по X убыв (от фаворита к аутсайдеру)`

- [ ] **Step 5: output template (lines 48-54).**

`old_string`:

```text
### Рейтинг (от высшего % к низшему)
**1. {Название} — 85%** [исходный | добавлено]
{Описание}
✅ Усиливает: ... ❌ Нарушает/риски: ... 🚩 Red flags: ...
Почему 85%: {1–2 предложения, источник}

**2. {Название} — 60%** ...
```

`new_string`:

```text
### Рейтинг (от высшего X к низшему)
**1. {Название} — X% / Y%** [исходный | добавлено]
{Описание}
✅ Усиливает: ... ❌ Нарушает/риски: ... 🚩 Red flags: ...
Почему X% / Y%: {1–2 предложения, источник}

**2. {Название} — X% / Y%** ...
**Свой вариант / ни один — N%**
```

- [ ] **Step 6: line 65.**

`old_string`: `пересчитай % для гибрида.`
`new_string`: ``пересчитай `X% / Y%` для гибрида.``

Lines 69 and 72 stay (they remain true: «рейтинг по вероятности»).

- [ ] **Step 7: frontmatter parses.**

```bash
python3 -c "import yaml; t=open('best-rank/SKILL.md').read().split('---')[1]; print(yaml.safe_load(t)['name'])"
```

Expected: `best-rank`.

---

## Task 10: `best-research/SKILL.md` pointers

**Serves:** FR-5 (`best-research`). Read the file first.

- [ ] **Step 1: description (lines 7-8).**

`old_string`:

```text
realistic variants with pros/cons, and rank them with confidence % delivered
  via the best-recommend format.
```

`new_string`:

```text
realistic variants with pros/cons, and score them X% / Y% (global CLAUDE.md
  section "Questions and Numbers") delivered via the best-recommend format.
```

- [ ] **Step 2: line 20.**

`old_string`: `дать варианты + % → рекомендовать`
`new_string`: ``дать варианты + `X% / Y%` → рекомендовать``

- [ ] **Step 3: line 60 (the whole paragraph; the 85/50/20 scale is removed).**

`old_string`: `Подай по формату `/best-recommend`: **проценты уверенности + объяснение как джуну + источник к каждому % + честный флаг гипотезы при сомнении**. Шкала: 85–100% — сильный фаворит; 50–84% — рабочий с оговорками; 20–49% — слабый/ситуативный; 0–19% — почти нет (но оставить с причиной).`

`new_string`: ``Подай по формату `/best-recommend`: **оценки `X% / Y%` + объяснение как джуну + источник к каждой оценке + честный флаг гипотезы при сомнении**. Смысл оценок, строка «Свой вариант / ни один» и порог автоматического выбора — глобальный CLAUDE.md → Questions and Numbers; отдельной шкалы нет.``

- [ ] **Step 4: line 90.**

`old_string`: `{блок по формату /best-recommend: % + как джуну + источник + флаг гипотезы}`
`new_string`: `{блок по формату /best-recommend: X% / Y% + как джуну + источник + флаг гипотезы}`

- [ ] **Step 5: line 96.**

`old_string`: `Pros/Cons и проценты честные`
`new_string`: `Pros/Cons и оценки честные`

- [ ] **Step 6: line 108 (addition to the design: the sibling summary still said "по % убыв", which contradicts `best-rank` after Task 9).**

`old_string`: `этот движок + ранжирование по % убыв.`
`new_string`: `этот движок + ранжирование по X убыв.`

- [ ] **Step 7: frontmatter parses.**

```bash
python3 -c "import yaml; t=open('best-research/SKILL.md').read().split('---')[1]; print(yaml.safe_load(t)['name'])"
```

Expected: `best-research`.

---

## Task 11: `best-questions/SKILL.md` pointers

**Serves:** FR-5 (`best-questions`), FR-1 (question header in its block), FR-2a (auto-select exception; never at USER APPROVAL gates — stated in the section, not repeated here, NFR-4). Read the file first.

- [ ] **Step 1: description (lines 5-7).**

`old_string`:

```text
and STOP after each for the user's choice. Thin
  wrapper over best-research — its specialization is iterating a queue of
  questions with a hard stop after every one.
```

`new_string`:

```text
and STOP after each for the user's choice unless the auto-select threshold of the
  global CLAUDE.md section "Questions and Numbers" is met. Thin wrapper over
  best-research — its specialization is iterating a queue of questions with a
  hard stop after every one that is not auto-selected.
```

- [ ] **Step 2: line 18.**

`old_string`: `СТОП после каждого, жду ответ.`
`new_string`: `СТОП после каждого (кроме автоматического выбора по порогу — глобальный CLAUDE.md → Questions and Numbers), жду ответ.`

- [ ] **Step 3: line 27.**

`old_string`: ``рекомендация по формату `best-recommend` (проценты)``
`new_string`: ``рекомендация по формату `best-recommend` (оценки `X% / Y%`)``

- [ ] **Step 4: block (lines 35-38) — the question header precedes the question.**

`old_string`:

```text
---
## Вопрос i/N: {текст вопроса}

{разбор по формату best-research: Контекст → Что сейчас в коде → Что нужно решить → Варианты (pros/cons) → Рекомендация (% по формату best-recommend)}
```

`new_string`:

```text
---
{шапка вопроса — глобальный CLAUDE.md → Questions and Numbers}
## Вопрос i/N: {текст вопроса}

{разбор по формату best-research: Контекст → Что сейчас в коде → Что нужно решить → Варианты (pros/cons) → Рекомендация (`X% / Y%` по формату best-recommend, со строкой «Свой вариант / ни один»)}
```

- [ ] **Step 5: line 44.**

`old_string`: `**СТОП.** Жди ответ. НЕ переходи к следующему вопросу.`

`new_string`: `**СТОП** — жди ответ, НЕ переходи к следующему вопросу. Исключение — автоматический выбор по порогу (глобальный CLAUDE.md → Questions and Numbers): показать разбор, пометить выбранный вариант «[выбран автоматически]» и идти дальше.`

- [ ] **Step 6: add a handling item after line 47.**

`old_string`: `- **Номер** → записать решение, к следующему вопросу.`

`new_string`:

```text
- **Номер** → записать решение, к следующему вопросу.
- **Автоматический выбор** → записать как решение с пометкой «[выбран автоматически]», к следующему вопросу.
```

- [ ] **Step 7: summary line 59 (`X` was a free placeholder and would now read as a score).**

`old_string`: `→ Вариант X: {решение}`
`new_string`: `→ Вариант {k}: {решение} [автоматический выбор | выбор пользователя]`

- [ ] **Step 8: rule 2 (line 69).**

`old_string`: `2. **СТОП после каждого** — жди ответ.`
`new_string`: `2. **СТОП после каждого** — жди ответ; единственное исключение — автоматический выбор по порогу из глобального CLAUDE.md → Questions and Numbers.`

- [ ] **Step 9: line 74.**

`old_string`: ``формат варианта, % рекомендация``
`new_string`: ``формат варианта, оценки `X% / Y%```

(the matched phrase ends before the original `)`, which stays after the replacement.)

- [ ] **Step 10: frontmatter parses.**

```bash
python3 -c "import yaml; t=open('best-questions/SKILL.md').read().split('---')[1]; print(yaml.safe_load(t)['name'])"
```

Expected: `best-questions`.

---

## Task 12: FR-5 evidence, CHANGELOG line, commit C

**Serves:** FR-5 (evidence), FR-8 (second CHANGELOG line), NFR-4.

- [ ] **Step 1: the old definitions are gone.**

```bash
grep -rn 'вероятность принятия\|не обязаны суммироваться\|85–100%\|confidence %' best-recommend/SKILL.md best-rank/SKILL.md best-research/SKILL.md best-questions/SKILL.md
```

Expected: no output (grep exit 1).

- [ ] **Step 2: the pointers and templates are present.**

```bash
grep -c 'Questions and Numbers' best-recommend/SKILL.md best-rank/SKILL.md best-research/SKILL.md best-questions/SKILL.md
```

Expected: each file `>= 3`.

```bash
grep -n 'X% / Y%' best-recommend/SKILL.md best-rank/SKILL.md best-research/SKILL.md best-questions/SKILL.md
```

Expected: matches in all four files, including the output templates of `best-recommend` and `best-rank`.

- [ ] **Step 3: no skill repeats the meaning of X or Y, the 100 % rule or the threshold numbers (NFR-4).**

```bash
grep -n '20 процентных\|сумме дают 100\|не ниже 80\|без переделки' best-recommend/SKILL.md best-rank/SKILL.md best-research/SKILL.md best-questions/SKILL.md
```

Expected: no output.

- [ ] **Step 4: the repo-wide SSoT guard and the whole suite.**

```bash
python3 -m pytest claude-home/hooks/test_principles_ssot.py -q
```

Expected: all passed.

```bash
make test
```

Expected: sum `484`, no failures.

- [ ] **Step 5: CHANGELOG — second line, under `### Changed`** (Edit tool; read lines 6-14 first).

`old_string`:

```text
### Changed
- `claude-home/hooks/explanation-terms.py` no longer blocks the turn
```

`new_string`:

````text
### Changed
- `best-recommend`, `best-rank`, `best-research`, `best-questions` (bd `python-ai-skills-r1f.3`): drop their own meanings of the percentage (`need not sum to 100`, `probability of acceptance`, the 85/50/20 scale) and point to the `claude-home/CLAUDE.md` section `Questions and Numbers`; their output templates show `X% / Y%` with the «Свой вариант / ни один» line, and `best-questions` opens each question with the question header and may auto-select only by the section's threshold. The user profile item 3 and the auto-memory `best-questions-auto-select-80.md` become pointers to the same section (outside git)
- `claude-home/hooks/explanation-terms.py` no longer blocks the turn
````

- [ ] **Step 6: stage and commit C.**

```bash
git add best-recommend/SKILL.md best-rank/SKILL.md best-research/SKILL.md best-questions/SKILL.md CHANGELOG.md
```

```bash
git commit -m "docs(best-family): point option scoring to the Questions and Numbers section" -m "The four best-* skills drop their own percentage meanings and show X% / Y% in their templates. Refs: python-ai-skills-r1f.3"
```

Expected: pre-commit passes (`principles-ssot` runs on `*.md`); one commit with 5 files. Justification: skill text is level 4 (no executable change), independent of the hook; a revert of the skill pointers must not touch the hook.

---

## Task 13: Profile and auto-memory (outside git — nothing committed)

**Serves:** FR-9. Edit/Write tools only (`~/.claude/projects` is sandbox-protected; the profile is outside the repo but within the allowed `~/ai-steward/**/*.md` area). If the harness refuses an Edit, stop and hand the exact text below to the user instead of working around it.

- [ ] **Step 1: profile — item 3.** Read `/home/bgs/ai-steward/Gena_Beeline_Local/CLAUDE.md` lines 18-28, then Edit.

`old_string`:

```text
3. В `/best-questions` варианты с уверенностью выше 80% выбираются
   автоматически; остановка только на 80% и ниже.
```

`new_string`:

```text
3. Автоматический выбор варианта в `/best-questions` и в любой другой рекомендации — только по порогу из глобального CLAUDE.md → Questions and Numbers; своих порогов здесь нет.
```

- [ ] **Step 2: auto-memory file — replace with a pointer.** Read `/home/bgs/.claude/projects/-home-bgs-ai-steward-Gena-Beeline-Local-python-ai-skills/memory/best-questions-auto-select-80.md`, then Write the whole file (file name and frontmatter keys are kept; `originSessionId` kept; `description` and `modified` and body replaced):

```text
---
name: best-questions-auto-select-80
description: "Superseded: option auto-select is the X% / Y% rule of the global CLAUDE.md section 'Questions and Numbers'; this memory only points there."
metadata:
  node_type: memory
  type: feedback
  originSessionId: c4d81a38-d881-46cc-96f3-8ea3ff2537c8
  modified: 2026-10-15T00:00:00.000Z
---

Superseded 2026-10-15 (bd python-ai-skills-r1f.3): the ">80 % confidence" threshold is replaced by the two-score rule written X% / Y% in claude-home/CLAUDE.md → "Questions and Numbers" (loaded at session start and re-sent before every answer by claude-home/hooks/question-memo-inject.sh). Do not apply the old threshold; the profile item 3 points to the same section.
```

- [ ] **Step 3: `MEMORY.md` index line 6** (Edit; read the file first).

`old_string`:

```text
- [best-questions auto-select >80%](best-questions-auto-select-80.md) — in /best-questions loops auto-pick variants with >80% confidence, stop only on ≤80%.
```

`new_string`:

```text
- [best-questions auto-select >80%](best-questions-auto-select-80.md) — superseded: option auto-select is the X% / Y% rule in global CLAUDE.md → Questions and Numbers; the file is a pointer only.
```

- [ ] **Step 4: verify by reading back (no shell writes involved).**

```bash
grep -n 'Questions and Numbers' /home/bgs/ai-steward/Gena_Beeline_Local/CLAUDE.md /home/bgs/.claude/projects/-home-bgs-ai-steward-Gena-Beeline-Local-python-ai-skills/memory/MEMORY.md /home/bgs/.claude/projects/-home-bgs-ai-steward-Gena-Beeline-Local-python-ai-skills/memory/best-questions-auto-select-80.md
```

Expected: one match in each of the three files.

```bash
grep -rn 'выше 80%\|>80% confidence' /home/bgs/ai-steward/Gena_Beeline_Local/CLAUDE.md
```

Expected: no output (the profile no longer defines an own threshold).

---

## Task 14: Live check (user-run) and bd notes

**Serves:** Discovery risks 5 and 10 (hook fires for typed slash commands; compliance observed), final acceptance. The agent cannot do this step: a fresh `claude` session is the user's action.

- [ ] **Step 1 (user): find the debug flag** (the plan does not assume its form).

```bash
claude --help
```

Expected: the line describing `--debug` (and, if present, a debug-file option).

- [ ] **Step 2 (user): start a fresh session from any project directory** (the hook is global): `claude --debug`. Type `/best-questions` with one question that has two or three options, e.g. `/best-questions Какой цвет у кнопки: красный или синий?`.

Expected, all three:
1. The first question starts with the three lines `План:`, `Сейчас:`, `Цель вопроса:` and only then the question (FR-1).
2. Each option carries `X% / Y%`; the list ends with «Свой вариант / ни один — N%»; X values plus that line sum to 100 % (FR-2a).
3. The latest file in `~/.claude/debug/` contains a `UserPromptSubmit` hook line mentioning `question-memo-inject.sh`; check with `grep -n 'question-memo-inject' ~/.claude/debug/*` (if the debug log lives elsewhere, the help of Step 1 names the place). This confirms the hook ran for a typed slash command (risk 5).

- [ ] **Step 3 (user): negative control.** In the same session answer with a number, then ask any plain question; expect the memo again before the answer (the debug log shows one hook run per prompt, three handlers on the event).

- [ ] **Step 4 (agent, after the user reports): record the evidence in bd notes** with the flag of Task 1 Step 3.

```bash
bd update python-ai-skills-r1f.3 --notes "Live check 2026-10-15: header present on first question: <yes|no>; X% / Y% with 'Свой вариант' line: <yes|no>; debug log shows question-memo-inject.sh on /best-questions: <yes|no>."
```

Expected: saved. If any answer is `no`, do not close the bead: file a bead for the cause (`bd create`), keep `python-ai-skills-r1f.3` open. Closing the bead (`bd close`) belongs to the Finish step of `do-feature`, not to this plan.

---

## Deviations from the design

1. **Grammar of the corrected coined words.** The design text «порог автоматический выбора» (appendix, `best-recommend` l.29, `best-research` l.60) is ungrammatical after the orchestrator's word replacement; the plan uses «порог автоматического выбора». The Section text itself is verbatim.
2. **One extra line** in `best-research/SKILL.md` (l.108, «по % убыв» → «по X убыв»): after `best-rank` ranks by X the engine's sibling summary would contradict it. Not in the design's line list.
3. **CHANGELOG split in two bullets / two commits** (design 2.9 drafted one): the section and hook bullet go in commit B, the skill-pointer bullet in commit C, so each commit's changelog line describes only what that commit contains. `<N> tests` is fixed to 11.
4. **Three commits instead of two:** a leading `docs` commit A for the approved spec and plan (they are untracked records; mixing them into code commits would break atomicity).
5. **`chmod 755` of the hook needs the sandbox disabled** (design note 3.1 covered Edit/Write but not the mode bit; `Write` creates mode 644 and settings run the hook by path).
6. **Task-numbering of the Codex check before the CHANGELOG** so the CHANGELOG sentence about Codex is written from the observed result (Task 6 branch).

## Self-review

**1. Every FR has a task.**
- FR-1 (question header) → Task 3 (section), Task 11 step 4 (header in the `best-questions` block), Task 14 step 2 (live).
- FR-2 (numbers rule, scope) → Task 3.
- FR-2a (two scores, 100 %, 20-point gap, Y at least 80 %, no auto-select at USER APPROVAL) → Task 3; skills in Tasks 8-11; Task 14 step 2 item 2.
- FR-3 (hook) → Tasks 2 (tests) and 4 (code).
- FR-4 (template handler, timeout 3) → Task 5 steps 2-6.
- FR-5 (four skills) → Tasks 8-11, evidence Task 12 steps 1-3.
- FR-6 (pytest file, Makefile list) → Task 2, Task 5 step 1.
- FR-7 (no Stop hook) → no task creates one; Task 3 rationale paragraph records the rejection. Checked: no Stop wiring is touched by Task 5 step 2 (only `UserPromptSubmit`).
- FR-8 (CHANGELOG) → Task 7 step 1, Task 12 step 5.
- FR-9 (profile, auto-memory) → Task 13.
- Scope items: appendix paragraph → Task 3 step 3; Codex check → Task 6; live check → Task 14.

**2. Every NFR has a verification step.**
- NFR-1 (size) → guard test (Task 2, GREEN in Task 3) + `wc -m` (Task 3 step 5).
- NFR-2 (runtime) → Task 4 step 4 (`time`, below 3 s).
- NFR-3 (advisory, exit 0) → tests 1, 3-6 (Task 2) + Task 4 step 4 exit code.
- NFR-4 (no copy of the rule text) → Task 7 step 3 (grep: one file), Task 12 step 3 (skills carry no meanings), fixture uses a marker.
- NFR-5 (project-neutral wording) → Task 7 step 4.
- NFR-6 (Codex path) → Task 5 step 6 (`ls -l ~/.codex/AGENTS.md`) and Task 6.

**3. No placeholders.** Every code block is complete (test file, hook, section, appendix paragraph, template entry, all skill replacements). The only fill-ins are observed values inside bd note texts (Tasks 6, 14), which cannot exist before the check runs and are marked by `<...>` as results.

**4. Reverse traceability (every symbol, parameter, config key → FR/NFR).**
- `QUESTION_MEMO_FILE` → FR-3 (env override), FR-6 (tests inject a fixture, precedent `TASK_LEVELS_FILE`).
- `HEADING`, `MAX_MEMO_CHARS`, `MAX_MEMO_LINES` → NFR-1 and Discovery risk 1; `REAL_CLAUDE_MD` → same guard.
- `cut_section` (test helper) → the guard's size check (NFR-1); it is test-only, 7 lines.
- `jq -e 'type == "object"'` → FR-3 ("stdin is malformed → nothing printed").
- `[ -f ] && [ -r ]` → FR-3 (file missing); the check is at a system boundary (filesystem).
- `awk` cut + `[ -n "$SECTION" ]` → FR-3 (section missing).
- framing line with `\($f)` → FR-3 ("framing line"); tests assert the path is in the context.
- template entry, `timeout: 3` → FR-4. Makefile line → FR-6. CHANGELOG → FR-8.

**5. Excess-code check (`~/.claude/skills/_code-quality/principles.md`).**
- Deletion test: removing the `jq -e` line breaks `test_malformed_input_degrades_to_silence`; removing the `-r` check, the directory test (`-f` covers the directory, `-r` covers an unreadable file — the same line as the pattern hook, one boundary check); removing `cut_section` breaks the guard.
- Trace test: all symbols traced above; no parameter, flag or option with a single value in use beyond the env override, which the tests use.
- Boundary test: validation only at stdin and the filesystem. No opt-out variable (Discovery scope OUT), no helper library (design 1.2 rejected; the duplicated fact is one `awk` line; trigger to extract is a third caller, bd `python-ai-skills-du5`), no Python port.
- Precedence: KISS and YAGNI applied; the 9th test of the design (stderr on the real file) is not added, as designed.

**6. Task order respects dependencies.** Tests (2) before section (3) before hook (4); the guard test becomes GREEN only after the section exists (3); the hook exists before the template wiring and the installer test (5); the installer re-render (5) before the installed-layout check; the Codex check (6) needs the section in the repo file (3); the CHANGELOG (7) is written after the Codex result (6); skills (8-11) and profile/memory (13) point to a section that exists (3) and is already committed (7); the live check (14) needs the re-rendered settings (5).

**7. Machine constraints encoded.** Edit/Write for protected paths (constraint 1; Tasks 2, 3, 4, 13); standalone git with explicit `git add` lists and the phantom-path warning (constraint 2; Tasks 1, 7, 12); `$TMPDIR` (Task 6); sandbox-disabled steps stated explicitly: `chmod` (Task 4 step 2), `make install-symlinks` (Task 5 step 5), `codex debug prompt-input` (Task 6 step 2); the quality gate with the 473 → 484 count and the untouched F401 (Tasks 1, 4, 7, 12); out-of-git edits (Task 13); user-run live check (Task 14).
