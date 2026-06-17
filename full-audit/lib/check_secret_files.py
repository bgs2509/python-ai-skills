#!/usr/bin/env python3
"""Verify no real secret files are tracked by git.

Allowlist (from global CLAUDE.md):
  - .env.example (any depth)
  - .env.*.example (any depth, e.g. .env.prod.example, .env.test.example)
  - tests/**/test.env, tests/**/*.testenv
Anything else matching secret patterns => FAIL.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from _self_check_emit import emit_finding, open_sidecar

PATTERNS = [
    re.compile(r"(^|/)\.env(\..+)?$"),
    re.compile(r".+\.pem$"),
    re.compile(r".+\.key$"),
    re.compile(r".+\.ppk$"),
    re.compile(r"(^|/)id_rsa(\..+)?$"),
    re.compile(r"(^|/)credentials\..+$"),
    re.compile(r"(^|/)\.netrc$"),
    re.compile(r"(^|/)\.npmrc$"),
]
ALLOW = [
    re.compile(r"(^|/)\.env\.example$"),
    re.compile(r"(^|/)\.env\.[^/]+\.example$"),
    re.compile(r"^tests/.*test\.env$"),
    re.compile(r"^tests/.*\.testenv$"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()
    try:
        out = subprocess.check_output(
            ["git", "ls-files"], text=True, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        print("not a git repo — skipped", file=sys.stderr)
        return 0
    bad: list[str] = []
    for path in out.splitlines():
        if not any(p.search(path) for p in PATTERNS):
            continue
        if any(a.search(path) for a in ALLOW):
            continue
        bad.append(path)
    if bad:
        print("Tracked files matching secret patterns (NOT in allowlist):")
        with open_sidecar(args.json_out) as sidecar:
            for p in bad:
                print(f"  {p}")
                emit_finding(
                    sidecar, "05-secret-files",
                    p, 0, "critical", "tracked-secret",
                    f"tracked file matches secret pattern: {p}",
                )
        return 1
    print("OK: no tracked secret files outside allowlist.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
