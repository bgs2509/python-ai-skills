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
    # The bulk-work nudge, not the model hint that any model-less launch gets.
    return "looks bulk/mechanical" in payload["hookSpecificOutput"]["additionalContext"]


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


# --- model hint (bd python-ai-skills-8of.4) -------------------------------------------

REGISTRY = {
    "tiers": {"top": "big-one", "mid": "middle-one", "cheap": "small-one"},
    "models": {
        "big-one": {"model_arg": "alias-top"},
        "middle-one": {"model_arg": "alias-mid"},
        "small-one": {"model_arg": "alias-cheap"},
    },
    "roles": {"reviewer": {"models": []}, "researcher": {"models": []}},
    "agent_work_types": {"entries": [
        {"work": "architecture", "tier": "top"},
        {"work": "writing code", "tier": "mid"},
        {"work": "read-only exploration", "tier": "cheap"},
        {"work": "code review", "role": "reviewer"},
    ]},
}


def launch(description="ask a question", subagent_type="general-purpose", model=None):
    ti = {"description": description, "prompt": "x", "subagent_type": subagent_type}
    if model:
        ti["model"] = model
    return {"tool_name": "Agent", "tool_input": ti}


def context(result):
    assert result.returncode == 0
    if not result.stdout.strip():
        return ""
    return json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


@pytest.fixture
def registry(tmp_path):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(REGISTRY))
    return {"MODEL_REGISTRY": str(path)}


def test_launch_without_model_gets_mapping_from_registry(registry):
    text = context(run(launch(), env_extra=registry))
    assert "architecture" in text and "`alias-top`" in text
    assert "read-only exploration" in text and "`alias-cheap`" in text
    assert "code review" in text and "--role reviewer" in text
    assert "looks bulk/mechanical" not in text


def test_launch_with_model_gets_no_model_hint(registry):
    assert context(run(launch(model="alias-mid"), env_extra=registry)) == ""


def test_fork_is_left_alone(registry):
    assert context(run(launch(subagent_type="fork"), env_extra=registry)) == ""


def test_explore_is_told_it_inherits_the_session_model(registry):
    text = context(run(launch(subagent_type="Explore"), env_extra=registry))
    assert "Explore" in text and "session model" in text


def test_broken_registry_still_gives_generic_hint(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    text = context(run(launch(), env_extra={"MODEL_REGISTRY": str(bad)}))
    assert "`model`" in text
    assert "alias-top" not in text


def test_bulk_and_model_hints_combine(registry):
    text = context(run(launch(description="inventory all modules"), env_extra=registry))
    assert "looks bulk/mechanical" in text
    assert "`alias-cheap`" in text


def test_shipped_registry_renders_real_aliases():
    shipped = Path(__file__).resolve().parent.parent / "model-registry.json"
    text = context(run(launch(), env_extra={"MODEL_REGISTRY": str(shipped)}))
    data = json.loads(shipped.read_text())
    cheap_alias = data["models"][data["tiers"]["cheap"]]["model_arg"]
    assert f"`{cheap_alias}`" in text
