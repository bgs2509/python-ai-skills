#!/usr/bin/env python3
"""Verify all runtime deps in pyproject.toml [project].dependencies use '==' pin."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from _self_check_emit import emit_finding, open_sidecar

PYPROJECT = Path("pyproject.toml")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()
    if not PYPROJECT.exists():
        print("pyproject.toml absent")
        return 0
    text = PYPROJECT.read_text(encoding="utf-8")
    m = re.search(
        r"^\s*dependencies\s*=\s*\[(.*?)\]",
        text,
        re.S | re.M,
    )
    if not m:
        print("no [project].dependencies block")
        return 0
    body = m.group(1)
    bad: list[str] = []
    items: list[str] = []
    for raw in re.findall(r'"([^"]+)"', body):
        items.append(raw)
        # Allow extras + ==X.Y.Z; reject >=, ~=, ^, *, no version
        spec = re.sub(r"\[[^\]]*\]", "", raw).strip()
        if "==" in spec:
            continue
        bad.append(raw)
    if bad:
        print("Runtime deps NOT pinned with '==':")
        with open_sidecar(args.json_out) as sidecar:
            for b in bad:
                print(f"  {b}")
                emit_finding(
                    sidecar, "19-pins",
                    "pyproject.toml", 0, "middle", "not-pinned",
                    f"runtime dep not pinned with '==': {b}",
                )
        return 1
    print(f"OK: all {len(items)} runtime deps pinned with '=='.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
