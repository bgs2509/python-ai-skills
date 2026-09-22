"""Tests for model-stats.py — the journal summary."""

import importlib.util
import json
import time
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "model_stats", Path(__file__).resolve().parent / "model-stats.py"
)
model_stats = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(model_stats)


def entry(model="glm-4.7", pool="zai", role="executor", outcome="ok", seconds=10.0, ts=None):
    return {
        "ts": ts or time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "role": role,
        "model": model,
        "pool": pool,
        "runner": "x",
        "ctx_chars": 100,
        "ctx_tokens": 22,
        "seconds": seconds,
        "outcome": outcome,
        "exit": 0,
        "attempt": 1,
        "session": "test",
    }


def write_journal(path: Path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def test_empty_journal_says_so(tmp_path):
    stats = model_stats.summarize([])
    assert stats["total_attempts"] == 0
    assert "empty" in model_stats.render(stats, {})


def test_missing_journal_file_is_not_an_error(tmp_path):
    assert model_stats.read_journal(tmp_path / "nope.jsonl", None) == []


def test_truncated_tail_line_does_not_break_the_report(tmp_path):
    journal = tmp_path / "j.jsonl"
    journal.write_text(json.dumps(entry()) + "\n" + '{"ts": "broken')
    rows = model_stats.read_journal(journal, None)
    assert len(rows) == 1, "the valid line must survive a half-written tail"


def test_counts_and_outcomes_per_model(tmp_path):
    journal = tmp_path / "j.jsonl"
    write_journal(
        journal,
        [
            entry(outcome="ok", seconds=10),
            entry(outcome="unavailable", seconds=2),
            entry(model="sonnet-low", pool="anthropic", outcome="ok", seconds=7),
        ],
    )
    stats = model_stats.summarize(model_stats.read_journal(journal, None))
    assert stats["total_attempts"] == 3
    assert stats["by_model"]["glm-4.7"]["calls"] == 2
    assert stats["by_model"]["glm-4.7"]["outcomes"] == {"ok": 1, "unavailable": 1}
    assert stats["by_pool"]["zai"] == {"calls": 2, "ok": 1}
    assert stats["by_role"]["executor"]["calls"] == 3


def test_off_scarce_pool_share(tmp_path):
    """The headline number: how much work avoided the Anthropic quota."""
    journal = tmp_path / "j.jsonl"
    write_journal(
        journal,
        [entry(pool="zai")] * 3 + [entry(model="sonnet-low", pool="anthropic")],
    )
    stats = model_stats.summarize(model_stats.read_journal(journal, None))
    assert stats["off_scarce_pool_pct"] == 75.0


def test_skipped_attempts_do_not_distort_latency(tmp_path):
    """context_overflow rows are pre-flight skips with seconds=0 — excluded."""
    journal = tmp_path / "j.jsonl"
    write_journal(
        journal,
        [
            entry(outcome="context_overflow", seconds=0),
            entry(outcome="ok", seconds=20),
            entry(outcome="ok", seconds=20),
        ],
    )
    stats = model_stats.summarize(model_stats.read_journal(journal, None))
    assert stats["by_model"]["glm-4.7"]["median_seconds"] == 20.0
    assert stats["by_model"]["glm-4.7"]["calls"] == 3, "the skip is still an attempt"


def test_quantiles_on_known_values():
    assert model_stats.quantile([1, 2, 3, 4, 5], 0.5) == 3
    assert model_stats.quantile([1, 2, 3, 4, 5], 0.9) == 5
    assert model_stats.quantile([], 0.5) == 0.0


def test_since_filter_drops_old_rows(tmp_path):
    journal = tmp_path / "j.jsonl"
    old = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(time.time() - 48 * 3600))
    write_journal(journal, [entry(ts=old), entry()])
    assert len(model_stats.read_journal(journal, since_hours=24)) == 1
    assert len(model_stats.read_journal(journal, since_hours=None)) == 2


def test_only_unexpired_penalties_are_listed(tmp_path):
    path = tmp_path / "p.json"
    path.write_text(
        json.dumps(
            {
                "expired": {"until": time.time() - 10, "reason": "unavailable"},
                "active": {"until": time.time() + 1800, "reason": "unavailable"},
            }
        )
    )
    active = model_stats.active_penalties(path)
    assert set(active) == {"active"}
    assert 25 <= active["active"]["minutes_left"] <= 31


def test_corrupt_penalties_file_is_survivable(tmp_path):
    path = tmp_path / "p.json"
    path.write_text("{not json")
    assert model_stats.active_penalties(path) == {}


def test_cli_json_output_is_parseable(tmp_path, capsys):
    journal = tmp_path / "j.jsonl"
    write_journal(journal, [entry()])
    rc = model_stats.main(["--journal", str(journal), "--penalties", str(tmp_path / "none.json"), "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["stats"]["total_attempts"] == 1
    assert payload["penalties"] == {}


def test_cli_text_output_mentions_each_model(tmp_path, capsys):
    journal = tmp_path / "j.jsonl"
    write_journal(journal, [entry(), entry(model="qwen38", pool="local", role="batch", seconds=190)])
    model_stats.main(["--journal", str(journal), "--penalties", str(tmp_path / "none.json")])
    text = capsys.readouterr().out
    assert "glm-4.7" in text and "qwen38" in text
    assert "active penalties: none" in text
