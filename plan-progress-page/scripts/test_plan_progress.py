"""Tests for render.py and session_hours.py of the plan-progress-page skill."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import render
import session_hours

EXAMPLE = Path(__file__).resolve().parent.parent / "assets" / "example-plan.json"


def plan() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_example_plan_is_valid_and_fills_every_placeholder() -> None:
    p = plan()
    assert render.validate(p) == []
    page = render.render(p)
    assert "{{" not in page
    assert "<title>Ход навыка plan-progress-page</title>" in page


def test_script_closing_tag_in_data_is_neutralised() -> None:
    p = plan()
    p["stages"][0]["detail"] = "</script><b>x</b>"
    page = render.render(p)
    assert "</script><b>" not in page
    assert "<\\/script>" in page


def test_validate_reports_each_broken_invariant() -> None:
    p = copy.deepcopy(plan())
    p["stages"][1]["done"] = 1.0  # done stage not full
    p["stages"][3]["state"] = "run"  # two run stages
    p["stages"][2]["fact"] = True  # fact on a run stage
    p["stages"][0]["start"] = "15.10.2026"
    errors = "\n".join(render.validate(p))
    assert "done == hours" in errors
    assert "exactly one stage must be 'run'" in errors
    assert "fact is true only for done" in errors
    assert "start must be" in errors


def test_all_done_plan_needs_no_run_stage() -> None:
    p = plan()
    for st in p["stages"]:
        st.update(state="done", done=st["hours"], fact=True)
    assert render.validate(p) == []


def test_states_out_of_order_are_rejected() -> None:
    p = plan()
    p["stages"][0].update(state="wait", done=0, fact=False)
    assert any("done… → run → wait…" in e for e in render.validate(p))


def test_encode_matches_claude_project_dir_naming() -> None:
    assert session_hours.encode("/home/bgs/ai-steward/Gena_Beeline_Local/python-ai-skills") == (
        "-home-bgs-ai-steward-Gena-Beeline-Local-python-ai-skills"
    )


def test_log_files_take_project_and_worktrees_but_not_sibling(tmp_path: Path) -> None:
    project = tmp_path / "work" / "Proj"
    project.mkdir(parents=True)
    base = session_hours.encode(str(project))
    for name in (base, base + "--claude-worktrees-feat", base + "-web"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "s.jsonl").write_text("")
    (tmp_path / base / "s1").mkdir()
    (tmp_path / base / "s1" / "sub.jsonl").write_text("")  # subagent transcript: skipped
    found = session_hours.log_files(str(project), root=tmp_path)
    assert sorted(f.parent.name for f in found) == sorted([base, base + "--claude-worktrees-feat"])


def test_working_hours_skips_breaks_and_clips_to_window() -> None:
    t0 = datetime(2026, 10, 15, 10, 0, tzinfo=timezone.utc)
    stamps = [t0 + timedelta(minutes=m) for m in (0, 5, 10, 40, 45, 200)]
    # gaps 5+5 counted, 30 is a break, 5 counted, 200 is outside the window
    assert session_hours.working_hours(stamps, t0, t0 + timedelta(minutes=60), timedelta(minutes=10)) == 0.25


def test_find_start_ignores_injected_text_and_respects_since(tmp_path: Path) -> None:
    def rec(ts: str, content: object) -> str:
        return json.dumps({"type": "user", "timestamp": ts, "message": {"content": content}})

    log = tmp_path / "s.jsonl"
    log.write_text(
        "\n".join(
            [
                rec("2026-10-01T08:00:00Z", "old release plan"),
                rec("2026-10-14T09:00:00Z", "<local-command-stdout>release</local-command-stdout>"),
                rec("2026-10-14T10:00:00Z", [{"type": "tool_result", "content": "release"}]),
                rec("2026-10-14T15:26:00Z", [{"type": "text", "text": "Можно выкатить release за два дня?"}]),
            ]
        )
    )
    since = datetime(2026, 10, 14, tzinfo=timezone.utc)
    hits = session_hours.find_start([log], "release", top=5, since=since)
    assert [h[0].hour for h in hits] == [15]


def test_time_view_inputs_are_validated() -> None:
    p = plan()
    p["updated"] = "19:10 15.10"
    p["work_window"] = [23, 10]
    p["stages"][0]["end"] = "15.10 18:00"  # before its start 18:59
    errors = "\n".join(render.validate(p))
    assert "updated must start with" in errors
    assert "work_window must be" in errors
    assert "end is earlier than start" in errors


def test_work_window_reaches_the_page() -> None:
    p = plan()
    p["work_window"] = [9, 21]
    assert '"work_window": [\n  9,\n  21\n ]' in render.render(p)
