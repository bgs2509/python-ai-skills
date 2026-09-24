"""Tests for model-run.sh — the deterministic model selector.

Every test uses a synthetic registry whose models run `cmd_template` shell
snippets, so no real model, network, or quota is touched.
"""

import json
import os
import signal
import subprocess
import time
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent / "model-run.sh"


def registry(models, roles, penalty_seconds=3600, policy=None):
    base_policy = {"penalty_seconds": penalty_seconds}
    if policy:
        base_policy.update(policy)
    return {
        "version": 1,
        "roles": roles,
        "models": models,
        "policy": base_policy,
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
    # A developer's exported MODEL_OUTPUTS must not redirect test outputs.
    proc_env.pop("MODEL_OUTPUTS", None)
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


def outputs_dir(env):
    """Default kept-outputs location: next to the journal (no MODEL_OUTPUTS override)."""
    return env["journal"].parent / "model-outputs"


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


def test_exit_zero_answer_mentioning_quota_is_ok(env):
    """Regression: exit 0 must not be relabelled by quota/429 words in the answer.

    Evidence: ~/.claude/model-journal.jsonl, 2026-09-22 19:44-19:48, session b2b75c8a —
    five consecutive exit-0 answers were mislabelled unavailable and their models penalised.
    """
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo 'quota 429 rate limit'")},
            {"executor": {"models": ["good"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]))
    assert result.returncode == 0, result.stderr
    assert env["out"].read_text().strip() == "quota 429 rate limit"
    assert journal_lines(env)[0]["outcome"] == "ok"
    assert json.loads(env["penalties"].read_text()) == {}


def test_exit_zero_answer_mentioning_context_window_is_ok(env):
    """Regression: exit 0 must not be relabelled by overflow words in the answer."""
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo 'maximum context'")},
            {"executor": {"models": ["good"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]))
    assert result.returncode == 0, result.stderr
    assert env["out"].read_text().strip() == "maximum context"
    assert journal_lines(env)[0]["outcome"] == "ok"


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
    assert not outputs_dir(env).exists(), "a dry run must not create the outputs directory"


def test_old_outputs_are_pruned_young_and_foreign_files_kept(env):
    """Retention runs on every real (non-dry) invocation, days from the registry."""
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo ANSWER")},
            {"executor": {"models": ["good"]}},
            policy={"output_retention_days": 14},
        ),
    )
    outputs = outputs_dir(env)
    outputs.mkdir()
    old_out = outputs / "old.out"
    young_out = outputs / "young.out"
    old_txt = outputs / "old.txt"
    for f in (old_out, young_out, old_txt):
        f.write_text("x")
    old_time = time.time() - 15 * 86400
    young_time = time.time() - 13 * 86400
    os.utime(old_out, (old_time, old_time))
    os.utime(old_txt, (old_time, old_time))
    os.utime(young_out, (young_time, young_time))

    run(env, "--role", "executor", "--out", str(env["out"]))

    assert not old_out.exists(), "a 15-day .out file must be pruned"
    assert young_out.exists(), "a 13-day .out file must survive 14-day retention"
    assert old_txt.exists(), "pruning must only touch *.out files"


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
    for name, spec in shipped["models"].items():
        assert isinstance(spec.get("capabilities", {}).get("web_search"), bool), (
            f"model {name} is missing capabilities.web_search"
        )
    assert shipped["models"]["qwen38"]["capabilities"]["web_search"] is False
    # penalize_on is read by model-run.sh; its complement is not stored (one source).
    assert shipped["policy"]["penalize_on"] == ["unavailable"]
    assert "no_penalty_on" not in shipped["policy"]
    assert isinstance(shipped["policy"]["output_retention_days"], int)
    assert shipped["policy"]["output_retention_days"] > 0


