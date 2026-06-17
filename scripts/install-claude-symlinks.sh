#!/usr/bin/env bash
# Idempotent installer: link this repo's Claude config into ~/.claude.
# Re-runnable safely (ln -sfn). Computes paths from the script location, so it
# is portable across machines/users (no hard-coded $HOME). Bootstrap on a new
# machine: clone the repo, then run `make install-symlinks` (or this script).
#
# SSoT = this repo. ~/.claude becomes thin symlinks. Secrets and runtime state
# (.credentials.json, .claude.json, settings.local.json, settings.json, hooks/,
# projects/, sessions/, history.jsonl, cache/, ...) are NEVER touched.
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
link "$REPO/claude-home/CLAUDE.md" "$CLAUDE_HOME/CLAUDE.md"
link "$REPO/claude-home/RTK.md"    "$CLAUDE_HOME/RTK.md"
# AGENTS.md mirrors CLAUDE.md (Codex/cross-tool discovery)
ln -sfn "CLAUDE.md" "$CLAUDE_HOME/AGENTS.md"; echo "  $CLAUDE_HOME/AGENTS.md -> CLAUDE.md"

echo "[global config dirs]"
link "$REPO/claude-home/rules"         "$CLAUDE_HOME/rules"
link "$REPO/claude-home/output-styles" "$CLAUDE_HOME/output-styles"
link "$REPO/claude-home/hooks"         "$CLAUDE_HOME/hooks"
link "$REPO/claude-home/scripts"       "$CLAUDE_HOME/scripts"

# settings.json is RENDERED from a template (not symlinked): it needs absolute,
# per-machine paths for hook commands (Claude does not expand ~ in hook commands).
# Machine-specific keys (enabledPlugins, extraKnownMarketplaces) live in
# settings.local.json, which Claude deep-merges on top — this script never touches it.
echo "[settings.json] (rendered from template; machine-specific paths)"
tmpl="$REPO/claude-home/settings.json.template"
if [ -f "$tmpl" ]; then
  [ -f "$CLAUDE_HOME/settings.json" ] && cp "$CLAUDE_HOME/settings.json" "$CLAUDE_HOME/settings.json.bak"
  sed "s|{{CLAUDE_HOME}}|$CLAUDE_HOME|g" "$tmpl" > "$CLAUDE_HOME/settings.json"
  python3 -m json.tool "$CLAUDE_HOME/settings.json" >/dev/null \
    && echo "  rendered $CLAUDE_HOME/settings.json (valid JSON; backup: settings.json.bak)" \
    || { echo "  ERROR: rendered settings.json is invalid JSON — restoring backup" >&2; \
         [ -f "$CLAUDE_HOME/settings.json.bak" ] && cp "$CLAUDE_HOME/settings.json.bak" "$CLAUDE_HOME/settings.json"; exit 1; }
else
  echo "  (no template found — skipped)"
fi

echo "Done. Run a second time to confirm idempotency."
