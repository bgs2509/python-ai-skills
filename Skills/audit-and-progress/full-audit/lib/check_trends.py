"""Trend detectors over .audit-history.jsonl.

Three detectors:
- find_sticky: fingerprint present in N most-recent consecutive runs.
- find_oscillating: fingerprint with on/off/on pattern in last K runs.
- find_cross_breaking: pairs (A, B) where A disappears AND B appears at the
  same commit boundary, in the same top-level src/<module>/, recurring ≥ 2 times.

All three are read-only over history. No git operations.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any


def _runs_in_order(history: list[dict[str, Any]]) -> list[str]:
    """Return unique run_ids in their first-seen chronological order."""
    seen: list[str] = []
    last: str | None = None
    for rec in history:
        rid = rec["run_id"]
        if rid != last:
            seen.append(rid)
            last = rid
    return seen


def _index_by_run(history: list[dict[str, Any]]) -> dict[str, set[str]]:
    idx: dict[str, set[str]] = defaultdict(set)
    for rec in history:
        if rec.get("_sentinel"):
            continue
        idx[rec["run_id"]].add(rec["fingerprint"])
    return idx


def _last_seen(history: list[dict[str, Any]], fp: str) -> dict[str, Any]:
    for rec in reversed(history):
        if rec.get("_sentinel"):
            continue
        if rec["fingerprint"] == fp:
            return rec
    raise KeyError(fp)


def _first_seen(history: list[dict[str, Any]], fp: str) -> dict[str, Any]:
    for rec in history:
        if rec.get("_sentinel"):
            continue
        if rec["fingerprint"] == fp:
            return rec
    raise KeyError(fp)


def _module_of(file: str) -> str:
    parts = file.replace("\\", "/").split("/")
    if "src" in parts:
        i = parts.index("src")
        if i + 1 < len(parts):
            return parts[i + 1]
    return file


def find_sticky(history: list[dict[str, Any]], min_consecutive: int = 3) -> list[dict[str, Any]]:
    runs = _runs_in_order(history)
    if len(runs) < min_consecutive:
        return []
    last_n_runs = runs[-min_consecutive:]
    idx = _index_by_run(history)
    common = set.intersection(*(idx[r] for r in last_n_runs))

    out: list[dict[str, Any]] = []
    for fp in common:
        latest = _last_seen(history, fp)
        first = _first_seen(history, fp)
        out.append({
            "fingerprint": fp,
            "check_id": latest["check_id"],
            "file": latest["file"],
            "line": latest["line"],
            "severity": latest["severity"],
            "message_raw": latest["message_raw"],
            "consecutive_runs": min_consecutive,
            "first_seen_commit": first["commit"],
            "last_seen_commit": latest["commit"],
        })
    return out


def find_oscillating(
    history: list[dict[str, Any]],
    window: int = 5,
    min_cycles: int = 2,
) -> list[dict[str, Any]]:
    runs = _runs_in_order(history)[-window:]
    if len(runs) < 3:
        return []
    idx = _index_by_run(history)
    all_fps: set[str] = set().union(*(idx[r] for r in runs))

    out: list[dict[str, Any]] = []
    for fp in all_fps:
        pattern = [fp in idx[r] for r in runs]
        # transitions: positions where state flips ON↔OFF
        transitions = sum(
            1 for i in range(1, len(pattern)) if pattern[i] != pattern[i - 1]
        )
        # one cycle = ON→OFF→ON (two transitions)
        cycles = transitions // 2
        if cycles >= min_cycles:
            latest = _last_seen(history, fp)
            out.append({
                "fingerprint": fp,
                "check_id": latest["check_id"],
                "file": latest["file"],
                "line": latest["line"],
                "severity": latest["severity"],
                "message_raw": latest["message_raw"],
                "cycles": cycles,
                "pattern": "".join("X" if p else "." for p in pattern),
                "runs_window": runs,
            })
    return out


def find_cross_breaking(
    history: list[dict[str, Any]],
    min_repeats: int = 2,
) -> list[dict[str, Any]]:
    runs = _runs_in_order(history)
    if len(runs) < 2:
        return []

    # per-(run_id, fingerprint) → module of the file at that occurrence
    fp_module: dict[tuple[str, str], str] = {}
    for rec in history:
        if rec.get("_sentinel"):
            continue
        fp_module[(rec["run_id"], rec["fingerprint"])] = _module_of(rec["file"])

    idx = _index_by_run(history)

    # collect (module, A, B) swaps per commit boundary
    swaps: dict[tuple[str, str, str], list[tuple[str, str]]] = defaultdict(list)
    for prev, curr in zip(runs, runs[1:]):
        gone = idx[prev] - idx[curr]
        appeared = idx[curr] - idx[prev]
        for a in gone:
            for b in appeared:
                ma = fp_module.get((prev, a))
                mb = fp_module.get((curr, b))
                if ma and ma == mb:
                    key = (ma, *sorted([a, b]))
                    swaps[key].append((prev, curr))

    out: list[dict[str, Any]] = []
    for (module, a, b), boundaries in swaps.items():
        if len(boundaries) >= min_repeats:
            out.append({
                "module": module,
                "fingerprint_a": a,
                "fingerprint_b": b,
                "repeats": len(boundaries),
                "boundaries": boundaries,
            })
    return out
