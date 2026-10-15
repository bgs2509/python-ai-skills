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
