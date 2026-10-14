"""Tests for task-level-inject.sh — PreToolUse(Skill) hook that delivers the task levels.

The task-level table lives in one place: the "Dev-project workflow" section of the
global CLAUDE.md. CLAUDE.md is read only at session start, so a running session
that predates the table would send every change through full do-feature. The hook
cuts that section at run time and injects it when do-feature is invoked; any other
skill, a missing file or odd input means silence.
"""

import json
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent / "task-level-inject.sh"
SECTION = "## Dev-project workflow (dev-projects only)\n\n**Rule (task levels):** sample level table\n"
DOC = "# Global\n\n## Project Classification\n\nbefore\n\n" + SECTION + "\n## Skill Hierarchy\n\nafter\n"


@pytest.fixture
def claude_md(tmp_path):
    path = tmp_path / "CLAUDE.md"
    path.write_text(DOC)
    return path


def run(payload, levels_file):
    return subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps(payload) if not isinstance(payload, str) else payload,
        capture_output=True,
        text=True,
        timeout=30,
        env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "TASK_LEVELS_FILE": str(levels_file)},
    )


def skill(name):
    return {"tool_name": "Skill", "tool_input": {"skill": name}}


def test_do_feature_gets_the_level_section(claude_md):
    result = run(skill("do-feature"), claude_md)
    assert result.returncode == 0
    out = json.loads(result.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse"
    assert "sample level table" in out["additionalContext"]
    assert "permissionDecision" not in out


def test_only_the_level_section_is_cut(claude_md):
    context = json.loads(run(skill("do-feature"), claude_md).stdout)["hookSpecificOutput"]["additionalContext"]
    assert "before" not in context
    assert "after" not in context
    assert "## Skill Hierarchy" not in context


@pytest.mark.parametrize("name", ["git-commit", "grace-fix", "superpowers:do-feature", "do-feature-clean", ""])
def test_other_skill_is_silent(name, claude_md):
    result = run(skill(name), claude_md)
    assert result.returncode == 0
    assert result.stdout == ""


def test_missing_file_is_silent(tmp_path):
    result = run(skill("do-feature"), tmp_path / "absent.md")
    assert result.returncode == 0
    assert result.stdout == ""


def test_file_without_the_section_is_silent(tmp_path):
    path = tmp_path / "CLAUDE.md"
    path.write_text("# Global\n\n## Skill Hierarchy\n\nafter\n")
    result = run(skill("do-feature"), path)
    assert result.returncode == 0
    assert result.stdout == ""


@pytest.mark.parametrize("payload", ["", "not json", {"tool_input": {}}, {"other": 1}])
def test_malformed_input_degrades_to_silence(payload, claude_md):
    result = run(payload, claude_md)
    assert result.returncode == 0
    assert result.stdout == ""
