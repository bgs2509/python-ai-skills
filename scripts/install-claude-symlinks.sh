#!/usr/bin/env bash
# Idempotent installer: link this repo's Claude config into ~/.claude.
# Re-runnable safely (ln -sfn). Computes paths from the script location, so it
# is portable across machines/users (no hard-coded $HOME). Bootstrap on a new
# machine: clone the repo, then run `make install-symlinks` (or this script).
#
# SSoT = this repo. ~/.claude becomes thin symlinks. Secrets and runtime state
# (.credentials.json, .claude.json, settings.local.json, projects/, sessions/,
# history.jsonl, cache/, ...) are NEVER touched. settings.json IS overwritten:
# it is rendered from claude-home/settings.json.template, guarded by a drift
# check that refuses to destroy hand edits (see the [settings.json] step).
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"

# --force replaces an existing REAL directory at a link path (e.g. migrating a
# machine that still has real skill dirs). Wrong symlinks and plain files are
# always replaced; only real directories require --force (rm -rf guard).
FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1

link() {  # link <target-in-repo> <link-path-in-claude-home>
  local target="$1" linkpath="$2"
  [ -e "$target" ] || { echo "MISSING target: $target" >&2; return 1; }
  mkdir -p "$(dirname "$linkpath")"
  if [ -L "$linkpath" ] && [ "$(readlink "$linkpath")" = "$target" ]; then
    return 0  # already correct
  fi
  if [ -L "$linkpath" ] || [ -f "$linkpath" ]; then
    rm -f "$linkpath"                                   # wrong symlink / file: safe
  elif [ -d "$linkpath" ]; then
    if [ "$FORCE" = "1" ]; then rm -rf "$linkpath"      # real dir: only with --force
    else echo "  SKIP (real dir; re-run with --force): $linkpath" >&2; return 0; fi
  fi
  ln -sfn "$target" "$linkpath"
  echo "  $linkpath -> $target"
}

echo "Repo:        $REPO"
echo "Claude home: $CLAUDE_HOME"

echo "[skills] (every repo dir containing SKILL.md)"
for d in "$REPO"/*/; do
  [ -f "${d}SKILL.md" ] || continue
  link "${d%/}" "$CLAUDE_HOME/skills/$(basename "$d")"
done

echo "[agents]"
for f in "$REPO"/agents/*.md; do
  [ -e "$f" ] || continue
  link "$f" "$CLAUDE_HOME/agents/$(basename "$f")"
done

echo "[commands]"
for f in "$REPO"/commands/*.md; do
  [ -e "$f" ] || continue
  link "$f" "$CLAUDE_HOME/commands/$(basename "$f")"
done

echo "[global instructions]"
link "$REPO/claude-home/CLAUDE.md"          "$CLAUDE_HOME/CLAUDE.md"
link "$REPO/claude-home/CLAUDE-APPENDIX.md" "$CLAUDE_HOME/CLAUDE-APPENDIX.md"
link "$REPO/claude-home/RTK.md"             "$CLAUDE_HOME/RTK.md"
# AGENTS.md mirrors CLAUDE.md (Codex/cross-tool discovery)
ln -sfn "CLAUDE.md" "$CLAUDE_HOME/AGENTS.md"; echo "  $CLAUDE_HOME/AGENTS.md -> CLAUDE.md"

# Codex reads skills from ~/.codex/skills. These links used to be made by hand,
# so 15 skills (do-*, best-*, git/sync) were missing and nothing regenerated
# them on a new machine; symlink-to-symlink chains like
# ~/.codex/skills/full-audit -> ~/.claude/skills/full-audit -> repo also broke
# whenever ~/.claude was rebuilt. Link straight from the repo, same list as
# Claude, one SSoT.
# Set CODEX_HOME=/dev/null (or any path without a skills dir) to opt out.
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
if [ -d "$CODEX_HOME" ]; then
  echo "[codex skills]"
  for d in "$REPO"/*/; do
    [ -f "${d}SKILL.md" ] || continue
    link "${d%/}" "$CODEX_HOME/skills/$(basename "$d")"
  done
fi

echo "[global config dirs]"
link "$REPO/claude-home/rules"         "$CLAUDE_HOME/rules"
link "$REPO/claude-home/output-styles" "$CLAUDE_HOME/output-styles"
link "$REPO/claude-home/hooks"         "$CLAUDE_HOME/hooks"
link "$REPO/claude-home/scripts"       "$CLAUDE_HOME/scripts"

