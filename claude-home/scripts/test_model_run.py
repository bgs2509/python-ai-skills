"""Tests for model-run.sh — the deterministic model selector.

Every test uses a synthetic registry whose models run `cmd_template` shell
snippets, so no real model, network, or quota is touched.
"""

import json
import os
import subprocess
import time
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent / "model-run.sh"


def registry(models, roles, penalty_seconds=3600):
    return {
        "version": 1,
        "roles": roles,
        "models": models,
        "policy": {"penalty_seconds": penalty_seconds},
    }


@pytest.fixture
def env(tmp_path):
    """Isolated registry/journal/penalties trio plus a task file."""
    task = tmp_path / "task.txt"
    task.write_text("do the thing\n")
    return {
        "registry": tmp_path / "registry.json",
        "journal": tmp_path / "journal.jsonl",
        "penalties": tmp_path / "penalties.json",
        "task": task,
        "out": tmp_path / "out.md",
    }


def run(env, *args):
    proc_env = dict(os.environ)
    proc_env.update(
        MODEL_REGISTRY=str(env["registry"]),
        MODEL_JOURNAL=str(env["journal"]),
        MODEL_PENALTIES=str(env["penalties"]),
        MODEL_RUN_SESSION="test",
    )
    return subprocess.run(
        ["bash", str(SCRIPT), "--task", str(env["task"]), *args],
        capture_output=True,
        text=True,
        env=proc_env,
        timeout=60,
    )


def write_registry(env, data):
    env["registry"].write_text(json.dumps(data))


def journal_lines(env):
    if not env["journal"].exists():
        return []
    return [json.loads(line) for line in env["journal"].read_text().splitlines() if line.strip()]


def model(cmd, **kw):
    spec = {"pool": "test", "runner": "custom", "cmd_template": cmd, "timeout_seconds": 10}
    spec.update(kw)
    return spec


def test_first_healthy_model_wins_and_is_journalled(env):
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo ANSWER"), "spare": model("echo NEVER")},
            {"executor": {"models": ["good", "spare"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]))
    assert result.returncode == 0, result.stderr
    assert env["out"].read_text().strip() == "ANSWER"

    lines = journal_lines(env)
    assert len(lines) == 1, "only the attempt that ran should be journalled"
    assert lines[0]["model"] == "good"
    assert lines[0]["outcome"] == "ok"
    assert lines[0]["role"] == "executor"
    assert lines[0]["ctx_chars"] > 0


def test_unavailable_model_is_penalised_and_next_one_answers(env):
    write_registry(
        env,
        registry(
            {
                "broken": model("cat >/dev/null; echo 'Error: rate limit exceeded' >&2; exit 1"),
                "spare": model("cat >/dev/null; echo RECOVERED"),
            },
            {"executor": {"models": ["broken", "spare"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]))
    assert result.returncode == 0
    assert env["out"].read_text().strip() == "RECOVERED"

    outcomes = [line["outcome"] for line in journal_lines(env)]
    assert outcomes == ["unavailable", "ok"]

    penalties = json.loads(env["penalties"].read_text())
    assert "broken" in penalties
    assert penalties["broken"]["reason"] == "unavailable"
    assert penalties["broken"]["until"] > time.time()
    assert "spare" not in penalties


def test_penalised_model_is_skipped_without_running(env):
    write_registry(
        env,
        registry(
            {
                "punished": model("cat >/dev/null; echo SHOULD_NOT_RUN"),
                "spare": model("cat >/dev/null; echo FROM_SPARE"),
            },
            {"executor": {"models": ["punished", "spare"]}},
        ),
    )
    env["penalties"].write_text(
        json.dumps({"punished": {"until": int(time.time()) + 3600, "reason": "unavailable"}})
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]))
    assert result.returncode == 0
    assert env["out"].read_text().strip() == "FROM_SPARE"
    assert [line["model"] for line in journal_lines(env)] == ["spare"]