def test_timeout_output_is_kept_and_journalled(env):
    write_registry(
        env,
        registry(
            {"slow": model("echo PARTIAL; sleep 5", timeout_seconds=1)},
            {"executor": {"models": ["slow"]}},
        ),
    )
    run(env, "--role", "executor", "--out", str(env["out"]))

    line = journal_lines(env)[0]
    assert line["outcome"] == "timeout"
    kept = Path(line["out_path"])
    assert kept.exists()
    assert kept.read_text().strip() == "PARTIAL"
    assert line["out_bytes"] == kept.stat().st_size
    assert kept.parent == outputs_dir(env)


def test_error_and_unavailable_outputs_are_kept(env):
    write_registry(
        env,
        registry(
            {
                "broken": model("cat >/dev/null; echo 'Error: rate limit exceeded' >&2; exit 1"),
                "buggy": model("cat >/dev/null; echo 'boom' >&2; exit 3"),
            },
            {"executor": {"models": ["broken", "buggy"]}},
        ),
    )
    run(env, "--role", "executor", "--out", str(env["out"]))

    lines = journal_lines(env)
    assert [line["outcome"] for line in lines] == ["unavailable", "error"]
    for line in lines:
        kept = Path(line["out_path"])
        assert kept.exists(), f"{line['outcome']} output must be kept"
        assert line["out_bytes"] > 0


def test_ok_and_preflight_overflow_carry_null_paths(env):
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
    run(env, "--role", "executor", "--out", str(env["out"]))

    lines = journal_lines(env)
    assert lines[0]["outcome"] == "context_overflow"
    assert lines[0]["out_path"] is None
    assert lines[0]["out_bytes"] is None
    assert lines[1]["outcome"] == "ok"
    assert lines[1]["out_path"] is None
    assert lines[1]["out_bytes"] is None


def test_outputs_default_next_to_journal(env):
    """No MODEL_OUTPUTS override: the kept file must land next to the journal, not in /tmp."""
    write_registry(
        env,
        registry(
            {"buggy": model("cat >/dev/null; echo boom >&2; exit 3")},
            {"executor": {"models": ["buggy"]}},
        ),
    )
    run(env, "--role", "executor", "--out", str(env["out"]))
    kept = Path(journal_lines(env)[0]["out_path"])
    assert kept.parent == outputs_dir(env)
    assert kept.parent == env["journal"].parent / "model-outputs"


def test_journal_line_has_no_output_text(env):
    marker = "SUPER_SECRET_TASK_MARKER_12345"
    write_registry(
        env,
        registry(
            {"buggy": model(f"cat >/dev/null; echo '{marker}' >&2; exit 3")},
            {"executor": {"models": ["buggy"]}},
        ),
    )
    run(env, "--role", "executor", "--out", str(env["out"]))
    raw_journal = env["journal"].read_text()
    assert marker not in raw_journal
    kept = Path(journal_lines(env)[0]["out_path"])
    assert marker in kept.read_text()


