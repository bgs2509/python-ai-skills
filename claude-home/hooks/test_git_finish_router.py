"""Tests for git-finish-router.sh — the UserPromptSubmit router for "git finish".

On 2026-10-13 a session asked to "выполнить git finish" invoked
superpowers:finishing-a-development-branch instead of the repo's git-finish skill.
The hook must name git-finish whenever the prompt asks for it in free text, stay
silent otherwise, and never fail a prompt.
"""

import json
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent / "git-finish-router.sh"


def run(payload):
    return subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps(payload) if not isinstance(payload, str) else payload,
        capture_output=True,
        text=True,
        timeout=30,
    )


def routed(result):
    assert result.returncode == 0, "the hook must never fail a prompt"
    if not result.stdout.strip():
        return False
    payload = json.loads(result.stdout)
    assert payload["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert "superpowers:finishing-a-development-branch" in context
    return "git-finish" in context


@pytest.mark.parametrize(
    "prompt",
    [
        "обновить документацию ... и потом выполнить git finish.",
        "Git Finish please",
        "сделай git-finish",
        "гит финиш",
        "давай Гит-финиш и всё",
    ],
)
def test_free_text_request_is_routed(prompt):
    assert routed(run({"prompt": prompt}))


@pytest.mark.parametrize(
    "prompt",
    [
        "/git-finish",
        "/git-finish --no-push",
        "закоммить изменения",
        "finish the refactoring of git helpers",
        "",
    ],
)
def test_other_prompts_stay_silent(prompt):
    assert not routed(run({"prompt": prompt}))


@pytest.mark.parametrize("payload", ["", "not json", {"other": 1}])
def test_malformed_input_degrades_to_silence(payload):
    assert not routed(run(payload))
