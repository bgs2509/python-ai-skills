#!/usr/bin/env python3
"""Detect stagnation between two consecutive round reports."""
import json
import sys
from pathlib import Path


def detect(cur_path: Path, prev_path: Path | None, threshold: float = 0.5) -> dict:
    cur = json.loads(cur_path.read_text())
    if prev_path is None or not prev_path.exists():
        return {"stagnation": False, "repeated": 0, "prev_critical": 0}
    prev = json.loads(prev_path.read_text())
    cur_crit = {f["fingerprint"] for f in cur["findings"] if f["severity"] == "critical"}
    prev_crit = {f["fingerprint"] for f in prev["findings"] if f["severity"] == "critical"}
    repeated = len(cur_crit & prev_crit)
    stagnation = bool(prev_crit) and (repeated / len(prev_crit)) >= threshold
    return {
        "stagnation": stagnation,
        "repeated": repeated,
        "prev_critical": len(prev_crit),
        "repeated_fingerprints": sorted(cur_crit & prev_crit),
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: stagnation.py <round-N.json> [round-N-1.json] [threshold]", file=sys.stderr)
        return 2
    cur = Path(sys.argv[1])
    prev = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    th = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    print(json.dumps(detect(cur, prev, th)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
