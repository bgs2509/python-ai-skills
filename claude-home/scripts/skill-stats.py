#!/usr/bin/env python3
"""skill-stats.py — attribute Claude Code token spend to skills.

Reads the session transcripts Claude Code keeps under ~/.claude/projects and
answers: which skills run, how often, how many tokens each one consumes, what
that costs at API prices, and which models their subagents use.

Attribution windows. A skill window opens at a Skill tool call or a /command.
  low bound  — closes at the next human-typed message or the next skill;
  high bound — closes only at the next skill or the end of the session.
Built-in commands are not skills; /clear closes every window. Each API
response is counted once (deduplicated by message id + request id).
Subagent transcripts belong to the skill open in the parent session when the
subagent started.

Facts only: every number is counted from transcript lines. The one external
constant is the price table (PRICES), with its source and date. Cost is the
API-equivalent; on a subscription it is a share of the quota, not a bill.

  skill-stats.py [--projects PATH] [--since DAYS] [--top N] [--json]
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

# $/MTok: (input, 5m cache write, 1h cache write, cache read, output).
# Source: https://platform.claude.com/docs/en/about-claude/pricing, read 2026-10-13.
PRICES = {
    "claude-fable-5-1": (10, 12.5, 20, 0.25, 50),
    "claude-fable-5": (10, 12.5, 20, 1.00, 50),
    "claude-opus-5-5": (4, 5, 8, 0.20, 20),
    "claude-opus-5": (5, 6.25, 10, 0.50, 25),
    "claude-opus-4-8": (5, 6.25, 10, 0.50, 25),
    "claude-sonnet-5-5": (2, 2.5, 4, 0.10, 10),
    "claude-sonnet-5": (2, 2.5, 4, 0.20, 10),
    "claude-haiku-5-5": (0.10, 0.125, 0.20, 0.01, 0.50),
    "claude-haiku-4-5-20251001": (1, 1.25, 2, 0.10, 5),
}
# Haiku 5.5 bills prompts over 100k tokens at a higher tier.
LONG_PROMPT_TIER = {"claude-haiku-5-5": (100_000, (0.50, 0.625, 1.00, 0.05, 2.50))}

BUILTINS = {
    "add-dir", "agents", "clear", "compact", "config", "context", "cost", "doctor", "effort",
    "exit", "fast", "help", "hooks", "ide", "login", "logout", "mcp", "memory", "model",
    "permissions", "plugin", "rename", "resume", "sandbox", "status", "theme", "usage",
    "usage-credits", "voice",
}
CMD_RE = re.compile(r"<command-name>/?([^<\s]+)</command-name>")
NOT_HUMAN = ("<", "Base directory for this skill", "[Request interrupted", "Caveat:")
TOKEN_FIELDS = ("input", "cache_write", "cache_read", "output")


CONTROL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def default_projects() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECTS_DIR", os.path.expanduser("~/.claude/projects")))


def quantile(values: list[float], q: float) -> float:
    """Nearest-rank quantile — no interpolation, no numpy dependency."""
    if not values:
        return 0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, round(q * (len(ordered) - 1))))
    return ordered[idx]


def parse_ts(value) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError):
        return None


def as_int(value) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def message_text(content) -> tuple[str, bool]:
    """Text of a user message and whether it carries a tool result."""
    if isinstance(content, str):
        return content, False
    parts, has_result = [], False
    for block in content if isinstance(content, list) else []:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "tool_result":
            has_result = True
        elif block.get("type") == "text" and isinstance(block.get("text"), str):
            parts.append(block["text"])
    return "\n".join(parts), has_result


def usage_event(record: dict, msg: dict, usage: dict) -> dict:
    split = usage.get("cache_creation")
    split = split if isinstance(split, dict) else {}
    return {
        "kind": "usage",
        "ts": record.get("timestamp", ""),
        "key": (msg.get("id"), record.get("requestId")),
        "model": str(msg.get("model", "?")),
        "input": as_int(usage.get("input_tokens")),
        "cache_write": as_int(usage.get("cache_creation_input_tokens")),
        "cache_write_1h": as_int(split.get("ephemeral_1h_input_tokens")),
        "cache_read": as_int(usage.get("cache_read_input_tokens")),
        "output": as_int(usage.get("output_tokens")),
    }


def records(path: Path):
    """Parsed JSON objects of one transcript. A truncated or non-object line, or a
    file that vanished after the directory walk, never breaks the report."""
    try:
        with path.open(errors="ignore") as fh:
            for line in fh:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if isinstance(record, dict):
                    yield record
    except OSError:
        return


def first_timestamp(path: Path) -> str:
    return next((r["timestamp"] for r in records(path) if isinstance(r.get("timestamp"), str)), "")


def scan(path: Path):
    """Yield skill / human / usage events of one transcript, in file order."""
    for record in records(path):
        msg = record.get("message")
        msg = msg if isinstance(msg, dict) else {}
        ts = record.get("timestamp", "")
        if record.get("type") == "assistant":
            content = msg.get("content")
            # The response that calls a skill belongs to that skill's window.
            for block in content if isinstance(content, list) else []:
                if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Skill":
                    args = block.get("input")
                    name = str(args.get("skill", "?")) if isinstance(args, dict) else "?"
                    key = block.get("id") or (msg.get("id"), name)
                    yield {"kind": "skill", "ts": ts, "name": name, "via": "tool", "key": key}
            usage = msg.get("usage")
            if isinstance(usage, dict):
                yield usage_event(record, msg, usage)
        elif record.get("type") == "user" and not record.get("isMeta"):
            text, has_result = message_text(msg.get("content"))
            command = CMD_RE.search(text)
            if command:
                key = record.get("uuid") or (ts, command.group(1))
                yield {"kind": "skill", "ts": ts, "name": command.group(1), "via": "slash", "key": key}
            elif not has_result and text.strip() and not text.lstrip().startswith(NOT_HUMAN):
                yield {"kind": "human", "ts": ts}


def cost_usd(ev: dict) -> float | None:
    price = PRICES.get(ev["model"])
    if price is None:
        return None
    tier = LONG_PROMPT_TIER.get(ev["model"])
    if tier and ev["input"] + ev["cache_read"] + ev["cache_write"] > tier[0]:
        price = tier[1]
    p_in, p_w5, p_w1, p_read, p_out = price
    write_1h = min(ev["cache_write_1h"], ev["cache_write"])
    return (ev["input"] * p_in + (ev["cache_write"] - write_1h) * p_w5 + write_1h * p_w1
            + ev["cache_read"] * p_read + ev["output"] * p_out) / 1e6


def new_skill() -> dict:
    return {
        "calls": 0, "tool_calls": 0, "slash_calls": 0, "sessions": set(),
        "tokens_low": 0, "tokens_high": 0, "non_cache_read_low": 0, "output_low": 0,
        "subagent_tokens": 0, "cost_usd": 0.0, "per_call": [],
        "subagent_models": defaultdict(lambda: {"calls": 0, "tokens": 0}),
    }


def is_subagent(path: Path, root: Path) -> bool:
    """`<root>/<project>/<session>/subagents/<agent>.jsonl` — judged relative to the
    root, so a `subagents` directory above it never reclassifies main transcripts."""
    parts = path.relative_to(root).parts
    return len(parts) >= 2 and parts[-2] == "subagents"


def collect(projects: Path, since_days: float | None = None) -> dict:
    """Walk every transcript under `projects` and attribute its usage.

    Window state is always rebuilt from the whole transcript; `since_days` only
    decides which calls and tokens are counted, so a window opened before the
    period still owns usage inside it."""
    cutoff = None
    if since_days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

    def counted(ts) -> bool:
        if cutoff is None:
            return True
        parsed = parse_ts(ts)
        return parsed is not None and parsed >= cutoff

    files = sorted(projects.glob("**/*.jsonl"))
    mains = [f for f in files if not is_subagent(f, projects)]
    subs = [f for f in files if is_subagent(f, projects)]

    skills: dict[str, dict] = defaultdict(new_skill)
    windows: dict[str, list] = defaultdict(list)  # session id -> [(ts, skill, call)]
    by_model = {"main": defaultdict(lambda: {"calls": 0, "tokens": 0, "cost_usd": 0.0}),
                "subagent": defaultdict(lambda: {"calls": 0, "tokens": 0, "cost_usd": 0.0})}
    totals = {f: 0 for f in TOKEN_FIELDS} | {"cost_usd": 0.0, "unpriced_tokens": 0}
    first_ctx = {"main": [], "subagent": []}
    seen_usage: set = set()
    seen_skill: set = set()

    def account(ev: dict, side: str) -> tuple[int, float]:
        tokens = sum(ev[f] for f in TOKEN_FIELDS)
        cost = cost_usd(ev)
        for f in TOKEN_FIELDS:
            totals[f] += ev[f]
        if cost is None:
            totals["unpriced_tokens"] += tokens
            cost = 0.0
        totals["cost_usd"] += cost
        m = by_model[side][ev["model"]]
        m["calls"] += 1
        m["tokens"] += tokens
        m["cost_usd"] += cost
        return tokens, cost

    def charge_low(name: str, call: list, ev: dict, tokens: int, cost: float) -> None:
        s = skills[name]
        s["tokens_low"] += tokens
        s["non_cache_read_low"] += tokens - ev["cache_read"]
        s["output_low"] += ev["output"]
        s["cost_usd"] += cost
        call[0] += tokens

    def first_request(side: str, ev: dict) -> None:
        if counted(ev["ts"]):
            first_ctx[side].append(ev["input"] + ev["cache_read"] + ev["cache_write"])

    for path in mains:
        sid = path.stem
        low = high = call = None
        first_done = False
        for ev in scan(path):
            if ev["kind"] == "skill":
                if ev["key"] in seen_skill:
                    continue
                seen_skill.add(ev["key"])
                if ev["name"] in BUILTINS:
                    # A built-in typed by the human ends the low window; /clear ends both.
                    low = call = None
                    if ev["name"] == "clear":
                        high = None
                    windows[sid].append((ev["ts"], None, None))
                    continue
                low = high = ev["name"]
                call = [0]
                if counted(ev["ts"]):
                    s = skills[low]
                    s["calls"] += 1
                    s[f"{ev['via']}_calls"] += 1
                    s["sessions"].add(sid)
                    s["per_call"].append(call)
                windows[sid].append((ev["ts"], low, call))
            elif ev["kind"] == "human":
                low = call = None
                windows[sid].append((ev["ts"], None, None))
            else:
                if ev["key"] in seen_usage:
                    continue
                seen_usage.add(ev["key"])
                if not first_done:
                    first_request("main", ev)
                    first_done = True
                if not counted(ev["ts"]):
                    continue
                tokens, cost = account(ev, "main")
                if low:
                    charge_low(low, call, ev, tokens, cost)
                if high:
                    skills[high]["tokens_high"] += tokens

    for path in subs:
        sid = path.parent.parent.name
        start = first_timestamp(path)
        owner = call = None
        for ts, name, ref in windows.get(sid, []):
            if ts and ts <= start:
                owner, call = name, ref
        first_done = False
        for ev in scan(path):
            if ev["kind"] != "usage" or ev["key"] in seen_usage:
                continue
            seen_usage.add(ev["key"])
            if not first_done:
                first_request("subagent", ev)
                first_done = True
            if not counted(ev["ts"]):
                continue
            tokens, cost = account(ev, "subagent")
            if owner:
                charge_low(owner, call, ev, tokens, cost)
                s = skills[owner]
                s["subagent_tokens"] += tokens
                s["tokens_high"] += tokens
                mix = s["subagent_models"][ev["model"]]
                mix["calls"] += 1
                mix["tokens"] += tokens

    return {"skills": skills, "by_model": by_model, "totals": totals, "first_ctx": first_ctx,
            "files": {"main": len(mains), "subagent": len(subs)}}


def summarize(raw: dict) -> dict:
    rows = []
    for name, s in raw["skills"].items():
        per_call = [c[0] for c in s["per_call"]]
        rows.append({
            "skill": name,
            "calls": s["calls"], "tool_calls": s["tool_calls"], "slash_calls": s["slash_calls"],
            "sessions": len(s["sessions"]),
            "tokens_low": s["tokens_low"], "tokens_high": s["tokens_high"],
            "non_cache_read_low": s["non_cache_read_low"], "output_low": s["output_low"],
            "subagent_tokens": s["subagent_tokens"],
            "per_call_median": quantile(per_call, 0.5), "per_call_p90": quantile(per_call, 0.9),
            "cost_usd": round(s["cost_usd"], 6),
            "subagent_models": {m: dict(v) for m, v in s["subagent_models"].items()},
        })
    rows.sort(key=lambda r: -r["tokens_low"])
    t = raw["totals"]
    tokens = sum(t[f] for f in TOKEN_FIELDS)
    totals = {
        "tokens": tokens, "cache_read": t["cache_read"], "output": t["output"],
        "cache_read_share": t["cache_read"] / tokens if tokens else 0.0,
        "cost_usd": round(t["cost_usd"], 6), "unpriced_tokens": t["unpriced_tokens"],
    }
    by_model = {side: {m: {**v, "cost_usd": round(v["cost_usd"], 6)} for m, v in models.items()}
                for side, models in raw["by_model"].items()}
    first = {side: {"count": len(v), "median": quantile(v, 0.5), "p90": quantile(v, 0.9)}
             for side, v in raw["first_ctx"].items()}
    return {"files": raw["files"], "totals": totals, "by_model": by_model,
            "first_request_context": first, "skills": rows}


def clean(text: str) -> str:
    """Skill and model names come from transcripts: never let them drive the terminal."""
    return CONTROL_RE.sub("?", str(text))


def millions(n: float) -> str:
    return f"{n / 1e6:,.1f}M"


def render(stats: dict, top: int) -> str:
    t = stats["totals"]
    out = [
        f"Transcripts: {stats['files']['main']} main, {stats['files']['subagent']} subagent",
        f"Tokens: {millions(t['tokens'])} (cache reads {t['cache_read_share']:.0%}), "
        f"API-equivalent ${t['cost_usd']:,.0f}, unpriced {millions(t['unpriced_tokens'])}",
    ]
    for side, f in stats["first_request_context"].items():
        out.append(f"First-request context, {side}: median {f['median']:,} p90 {f['p90']:,} (n={f['count']})")
    out.append("")
    out.append(f"{'skill':<34}{'calls':>6}{'sess':>5}{'low':>10}{'high':>10}"
               f"{'median/call':>13}{'p90/call':>11}{'subagent':>10}{'cost $':>9}")
    for r in stats["skills"][:top]:
        out.append(f"{clean(r['skill'])[:33]:<34}{r['calls']:>6}{r['sessions']:>5}{millions(r['tokens_low']):>10}"
                   f"{millions(r['tokens_high']):>10}{millions(r['per_call_median']):>13}"
                   f"{millions(r['per_call_p90']):>11}{millions(r['subagent_tokens']):>10}{r['cost_usd']:>9,.0f}")
        if r["subagent_models"]:
            mix = ", ".join(f"{clean(m)} {v['calls']}" for m, v in
                            sorted(r["subagent_models"].items(), key=lambda kv: -kv[1]["tokens"]))
            out.append(f"{'':<4}subagent models: {mix}")
    return "\n".join(out)


def non_negative_days(value: str) -> float:
    days = float(value)
    if not math.isfinite(days) or days < 0:
        raise argparse.ArgumentTypeError(f"expected a finite number of days >= 0, got {value!r}")
    return days


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError(f"expected an integer >= 1, got {value!r}")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--projects", type=Path, default=default_projects(), help="transcripts root")
    parser.add_argument("--since", type=non_negative_days, metavar="DAYS", help="only events newer than this")
    parser.add_argument("--top", type=positive_int, default=25, help="rows in the text report")
    parser.add_argument("--json", action="store_true", help="machine-readable output, all rows")
    args = parser.parse_args(argv)
    if not args.projects.is_dir():
        parser.error(f"--projects: not a readable directory: {args.projects}")

    stats = summarize(collect(args.projects, args.since))
    print(json.dumps(stats, indent=2) if args.json else render(stats, args.top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
