#!/usr/bin/env python3
"""model-stats.py — read the model journal and answer four questions.

  1. Which models actually ran, how often, and how did they end?
  2. How fast were they really (median and p90, not the passport guess)?
  3. How much work stayed off the scarce Anthropic pool?
  4. Which models are penalised right now?

Facts only: every number here is counted from journal lines written by
model-run.sh. Nothing is scored, judged, or estimated. Outcome names are
whatever model-run.sh writes (ok, unavailable, context_overflow, timeout,
check_failed, error) — this module counts and renders them generically and
never special-cases one, so a new outcome value needs no change here.

  model-stats.py [--journal PATH] [--penalties PATH] [--since HOURS] [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

SCARCE_POOL = "anthropic"


def default_path(env_var: str, fallback: str) -> Path:
    return Path(os.environ.get(env_var, os.path.expanduser(fallback)))


def read_journal(path: Path, since_hours: float | None) -> list[dict]:
    if not path.exists():
        return []
    cutoff = None
    if since_hours is not None:
        cutoff = datetime.now().astimezone() - timedelta(hours=since_hours)

    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue  # a truncated tail line must not break the report
        if cutoff is not None:
            try:
                if datetime.fromisoformat(row["ts"]) < cutoff:
                    continue
            except (KeyError, ValueError):
                continue
        rows.append(row)
    return rows


def quantile(values: list[float], q: float) -> float:
    """Nearest-rank quantile — no interpolation, no numpy dependency."""
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, round(q * (len(ordered) - 1))))
    return ordered[idx]


def summarize(rows: list[dict]) -> dict:
    by_model: dict[str, dict] = defaultdict(
        lambda: {"calls": 0, "outcomes": defaultdict(int), "seconds": [], "pool": "?"}
    )
    by_pool: dict[str, dict] = defaultdict(lambda: {"calls": 0, "ok": 0})
    by_role: dict[str, dict] = defaultdict(lambda: {"calls": 0, "ok": 0})

    for row in rows:
        model = row.get("model", "?")
        pool = row.get("pool", "?")
        role = row.get("role", "?")
        outcome = row.get("outcome", "?")

        entry = by_model[model]
        entry["calls"] += 1
        entry["pool"] = pool
        entry["outcomes"][outcome] += 1
        # Skipped-before-running attempts carry seconds=0; they would drag the
        # latency picture toward zero, so only timed attempts count.
        if outcome != "context_overflow" and row.get("seconds", 0):
            entry["seconds"].append(float(row["seconds"]))

        by_pool[pool]["calls"] += 1
        by_role[role]["calls"] += 1
        if outcome == "ok":
            by_pool[pool]["ok"] += 1
            by_role[role]["ok"] += 1

    total = len(rows)
    scarce_calls = by_pool.get(SCARCE_POOL, {}).get("calls", 0)
    return {
        "total_attempts": total,
        "by_model": {
            name: {
                "pool": data["pool"],
                "calls": data["calls"],
                "outcomes": dict(data["outcomes"]),
                "median_seconds": round(quantile(data["seconds"], 0.5), 1),
                "p90_seconds": round(quantile(data["seconds"], 0.9), 1),
            }
            for name, data in by_model.items()
        },
        "by_pool": {name: dict(data) for name, data in by_pool.items()},
        "by_role": {name: dict(data) for name, data in by_role.items()},
        "off_scarce_pool_pct": round(100 * (total - scarce_calls) / total, 1) if total else 0.0,
        "window": {
            "first": min((r.get("ts", "") for r in rows), default=""),
            "last": max((r.get("ts", "") for r in rows), default=""),
        },
    }


def active_penalties(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}
    now = time.time()
    return {
        model: {"reason": body.get("reason", "?"), "minutes_left": round((body["until"] - now) / 60)}
        for model, body in data.items()
        if isinstance(body, dict) and body.get("until", 0) > now
    }


def render(stats: dict, penalties: dict[str, dict]) -> str:
    if not stats["total_attempts"]:
        return "model journal is empty — no attempts recorded yet"

    out = []
    w = stats["window"]
    out.append(f"attempts: {stats['total_attempts']}   window: {w['first'][:19]} .. {w['last'][:19]}")
    out.append(f"kept off the {SCARCE_POOL} pool: {stats['off_scarce_pool_pct']}% of attempts")
    out.append("")

    out.append(f"{'model':<18}{'pool':<11}{'calls':>6}{'median':>8}{'p90':>7}  outcomes")
    for name, data in sorted(stats["by_model"].items(), key=lambda kv: -kv[1]["calls"]):
        outcomes = " ".join(f"{k}={v}" for k, v in sorted(data["outcomes"].items()))
        out.append(
            f"{name:<18}{data['pool']:<11}{data['calls']:>6}"
            f"{data['median_seconds']:>8}{data['p90_seconds']:>7}  {outcomes}"
        )

    out.append("")
    out.append(f"{'pool':<18}{'calls':>6}{'ok':>6}")
    for name, data in sorted(stats["by_pool"].items(), key=lambda kv: -kv[1]["calls"]):
        out.append(f"{name:<18}{data['calls']:>6}{data['ok']:>6}")

    out.append("")
    out.append(f"{'role':<18}{'calls':>6}{'ok':>6}")
    for name, data in sorted(stats["by_role"].items(), key=lambda kv: -kv[1]["calls"]):
        out.append(f"{name:<18}{data['calls']:>6}{data['ok']:>6}")

    out.append("")
    if penalties:
        out.append("active penalties:")
        for model, body in sorted(penalties.items()):
            out.append(f"  {model:<16} {body['reason']:<14} {body['minutes_left']} min left")
    else:
        out.append("active penalties: none")

    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--journal", type=Path, default=default_path("MODEL_JOURNAL", "~/.claude/model-journal.jsonl"))
    parser.add_argument("--penalties", type=Path, default=default_path("MODEL_PENALTIES", "~/.claude/model-penalties.json"))
    parser.add_argument("--since", type=float, metavar="HOURS", help="only attempts newer than this")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    rows = read_journal(args.journal, args.since)
    stats = summarize(rows)
    penalties = active_penalties(args.penalties)

    if args.json:
        print(json.dumps({"stats": stats, "penalties": penalties}, indent=2))
    else:
        print(render(stats, penalties))
    return 0


if __name__ == "__main__":
    sys.exit(main())
