#!/usr/bin/env python3
"""Plan start and actual working hours from Claude Code session logs.

Usage:
  session_hours.py start --project PATH --pattern REGEX [--since "YYYY-MM-DD HH:MM"] [--tz ZONE] [--top N]
  session_hours.py hours --project PATH --from "YYYY-MM-DD HH:MM" --to "YYYY-MM-DD HH:MM"
                         [--tz ZONE] [--gap-min 10]

Logs are read from ~/.claude/projects/<encoded PATH> and every worktree
directory <encoded PATH>--claude-worktrees-*; <encoded PATH> is PATH with
each non-alphanumeric character replaced by "-". Matching the encoded path
exactly keeps a sibling project such as "<name>-web" out of the count.

start  — earliest user prompts whose text matches REGEX (case-insensitive);
         harness-injected text (<local-command…>, <command-…>, tool results)
         is ignored. --since drops older prompts: a project has many plans,
         and plan keywords recur in earlier ones.
hours  — sum of gaps between consecutive record timestamps of all sessions
         inside [from, to]; a gap longer than --gap-min is a break and does
         not count.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterator
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

LOG_ROOT = Path.home() / ".claude" / "projects"
INJECTED = ("<local-command", "<command-", "<system-reminder", "Caveat:", "Another Claude session sent a message")


def encode(project: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", str(Path(project).expanduser().resolve()))


def log_files(project: str, root: Path = LOG_ROOT) -> list[Path]:
    base = encode(project)
    dirs = [d for d in root.iterdir() if d.is_dir() and (d.name == base or d.name.startswith(base + "--claude-worktrees-"))]
    # Top-level session files only: subagent transcripts overlap their parent session in time.
    return sorted(f for d in dirs for f in d.glob("*.jsonl"))


def records(files: list[Path]) -> Iterator[tuple[datetime, dict, Path]]:
    for f in files:
        with f.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = rec.get("timestamp")
                if isinstance(ts, str):
                    yield datetime.fromisoformat(ts.replace("Z", "+00:00")), rec, f


def prompt_text(rec: dict) -> str:
    """Text the person typed; empty for tool results and harness-injected text."""
    if rec.get("type") != "user" or rec.get("isMeta"):
        return ""
    content = (rec.get("message") or {}).get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    else:
        return ""
    text = text.strip()
    return "" if text.startswith(INJECTED) else text


def find_start(files: list[Path], pattern: str, top: int, since: datetime | None = None) -> list[tuple[datetime, str, str]]:
    rx = re.compile(pattern, re.IGNORECASE)
    hits = [
        (ts, f.stem, txt)
        for ts, rec, f in records(files)
        if (since is None or ts >= since) and (txt := prompt_text(rec)) and rx.search(txt)
    ]
    return sorted(hits)[:top]


def working_hours(stamps: list[datetime], start: datetime, end: datetime, gap: timedelta) -> float:
    inside = sorted(t for t in stamps if start <= t <= end)
    total = sum(
        ((b - a) for a, b in zip(inside, inside[1:]) if b - a <= gap),
        timedelta(),
    )
    return total.total_seconds() / 3600


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("start", "hours"):
        p = sub.add_parser(name)
        p.add_argument("--project", required=True, help="project working directory")
        p.add_argument("--tz", default="Europe/Istanbul", help="owner time zone for input and output")
    sub.choices["start"].add_argument("--pattern", required=True)
    sub.choices["start"].add_argument("--top", type=int, default=5)
    sub.choices["start"].add_argument("--since", help="ignore prompts before this local time")
    sub.choices["hours"].add_argument("--from", dest="frm", required=True)
    sub.choices["hours"].add_argument("--to", required=True)
    sub.choices["hours"].add_argument("--gap-min", type=float, default=10.0)
    args = ap.parse_args(argv)

    tz = ZoneInfo(args.tz)
    files = log_files(args.project)
    if not files:
        print(f"no session logs for {args.project} under {LOG_ROOT}", file=sys.stderr)
        return 1
    if args.cmd == "start":
        since = datetime.strptime(args.since, "%Y-%m-%d %H:%M").replace(tzinfo=tz) if args.since else None
        hits = find_start(files, args.pattern, args.top, since)
        if not hits:
            print("no user prompt matches the pattern", file=sys.stderr)
            return 1
        for ts, session, text in hits:
            snippet = " ".join(text.split())[:140]
            print(f"{ts.astimezone(tz):%Y-%m-%d %H:%M} session {session[:8]}  {snippet}")
        return 0
    start = datetime.strptime(args.frm, "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    end = datetime.strptime(args.to, "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    stamps = [ts for ts, _, _ in records(files)]
    hours = working_hours(stamps, start, end, timedelta(minutes=args.gap_min))
    print(f"{hours:.2f} h of activity in {args.frm} → {args.to} ({args.tz}), breaks > {args.gap_min:g} min excluded, {len(files)} log files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
