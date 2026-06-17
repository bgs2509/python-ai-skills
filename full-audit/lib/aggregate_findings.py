"""Read .full_audit_tmp/excerpts/*.txt + self-check sidecars + AI report,
dispatch to parsers, emit .full_audit_tmp/findings.jsonl with fingerprints.

Usage:
  python3 aggregate_findings.py \
      --excerpts .full_audit_tmp/excerpts \
      --out      .full_audit_tmp/findings.jsonl \
      --ai-report docs/reports/<date>-audit.md \
      --self-check-sidecar .full_audit_tmp/sidecars/10-ssot-drift.jsonl
      [--self-check-sidecar ... (repeatable)]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from fingerprint import compute_fingerprint, compute_fingerprint_loose, normalize_message
from normalize_findings import (
    parse_ai_section_json,
    parse_gitleaks,
    parse_mypy,
    parse_ruff,
)

# excerpt-id → parser. Add more as parsers grow.
PARSERS: dict[str, Callable[[str], list[dict[str, Any]]]] = {
    "01-ruff-check": parse_ruff,
    "03-mypy": parse_mypy,
    "04-gitleaks": parse_gitleaks,
}


def _enrich(rec: dict[str, Any]) -> dict[str, Any]:
    rec["message_canonical"] = normalize_message(rec["message_raw"])
    rec["fingerprint"] = compute_fingerprint(
        rec["check_id"], rec["file"], rec["line"], rec["message_raw"]
    )
    rec["fingerprint_loose"] = compute_fingerprint_loose(
        rec["check_id"], rec["file"], rec["message_raw"]
    )
    rec["line_bucket"] = int(rec["line"]) // 5
    return rec


def aggregate(
    excerpts_dir: Path,
    out_path: Path,
    ai_report_path: Path | None,
    self_check_sidecars: list[Path],
) -> int:
    all_findings: list[dict[str, Any]] = []

    for excerpt_id, parser in PARSERS.items():
        f = excerpts_dir / f"{excerpt_id}.txt"
        if f.exists():
            all_findings.extend(parser(f.read_text()))

    for sidecar in self_check_sidecars:
        if not sidecar.exists():
            continue
        for line in sidecar.read_text().splitlines():
            if line.strip():
                all_findings.append(json.loads(line))

    if ai_report_path and ai_report_path.exists():
        all_findings.extend(parse_ai_section_json(ai_report_path.read_text()))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fp:
        for rec in all_findings:
            fp.write(json.dumps(_enrich(rec)) + "\n")

    return len(all_findings)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--excerpts", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--ai-report", type=Path, default=None)
    p.add_argument("--self-check-sidecar", type=Path, action="append", default=[])
    args = p.parse_args()
    n = aggregate(args.excerpts, args.out, args.ai_report, args.self_check_sidecar)
    print(f"aggregated {n} findings → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
