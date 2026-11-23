"""Tests for per-tool finding parsers."""
from pathlib import Path

from normalize_findings import parse_gitleaks, parse_mypy, parse_ruff


def test_parse_ruff_extracts_three_findings(golden_dir: Path):
    raw = (golden_dir / "ruff_concise.txt").read_text()
    findings = parse_ruff(raw)
    assert len(findings) == 3


def test_parse_ruff_first_finding_fields(golden_dir: Path):
    raw = (golden_dir / "ruff_concise.txt").read_text()
    f = parse_ruff(raw)[0]
    assert f["file"] == "src/processor/m2_preproc.py"
    assert f["line"] == 12
    assert f["rule_id"] == "F401"
    assert "imported but unused" in f["message_raw"]
    assert f["severity"] == "middle"


def test_parse_mypy_extracts_only_errors(golden_dir: Path):
    raw = (golden_dir / "mypy.txt").read_text()
    findings = parse_mypy(raw)
    assert len(findings) == 2   # the `note:` line is filtered


def test_parse_mypy_extracts_rule_in_brackets(golden_dir: Path):
    f = parse_mypy((golden_dir / "mypy.txt").read_text())[0]
    assert f["rule_id"] == "no-untyped-def"
    assert f["check_id"] == "03-mypy"
    assert f["file"] == "src/processor/m2_preproc.py"
    assert f["line"] == 42


def test_parse_gitleaks_extracts_two_critical(golden_dir: Path):
    raw = (golden_dir / "gitleaks.json").read_text()
    findings = parse_gitleaks(raw)
    assert len(findings) == 2
    assert all(f["severity"] == "critical" for f in findings)
    assert findings[0]["check_id"] == "04-gitleaks"
    assert findings[0]["rule_id"] == "aws-access-token"


from normalize_findings import parse_ai_section_json


def test_parse_ai_section_extracts_json_block(golden_dir):
    raw = (golden_dir / "ai_section_with_json.md").read_text()
    findings = parse_ai_section_json(raw)
    assert len(findings) == 2
    f0 = findings[0]
    assert f0["check_id"] == "ai-spec-conflict"
    assert f0["severity"] == "critical"
    assert f0["file"] == "src/processor/m2_preproc.py"
    assert f0["line"] == 17
