"""Render `## Trends` markdown section from check_trends results."""
from __future__ import annotations

from typing import Any

MIN_RUNS_FOR_TRENDS = 3


def _row_sticky(s: dict[str, Any]) -> str:
    return (
        f"- **[{s['severity']}]** `{s['file']}:{s['line']}` — "
        f"{s['check_id']} — {s['message_raw']} "
        f"(seen in {s['consecutive_runs']} consecutive runs, "
        f"first {s['first_seen_commit']} → last {s['last_seen_commit']})"
    )


def _row_osc(o: dict[str, Any]) -> str:
    return (
        f"- **[{o['severity']}]** `{o['file']}:{o['line']}` — "
        f"{o['check_id']} — {o['message_raw']} "
        f"(cycles: {o['cycles']}, pattern over last {len(o['runs_window'])} runs: `{o['pattern']}`)"
    )


def _row_cb(c: dict[str, Any]) -> str:
    boundaries = ", ".join(f"{a}→{b}" for a, b in c["boundaries"])
    return (
        f"- module **{c['module']}** — fingerprints `{c['fingerprint_a'][:8]}` ↔ "
        f"`{c['fingerprint_b'][:8]}` alternate {c['repeats']}× "
        f"(commits: {boundaries})"
    )


def render_trends_section(
    sticky: list[dict[str, Any]],
    oscillating: list[dict[str, Any]],
    cross_breaking: list[dict[str, Any]],
    total_runs: int,
) -> str:
    if total_runs < MIN_RUNS_FOR_TRENDS:
        return ""

    out = ["## Trends", ""]
    out.append(f"_History window: {total_runs} audit runs._")
    out.append("")

    out.append("### Sticky (repeated)")
    out.append(
        "_Fingerprints present in the last 3 consecutive runs. "
        "Fix didn't land or is being re-broken._"
    )
    if sticky:
        out.extend(_row_sticky(s) for s in sticky)
    else:
        out.append("- none")
    out.append("")

    out.append("### Oscillating (circular type 1)")
    out.append(
        "_Fingerprints appear → disappear → reappear within the last 5 runs. "
        "Fix likely treated the symptom not the cause._"
    )
    if oscillating:
        out.extend(_row_osc(o) for o in oscillating)
    else:
        out.append("- none")
    out.append("")

    out.append("### Cross-breaking pairs (circular type 3)")
    out.append(
        "_Fix to fingerprint A coincides with appearance of fingerprint B "
        "in the same module, pattern recurs. Common root cause likely._"
    )
    if cross_breaking:
        out.extend(_row_cb(c) for c in cross_breaking)
    else:
        out.append("- none")
    out.append("")

    out.append("### Recommendations")
    out.append("- **Sticky** → open Beads bug; do NOT close the audit finding until fingerprint disappears for ≥ 2 runs.")
    out.append("- **Oscillating** → escalate to /audit-loop with `--start-from=<fingerprint>`; root-cause review required.")
    out.append("- **Cross-breaking pairs** → invariant violation; refactor the module owning both fingerprints; do not patch A and B in isolation.")
    out.append("")

    return "\n".join(out)
