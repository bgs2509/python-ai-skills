#!/usr/bin/env bash
# Scheduled entry point for hosts that pull updates before cleaning (vpn-2).
#
# The pull and the cleanup are deliberately two processes: a script that
# rewrites itself and then keeps going is half old and half new. Here the file
# being updated is never the file currently executing.
#
# Failing to update is not a reason to skip the cleanup — it runs on whatever
# version is already on disk.
#
# Usage: housekeeping-wrapper.sh [args passed through to housekeeping.py]

set -uo pipefail

REPO="${HOUSEKEEPING_REPO:-$HOME/works/python-ai-skills}"
SCRIPT="$REPO/claude-home/housekeeping/housekeeping.py"
LOG="$HOME/.claude/housekeeping.log"

log() {
    mkdir -p "$(dirname "$LOG")"
    printf '%s host=%s %s\n' "$(date --iso-8601=seconds)" "$(uname -n)" "$*" >>"$LOG"
}

if [ ! -d "$REPO/.git" ]; then
    log 'level=ERROR part=wrapper message="repository missing, cannot run"' \
        "repo=$REPO"
    exit 1
fi

if [ -n "$(git -C "$REPO" status --porcelain -- . 2>/dev/null)" ]; then
    # Resolving this automatically would mean discarding someone's edit.
    log 'part=wrapper action=skip-pull reason="local changes in the clone"'
elif ! pull_output=$(git -C "$REPO" pull --ff-only 2>&1); then
    log 'level=ERROR part=wrapper action=pull-failed' \
        "message=\"$(printf '%s' "$pull_output" | tr '\n' ' ' | cut -c1-200)\""
else
    log 'part=wrapper action=pull' \
        "message=\"$(printf '%s' "$pull_output" | tr '\n' ' ' | cut -c1-120)\""
fi

if [ ! -f "$SCRIPT" ]; then
    log 'level=ERROR part=wrapper message="cleanup script missing after update"' \
        "script=$SCRIPT"
    exit 1
fi

exec python3 "$SCRIPT" "$@"
