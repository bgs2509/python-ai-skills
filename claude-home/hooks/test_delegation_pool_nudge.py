"""Tests for delegation-pool-nudge.sh — the PreToolUse nudge on Task dispatch.

The hook is advisory: it must never block a Task, never crash on odd input,
and must stay quiet on judgement work (where the strong pool is the right
answer and a nudge would be noise).
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent / "delegation-pool-nudge.sh"


def run(payload, env_extra=None):
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps(payload) if not isinstance(payload, str) else payload,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def task(description="", prompt=""):
    return {"tool_name": "Task", "tool_input": {"description": description, "prompt": prompt}}


def nudged(result):
    assert result.returncode == 0, "the hook must never fail a Task"
    if not result.stdout.strip():
        return False
    payload = json.loads(result.stdout)
    assert payload["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    return "model-run.sh" in payload["hookSpecificOutput"]["additionalContext"]


@pytest.mark.parametrize(
    "description",
    [
        "grep the whole repo for deprecated imports",
        "Inventory all skills that mention routing",
        "read all files under docs/ and summarize",
        "bulk rename the old helper across the codebase",
        "draft tests from the finished spec",
        "sweep the logs for error patterns",
    ],
)
def test_bulk_work_is_nudged(description):
    assert nudged(run(task(description=description)))


@pytest.mark.parametrize(
    "description",
    [
        "design the module boundaries for the new service",
        "review this diff for security problems",
        "decide between the two storage approaches",
        "debug the root cause of the flaky test",
    ],
)
def test_judgement_work_is_left_alone(description):
    """Strong-pool work: a nudge here would be noise, not saving."""
    assert not nudged(run(task(description=description)))


def test_bulk_wording_inside_judgement_work_stays_silent():
    """Judgement wins over bulk — 'review all modules' is still review."""
    assert not nudged(run(task(description="review all modules and decide the architecture")))


def test_unrelated_task_is_not_nudged():
    assert not nudged(run(task(description="ask the user which option they prefer")))


def test_prompt_field_is_considered_too():
    assert nudged(run(task(description="helper", prompt="enumerate every TODO in the tree")))


def test_empty_input_is_silent():
    assert not nudged(run(task()))


def test_malformed_stdin_does_not_crash():
    result = run("{not json at all")
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_missing_tool_input_does_not_crash():
    result = run({"tool_name": "Task"})
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_opt_out_switch_silences_the_hook():
    result = run(task(description="grep everything"), env_extra={"DELEGATION_NUDGE": "off"})
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_nudge_names_the_runner_and_the_registry():
    payload = json.loads(run(task(description="inventory all modules")).stdout)
    text = payload["hookSpecificOutput"]["additionalContext"]
    assert "model-run.sh" in text
    assert "model-registry.json" in text
    assert "--role executor" in text