def test_expired_penalty_lets_the_model_run_again(env):
    write_registry(
        env,
        registry(
            {"revived": model("cat >/dev/null; echo BACK")},
            {"executor": {"models": ["revived"]}},
        ),
    )
    env["penalties"].write_text(
        json.dumps({"revived": {"until": int(time.time()) - 5, "reason": "unavailable"}})
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]))
    assert result.returncode == 0
    assert env["out"].read_text().strip() == "BACK"


def test_context_overflow_skips_ahead_without_penalty(env):
    """A task larger than the window must not punish the model — it is not broken."""
    write_registry(
        env,
        registry(
            {
                "tiny": model("cat >/dev/null; echo NEVER", context_tokens=1),
                "roomy": model("cat >/dev/null; echo FITS", context_tokens=1000000),
            },
            {"executor": {"models": ["tiny", "roomy"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]))
    assert result.returncode == 0
    assert env["out"].read_text().strip() == "FITS"

    lines = journal_lines(env)
    assert lines[0]["model"] == "tiny"
    assert lines[0]["outcome"] == "context_overflow"
    assert json.loads(env["penalties"].read_text()) == {}, "overflow must not penalise"


def test_reported_overflow_is_detected_from_output(env):
    write_registry(
        env,
        registry(
            {
                "complains": model("cat >/dev/null; echo 'Prompt is too long' >&2; exit 1"),
                "spare": model("cat >/dev/null; echo OK2"),
            },
            {"executor": {"models": ["complains", "spare"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]))
    assert result.returncode == 0
    assert journal_lines(env)[0]["outcome"] == "context_overflow"
    assert json.loads(env["penalties"].read_text()) == {}


def test_timeout_is_not_penalised_by_default(env):
    """Slowness is a passport property (qwen takes 190 s legitimately), not a fault."""
    write_registry(
        env,
        registry(
            {
                "slow": model("cat >/dev/null; sleep 5", timeout_seconds=1),
                "spare": model("cat >/dev/null; echo QUICK"),
            },
            {"executor": {"models": ["slow", "spare"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]))
    assert result.returncode == 0
    assert env["out"].read_text().strip() == "QUICK"
    assert journal_lines(env)[0]["outcome"] == "timeout"
    assert json.loads(env["penalties"].read_text()) == {}


def test_timeout_penalty_is_opt_in_per_model(env):
    write_registry(
        env,
        registry(
            {
                "slow": model(
                    "cat >/dev/null; sleep 5", timeout_seconds=1, penalize_on_timeout=True
                ),
                "spare": model("cat >/dev/null; echo QUICK"),
            },
            {"executor": {"models": ["slow", "spare"]}},
        ),
    )
    run(env, "--role", "executor", "--out", str(env["out"]))
    penalties = json.loads(env["penalties"].read_text())
    assert penalties["slow"]["reason"] == "timeout"


def test_exhausted_role_exits_nonzero(env):
    write_registry(
        env,
        registry(
            {"only": model("cat >/dev/null; echo 'quota exceeded' >&2; exit 1")},
            {"executor": {"models": ["only"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]))
    assert result.returncode == 1
    assert "exhausted" in result.stderr


def test_dry_run_touches_nothing(env):
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo SHOULD_NOT_RUN")},
            {"executor": {"models": ["good"]}},
        ),
    )
    result = run(env, "--role", "executor", "--dry-run")
    assert result.returncode == 0
    assert "good" in result.stdout
    assert not env["journal"].exists() or journal_lines(env) == []
    assert not env["out"].exists()


def test_unknown_role_is_a_usage_error(env):
    write_registry(env, registry({}, {"executor": {"models": []}}))
    result = run(env, "--role", "nosuchrole")
    assert result.returncode == 2
    assert "no models" in result.stderr


def test_shipped_registry_is_valid_and_self_consistent():
    """Every model named by a role must exist in .models."""
    shipped = json.loads((SCRIPT.resolve().parent.parent / "model-registry.json").read_text())
    known = set(shipped["models"])
    for role, body in shipped["roles"].items():
        for name in body["models"]:
            assert name in known, f"role {role} references unknown model {name}"
    for tier, name in shipped["tiers"].items():
        if tier.startswith("_"):  # documentation key, not a tier
            continue
        assert name in known, f"tier {tier} references unknown model {name}"
