"""Tests for principles-inject.sh — PreToolUse(Skill) hook that delivers the code principles.

The principles live in one file (_code-quality/principles.md). Skills that write,
plan or review code must see it, including superpowers skills this repo cannot
edit. The hook injects the file as additionalContext for listed skills only, and
never fails a call: an unlisted skill, a missing file or odd input means silence.
"""

import json
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent / "principles-inject.sh"
TEXT = "1. **KISS** - sample principle text\n"


@pytest.fixture
def principles(tmp_path):
    path = tmp_path / "principles.md"
    path.write_text(TEXT)
    return path


def run(payload, principles_file):
    return subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps(payload) if not isinstance(payload, str) else payload,
        capture_output=True,
        text=True,
        timeout=30,
        env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "PRINCIPLES_FILE": str(principles_file)},
    )


def skill(name):
    return {"tool_name": "Skill", "tool_input": {"skill": name}}


@pytest.mark.parametrize(
    "name",
    ["do-feature", "grace-execute", "grace-reviewer", "superpowers:writing-plans", "superpowers:brainstorming"],
)
def test_listed_skill_gets_principles(name, principles):
    result = run(skill(name), principles)
    assert result.returncode == 0
    out = json.loads(result.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse"
    assert TEXT in out["additionalContext"]
    assert "principles.md" in out["additionalContext"].splitlines()[0]
    assert "permissionDecision" not in out


@pytest.mark.parametrize("name", ["git-commit", "git-finish", "writing-plans-notes", "superpowers:do-feature", ""])
def test_unlisted_skill_is_silent(name, principles):
    result = run(skill(name), principles)
    assert result.returncode == 0
    assert result.stdout == ""


def test_missing_file_is_silent(tmp_path):
    result = run(skill("do-feature"), tmp_path / "absent.md")
    assert result.returncode == 0
    assert result.stdout == ""


@pytest.mark.parametrize("payload", ["", "not json", {"tool_input": {}}, {"other": 1}])
def test_malformed_input_degrades_to_silence(payload, principles):
    result = run(payload, principles)
    assert result.returncode == 0
    assert result.stdout == ""
