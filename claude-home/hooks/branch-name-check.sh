#!/usr/bin/env bash
# PreToolUse launcher: all logic is in branch-name-check.py (python3 -I: no planted modules).
exec /usr/bin/env python3 -I "$(dirname "$0")/branch-name-check.py"
