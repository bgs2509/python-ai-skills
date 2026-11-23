#!/usr/bin/env python3
"""Append a single result line to .full_audit_tmp/results.jsonl.

Used by the agent after running MCP tools (e.g. sentrux) that bash run.sh
cannot invoke directly.

Usage:
  python lib/append_result.py <id> <name> <status> <metric> [exit]
  status ∈ {PASS, FAIL, WARN, SKIPPED}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 5:
        print("usage: append_result.py <id> <name> <status> <metric> [exit]", file=sys.stderr)
        return 2
    id_, name, status, metric = sys.argv[1:5]
    exit_code = int(sys.argv[5]) if len(sys.argv) > 5 else (0 if status == "PASS" else 1)
    if status not in {"PASS", "FAIL", "WARN", "SKIPPED"}:
        print(f"invalid status: {status}", file=sys.stderr)
        return 2
    path = Path(".full_audit_tmp/results.jsonl")
    path.parent.mkdir(exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps({
            "id": id_, "name": name, "status": status,
            "exit": exit_code, "metric": metric,
        }) + "\n")
    print(f"appended: {id_} {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
