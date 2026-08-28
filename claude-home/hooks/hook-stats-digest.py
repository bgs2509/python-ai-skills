#!/usr/bin/env python3
"""Weekly hook-journal digest (SessionStart hook).

Once per week, on the first session start after the period elapses, emits a
compact digest of ~/.claude/hook-stats/blocks.jsonl to stdout (SessionStart
stdout is injected into session context) and asks the model to flag
false-positive patterns. Silent on every other session start, silent when the
journal has no new records, and never blocks the session (all errors -> exit 0).

Marker file: ~/.claude/hook-stats/.last-digest (ISO timestamp of last digest).
"""
import collections
import datetime
import json
import pathlib
import sys

PERIOD_DAYS = 7
TOP_N = 5


def main() -> int:
    stats_dir = pathlib.Path.home() / ".claude" / "hook-stats"
    journal = stats_dir / "blocks.jsonl"
    marker = stats_dir / ".last-digest"
    now = datetime.datetime.now(datetime.timezone.utc)

    if not journal.is_file():
        return 0

    last = None
    if marker.is_file():
        try:
            last = datetime.datetime.fromisoformat(marker.read_text().strip())
        except ValueError:
            last = None
    if last is not None and (now - last).days < PERIOD_DAYS:
        return 0

    since = last or (now - datetime.timedelta(days=PERIOD_DAYS))
    per_hook = collections.Counter()
    details = collections.defaultdict(collections.Counter)
    total = 0
    for line in journal.read_text(errors="ignore").splitlines():
        try:
            rec = json.loads(line)
            ts = datetime.datetime.fromisoformat(rec["ts"])
        except (ValueError, KeyError):
            continue
        if ts < since:
            continue
        hook = rec.get("hook", "?")
        per_hook[hook] += 1
        total += 1
        for tok in rec.get("unverified", []) or []:
            details[hook][tok] += 1
        if rec.get("kind"):
            details[hook][rec["kind"]] += 1

    # Refresh the marker even when quiet, so the next digest window starts now.
    marker.write_text(now.isoformat(timespec="seconds") + "\n")

    if total == 0:
        return 0

    lines = [
        f"[hook-stats] Weekly digest: {total} hook block(s) since {since.date()}:"
    ]
    for hook, cnt in per_hook.most_common():
        top = ", ".join(f"{t}×{c}" for t, c in details[hook].most_common(TOP_N))
        lines.append(f"  - {hook}: {cnt}" + (f" (top: {top})" if top else ""))
    lines.append(
        "If any trigger looks like a false positive, tell the user and propose "
        "a concrete hook tweak (extend IGNORE/corpus, narrow a pattern). "
        "Full journal: ~/.claude/hook-stats/blocks.jsonl"
    )
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