def test_expect_miss_is_check_failed_and_next_model_answers(env):
    write_registry(
        env,
        registry(
            {
                "vague": model("cat >/dev/null; echo NO URL"),
                "precise": model("cat >/dev/null; echo '=== URL ==='"),
            },
            {"executor": {"models": ["vague", "precise"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]), "--expect", "^=== URL ===$")
    assert result.returncode == 0, result.stderr
    assert env["out"].read_text().strip() == "=== URL ==="

    outcomes = [line["outcome"] for line in journal_lines(env)]
    assert outcomes == ["check_failed", "ok"]
    assert json.loads(env["penalties"].read_text()) == {}


def test_empty_exit_zero_output_is_check_failed(env):
    write_registry(
        env,
        registry(
            {"mute": model("cat >/dev/null")},
            {"executor": {"models": ["mute"]}},
        ),
    )
    run(env, "--role", "executor", "--out", str(env["out"]))
    line = journal_lines(env)[0]
    assert line["outcome"] == "check_failed"
    assert line["out_bytes"] == 0


def test_invalid_expect_regex_is_usage_error(env):
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo ANSWER")},
            {"executor": {"models": ["good"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]), "--expect", "(")
    assert result.returncode == 2
    assert "valid extended regex" in result.stderr
    assert not env["journal"].exists() or journal_lines(env) == []


def test_expect_matching_task_text_is_usage_error(env):
    env["task"].write_text("please answer with === URL === at the end\n")
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo ANSWER")},
            {"executor": {"models": ["good"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]), "--expect", "=== URL ===")
    assert result.returncode == 2
    assert "matches the task text" in result.stderr


def test_help_lists_expect_and_check_failed():
    result = subprocess.run(
        ["bash", str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "--expect" in result.stdout
    assert "check_failed" in result.stdout
    assert "set -uo" not in result.stdout


@pytest.mark.parametrize("flag", ["--role", "--task", "--out", "--expect"])
def test_value_flag_without_value_is_usage_error_not_a_hang(flag, env):
    result = subprocess.run(
        ["bash", str(SCRIPT), "--role", "executor", "--task", str(env["task"]), flag],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 2
    assert "needs a value" in result.stderr


def test_unusable_outputs_dir_stops_before_any_attempt(env, tmp_path):
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo ANSWER")},
            {"executor": {"models": ["good"]}},
        ),
    )
    # A regular file where the directory should be: mkdir -p cannot create it.
    outputs_dir(env).write_text("not a directory\n")
    result = run(env, "--role", "executor", "--out", str(env["out"]))
    assert result.returncode == 2
    assert "outputs dir" in result.stderr
    assert journal_lines(env) == [], "a local fault must not be journalled as a model failure"


@pytest.mark.parametrize("days", ["abc", "1.5", "0", ""])
def test_invalid_retention_days_is_usage_error(days, env):
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo ANSWER")},
            {"executor": {"models": ["good"]}},
            policy={"output_retention_days": days},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]))
    assert result.returncode == 2
    assert "output_retention_days" in result.stderr
    assert journal_lines(env) == []


def test_failed_move_to_out_is_not_success_and_keeps_answer(env, tmp_path):
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo ANSWER")},
            {"executor": {"models": ["good"]}},
        ),
    )
    bad_out = tmp_path / "no-such-dir" / "out.md"
    result = run(env, "--role", "executor", "--out", str(bad_out))
    assert result.returncode != 0
    kept = list(outputs_dir(env).glob("*.out"))
    assert len(kept) == 1 and kept[0].read_text().strip() == "ANSWER"
    assert str(kept[0]) in result.stderr


