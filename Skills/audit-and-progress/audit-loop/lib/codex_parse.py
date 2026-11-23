#!/usr/bin/env python3
"""Parse and validate codex JSON output with fallbacks. Adds fingerprints."""
import hashlib
import json
import re
import sys
from pathlib import Path


def parse(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.S)
    if m:
        return json.loads(m.group(1))
    m = re.search(r"(\{[\s\S]*\})", raw)
    if m:
        return json.loads(m.group(1))
    raise ValueError("codex output not parseable as JSON")


def validate(data: dict) -> None:
    assert "round" in data and "summary" in data and "findings" in data, "missing top-level keys"
    for f in data["findings"]:
        assert f.get("severity") in ("critical", "medium", "minor"), f"bad severity: {f}"


def fingerprint(module_id: str | None, category: str, kind: str) -> str:
    return hashlib.sha1(f"{module_id}|{category}|{kind}".encode()).hexdigest()[:8]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: codex_parse.py <round-N.json>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    raw = path.read_text()
    try:
        data = parse(raw)
        validate(data)
    except (ValueError, AssertionError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    for f in data["findings"]:
        f["fingerprint"] = fingerprint(f.get("module_id"), f.get("category"), f.get("kind"))
    path.write_text(json.dumps(data, indent=2))
    print(json.dumps({"ok": True, "summary": data["summary"], "count": len(data["findings"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
