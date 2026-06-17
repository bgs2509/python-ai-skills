#!/usr/bin/env python3
"""Detect SSoT drift between docs and code.

Checks (best-effort; missing artefacts are skipped not failed):

1. docs/knowledge-graph.xml mentions modules that no longer exist in src/.
2. src/ python modules absent from knowledge-graph.xml (only RUNTIME-like dirs).
3. requirements.xml older than discovery.md frontmatter mtime (regen needed).
4. technology.xml older than design.md frontmatter mtime.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from _self_check_emit import emit_finding, open_sidecar

ROOT = Path.cwd()
ISSUES: list[str] = []


def _mtime(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0


def check_xml_vs_code() -> None:
    kg = ROOT / "docs" / "knowledge-graph.xml"
    if not kg.exists():
        return
    text = kg.read_text(encoding="utf-8", errors="ignore")
    # FILE attribute references in graph
    referenced = set(re.findall(r'(?:FILE|path)="([^"]+\.py)"', text))
    src_dir = ROOT / "src"
    if not src_dir.exists():
        return
    actual = set()
    for p in src_dir.rglob("*.py"):
        rel = p.relative_to(ROOT).as_posix()
        if "alembic/versions" in rel or rel.endswith("__init__.py"):
            continue
        actual.add(rel)
    missing_in_code = sorted(referenced - actual)
    missing_in_graph = sorted(actual - referenced)
    for m in missing_in_code:
        ISSUES.append(f"knowledge-graph references missing file: {m}")
    # Don't fail on missing_in_graph; just warn (info-level)
    if missing_in_graph:
        sample = ", ".join(missing_in_graph[:5])
        more = f" (+{len(missing_in_graph) - 5} more)" if len(missing_in_graph) > 5 else ""
        print(f"INFO: {len(missing_in_graph)} src/*.py not in knowledge-graph.xml: {sample}{more}")


def check_xml_freshness() -> None:
    pairs = [
        ("docs/superpowers/specs", "discovery", "docs/requirements.xml"),
        ("docs/superpowers/specs", "design", "docs/technology.xml"),
    ]
    for spec_dir, kind, xml_path in pairs:
        sd = ROOT / spec_dir
        xml = ROOT / xml_path
        if not sd.exists() or not xml.exists():
            continue
        latest = max(
            (_mtime(p) for p in sd.glob(f"*-{kind}.md")),
            default=0.0,
        )
        if latest == 0.0:
            continue
        if latest > _mtime(xml) + 1:
            ISSUES.append(
                f"{xml_path} stale: latest *-{kind}.md newer by "
                f"{int(latest - _mtime(xml))}s — run pre-commit / md_to_xml.py"
            )


def _extract_file(issue: str) -> str:
    if issue.startswith("knowledge-graph references missing file: "):
        return issue.split(": ", 1)[1].strip()
    if " stale: " in issue:
        return issue.split(" stale:", 1)[0].strip()
    return "<aggregate>"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()
    if not (ROOT / "docs").exists():
        print("docs/ absent — skipping SSoT drift checks")
        return 0
    check_xml_vs_code()
    check_xml_freshness()
    if ISSUES:
        with open_sidecar(args.json_out) as sidecar:
            for i in ISSUES:
                print(f"DRIFT: {i}")
                file = _extract_file(i)
                emit_finding(
                    sidecar, "10-ssot-drift", file, 0, "middle", "drift", i
                )
        return 1
    print("OK: no SSoT drift detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