# settings.json is RENDERED from a template (not symlinked): it needs absolute,
# per-machine paths for hook commands (Claude does not expand ~ in hook commands).
# `extraKnownMarketplaces` lives in settings.local.json, which Claude deep-merges
# on top — this script never touches it.
#
# RUNTIME-OWNED KEYS. Two keys are written into the live file by Claude itself:
#   model           — by `/model`
#   enabledPlugins  — by `claude plugin enable` (verified 2026-08-31: it writes
#                     to settings.json; the copy in settings.local.json is NOT
#                     honoured, which is why 3 enabled plugins loaded as disabled)
# Both are carried over from the live file into each render and masked in the
# drift guard, so a UI-side change is neither flagged as a hand edit nor reverted.
echo "[settings.json] (rendered from template; machine-specific paths)"
tmpl="$REPO/claude-home/settings.json.template"
if [ -f "$tmpl" ]; then
  live="$CLAUDE_HOME/settings.json"
  stamp="$CLAUDE_HOME/settings.json.rendered"   # copy of the previous render, for drift detection
  new="$(mktemp)"
  model="opus"
  if [ -f "$live" ]; then
    model="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("model") or "opus")' "$live" 2>/dev/null || echo opus)"
  fi
  sed -e "s|{{CLAUDE_HOME}}|$CLAUDE_HOME|g" -e "s|{{MODEL}}|$model|g" "$tmpl" > "$new"
  python3 -m json.tool "$new" >/dev/null \
    || { echo "  ERROR: template renders invalid JSON — nothing overwritten" >&2; rm -f "$new"; exit 1; }
  # Carry `enabledPlugins` over: which plugins are installed is machine-specific,
  # so the template does not declare it, but the runtime keeps it here.
  if [ -f "$live" ]; then
    python3 - "$new" "$live" <<'PY' || true
import json, sys
new_p, live_p = sys.argv[1], sys.argv[2]
try:
    live = json.load(open(live_p, encoding="utf-8"))
except Exception:
    sys.exit(0)
if "enabledPlugins" not in live:
    sys.exit(0)
new = json.load(open(new_p, encoding="utf-8"))
new["enabledPlugins"] = live["enabledPlugins"]
with open(new_p, "w", encoding="utf-8") as f:
    json.dump(new, f, indent=2, ensure_ascii=False)
    f.write("\n")
PY
  fi
  # Drift guard: refuse to destroy hand edits made to the live file since the
  # last render. Baseline = previous render if we have it, else the fresh one.
  # Runtime-owned keys are stripped on both sides before comparing (see above).
  base="$stamp"; [ -f "$base" ] || base="$new"
  strip_runtime() {  # canonical JSON without the keys Claude itself writes
    python3 -c 'import json,sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
for k in ("model", "enabledPlugins"):
    d.pop(k, None)
print(json.dumps(d, indent=2, sort_keys=True, ensure_ascii=False))' "$1" 2>/dev/null
  }
  if [ -f "$live" ] && ! diff -q <(strip_runtime "$base") <(strip_runtime "$live") >/dev/null 2>&1; then
    if [ "$FORCE" = "1" ]; then
      echo "  WARN: overwriting hand-edited $live (--force); backup: settings.json.bak" >&2
    else
      echo "  DRIFT: $live was edited by hand since the last render." >&2
      echo "  Backport the edits into claude-home/settings.json.template first," >&2
      echo "  or re-run with --force to overwrite them. Diff (baseline -> live):" >&2
      diff <(strip_runtime "$base") <(strip_runtime "$live") | sed 's/^/    /' >&2 || true
      rm -f "$new"; exit 1
    fi
  fi
  [ -f "$live" ] && cp "$live" "$live.bak"
  mv "$new" "$live"
  cp "$live" "$stamp"
  echo "  rendered $live (valid JSON; backup: settings.json.bak)"
else
  echo "  (no template found — skipped)"
fi

# git-template hook is COPIED, not symlinked: `git init` copies the template
# tree into every new repo, and a symlink there would break if the repo moves.
echo "[git-template]"
GIT_TMPL_SRC="$REPO/claude-home/git-template/pre-commit"
GIT_TMPL_DST="$HOME/.git-template/hooks/pre-commit"
if [ -f "$GIT_TMPL_SRC" ]; then
  mkdir -p "$(dirname "$GIT_TMPL_DST")"
  install -m 755 "$GIT_TMPL_SRC" "$GIT_TMPL_DST"
  echo "  installed $GIT_TMPL_DST"

  # This repo predates init.templatedir, so `git init` never copied the hook
  # here: the repo defining the security baseline was the only one committing
  # with no secret scan. The template only ever applies to NEW repos, so the
  # bootstrap hook is installed into this checkout explicitly. Any pre-existing
  # hook that is not this template is left alone (a project override wins).
  REPO_HOOK="$REPO/.git/hooks/pre-commit"
  if [ -d "$REPO/.git/hooks" ]; then
    if [ ! -e "$REPO_HOOK" ]; then
      install -m 755 "$GIT_TMPL_SRC" "$REPO_HOOK"
      echo "  installed $REPO_HOOK"
    elif cmp -s "$GIT_TMPL_SRC" "$REPO_HOOK"; then
      : # already the template, byte-identical — nothing to do
    elif grep -q 'Bootstrap pre-commit hook installed via ~/.git-template' "$REPO_HOOK" 2>/dev/null; then
      install -m 755 "$GIT_TMPL_SRC" "$REPO_HOOK"   # older copy of the template
      echo "  updated $REPO_HOOK"
    else
      echo "  SKIP $REPO_HOOK (project-specific hook, not the template)" >&2
    fi
  fi
fi

echo "Done. Run a second time to confirm idempotency."
