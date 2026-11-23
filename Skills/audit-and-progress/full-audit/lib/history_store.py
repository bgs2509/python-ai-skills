"""Persistent audit history store.

`docs/reports/.audit-history.jsonl` — one JSON line per (run, finding) occurrence.
Append-only; never rewritten. Read by check_trends.py.
"""
from __future__ import annotations

import argparse
import datetime
import json
import subprocess
from pathlib import Path
from typing import Any


def _date_from_run_id(run_id: str) -> str:
    return run_id.split("T", 1)[0]


def append_run(
    history_path: Path,
    findings_path: Path,
    commit: str,
    run_id: str,
) -> int:
    history_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with history_path.open("a", encoding="utf-8") as out:
        for line in findings_path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            rec["commit"] = commit
            rec["run_id"] = run_id
            rec["date"] = _date_from_run_id(run_id)
            out.write(json.dumps(rec) + "\n")
            n += 1
        if n == 0:
            # Sentinel row: marks the run occurred even though it produced
            # zero findings. Without this, clean codebases never accumulate
            # enough runs to trigger trend detection.
            out.write(json.dumps({
                "run_id": run_id,
                "commit": commit,
                "date": _date_from_run_id(run_id),
                "_sentinel": True,
            }) + "\n")
    return n


def read_history(history_path: Path) -> list[dict[str, Any]]:
    if not history_path.exists():
        return []
    return [
        json.loads(l) for l in history_path.read_text().splitlines() if l.strip()
    ]


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, timeout=5
        ).strip()[:10]
    except Exception:
        return "unknown"


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("append")
    a.add_argument("--history", type=Path, required=True)
    a.add_argument("--findings", type=Path, required=True)
    a.add_argument("--commit", default=None)
    args = p.parse_args()
    if args.cmd == "append":
        commit = args.commit or _git_head()
        run_id = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        n = append_run(args.history, args.findings, commit, run_id)
        print(f"appended {n} findings to {args.history}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
