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
# The template puts CLAUDE_HOME inside single-quoted hook commands, inside JSON
# strings, through a `sed s|…|…|` substitution. Spaces are fine; these
# characters would break one of the three layers (bd python-ai-skills-4nb).
case "$CLAUDE_HOME" in
  *[\'\"\\\|\&]* | *$'\n'*)
    echo "ERROR: CLAUDE_HOME must not contain ' \" \\ | & or a newline: $CLAUDE_HOME" >&2
    exit 1 ;;
esac

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

# Install the same flat namespace in every enabled client. Validate the
# entire inventory and all destinations before writing any skill links.
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
PI_HOME="${PI_HOME:-$HOME/.pi/agent}"
skill_homes=("$CLAUDE_HOME/skills")
if [ -d "$CODEX_HOME" ]; then skill_homes+=("$CODEX_HOME/skills"); fi
if [ -d "$PI_HOME" ]; then skill_homes+=("$PI_HOME/skills"); fi

shopt -s nullglob
# Exactly one category level; resources and test fixtures cannot register skills.
skill_files=("$REPO"/Skills/*/*/SKILL.md)
shopt -u nullglob
if [ "${#skill_files[@]}" -eq 0 ]; then
  echo 'ERROR: no repo skills found' >&2
  exit 1
fi
seen=' '
for file in "${skill_files[@]}"; do
  d="${file%/*}"
  name="${d##*/}"
  declared=$(awk 'NR == 1 && $0 != "---" {exit} NR > 1 && $0 == "---" {exit} /^name: / {sub(/^name: +/, ""); print}' "$file")
  if ! [[ "$name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || [ "${#name}" -gt 64 ] || [ "$declared" != "$name" ]; then
    echo "ERROR: invalid skill directory or name: $file" >&2
    exit 1
  fi
  if [[ "$seen" == *" $name "* ]]; then
    echo "ERROR: duplicate skill name: $name" >&2
    exit 1
  fi
  seen+="$name "
  for home in "${skill_homes[@]}"; do
    dest="$home/$name"
    if [ -L "$dest" ]; then
      target=$(readlink "$dest")
      if [[ "$target" == "$d" || "$target" == "$REPO/$name" ]]; then
        continue
      fi
      previous="${target#"$REPO/Skills/"}"
      if [[ "$previous" != "$target" && "$previous" == */"$name" && "${previous%/*}" != */* ]]; then
        continue
      fi
    elif [ ! -e "$dest" ]; then
      continue
    elif [ -d "$dest" ] && [ "$FORCE" = 1 ]; then
      continue
    fi
    echo "ERROR: skill destination is not owned by this checkout: $dest" >&2
    exit 1
  done
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
# RTK.md and rules/ were folded into CLAUDE.md: Codex reads ~/.codex/AGENTS.md
# as one file, without @-imports or rules/. Drop their now-dangling links.
for l in "$CLAUDE_HOME/RTK.md" "$CLAUDE_HOME/rules"; do
  if [ -L "$l" ] && [ ! -e "$l" ]; then rm -f "$l"; echo "  removed dangling $l"; fi
done
# AGENTS.md mirrors CLAUDE.md (Codex/cross-tool discovery)
ln -sfn "CLAUDE.md" "$CLAUDE_HOME/AGENTS.md"; echo "  $CLAUDE_HOME/AGENTS.md -> CLAUDE.md"

# Codex reads skills from ~/.codex/skills. These links used to be made by hand,
# so 15 skills (do-*, best-*, git/sync) were missing and nothing regenerated
# them on a new machine; symlink-to-symlink chains like
# ~/.codex/skills/full-audit -> ~/.claude/skills/full-audit -> repo also broke
# whenever ~/.claude was rebuilt. Link straight from the repo, same list as
# Claude, one SSoT.
# Set CODEX_HOME=/dev/null (or any path without a skills dir) to opt out.
if [ -d "$CODEX_HOME" ]; then
  echo "[codex instructions]"
  link "$REPO/claude-home/CLAUDE.md" "$CODEX_HOME/AGENTS.md"
fi

echo "[global config dirs]"
link "$REPO/claude-home/output-styles" "$CLAUDE_HOME/output-styles"
link "$REPO/claude-home/hooks"         "$CLAUDE_HOME/hooks"
link "$REPO/claude-home/scripts"       "$CLAUDE_HOME/scripts"
# Configuration, so it is symlinked. The runtime state it drives
# (model-journal.jsonl, model-penalties.json) stays machine-local and uncommitted.
link "$REPO/claude-home/model-registry.json" "$CLAUDE_HOME/model-registry.json"
# RTK config (hook exclusions): lives under XDG, not ~/.claude.
link "$REPO/claude-home/rtk/config.toml" "${XDG_CONFIG_HOME:-$HOME/.config}/rtk/config.toml"

# settings.json is RENDERED from a template (not symlinked): it needs absolute,
# per-machine paths for hook commands (Claude does not expand ~ in hook commands).
# `extraKnownMarketplaces` lives in settings.local.json, which Claude deep-merges
# on top — this script never touches it.
#
# RUNTIME-OWNED KEYS. These keys are written into the live file by Claude itself:
#   model           — by `/model`
#   enabledPlugins  — by `claude plugin enable` (verified 2026-08-31: it writes
#                     to settings.json; the copy in settings.local.json is NOT
#                     honoured, which is why 3 enabled plugins loaded as disabled)
#   autoMode        — by `/auto-mode-setup` and the Auto mode tab of `/permissions`;
#                     the classifier reads it ONLY from ~/.claude/settings.json,
#                     never from settings.local.json (auto-mode-config docs)
#   modelSettings   — per-model effort, written by the effort control
#   voiceEnabled    — by the voice toggle
# All are carried over from the live file into each render and masked in the
# drift guard, so a UI-side change is neither flagged as a hand edit nor reverted.
# Orca also appends local hook groups, which must survive template upgrades.
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
  # Protect hand edits while allowing the known runtime-owned settings.
  base="$stamp"; [ -f "$base" ] || base="$new"
  if [ -f "$live" ] && ! python3 - "$new" "$live" "$base" "$FORCE" <<'PY'
import json
import sys
from pathlib import Path

new_p, live_p, base_p = map(Path, sys.argv[1:4])
force = sys.argv[4] == "1"
runtime_keys = ("model", "enabledPlugins", "autoMode", "modelSettings", "voiceEnabled")


def is_orca_handler(handler):
    command = handler.get("command", "")
    return (
        handler.get("type") == "command"
        and isinstance(command, str)
        and ".orca/agent-hooks/claude-hook.sh" in command
        and ("ORCA_AGENT_HOOK_PORT" in command or "ORCA_HOOK_AGENT_PID" in command)
    )


def separate_runtime(config):
    runtime = {key: config.pop(key) for key in runtime_keys if key in config}
    orca = {}
    hooks = config.get("hooks", {})
    for event, groups in list(hooks.items()):
        local = [group for group in groups if group.get("hooks") and all(
            is_orca_handler(h) for h in group["hooks"]
        )]
        if local:
            orca[event] = local
            shared = [group for group in groups if group not in local]
            if shared:
                hooks[event] = shared
            else:
                del hooks[event]
    return runtime, orca


try:
    new, live, base = (json.loads(p.read_text(encoding="utf-8")) for p in (new_p, live_p, base_p))
    runtime, orca = separate_runtime(live)
    separate_runtime(base)
except (OSError, ValueError, AttributeError, TypeError) as error:
    print(f"  ERROR: cannot compare existing Claude settings: {error}", file=sys.stderr)
    sys.exit(1)

if base != live:
    keys = ", ".join(sorted(k for k in base.keys() | live.keys() if k not in base or k not in live or base[k] != live[k]))
    if not force:
        print(f"  DRIFT: {live_p} differs from the last render (keys: {keys}).", file=sys.stderr)
        print("  Reconcile the shared settings before re-running; --force overwrites changes.", file=sys.stderr)
        sys.exit(1)
    print(f"  WARN: overwriting hand-edited settings (keys: {keys}); backup: settings.json.bak", file=sys.stderr)

new.update(runtime)
for event, groups in orca.items():
    handlers = new.setdefault("hooks", {}).setdefault(event, [])
    for group in groups:
        if group not in handlers:
            handlers.append(group)
new_p.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY
  then
    rm -f "$new"
    exit 1
  fi
  [ -f "$live" ] && cp "$live" "$live.bak"
  mv "$new" "$live"
  cp "$live" "$stamp"
  echo "  rendered $live (valid JSON; backup: settings.json.bak)"
else
  echo "  (no template found — skipped)"
fi

# Do not switch skills if the settings drift guard rejected the update.
for home in "${skill_homes[@]}"; do
  echo "[skills] $home"
  for file in "${skill_files[@]}"; do
    d="${file%/*}"
    link "$d" "$home/${d##*/}"
  done
  # Retire only links to this checkout's former underscore-prefixed directories.
  for name in adr architecture caching code-quality database docker docworkflow error-handling http init linters logging report security testing; do
    old="$home/_$name"
    if [ -L "$old" ] && [ "$(readlink "$old")" = "$REPO/_$name" ]; then
      rm -f "$old"
      echo "  retired $old"
    fi
  done
done

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
