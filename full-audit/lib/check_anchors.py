#!/usr/bin/env python3
"""Verify START_BLOCK_<NAME> / END_BLOCK_<NAME> markers are paired and unique.

Per global CLAUDE.md "Semantic Markup Is Load-Bearing Structure":
markers MUST be uniquely named, paired, proportionally sized.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

from _self_check_emit import emit_finding, open_sidecar

START = re.compile(r"#\s*START_BLOCK_([A-Z0-9_]+)")
END = re.compile(r"#\s*END_BLOCK_([A-Z0-9_]+)")
ROOT = Path.cwd() / "src"


def _extract_file(issue: str) -> str:
    # All current ISSUES embed the file via "<path>::<anchor>". The path may
    # be absolute (Path.cwd() / 'src' / ...). We want the path part only.
    marker = "::"
    if marker in issue:
        before = issue.split(marker, 1)[0]
        # 'before' is the issue prefix followed by the path. Strip the prefix.
        for prefix in ("unpaired: ", "duplicate START anchor: ", "END without START: "):
            if before.startswith(prefix):
                return before[len(prefix):].strip()
        return before.strip()
    return "<aggregate>"


def _classify_anchor_issue(issue: str) -> str:
    if issue.startswith("unpaired: "):
        return "unpaired"
    if issue.startswith("duplicate START anchor: "):
        return "duplicate"
    if issue.startswith("END without START: "):
        return "orphan-end"
    return "anchor"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()
    if not ROOT.exists():
        print("src/ absent — skipping")
        return 0
    starts: Counter[str] = Counter()
    ends: Counter[str] = Counter()
    locations: dict[str, list[str]] = {}
    for p in ROOT.rglob("*.py"):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for m in START.finditer(line):
                key = f"{p}::{m.group(1)}"
                starts[key] += 1
                locations.setdefault(key, []).append(f"{p}:{i}")
            for m in END.finditer(line):
                key = f"{p}::{m.group(1)}"
                ends[key] += 1
    issues: list[str] = []
    for key, n in starts.items():
        if ends[key] != n:
            issues.append(f"unpaired: {key} (start={n}, end={ends[key]})")
        if n > 1:
            issues.append(f"duplicate START anchor: {key} at {locations[key]}")
    for key, n in ends.items():
        if key not in starts:
            issues.append(f"END without START: {key}")
    if issues:
        with open_sidecar(args.json_out) as sidecar:
            for i in issues[:50]:
                print(i)
                emit_finding(
                    sidecar, "11-block-anchors",
                    _extract_file(i), 0, "middle",
                    _classify_anchor_issue(i), i,
                )
        if len(issues) > 50:
            print(f"... +{len(issues) - 50} more")
        # Findings beyond 50 are intentionally NOT emitted to keep sidecar size bounded.
        return 1
    total = sum(starts.values())
    print(f"OK: {total} block anchors, all paired & unique.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
