"""Tests for skill-finish-guard.sh — PreToolUse(Skill) guard for the superpowers finish skill.

git-finish-router.sh only sees user prompts. superpowers subagent-driven-development
and executing-plans chain into superpowers:finishing-a-development-branch by
themselves, which offers a Pull Request and never pushes after a local merge. The
guard must deny exactly that skill with a reason naming git-finish, stay silent for
every other skill, and never fail a call on odd input.
"""

import json
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent / "skill-finish-guard.sh"


def run(payload):
    return subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps(payload) if not isinstance(payload, str) else payload,
        capture_output=True,
        text=True,
        timeout=30,
    )


def skill(name):
    return {"tool_name": "Skill", "tool_input": {"skill": name}}


def test_superpowers_finish_is_denied_with_redirect():
    result = run(skill("superpowers:finishing-a-development-branch"))
    assert result.returncode == 0
    out = json.loads(result.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse"
    assert out["permissionDecision"] == "deny"
    assert "git-finish" in out["permissionDecisionReason"]


@pytest.mark.parametrize(
    "name",
    [
        "git-finish",
        "superpowers:brainstorming",
        "superpowers:executing-plans",
        "finishing-a-development-branch-notes",
        "",
    ],
)
def test_other_skills_pass_silently(name):
    result = run(skill(name))
    assert result.returncode == 0
    assert result.stdout == ""


@pytest.mark.parametrize("payload", ["", "not json", {"tool_input": {}}, {"other": 1}])
def test_malformed_input_degrades_to_silence(payload):
    result = run(payload)
    assert result.returncode == 0
    assert result.stdout == ""
