#!/usr/bin/env python3
"""Find all commits with a given fingerprint and propose a revert plan."""
import json
import subprocess
import sys
from pathlib import Path

STATE = Path("docs/audit-loop/state.json")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: revert_finding.py <fingerprint>", file=sys.stderr)
        return 2
    fp = sys.argv[1]
    state = json.loads(STATE.read_text())
    commits: list[tuple[int, str, str]] = []
    for r in state.get("rounds", []):
        for src in ("auto_applied", "asked"):
            for item in r.get(src, []):
                if item.get("fingerprint") == fp and item.get("commit_sha"):
                    commits.append((r["n"], src, item["commit_sha"]))
    if not commits:
        print(f"no commits found for fingerprint {fp}")
        return 0
    print(f"Commits touching fingerprint {fp}:")
    for n, src, sha in commits:
        try:
            subj = subprocess.check_output(["git", "log", "-1", "--format=%s", sha], text=True).strip()
        except subprocess.CalledProcessError:
            subj = "(commit not found)"
        print(f"  R{n} [{src}] {sha} {subj}")
    print("\nRevert plan (newest first):")
    for _, _, sha in reversed(commits):
        print(f"  git revert {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
