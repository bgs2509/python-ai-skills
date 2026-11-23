#!/usr/bin/env python3
"""Render audit report markdown from results.jsonl + excerpts/."""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

STATUS_ICON = {
    "PASS": "✓",
    "FAIL": "✗",
    "WARN": "⚠",
    "SKIPPED": "—",
}

REQUIRED_IDS = {
    "01-ruff-check", "02-ruff-format", "03-mypy",
    "04-gitleaks", "05-secret-files",
    "06-pytest-unit",
    "08-grace-lint",
    "10-ssot-drift", "11-block-anchors", "12-contracts",
    "19-pins",
}


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: render.py results.jsonl", file=sys.stderr)
        return 2
    jsonl = Path(sys.argv[1])
    tmp = jsonl.parent
    excerpts = tmp / "excerpts"
    rows = [json.loads(l) for l in jsonl.read_text().splitlines() if l.strip()]

    today = datetime.date.today().isoformat()
    cwd = Path.cwd().name

    out: list[str] = []
    out.append(f"# Full audit — {cwd} — {today}\n")

    ctx = excerpts / "00-context.txt"
    if ctx.exists():
        out.append("## Context\n```\n" + ctx.read_text().strip() + "\n```\n")

    out.append("## Summary\n")
    out.append("| # | Check | Status | Metric | Exit |")
    out.append("|---|-------|--------|--------|------|")

    pass_n = fail_n = warn_n = skip_n = 0
    required_fail = 0
    for r in rows:
        if r["id"] == "00-context":
            continue
        st = r["status"]
        icon = STATUS_ICON.get(st, "?")
        if st == "PASS":
            pass_n += 1
        elif st == "FAIL":
            fail_n += 1
            if r["id"] in REQUIRED_IDS:
                required_fail += 1
        elif st == "WARN":
            warn_n += 1
        else:
            skip_n += 1
        out.append(
            f"| {r['id']} | {r['name']} | {icon} {st} | {r['metric']} | {r['exit']} |"
        )
    total = pass_n + fail_n + warn_n + skip_n
    out.append("")
    out.append(
        f"**Totals:** {pass_n}/{total} pass · {fail_n} fail · {warn_n} warn · "
        f"{skip_n} skipped · **{required_fail} required failures**\n"
    )

    out.append("## Details\n")
    for r in rows:
        if r["id"] == "00-context":
            continue
        ex = excerpts / f"{r['id']}.txt"
        body = ex.read_text() if ex.exists() else "(no output)"
        body = body.strip() or "(empty)"
        st = r["status"]
        icon = STATUS_ICON.get(st, "?")
        out.append(f"### {r['id']} — {r['name']} — {icon} {st}")
        out.append(f"- exit: `{r['exit']}` · metric: `{r['metric']}`")
        out.append("```")
        out.append(body)
        out.append("```\n")

    # ---- Trend section (sticky / oscillating / cross-breaking) ----
    history_path = Path("docs/reports/.audit-history.jsonl")
    if history_path.exists():
        try:
            from history_store import read_history
            from check_trends import (
                find_sticky, find_oscillating, find_cross_breaking,
            )
            from render_trends import render_trends_section

            history = read_history(history_path)
            runs = {r["run_id"] for r in history}
            sticky = find_sticky(history, min_consecutive=3)
            osc = find_oscillating(history, window=5, min_cycles=2)
            cb = find_cross_breaking(history, min_repeats=2)
            trends_md = render_trends_section(sticky, osc, cb, total_runs=len(runs))
            if trends_md:
                out.append(trends_md)
        except Exception as exc:
            # Trend rendering is best-effort — must NOT fail the pipeline.
            out.append(f"\n_Trend detection failed: {exc!r}_\n")

    print("\n".join(out))
    return 0 if required_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
