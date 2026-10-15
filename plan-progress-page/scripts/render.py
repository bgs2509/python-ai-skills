#!/usr/bin/env python3
"""Render a plan-progress page from a plan JSON file and the reference template.

Usage: render.py <plan.json> <out.html>

The JSON is validated first; any broken invariant aborts with exit 1 and a
list of problems, so a wrong page is never written.
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "template.html"
TIME_RE = re.compile(r"^\d\d\.\d\d \d\d:\d\d$")
# "updated" carries the year the page reads every "ДД.ММ ЧЧ:ММ" in.
UPDATED_RE = re.compile(r"^(\d\d)\.(\d\d)\.(\d{4}) (\d\d):(\d\d)\b")
STATES = {"done", "run", "wait"}
SUB_STATES = {"d", "r", "w"}
EPS = 1e-9


def _key(t: str) -> tuple[int, int, int, int]:
    """Sort key of 'ДД.ММ ЧЧ:ММ' within one year: (month, day, hour, minute)."""
    day, month, hour, minute = int(t[0:2]), int(t[3:5]), int(t[6:8]), int(t[9:11])
    return month, day, hour, minute


def validate(plan: dict) -> list[str]:
    """Return every broken invariant of the plan; empty list means valid."""
    errors: list[str] = []
    for key in ("title", "updated", "start", "finish", "meta", "foot", "stages"):
        if key not in plan:
            errors.append(f"missing top-level key: {key}")
    if errors:
        return errors
    for key in ("start", "finish"):
        if not TIME_RE.match(plan[key]):
            errors.append(f"{key} must be 'ДД.ММ ЧЧ:ММ', got {plan[key]!r}")
    if not UPDATED_RE.match(plan["updated"]):
        errors.append(f"updated must start with 'ДД.ММ.ГГГГ ЧЧ:ММ', got {plan['updated']!r}")
    window = plan.get("work_window", [10, 23])
    if not (isinstance(window, list) and len(window) == 2 and all(isinstance(h, int) for h in window) and 0 <= window[0] < window[1] <= 24):
        errors.append(f"work_window must be [start_hour, end_hour] with 0 <= start < end <= 24, got {window!r}")
    stages = plan["stages"]
    if not stages:
        return errors + ["stages is empty"]
    ann_idx: list[int] = []
    for i, st in enumerate(stages, 1):
        where = f"stage {i} ({st.get('name', '?')})"
        state, hours, done = st.get("state"), st.get("hours", 0), st.get("done", 0)
        if state not in STATES:
            errors.append(f"{where}: state must be one of {sorted(STATES)}")
        if not hours > 0:
            errors.append(f"{where}: hours must be > 0")
        if not -EPS <= done <= hours + EPS:
            errors.append(f"{where}: done must be within 0..hours")
        if state == "done" and abs(done - hours) > EPS:
            errors.append(f"{where}: a done stage must have done == hours")
        if state == "wait" and done > EPS:
            errors.append(f"{where}: a waiting stage must have done == 0")
        if state != "done" and st.get("fact"):
            errors.append(f"{where}: fact is true only for done stages (run shows 'начало факт, конец прогноз')")
        for key in ("start", "end"):
            if not TIME_RE.match(st.get(key, "")):
                errors.append(f"{where}: {key} must be 'ДД.ММ ЧЧ:ММ'")
        if TIME_RE.match(st.get("start", "")) and TIME_RE.match(st.get("end", "")) and _key(st["end"]) < _key(st["start"]):
            errors.append(f"{where}: end is earlier than start")
        for sub in st.get("subs", []):
            if len(sub) != 2 or sub[0] not in SUB_STATES:
                errors.append(f"{where}: sub-stage {sub!r} must be [d|r|w, text]")
        if st.get("ann"):
            ann_idx.append(i)
    runs = [s for s in stages if s.get("state") == "run"]
    all_done = all(s.get("state") == "done" for s in stages)
    if len(runs) != 1 and not all_done:
        errors.append(f"exactly one stage must be 'run' (found {len(runs)}) unless every stage is done")
    order = [s.get("state") for s in stages]
    rank = {"done": 0, "run": 1, "wait": 2}
    if order != sorted(order, key=lambda x: rank.get(x, 3)):
        errors.append("states must go done… → run → wait… so the arrow lands inside the run stage")
    if ann_idx and ann_idx != list(range(ann_idx[0], ann_idx[-1] + 1)):
        errors.append(f"ann stages must be contiguous, got {ann_idx}")
    if ann_idx and not plan.get("ann_label"):
        errors.append("ann_label is required when any stage has ann")
    return errors


def render(plan: dict) -> str:
    """Fill the template; meta values and foot paragraphs are trusted HTML."""
    meta = "\n".join(
        f"    <div><dt>{html.escape(label)}</dt><dd>{value}</dd></div>" for label, value in plan["meta"]
    )
    foot = "\n".join(f"    <p>{para}</p>" for para in plan["foot"])
    data = {k: plan[k] for k in ("updated", "start", "finish", "stages")}
    data["ann_label"] = plan.get("ann_label", "")
    data["ann_summary"] = plan.get("ann_summary", "")
    data["work_window"] = plan.get("work_window", [10, 23])
    # "</" inside a <script> block would close it early.
    data_js = json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/")
    out = TEMPLATE.read_text(encoding="utf-8")
    for key, value in (
        ("{{TITLE}}", html.escape(plan["title"])),
        ("{{META}}", meta),
        ("{{FOOT}}", foot),
        ("{{DATA}}", data_js),
    ):
        out = out.replace(key, value)
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    plan = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    errors = validate(plan)
    if errors:
        print("plan.json is invalid:", *errors, sep="\n  - ", file=sys.stderr)
        return 1
    Path(argv[2]).write_text(render(plan), encoding="utf-8")
    total = sum(s["hours"] for s in plan["stages"])
    done = sum(s["done"] for s in plan["stages"])
    print(f"written {argv[2]}: done {100 * done / total:.1f}% ({done:g} h of {total:g} h), finish {plan['finish']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
