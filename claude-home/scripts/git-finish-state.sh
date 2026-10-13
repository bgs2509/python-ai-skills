#!/bin/bash
# git-finish-state.sh — the read-only state probe of /git-finish, in one call.
#
# /git-finish runs at the end of a session, when the session context is at its
# largest; every separate tool call re-reads that context (measured 2026-10-13:
# 12 requests per run, median ~400k tokens each). This script answers Phase 2 and
# most of Phase 1.1 in one call.
#
#   git-finish-state.sh [<repo-dir>] [--base <branch>]
#
# It runs INSIDE the Bash sandbox on purpose (external review 2026-10-13): a
# sandbox exclusion would point at a file anyone can edit, and git executes
# commands from a repository's own config (core.fsmonitor, core.sshCommand). So
# it never touches the network — the remote state comes from local
# remote-tracking refs, i.e. as of the last fetch — and it does not print
# `git status`, which lists the sandbox's mount points as untracked files when
# sandboxed. Run plain `git status --porcelain` as a separate call for that.
#
# Output: key=value lines (always the same keys), then `--- log` and
# `--- bd in_progress`. A failing git command is reported as `error=...`, never
# turned into a plausible empty value. Never writes anything; exit 0 always.

DIR="."
BASE_ARG=""
while [ $# -gt 0 ]; do
    case "$1" in
        --base)
            if [ -n "${2:-}" ]; then BASE_ARG="$2"; shift 2; else echo "error=--base needs a value"; shift; fi ;;
        -*) DIR="./$1"; shift ;;   # bash `cd -- -` still means $OLDPWD
        *) DIR="$1"; shift ;;
    esac
done

MODE=""; BRANCH=""; BASE=""; MAIN_ROOT=""; WORKTREE=""; REMOTE=""; ON_REMOTE=""; AHEAD=""
ERRORS=()
LOG=""

emit() {
    echo "mode=$MODE"
    echo "branch=$BRANCH"
    echo "base=$BASE"
    echo "main_root=$MAIN_ROOT"
    echo "worktree=$WORKTREE"
    echo "remote=$REMOTE"
    echo "branch_on_remote=$ON_REMOTE"
    echo "ahead_of_origin=$AHEAD"
    for e in "${ERRORS[@]}"; do echo "error=$e"; done
    echo "--- log"
    [ -n "$LOG" ] && echo "$LOG"
    echo "--- bd in_progress"
    if command -v bd >/dev/null 2>&1; then
        bd list --status=in_progress 2>&1
    else
        echo "bd: not on PATH"
    fi
    exit 0
}

g() { git --no-optional-locks "$@"; }

if ! cd -- "$DIR" 2>/dev/null; then
    MODE=no-git; ERRORS+=("cannot enter $DIR"); emit
fi
if [ "$(g rev-parse --is-inside-work-tree 2>/dev/null)" != "true" ]; then
    MODE=no-git; emit
fi

BRANCH=$(g branch --show-current 2>/dev/null)
TOP=$(g rev-parse --show-toplevel 2>/dev/null)
GIT_DIR_ABS=$(g rev-parse --path-format=absolute --git-dir 2>/dev/null)
COMMON_DIR=$(g rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
# A linked worktree has its own git dir (.git/worktrees/<name>) apart from the
# common one; the main working tree does not — whatever the repository layout
# (with --separate-git-dir neither `dirname` of the common dir nor the first
# `git worktree list` entry is the working tree).
LINKED=no
if [ -n "$GIT_DIR_ABS" ] && [ -n "$COMMON_DIR" ] && [ "$GIT_DIR_ABS" != "$COMMON_DIR" ]; then
    LINKED=yes
    MAIN_ROOT=$(g worktree list --porcelain 2>/dev/null | awk '/^worktree /{print substr($0, 10); exit}')
    [ -z "$MAIN_ROOT" ] && ERRORS+=("git worktree list failed")
else
    MAIN_ROOT="$TOP"
fi

# Base branch: explicit argument, then origin/HEAD, then main/master. Never trust
# `git rev-parse --abbrev-ref origin/HEAD` — it prints the literal "origin/HEAD"
# when the ref is not configured.
BASE="$BASE_ARG"
[ -z "$BASE" ] && BASE=$(g symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')
if [ -z "$BASE" ]; then
    for b in main master; do
        if g show-ref --verify --quiet "refs/heads/$b"; then BASE=$b; break; fi
    done
fi

if [ -z "$BRANCH" ]; then
    MODE=detached
elif [ -z "$BASE" ]; then
    MODE=unknown-base          # ask the user, or pass --base
elif [ "$BRANCH" = "$BASE" ]; then
    MODE=base
else
    MODE=branch
fi

# Only a linked worktree is removable; the main working tree never is.
if [ -n "$BRANCH" ] && [ "$LINKED" = yes ]; then
    WORKTREE="$TOP"
fi

if g remote get-url origin >/dev/null 2>&1; then
    REMOTE=yes
    if [ -n "$BRANCH" ] && g show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
        ON_REMOTE=yes
    else
        ON_REMOTE=no
    fi
    if [ -n "$BASE" ] && g show-ref --verify --quiet "refs/remotes/origin/$BASE"; then
        AHEAD=$(g rev-list --count "origin/$BASE..$BASE" 2>/dev/null) || { AHEAD=unknown; ERRORS+=("git rev-list failed"); }
    else
        AHEAD=unknown
    fi
else
    REMOTE=no; ON_REMOTE=no; AHEAD=unknown
fi

if ! LOG=$(g log --oneline -20 2>&1); then
    ERRORS+=("git log failed: ${LOG%%$'\n'*}"); LOG=""
fi
emit