def test_kept_output_is_private_and_ok_answer_leaves_no_file(env):
    write_registry(
        env,
        registry(
            {"broken": model("cat >/dev/null; exit 3"), "good": model("cat >/dev/null; echo ANSWER")},
            {"executor": {"models": ["broken", "good"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]))
    assert result.returncode == 0, result.stderr
    kept = list(outputs_dir(env).glob("*.out"))
    assert len(kept) == 1, "only the non-ok attempt keeps a file"
    assert (kept[0].stat().st_mode & 0o777) == 0o600


def test_penalize_on_from_registry_is_honoured(env):
    write_registry(
        env,
        registry(
            {"mute": model("cat >/dev/null"), "good": model("cat >/dev/null; echo ANSWER")},
            {"executor": {"models": ["mute", "good"]}},
            policy={"penalize_on": ["unavailable", "check_failed"]},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]))
    assert result.returncode == 0, result.stderr
    penalties = json.loads(env["penalties"].read_text())
    assert penalties["mute"]["reason"] == "check_failed"


def test_unavailable_is_penalised_when_policy_has_no_penalize_on(env):
    write_registry(
        env,
        registry(
            {"broken": model("cat >/dev/null; echo 'quota exceeded' >&2; exit 1")},
            {"executor": {"models": ["broken"]}},
        ),
    )
    run(env, "--role", "executor", "--out", str(env["out"]))
    assert json.loads(env["penalties"].read_text())["broken"]["reason"] == "unavailable"


def test_sigterm_during_attempt_is_journalled_as_interrupted(env):
    marker = "37.4242"  # unique sleep argument to find the child process
    write_registry(
        env,
        registry(
            {"slow": model(f"cat >/dev/null; sleep {marker}", timeout_seconds=60)},
            {"executor": {"models": ["slow"]}},
        ),
    )
    proc_env = dict(os.environ)
    proc_env.pop("MODEL_OUTPUTS", None)
    proc_env.update(
        MODEL_REGISTRY=str(env["registry"]),
        MODEL_JOURNAL=str(env["journal"]),
        MODEL_PENALTIES=str(env["penalties"]),
        MODEL_RUN_SESSION="test",
    )
    proc = subprocess.Popen(
        ["bash", str(SCRIPT), "--task", str(env["task"]), "--role", "executor", "--out", str(env["out"])],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=proc_env,
    )
    deadline = time.time() + 10
    while time.time() < deadline and not list(outputs_dir(env).glob("*.out")):
        time.sleep(0.1)
    time.sleep(0.5)  # let the model command start
    started = time.time()
    proc.send_signal(signal.SIGTERM)
    _, err = proc.communicate(timeout=10)
    assert proc.returncode == 143, err
    assert time.time() - started < 5, "the trap must not wait for the model timeout"
    lines = journal_lines(env)
    assert [ln["outcome"] for ln in lines] == ["interrupted"]
    assert Path(lines[0]["out_path"]).exists()
    time.sleep(0.3)
    ps = subprocess.run(["pgrep", "-f", f"sleep {marker}"], capture_output=True, text=True)
    assert ps.stdout.strip() == "", "the model command must be stopped"


def test_help_lists_interrupted_and_penalize_on():
    result = subprocess.run(["bash", str(SCRIPT), "--help"], capture_output=True, text=True, timeout=10)
    assert "interrupted" in result.stdout
    assert "penalize_on" in result.stdout


def test_role_timeout_overrides_a_shorter_model_timeout(env):
    write_registry(
        env,
        registry(
            {"slowish": model("cat >/dev/null; sleep 2; echo LATE", timeout_seconds=1)},
            {"researcher": {"models": ["slowish"], "timeout_seconds": 5}},
        ),
    )
    result = run(env, "--role", "researcher", "--out", str(env["out"]))
    assert result.returncode == 0, result.stderr
    assert env["out"].read_text().strip() == "LATE"


def test_model_timeout_applies_when_role_has_none(env):
    write_registry(
        env,
        registry(
            {"slowish": model("cat >/dev/null; sleep 2; echo LATE", timeout_seconds=1)},
            {"executor": {"models": ["slowish"]}},
        ),
    )
    run(env, "--role", "executor", "--out", str(env["out"]))
    assert [ln["outcome"] for ln in journal_lines(env)] == ["timeout"]


@pytest.mark.parametrize("bad", ["abc", "0", "1.5"])
def test_invalid_role_timeout_is_usage_error(bad, env):
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo ANSWER")},
            {"researcher": {"models": ["good"], "timeout_seconds": bad}},
        ),
    )
    result = run(env, "--role", "researcher", "--out", str(env["out"]))
    assert result.returncode == 2
    assert "timeout_seconds" in result.stderr
    assert journal_lines(env) == []


def test_shipped_researcher_role():
    shipped = json.loads((SCRIPT.resolve().parent.parent / "model-registry.json").read_text())
    role = shipped["roles"]["researcher"]
    assert role["models"] == ["glm-5.3-high", "gpt-terra-high", "sonnet-low"]
    assert role["timeout_seconds"] == 900
    for name in role["models"]:
        assert shipped["models"][name]["capabilities"]["web_search"] is True, name


def test_help_mentions_role_timeout():
    result = subprocess.run(["bash", str(SCRIPT), "--help"], capture_output=True, text=True, timeout=10)
    assert "roles.<role>.timeout_seconds" in result.stdout


def test_dry_run_shows_the_effective_timeout(env):
    write_registry(
        env,
        registry(
            {"m": model("echo X", timeout_seconds=1)},
            {"withrole": {"models": ["m"], "timeout_seconds": 5}, "plain": {"models": ["m"]}},
        ),
    )
    assert "timeout=5" in run(env, "--role", "withrole", "--dry-run").stdout
    assert "timeout=1" in run(env, "--role", "plain", "--dry-run").stdout


