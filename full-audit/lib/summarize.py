#!/usr/bin/env python3
"""Print colored stdout brief: what ran, critical/middle/minor results, remediation hints.

Reads .full_audit_tmp/results.jsonl. Stays at <80 chars wide.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# id -> severity bucket on FAIL ("critical" | "middle"). WARN/SKIP buckets handled separately.
SEVERITY: dict[str, str] = {
    # Security / correctness blockers — fix before doing anything else.
    "04-gitleaks":      "critical",
    "05-secret-files":  "critical",
    "06-pytest-unit":   "critical",
    "18-pip-audit":     "critical",
    # Required quality gates — fix before merge.
    "01-ruff-check":    "middle",
    "02-ruff-format":   "middle",
    "03-mypy":          "middle",
    "08-grace-lint":    "middle",
    "10-ssot-drift":    "middle",
    "11-block-anchors": "middle",
    "12-contracts":     "middle",
    "19-pins":          "middle",
}

# id -> one-line remediation. Concrete commands beat prose.
ADVICE: dict[str, str] = {
    "01-ruff-check":    "uv run ruff check . --fix    (root: dead code / unused imports / async misuse)",
    "02-ruff-format":   "uv run ruff format .         (zero-discussion auto-fix)",
    "03-mypy":          "add type annotations; src.shared.* is strict — start there",
    "04-gitleaks":      "ROTATE secret NOW; then `git filter-repo --invert-paths --path <file>` + force-push (with team consent)",
    "05-secret-files":  "git rm --cached <file>; add to .gitignore; rotate the secret",
    "06-pytest-unit":   "uv run pytest tests/unit -x -vv  (stop at first failure, full traceback)",
    "07-pytest-int":    "make test-up && make test-integration  (DB+migrations required)",
    "08-grace-lint":    "follow `grace lint` output; for SSoT drift run grace-refresh skill",
    "10-ssot-drift":    "edit discovery.md/design.md and let pre-commit regen XML; or run grace-refresh",
    "11-block-anchors": "pair every START_BLOCK_<X> with END_BLOCK_<X>; rename duplicates",
    "12-contracts":     "add MODULE_CONTRACT header to listed modules (see references/checks.md)",
    "13-bd-doctor":     "bd doctor; resolve sync issues before next bd close",
    "13b-bd-stale":     "bd stale; close finished issues, defer with `bd defer --until=<date>`",
    "13c-bd-orphans":   "bd orphans; fix broken dep links or delete the issue",
    "14-radon-cc":      "refactor CC≥C functions: early returns, extract helpers, kill nested ifs",
    "15-radon-mi":      "split modules with MI≤B; reduce length AND complexity together",
    "16-vulture":       "delete unused code; for false-positives mark with `_ = symbol` or vulture allowlist",
    "17-interrogate":   "add docstrings to public functions/classes of touched modules",
    "18-pip-audit":     "bump affected dep to secure version; keep `==` pin; rerun",
    "19-pins":          "replace >=, ~=, ^ with `==<exact>` in pyproject.toml [project].dependencies",
    "21-total-test":    "open `make total-test` output, rerun failing sub-step in isolation",
}


def _color(enable: bool) -> dict[str, str]:
    if not enable:
        return dict.fromkeys(
            ["RESET", "BOLD", "DIM", "RED", "YEL", "GRN", "CYN", "MAG"], ""
        )
    return {
        "RESET": "\033[0m", "BOLD": "\033[1m", "DIM": "\033[2m",
        "RED": "\033[1;31m", "YEL": "\033[1;33m",
        "GRN": "\033[1;32m", "CYN": "\033[1;36m", "MAG": "\033[1;35m",
    }


def _fmt_duration(sec: float) -> str:
    if sec < 60:
        return f"{sec:.1f}s"
    m, s = divmod(int(sec), 60)
    return f"{m}m {s:02d}s"


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: summarize.py results.jsonl [duration_sec]", file=sys.stderr)
        return 2
    rows = [
        json.loads(l) for l in Path(sys.argv[1]).read_text().splitlines() if l.strip()
    ]
    rows = [r for r in rows if r["id"] != "00-context"]
    duration = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0

    use_color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
    C = _color(use_color)

    pass_ = [r for r in rows if r["status"] == "PASS"]
    fail_ = [r for r in rows if r["status"] == "FAIL"]
    warn_ = [r for r in rows if r["status"] == "WARN"]
    skip_ = [r for r in rows if r["status"] == "SKIPPED"]

    critical = [r for r in fail_ if SEVERITY.get(r["id"]) == "critical"]
    middle = [r for r in fail_ if SEVERITY.get(r["id"]) == "middle"]
    middle += [r for r in fail_ if r["id"] not in SEVERITY]  # unknown FAIL → middle
    minor_warn = warn_
    minor_skip = skip_

    required_fail = len(critical) + len([r for r in middle if r["id"] in SEVERITY])

    bar = "═" * 67
    print()
    print(f"{C['CYN']}{bar}{C['RESET']}")
    print(f"{C['BOLD']}  Full Audit — Brief{C['RESET']}")
    print(f"{C['CYN']}{bar}{C['RESET']}")
    print(
        f"  Pipeline: {C['GRN']}{len(pass_)} PASS{C['RESET']} · "
        f"{C['RED']}{len(fail_)} FAIL{C['RESET']} · "
        f"{C['YEL']}{len(warn_)} WARN{C['RESET']} · "
        f"{C['DIM']}{len(skip_)} SKIPPED{C['RESET']}   "
        f"({len(rows)} total)"
    )
    print(
        f"  Required: {C['BOLD']}{required_fail}{C['RESET']} required failures"
    )
    if duration:
        print(f"  Duration: {_fmt_duration(duration)}")
    print()

    def _section(title: str, items: list[dict], color: str, icon: str, advice: bool):
        if not items:
            return
        print(f"  {color}{C['BOLD']}{title}{C['RESET']}")
        for r in items:
            print(f"    {color}{icon}{C['RESET']} "
                  f"{C['BOLD']}{r['id']:<18}{C['RESET']} {r['name']}")
            if advice:
                hint = ADVICE.get(r["id"])
                if hint:
                    print(f"       {C['DIM']}→{C['RESET']} {hint}")
        print()

    _section(
        "CRITICAL  (security / correctness — fix immediately)",
        critical, C["RED"], "✗", advice=True,
    )
    _section(
        "MIDDLE    (required quality — fix before merge)",
        middle, C["YEL"], "✗", advice=True,
    )
    _section(
        "MINOR — warnings (optional checks failed)",
        minor_warn, C["MAG"], "⚠", advice=True,
    )
    if minor_skip:
        print(f"  {C['DIM']}{C['BOLD']}MINOR — skipped (tools/artefacts unavailable){C['RESET']}")
        for r in minor_skip:
            print(f"    {C['DIM']}— {r['id']:<18} {r['name']:<28} ({r['metric']}){C['RESET']}")
        print()

    print(f"{C['CYN']}{bar}{C['RESET']}")
    if required_fail == 0:
        print(f"  {C['GRN']}{C['BOLD']}Exit 0 — all required checks PASS{C['RESET']}")
    else:
        print(f"  {C['RED']}{C['BOLD']}Exit 1 — {required_fail} required failure(s){C['RESET']}")
    print(f"{C['CYN']}{bar}{C['RESET']}")
    print()
    return 0 if required_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
