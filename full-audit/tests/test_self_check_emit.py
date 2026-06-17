"""Tests for the shared self-check JSON emitter."""
import json
from pathlib import Path

from _self_check_emit import emit_finding, open_sidecar


def test_emit_finding_writes_one_line(tmp_path: Path):
    sidecar = tmp_path / "out.jsonl"
    with open_sidecar(sidecar) as f:
        emit_finding(f, "10-ssot-drift", "discovery.md", 1, "middle", "drift",
                     "FR-5 missing from requirements.xml")
    lines = sidecar.read_text().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["check_id"] == "10-ssot-drift"
    assert rec["file"] == "discovery.md"


def test_open_sidecar_with_none_is_noop(tmp_path: Path):
    """When sidecar path is None (flag not passed), emit_finding does nothing safely."""
    with open_sidecar(None) as f:
        assert f is None
        emit_finding(f, "10-ssot-drift", "x.md", 0, "middle", "drift", "msg")  # must not raise
