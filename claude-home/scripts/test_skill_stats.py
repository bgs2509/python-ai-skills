"""Tests for skill-stats.py — token attribution of Claude Code transcripts to skills."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("skill_stats", HERE / "skill-stats.py")
skill_stats = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(skill_stats)


# --- transcript record builders -------------------------------------------------------


def assistant(ts, msg_id, model="claude-sonnet-5-5", inp=10, cw=0, cr=1000, out=5,
              tool=None, cw_1h=None):
    usage = {
        "input_tokens": inp,
        "cache_creation_input_tokens": cw,
        "cache_read_input_tokens": cr,
        "output_tokens": out,
    }
    if cw_1h is not None:
        usage["cache_creation"] = {"ephemeral_5m_input_tokens": cw - cw_1h,
                                   "ephemeral_1h_input_tokens": cw_1h}
    content = [{"type": "text", "text": "x"}]
    if tool:
        content.append({"type": "tool_use", "name": "Skill", "input": {"skill": tool}})
    return {"type": "assistant", "timestamp": ts, "requestId": "req_" + msg_id,
            "message": {"id": msg_id, "model": model, "usage": usage, "content": content}}


def human(ts, text="please do it"):
    return {"type": "user", "timestamp": ts, "message": {"role": "user", "content": text}}


def slash(ts, name):
    return human(ts, f"<command-name>/{name}</command-name>\n<command-args></command-args>")


def tool_result(ts):
    return {"type": "user", "timestamp": ts,
            "message": {"content": [{"type": "tool_result", "content": "ok"}]}}


def write(path: Path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in records))


T = "2026-10-01T10:00:{:02d}.000Z"


def run(tmp_path, **kw):
    return skill_stats.summarize(skill_stats.collect(tmp_path, **kw))


def row(stats, name):
    return next(r for r in stats["skills"] if r["skill"] == name)


# --- windows --------------------------------------------------------------------------


def test_low_window_closes_on_human_message_high_continues(tmp_path):
    write(tmp_path / "p" / "s1.jsonl", [
        human(T.format(0)),
        assistant(T.format(1), "m1", tool="git-finish", cr=100, inp=0, out=0),
        tool_result(T.format(2)),
        assistant(T.format(3), "m2", cr=200, inp=0, out=0),
        human(T.format(4)),
        assistant(T.format(5), "m3", cr=400, inp=0, out=0),
    ])
    r = row(run(tmp_path), "git-finish")
    assert r["calls"] == 1 and r["tool_calls"] == 1 and r["sessions"] == 1
    assert r["tokens_low"] == 300
    assert r["tokens_high"] == 700


def test_skill_meta_message_does_not_close_window(tmp_path):
    meta = {"type": "user", "timestamp": T.format(2), "isMeta": True,
            "message": {"content": [{"type": "text", "text": "Base directory for this skill: /x"}]}}
    write(tmp_path / "p" / "s1.jsonl", [
        assistant(T.format(1), "m1", tool="do-feature", cr=100, inp=0, out=0),
        meta,
        assistant(T.format(3), "m2", cr=50, inp=0, out=0),
    ])
    assert row(run(tmp_path), "do-feature")["tokens_low"] == 150


def test_slash_command_opens_window_and_builtins_are_ignored(tmp_path):
    write(tmp_path / "p" / "s1.jsonl", [
        slash(T.format(0), "model"),
        slash(T.format(1), "progress-watch"),
        assistant(T.format(2), "m1", cr=100, inp=0, out=0),
        slash(T.format(3), "clear"),
        assistant(T.format(4), "m2", cr=900, inp=0, out=0),
    ])
    stats = run(tmp_path)
    names = {r["skill"] for r in stats["skills"]}
    assert names == {"progress-watch"}
    r = row(stats, "progress-watch")
    assert r["slash_calls"] == 1
    assert r["tokens_low"] == 100 and r["tokens_high"] == 100  # /clear closes both windows


def test_next_skill_takes_over_window(tmp_path):
    write(tmp_path / "p" / "s1.jsonl", [
        assistant(T.format(1), "m1", tool="do-feature", cr=100, inp=0, out=0),
        assistant(T.format(2), "m2", tool="best-questions", cr=10, inp=0, out=0),
        assistant(T.format(3), "m3", cr=1, inp=0, out=0),
    ])
    stats = run(tmp_path)
    assert row(stats, "do-feature")["tokens_low"] == 100
    assert row(stats, "best-questions")["tokens_low"] == 11


def test_streamed_duplicate_responses_counted_once(tmp_path):
    a = assistant(T.format(1), "m1", tool="git-commit", cr=100, inp=0, out=0)
    write(tmp_path / "p" / "s1.jsonl", [a, a, a])
    stats = run(tmp_path)
    assert row(stats, "git-commit")["tokens_low"] == 100
    assert stats["totals"]["tokens"] == 100


def test_invalid_line_is_skipped(tmp_path):
    f = tmp_path / "p" / "s1.jsonl"
    write(f, [assistant(T.format(1), "m1", tool="git-commit", cr=5, inp=0, out=0)])
    with f.open("a") as fh:
        fh.write('{"truncated": \n')
    assert row(run(tmp_path), "git-commit")["tokens_low"] == 5


# --- subagents ------------------------------------------------------------------------


def test_subagent_tokens_and_model_mix_go_to_parent_skill(tmp_path):
    write(tmp_path / "p" / "sess1.jsonl", [
        assistant(T.format(1), "m1", tool="do-feature", cr=100, inp=0, out=0),
        assistant(T.format(9), "m2", cr=1, inp=0, out=0),
    ])
    write(tmp_path / "p" / "sess1" / "subagents" / "agent-a.jsonl", [
        assistant(T.format(5), "s1", model="claude-haiku-5-5", cr=40, inp=0, out=0),
        assistant(T.format(6), "s2", model="claude-haiku-5-5", cr=60, inp=0, out=0),
    ])
    r = row(run(tmp_path), "do-feature")
    assert r["subagent_tokens"] == 100
    assert r["tokens_low"] == 201
    assert r["subagent_models"] == {"claude-haiku-5-5": {"calls": 2, "tokens": 100}}


# --- statistics and cost --------------------------------------------------------------


def test_per_invocation_median_and_p90(tmp_path):
    recs = []
    for i, cr in enumerate([10, 20, 30, 40, 1000]):
        recs.append(assistant(T.format(2 * i), f"m{i}", tool="progress-watch", cr=cr, inp=0, out=0))
        recs.append(human(T.format(2 * i + 1)))
    write(tmp_path / "p" / "s1.jsonl", recs)
    r = row(run(tmp_path), "progress-watch")
    assert r["calls"] == 5
    assert r["per_call_median"] == 30
    assert r["per_call_p90"] == 1000


def test_cost_uses_cache_write_split_and_price_table(tmp_path):
    # Opus 5.5: input 4, 5m write 5, 1h write 8, cache read 0.20, output 20 ($/MTok)
    write(tmp_path / "p" / "s1.jsonl", [
        assistant(T.format(1), "m1", model="claude-opus-5-5", tool="git-finish",
                  inp=1_000_000, cw=2_000_000, cw_1h=1_000_000, cr=1_000_000, out=1_000_000),
    ])
    stats = run(tmp_path)
    expected = 4 + 5 + 8 + 0.20 + 20
    assert row(stats, "git-finish")["cost_usd"] == pytest.approx(expected)
    assert stats["totals"]["cost_usd"] == pytest.approx(expected)
    assert stats["by_model"]["main"]["claude-opus-5-5"]["cost_usd"] == pytest.approx(expected)


def test_haiku_5_5_switches_to_long_prompt_tier_above_100k(tmp_path):
    write(tmp_path / "p" / "s1.jsonl", [
        assistant(T.format(1), "m1", model="claude-haiku-5-5", inp=50_000, cr=0, out=1_000_000),
        assistant(T.format(2), "m2", model="claude-haiku-5-5", inp=150_000, cr=0, out=1_000_000),
    ])
    cost = run(tmp_path)["totals"]["cost_usd"]
    short = 50_000 * 0.10 / 1e6 + 0.50
    long_ = 150_000 * 0.50 / 1e6 + 2.50
    assert cost == pytest.approx(short + long_)


def test_unpriced_model_tokens_reported_not_costed(tmp_path):
    write(tmp_path / "p" / "s1.jsonl", [
        assistant(T.format(1), "m1", model="glm-5.3", inp=0, cr=777, out=0),
    ])
    totals = run(tmp_path)["totals"]
    assert totals["unpriced_tokens"] == 777
    assert totals["cost_usd"] == 0


def test_totals_cache_read_share(tmp_path):
    write(tmp_path / "p" / "s1.jsonl", [assistant(T.format(1), "m1", inp=0, cr=90, out=10)])
    totals = run(tmp_path)["totals"]
    assert totals["tokens"] == 100
    assert totals["cache_read_share"] == pytest.approx(0.9)


def test_first_request_context_size(tmp_path):
    write(tmp_path / "p" / "a.jsonl", [
        assistant(T.format(1), "m1", inp=10, cw=0, cr=60_000, out=1),
        assistant(T.format(2), "m2", inp=10, cw=0, cr=90_000, out=1),
    ])
    write(tmp_path / "p" / "b.jsonl", [assistant(T.format(1), "n1", inp=0, cw=70_000, cr=0, out=1)])
    first = run(tmp_path)["first_request_context"]["main"]
    assert first["count"] == 2
    assert first["median"] in (60_010, 70_000)
    assert first["p90"] == 70_000


def test_since_filter_drops_old_events(tmp_path):
    write(tmp_path / "p" / "s1.jsonl", [
        assistant("2020-01-01T00:00:00.000Z", "old", tool="git-commit", cr=5, inp=0, out=0),
    ])
    stats = run(tmp_path, since_days=30)
    assert stats["skills"] == []
    assert stats["totals"]["tokens"] == 0


# --- CLI and template -----------------------------------------------------------------


def test_cli_json_smoke(tmp_path):
    write(tmp_path / "p" / "s1.jsonl", [assistant(T.format(1), "m1", tool="git-commit", cr=5)])
    out = subprocess.run([sys.executable, str(HERE / "skill-stats.py"), "--projects",
                          str(tmp_path), "--json"], capture_output=True, text=True, check=True)
    data = json.loads(out.stdout)
    assert data["skills"][0]["skill"] == "git-commit"


def test_cli_text_report_runs(tmp_path):
    write(tmp_path / "p" / "s1.jsonl", [assistant(T.format(1), "m1", tool="git-commit", cr=5)])
    out = subprocess.run([sys.executable, str(HERE / "skill-stats.py"), "--projects",
                          str(tmp_path), "--top", "5"], capture_output=True, text=True, check=True)
    assert "git-commit" in out.stdout


def test_template_keeps_transcripts_180_days():
    template = json.loads((HERE.parent / "settings.json.template").read_text())
    assert template["cleanupPeriodDays"] == 180
