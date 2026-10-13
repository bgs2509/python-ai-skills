#!/bin/bash
# git-finish-state.sh — the read-only state probe of /git-finish, in ONE call.
#
# /git-finish runs at the end of a session, when the session context is at its
# largest; every separate tool call re-reads that context (measured 2026-10-13:
# 12 requests per run, median ~400k tokens each). This script answers Phase 1.1's
# cross-check and all of Phase 2 in one call instead of five to seven.
#
#   git-finish-state.sh <repo-dir> [--base <branch>]
#
# Pass the directory explicitly (`.` is fine): the sandbox exclusion matches
# "git-finish-state.sh *", so a call without arguments would stay sandboxed and
# `git status` would list the sandbox's mount points as untracked files.
#
# Output: key=value lines, then three blocks (`--- status`, `--- log`,
# `--- bd in_progress`). Never writes anything; `git --no-optional-locks` keeps it
# off the index lock. Exit 0 always — every finding is in the output.

DIR="${1:-.}"
shift || true
BASE_ARG=""
while [ $# -gt 0 ]; do
    case "$1" in
        --base) BASE_ARG="${2:-}"; shift 2 ;;
        *) shift ;;
    esac
done

cd "$DIR" 2>/dev/null || { echo "mode=no-git"; echo "error=cannot enter $DIR"; exit 0; }

g() { git --no-optional-locks "$@" 2>/dev/null; }

if [ "$(g rev-parse --is-inside-work-tree)" != "true" ]; then
    echo "mode=no-git"
    exit 0
fi

BRANCH=$(g branch --show-current)
MAIN_ROOT=$(dirname "$(g rev-parse --path-format=absolute --git-common-dir)")
TOP=$(g rev-parse --show-toplevel)

# Base branch: explicit argument, then origin/HEAD, then main/master. Never trust
# `git rev-parse --abbrev-ref origin/HEAD` — it prints the literal "origin/HEAD"
# when the ref is not configured.
BASE="$BASE_ARG"
if [ -z "$BASE" ]; then
    BASE=$(g symbolic-ref --short refs/remotes/origin/HEAD | sed 's#^origin/##')
fi
if [ -z "$BASE" ]; then
    for b in main master; do
        if g show-ref --verify --quiet "refs/heads/$b"; then BASE=$b; break; fi
    done
fi

if [ -z "$BRANCH" ]; then
    MODE=detached
elif [ -n "$BASE" ] && [ "$BRANCH" = "$BASE" ]; then
    MODE=base
else
    MODE=branch
fi

# A linked worktree is removable only when it is not the main clone itself.
WORKTREE=""
if [ -n "$BRANCH" ] && [ "$TOP" != "$MAIN_ROOT" ]; then
    WORKTREE="$TOP"
fi

if g remote get-url origin >/dev/null; then
    REMOTE=yes
    if g ls-remote --exit-code --heads origin "$BRANCH" >/dev/null; then ON_REMOTE=yes; else ON_REMOTE=no; fi
    if g rev-parse --verify --quiet "origin/$BASE" >/dev/null; then
        AHEAD=$(g rev-list --count "origin/$BASE..$BASE")
    else
        AHEAD=unknown
    fi
else
    REMOTE=no; ON_REMOTE=no; AHEAD=unknown
fi

echo "mode=$MODE"
echo "branch=$BRANCH"
echo "base=$BASE"
echo "main_root=$MAIN_ROOT"
echo "worktree=$WORKTREE"
echo "remote=$REMOTE"
echo "branch_on_remote=$ON_REMOTE"
echo "ahead_of_origin=$AHEAD"
echo "--- status"
g status --porcelain
echo "--- log"
g log --oneline -20
echo "--- bd in_progress"
if command -v bd >/dev/null 2>&1; then
    bd list --status=in_progress 2>&1 | head -40
else
    echo "bd: not on PATH"
fi
exit 0
