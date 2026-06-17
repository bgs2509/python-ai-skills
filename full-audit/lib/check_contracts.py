#!/usr/bin/env python3
"""Verify every non-trivial src/**/*.py has START_MODULE_CONTRACT / END_MODULE_CONTRACT."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _self_check_emit import emit_finding, open_sidecar

ROOT = Path.cwd() / "src"
EXEMPT_SUFFIX = ("__init__.py",)
EXEMPT_DIRS = ("alembic/versions",)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()
    if not ROOT.exists():
        print("src/ absent — skipping")
        return 0
    missing: list[str] = []
    total = 0
    for p in ROOT.rglob("*.py"):
        rel = p.relative_to(Path.cwd()).as_posix()
        if any(rel.endswith(s) for s in EXEMPT_SUFFIX):
            continue
        if any(d in rel for d in EXEMPT_DIRS):
            continue
        total += 1
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "START_MODULE_CONTRACT" not in text or "END_MODULE_CONTRACT" not in text:
            missing.append(rel)
    if missing:
        print(f"Missing MODULE_CONTRACT in {len(missing)}/{total} files:")
        with open_sidecar(args.json_out) as sidecar:
            for m in missing[:30]:
                print(f"  {m}")
                emit_finding(
                    sidecar, "12-contracts",
                    m, 0, "middle", "missing-contract",
                    f"file missing MODULE_CONTRACT: {m}",
                )
        if len(missing) > 30:
            print(f"  ... +{len(missing) - 30} more")
        return 1
    print(f"OK: {total} modules — all carry MODULE_CONTRACT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