def test_shipped_roles_other_than_researcher_keep_model_timeouts():
    shipped = json.loads((SCRIPT.resolve().parent.parent / "model-registry.json").read_text())
    for name, role in shipped["roles"].items():
        if name not in ("researcher", "reviewer"):
            assert "timeout_seconds" not in role, f"role {name} must keep per-model timeouts"


@pytest.mark.parametrize("bad", [False, "", "900", -3])
def test_role_timeout_must_be_a_json_positive_integer(bad, env):
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo ANSWER")},
            {"researcher": {"models": ["good"], "timeout_seconds": bad}},
        ),
    )
    result = run(env, "--role", "researcher", "--out", str(env["out"]))
    assert result.returncode == 2, result.stderr
    assert "timeout_seconds" in result.stderr


def test_reference_only_role_is_refused(env):
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo ANSWER")},
            {"orchestrator": {"models": ["good"], "dispatch": False}},
        ),
    )
    for extra in ([], ["--dry-run"]):
        result = run(env, "--role", "orchestrator", "--out", str(env["out"]), *extra)
        assert result.returncode == 2
        assert "reference-only" in result.stderr
    assert journal_lines(env) == []


def test_shipped_orchestrator_role_is_reference_only():
    shipped = json.loads((SCRIPT.resolve().parent.parent / "model-registry.json").read_text())
    assert shipped["roles"]["orchestrator"]["dispatch"] is False
    for name, role in shipped["roles"].items():
        if name != "orchestrator":
            assert role.get("dispatch", True) is True, name


@pytest.mark.parametrize("flag", ["--role", "--task", "--out", "--expect"])
def test_a_flag_is_not_taken_as_another_flags_value(flag, env):
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo RAN")},
            {"executor": {"models": ["good"]}},
        ),
    )
    args = {"--role": "executor", "--task": str(env["task"]), "--out": str(env["out"])}
    argv = [a for k, v in args.items() if k != flag for a in (k, v)]
    result = subprocess.run(
        ["bash", str(SCRIPT), *argv, flag, "--dry-run"],
        capture_output=True, text=True, timeout=10,
        env={**os.environ, "MODEL_REGISTRY": str(env["registry"]), "MODEL_JOURNAL": str(env["journal"]),
             "MODEL_PENALTIES": str(env["penalties"]), "MODEL_OUTPUTS": str(outputs_dir(env))},
    )
    assert result.returncode == 2, result.stderr
    assert "needs a value" in result.stderr
    assert journal_lines(env) == [], "the model must not run"


def test_empty_expect_is_usage_error(env):
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo RAN")},
            {"executor": {"models": ["good"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]), "--expect", "")
    assert result.returncode == 2
    assert "--expect" in result.stderr
    assert journal_lines(env) == []


def test_out_path_starting_with_dash_is_written(env, tmp_path, monkeypatch):
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo ANSWER")},
            {"executor": {"models": ["good"]}},
        ),
    )
    monkeypatch.chdir(tmp_path)
    result = run(env, "--role", "executor", "--out", "-answer.md")
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "-answer.md").read_text().strip() == "ANSWER"


def test_dry_run_creates_no_state(env, tmp_path):
    env["journal"] = tmp_path / "state" / "journal.jsonl"
    env["penalties"] = tmp_path / "state" / "penalties.json"
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo SHOULD_NOT_RUN")},
            {"executor": {"models": ["good"]}},
        ),
    )
    result = run(env, "--role", "executor", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "state").exists(), "dry run must not create the journal dir or penalties file"


def test_codex_command_writes_the_final_message_to_the_answer_file(env):
    write_registry(
        env,
        registry(
            {"cx": {"pool": "openai", "runner": "codex", "model_arg": "m", "timeout_seconds": 10}},
            {"executor": {"models": ["cx"]}},
        ),
    )
    out = run(env, "--role", "executor", "--dry-run").stdout
    assert '-o "$MODEL_RUN_ANSWER_FILE"' in out


