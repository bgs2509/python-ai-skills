#!/usr/bin/env python3
"""PID-based lock for audit-loop. Prevents concurrent runs in same repo."""
import json
import os
import sys
import time
from pathlib import Path

LOCK = Path("docs/audit-loop/.lock")


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def acquire() -> int:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        try:
            data = json.loads(LOCK.read_text())
            if _alive(data["pid"]):
                print(f"ERROR: audit-loop already running (pid={data['pid']}, since {data['ts']})", file=sys.stderr)
                return 2
        except (json.JSONDecodeError, KeyError):
            pass
        # stale lock, overwrite
    LOCK.write_text(json.dumps({"pid": os.getpid(), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}))
    print("ok")
    return 0


def release() -> int:
    if LOCK.exists():
        LOCK.unlink()
    print("ok")
    return 0


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ("acquire", "release"):
        print("usage: lock.py {acquire|release}", file=sys.stderr)
        return 2
    return acquire() if sys.argv[1] == "acquire" else release()


if __name__ == "__main__":
    sys.exit(main())
