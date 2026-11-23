"""Tests for lib/codex_parse.py."""
import json
import subprocess
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(LIB))
import codex_parse  # noqa: E402


def test_parse_raw_json():
    raw = '{"round": 1, "summary": {}, "findings": []}'
    assert codex_parse.parse(raw) == {"round": 1, "summary": {}, "findings": []}


def test_parse_strips_markdown_fences():
    raw = '```json\n{"round": 2, "summary": {}, "findings": []}\n```'
    assert codex_parse.parse(raw)["round"] == 2


def test_parse_extracts_first_balanced_object():
    raw = 'leading prose\n{"round": 3, "summary": {}, "findings": []}\ntrailing'
    assert codex_parse.parse(raw)["round"] == 3


def test_parse_unparseable_raises():
    import pytest
    with pytest.raises(ValueError):
        codex_parse.parse("not json at all")


def test_validate_rejects_bad_severity():
    import pytest
    bad = {"round": 1, "summary": {}, "findings": [{"severity": "blocker"}]}
    with pytest.raises(AssertionError):
        codex_parse.validate(bad)


def test_validate_rejects_missing_keys():
    import pytest
    with pytest.raises(AssertionError):
        codex_parse.validate({"round": 1})


def test_fingerprint_stable_and_8_chars():
    fp1 = codex_parse.fingerprint("M-PREPROC", "bug", "missing-await")
    fp2 = codex_parse.fingerprint("M-PREPROC", "bug", "missing-await")
    assert fp1 == fp2
    assert len(fp1) == 8


def test_fingerprint_differs_per_field():
    fp1 = codex_parse.fingerprint("M-A", "bug", "x")
    fp2 = codex_parse.fingerprint("M-B", "bug", "x")
    fp3 = codex_parse.fingerprint("M-A", "regression", "x")
    fp4 = codex_parse.fingerprint("M-A", "bug", "y")
    assert len({fp1, fp2, fp3, fp4}) == 4


def test_main_writes_fingerprints(tmp_path):
    p = tmp_path / "round-1.json"
    p.write_text(json.dumps({
        "round": 1,
        "summary": {"critical": 1, "medium": 0, "minor": 0},
        "findings": [{"severity": "critical", "module_id": "M-X", "category": "bug", "kind": "k"}],
    }))
    r = subprocess.run([sys.executable, str(LIB / "codex_parse.py"), str(p)], capture_output=True, text=True)
    assert r.returncode == 0
    data = json.loads(p.read_text())
    assert "fingerprint" in data["findings"][0]
    assert len(data["findings"][0]["fingerprint"]) == 8
