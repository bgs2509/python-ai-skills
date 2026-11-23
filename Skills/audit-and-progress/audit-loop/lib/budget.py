#!/usr/bin/env python3
"""Per-fingerprint round budget. Counts how many prior rounds touched a fingerprint."""
import json
import sys
from pathlib import Path

STATE = Path("docs/audit-loop/state.json")


def appearances(fp: str, state: dict) -> int:
    """Count rounds where this fingerprint appeared in auto_applied/asked/still_open."""
    n = 0
    for r in state.get("rounds", []):
        seen = False
        for src in ("auto_applied", "asked", "still_open"):
            if any(item.get("fingerprint") == fp for item in r.get(src, [])):
                seen = True
                break
        if seen:
            n += 1
    return n


def over_budget(fp: str, state: dict, limit: int = 2) -> bool:
    return appearances(fp, state) >= limit


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: budget.py <fingerprint> [limit]", file=sys.stderr)
        return 2
    fp = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    if not STATE.exists():
        print(json.dumps({"appearances": 0, "over_budget": False, "limit": limit}))
        return 0
    state = json.loads(STATE.read_text())
    n = appearances(fp, state)
    print(json.dumps({"appearances": n, "over_budget": n >= limit, "limit": limit}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
