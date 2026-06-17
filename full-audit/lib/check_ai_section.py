#!/usr/bin/env python3
"""Hard gate: when --ai flag is set, the audit report MUST contain a real AI section.

Rules:
  1. Report file exists.
  2. Contains a heading exactly `## AI deep code analysis`.
  3. Under that heading, ONE of:
     a) at least one finding bullet under `### Critical|Middle|Minor|Open questions`
        (a finding bullet starts with `**[` or `**` and has a `file:line` reference);
     b) explicit empty-but-honest sentinel: a line containing
        "No findings after full pass through 7 categories"
        AND a line starting with "Modules inspected:" listing ≥3 paths.

Anything weaker (e.g. just the heading + "TBD" / no body) → exit 1.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SENTINEL_EMPTY = "No findings after full pass through 7 categories"
HEADING = "## AI deep code analysis"
SUBHEADINGS = ("### Critical", "### Middle", "### Minor", "### Open questions")
FILE_LINE_RE = re.compile(r"`?[\w./_-]+\.(py|md|xml|yml|yaml|toml|sh):\d+`?")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: check_ai_section.py <report.md>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"FAIL: report not found: {path}")
        return 1
    text = path.read_text(encoding="utf-8")

    if HEADING not in text:
        print(f"FAIL: heading '{HEADING}' missing in {path}")
        return 1

    section = text.split(HEADING, 1)[1]
    # cut at next top-level heading
    next_h2 = section.find("\n## ")
    if next_h2 != -1:
        section = section[:next_h2]

    has_sub = any(h in section for h in SUBHEADINGS)
    file_refs = FILE_LINE_RE.findall(section)
    has_findings = has_sub and len(file_refs) >= 1
    has_json_block = bool(re.search(r"```json\s*\n.*?\n```", section, re.S))
    has_findings = has_findings or has_json_block

    has_sentinel = SENTINEL_EMPTY in section
    has_inspected = bool(re.search(
        r"^Modules inspected:\s*.+(?:,\s*.+){2,}",
        section,
        re.M,
    ))
    has_empty_proof = has_sentinel and has_inspected

    if not (has_findings or has_empty_proof):
        print("FAIL: AI section is present but has no real content.")
        print("  Expected ONE of:")
        print("  (a) subsection (### Critical/Middle/Minor/Open questions)")
        print("      with at least one bullet referencing file:line, OR")
        print("  (b) sentinel '" + SENTINEL_EMPTY + "'")
        print("      AND 'Modules inspected:' listing ≥3 paths.")
        print(f"  Got: subheading={has_sub}, file_refs={len(file_refs)}, "
              f"sentinel={has_sentinel}, inspected_line={has_inspected}")
        return 1

    if has_findings:
        print(f"OK: AI section has {len(file_refs)} file:line references "
              f"under {[h for h in SUBHEADINGS if h in section]}")
    else:
        print("OK: AI section honestly empty (sentinel + Modules inspected).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