LOG_AND_ANSWER = 'cat >/dev/null; echo "LOG LINE 1"; echo "LOG LINE 2"; printf "FINAL ANSWER\\nVERDICT-OK\\n" > "$MODEL_RUN_ANSWER_FILE"'


def test_answer_file_is_delivered_instead_of_the_log(env):
    write_registry(
        env,
        registry({"cx": model(LOG_AND_ANSWER)}, {"executor": {"models": ["cx"]}}),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]))
    assert result.returncode == 0, result.stderr
    assert env["out"].read_text() == "FINAL ANSWER\nVERDICT-OK\n"
    assert list(outputs_dir(env).glob("*")) == [], "an ok attempt leaves no files behind"


def test_expect_is_checked_against_the_answer_file(env):
    write_registry(
        env,
        registry(
            {"cx": model('cat >/dev/null; echo "VERDICT-OK in the log only"; echo "no verdict" > "$MODEL_RUN_ANSWER_FILE"'),
             "good": model(LOG_AND_ANSWER)},
            {"executor": {"models": ["cx", "good"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]), "--expect", "^VERDICT-OK$")
    assert result.returncode == 0, result.stderr
    assert [ln["outcome"] for ln in journal_lines(env)] == ["check_failed", "ok"]


def test_empty_answer_file_falls_back_to_stdout(env):
    write_registry(
        env,
        registry({"plain": model("cat >/dev/null; echo STDOUT ANSWER")}, {"executor": {"models": ["plain"]}}),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]))
    assert result.returncode == 0, result.stderr
    assert env["out"].read_text().strip() == "STDOUT ANSWER"


def test_non_ok_attempt_keeps_the_log_and_no_answer_file(env):
    write_registry(
        env,
        registry(
            {"cx": model('cat >/dev/null; echo "LOG ONLY"; echo "partial" > "$MODEL_RUN_ANSWER_FILE"; exit 3')},
            {"executor": {"models": ["cx"]}},
        ),
    )
    run(env, "--role", "executor", "--out", str(env["out"]))
    line = journal_lines(env)[0]
    assert line["outcome"] == "error"
    assert "LOG ONLY" in Path(line["out_path"]).read_text()
    assert [p.name for p in outputs_dir(env).iterdir()] == [Path(line["out_path"]).name]


def test_shipped_reviewer_role():
    shipped = json.loads((SCRIPT.resolve().parent.parent / "model-registry.json").read_text())
    role = shipped["roles"]["reviewer"]
    assert role["models"] == ["gpt-sol-xhigh", "glm-5.3-high", "opus-xhigh"]
    assert role["timeout_seconds"] == 1800


def test_answer_file_is_private_whatever_the_umask(env):
    write_registry(
        env,
        registry({"cx": model(LOG_AND_ANSWER)}, {"executor": {"models": ["cx"]}}),
    )
    proc_env = {**os.environ, "MODEL_REGISTRY": str(env["registry"]), "MODEL_JOURNAL": str(env["journal"]),
                "MODEL_PENALTIES": str(env["penalties"]), "MODEL_OUTPUTS": str(outputs_dir(env))}
    cmd = f'umask 0002; bash "{SCRIPT}" --role executor --task "{env["task"]}" --out "{env["out"]}"'
    result = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, env=proc_env, timeout=30)
    assert result.returncode == 0, result.stderr
    assert env["out"].stat().st_mode & 0o077 == 0, oct(env["out"].stat().st_mode)


def test_failed_move_of_an_answer_file_leaves_only_the_answer(env, tmp_path):
    write_registry(
        env,
        registry({"cx": model(LOG_AND_ANSWER)}, {"executor": {"models": ["cx"]}}),
    )
    result = run(env, "--role", "executor", "--out", str(tmp_path / "missing-dir" / "x.md"))
    assert result.returncode == 2
    kept = list(outputs_dir(env).iterdir())
    assert len(kept) == 1 and kept[0].read_text() == "FINAL ANSWER\nVERDICT-OK\n"
    assert str(kept[0]) in result.stderr
