# Installing the python-pipeline Plugin

> Step-by-step instructions for installing the local `python-pipeline` plugin in Claude Code.
> For updating an already installed plugin, see [`docs/plugin-update.md`](plugin-update.md).

---

## Prerequisites

| Requirement | Check |
|-------------|-------|
| Claude Code CLI installed | `claude --version` |
| Git installed | `git --version` |
| Repository `python-ai-skills` cloned | `ls ~/Henry_Bud_GitHub/python-ai-skills/.claude-plugin/plugin.json` |

---

## Architecture: Plugin vs Skills

Before installing — it is important to understand that **the plugin and skills are different mechanisms**.

### What the plugin provides (`~/.claude/plugins/`)

The plugin registers **commands** and **agents**:
- `/pipeline` — from `commands/pipeline.md`
- `py-quality`, `py-security`, `py-doc-manager`, `py-test-writer`, `py-supervisor` — from `agents/*.md`

### What `~/.claude/skills/` provides

Skills (slash commands `/_docworkflow`, `/_code-quality`, etc.) are registered **separately** via symlinks in `~/.claude/skills/`. Without these symlinks, skills are **not visible** as slash commands, even if the plugin is installed.

### Full Structure

```
~/.claude/
├── settings.json                 # Global settings (permissions, hooks, plugins)
├── settings.local.json           # Accumulated permissions (created automatically)
├── skills/                       # ⚠️ Symlinks to skills (for /_* slash commands)
│   ├── _docworkflow → ~/Henry_Bud_GitHub/python-ai-skills/_docworkflow/
│   ├── _code-quality → ~/Henry_Bud_GitHub/python-ai-skills/_code-quality/
│   └── ... (15 skills)
└── plugins/
    ├── known_marketplaces.json   # Marketplace registry
    ├── installed_plugins.json    # Installed plugin metadata
    ├── config.json               # Configuration
    ├── local/                    # Symlinks to local plugins
    │   └── python-pipeline → ~/Henry_Bud_GitHub/python-ai-skills
    ├── cache/                    # Cache (working files that Claude Code reads)
    │   └── local-plugins/
    │       └── python-pipeline/
    │           └── 1.2.1/
    │               ├── commands/
    │               ├── agents/
    │               └── ...
    └── marketplaces/
```

**Key points:**
- **Plugin** (`plugins/`) → commands (`/pipeline`) and agents
- **Skills** (`skills/`) → slash commands (`/_docworkflow`, `/_code-quality`, etc.)
- `cache/` contains a **copy** of plugin files, tied to the **version** from `plugin.json`
- Claude Code reads files **only from cache**, not directly from the source
- **Both mechanisms are needed** for full functionality

---

## Installation Procedure

### Step 1. Clone the repository (if not already done)

```bash
cd ~/Henry_Bud_GitHub
git clone <repository-url> python-ai-skills
```

If the repository already exists — make sure it is on the current branch:

```bash
cd ~/Henry_Bud_GitHub/python-ai-skills
git pull
```

### Step 2. Register the local marketplace

A local marketplace is a directory where Claude Code looks for plugins. You need to add `~/.claude/plugins/local` as a marketplace named `local-plugins`:

```bash
claude plugins marketplace add local-plugins --directory ~/.claude/plugins/local
```

**Check:** after execution, `~/.claude/plugins/known_marketplaces.json` should contain an entry:

```json
{
  "local-plugins": {
    "source": {
      "source": "directory",
      "path": "/home/USER/.claude/plugins/local"
    }
  }
}
```

> **Note:** this step is performed **once**. When installing subsequent local plugins, the marketplace will already be registered.

### Step 3. Create a symlink to the plugin

Create a symbolic link from `~/.claude/plugins/local/` to the repository root:

```bash
mkdir -p ~/.claude/plugins/local
ln -s ~/Henry_Bud_GitHub/python-ai-skills ~/.claude/plugins/local/python-pipeline
```

**Important:** the symlink name (`python-pipeline`) must match the `name` field in `.claude-plugin/plugin.json`.

**Check:**

```bash
ls -la ~/.claude/plugins/local/python-pipeline
# Expected output:
# python-pipeline -> /home/USER/Henry_Bud_GitHub/python-ai-skills
```

### Step 4. Create skill symlinks

> **Without this step, skills `/_docworkflow`, `/_code-quality`, etc. will NOT be visible as slash commands.**

```bash
mkdir -p ~/.claude/skills

for skill in _adr _architecture _caching _code-quality _database _docker _docworkflow _error-handling _http _init _linters _logging _report _security _testing; do
  ln -s ~/Henry_Bud_GitHub/python-ai-skills/${skill}/ ~/.claude/skills/${skill}
done
```

**Check:**

```bash
ls -la ~/.claude/skills/
# Should show 15 symlinks, each pointing to the corresponding directory in python-ai-skills
```

Claude Code looks for skills in `~/.claude/skills/` and registers each folder with `SKILL.md` as a slash command.

### Step 5. Install the plugin

```bash
claude plugins install python-pipeline@local-plugins
```

This command:
1. Finds `python-pipeline` in the `local-plugins` marketplace
2. Reads `.claude-plugin/plugin.json` from the source
3. Copies plugin files to `~/.claude/plugins/cache/local-plugins/python-pipeline/<version>/`
4. Writes metadata to `~/.claude/plugins/installed_plugins.json`

**Expected output:**

```
✔ Installed python-pipeline@local-plugins (version 1.2.0)
```

### Step 6. Restart Claude Code

```bash
# Exit the current session
exit
# Start again
claude
```

Claude Code loads plugins at startup. Without a restart, the new plugin will not be visible.

### Step 7. Verify the installation

In a new Claude Code session:

```bash
claude plugins list
```

The plugin `python-pipeline@local-plugins` should be in the list with the current version.

Additional check — invoke the plugin command and a skill:

```
/pipeline          # Command from the plugin (commands/)
/_docworkflow      # Skill from ~/.claude/skills/
```

Both should be recognized. If `/pipeline` works but `/_docworkflow` does not, step 4 (skill symlinks) was skipped.

---

## Fresh Install (all commands)

For a quick install on a clean system — all steps in one block:

```bash
# 1. Clone the repository
cd ~/Henry_Bud_GitHub
git clone <repository-url> python-ai-skills

# 2. Register the local marketplace
claude plugins marketplace add local-plugins --directory ~/.claude/plugins/local

# 3. Create the plugin symlink
mkdir -p ~/.claude/plugins/local
ln -s ~/Henry_Bud_GitHub/python-ai-skills ~/.claude/plugins/local/python-pipeline

# 4. Create skill symlinks
mkdir -p ~/.claude/skills
for skill in _adr _architecture _caching _code-quality _database _docker _docworkflow _error-handling _http _init _linters _logging _report _security _testing; do
  ln -s ~/Henry_Bud_GitHub/python-ai-skills/${skill}/ ~/.claude/skills/${skill}
done

# 5. Install the plugin
claude plugins install python-pipeline@local-plugins

# 6. Restart Claude Code
```

---

## Choosing Scope: User vs Project

The plugin can be installed in two scopes:

| Scope | Flag | Action | When to use |
|-------|------|--------|-------------|
| `user` | (default) | Available in all projects | General development skills |
| `project` | `--scope project` | Only for the current project | Project-specific rules |

```bash
# Install for a specific project
claude plugins install python-pipeline@local-plugins --scope project
```

`python-pipeline` is recommended to install in `user` scope, as the skills are applicable to any Python project.

---

## Plugin Structure

The plugin is defined by the `.claude-plugin/plugin.json` file in the repository root:

```json
{
  "name": "python-pipeline",
  "version": "1.2.0",
  "description": "Python development pipeline — orchestrates 9 phases, 15 skills, 5 agents via Agent Teams",
  "author": { "name": "bgs" }
}
```

| Field | Description |
|-------|-------------|
| `name` | Unique plugin name. Must match the symlink name |
| `version` | Version in SemVer format. Used for caching |
| `description` | Description (displayed in `plugins list`) |
| `author` | Author information |

---

## Common Errors and Solutions

### Error 1: `Plugin "python-pipeline" not found`

**Symptom:**
```
Error: Plugin "python-pipeline" not found
```

**Causes and solutions:**

| Cause | Solution |
|-------|----------|
| Marketplace suffix not specified | Use `python-pipeline@local-plugins` |
| Marketplace `local-plugins` not registered | Execute step 2 (marketplace registration) |
| Symlink not created or points to wrong location | Check: `ls -la ~/.claude/plugins/local/python-pipeline` |
| Symlink name does not match `name` in `plugin.json` | Recreate symlink with the correct name |

**Diagnostics:**

```bash
# Check marketplace
cat ~/.claude/plugins/known_marketplaces.json | grep local-plugins

# Check symlink
ls -la ~/.claude/plugins/local/

# Check plugin.json
cat ~/.claude/plugins/local/python-pipeline/.claude-plugin/plugin.json
```

---

### Error 2: `Marketplace "local-plugins" not found`

**Symptom:**
```
Error: Marketplace "local-plugins" not found
```

**Cause:** local marketplace is not registered.

**Solution:**

```bash
claude plugins marketplace add local-plugins --directory ~/.claude/plugins/local
```

---

### Error 3: Broken symlink (dangling symlink)

**Symptom:** `ls -la` shows the symlink in red, or the install command cannot find `plugin.json`.

**Cause:** repository was moved or deleted.

**Solution:**

```bash
# Remove old symlink
rm ~/.claude/plugins/local/python-pipeline

# Create new one with the correct path
ln -s /actual/path/to/python-ai-skills ~/.claude/plugins/local/python-pipeline

# Verify
ls -la ~/.claude/plugins/local/python-pipeline
cat ~/.claude/plugins/local/python-pipeline/.claude-plugin/plugin.json
```

---

### Error 4: `Unknown skill: _docworkflow` (skills not visible as slash commands)

**Symptom:**
```
› Unknown skill: _docworkflow
```

Plugin is installed, `/pipeline` works, but `/_docworkflow`, `/_code-quality` and other skills with `_` prefix are not recognized.

**Cause:** the `~/.claude/skills/` directory with skill symlinks is missing. The plugin registers only commands (`/pipeline`) and agents, while skills are a **separate mechanism** via `~/.claude/skills/`.

**Solution:**

```bash
mkdir -p ~/.claude/skills

for skill in _adr _architecture _caching _code-quality _database _docker _docworkflow _error-handling _http _init _linters _logging _report _security _testing; do
  ln -s ~/Henry_Bud_GitHub/python-ai-skills/${skill}/ ~/.claude/skills/${skill}
done

# Restart Claude Code
```

**Check:**

```bash
ls ~/.claude/skills/
# Should show 15 symlinks
```

> **Important:** this is the most common error when installing on a new machine. Symlinks in `~/.claude/skills/` must be created on each machine separately — they are not transferred with the plugin.

---

### Error 5: Plugin is installed but `/pipeline` does not work

**Symptom:** `claude plugins list` shows the plugin, but `/pipeline` and other commands are not recognized.

**Causes and solutions:**

| Cause | Solution |
|-------|----------|
| Claude Code not restarted after installation | Restart Claude Code |
| Cache is corrupted | Clear cache and reinstall (see below) |
| Cache version is outdated | Run `claude plugins update python-pipeline@local-plugins` |

**Cache clearing and reinstallation:**

```bash
rm -rf ~/.claude/plugins/cache/local-plugins/python-pipeline
claude plugins install python-pipeline@local-plugins
# Restart Claude Code
```

---

### Error 6: `Permission denied` when creating symlink

**Cause:** no write permissions for `~/.claude/plugins/local/`.

**Solution:**

```bash
mkdir -p ~/.claude/plugins/local
# If still getting errors:
ls -la ~/.claude/plugins/ | grep local
# Ensure the directory is owned by the current user
```

---

### Error 7: Wrong version installed

**Symptom:** `claude plugins list` shows an old version.

**Cause:** version not updated in `.claude-plugin/plugin.json`, or there are uncommitted changes.

**Solution:**

```bash
# Check version in source
cat ~/Henry_Bud_GitHub/python-ai-skills/.claude-plugin/plugin.json

# Update to current version
claude plugins update python-pipeline@local-plugins

# Restart Claude Code
```

---

### Error 8: `already at the latest version` on first install

**Symptom:**
```
✔ python-pipeline is already at the latest version (1.2.0).
```

**Cause:** the plugin was already installed previously (possibly in another session or by another user).

**This is not an error** — the plugin is installed and up to date. Simply restart Claude Code if skills are not visible.

---

## Uninstalling the Plugin

```bash
# Remove from Claude Code
claude plugins uninstall python-pipeline@local-plugins

# Optional: remove symlink
rm ~/.claude/plugins/local/python-pipeline

# Optional: clear cache
rm -rf ~/.claude/plugins/cache/local-plugins/python-pipeline
```

---

## Diagnostics: Full Check

If something is not working — run all checks in order:

```bash
# 1. Is the marketplace registered?
cat ~/.claude/plugins/known_marketplaces.json | python3 -m json.tool

# 2. Does the plugin symlink exist and is it valid?
ls -la ~/.claude/plugins/local/python-pipeline
cat ~/.claude/plugins/local/python-pipeline/.claude-plugin/plugin.json

# 3. Does the cache exist?
ls ~/.claude/plugins/cache/local-plugins/python-pipeline/

# 4. Are metadata correct?
cat ~/.claude/plugins/installed_plugins.json | python3 -m json.tool

# 5. Does the cache version match the source?
# Source:
cat ~/Henry_Bud_GitHub/python-ai-skills/.claude-plugin/plugin.json
# Cache:
ls ~/.claude/plugins/cache/local-plugins/python-pipeline/

# 6. Do skill symlinks exist?
ls -la ~/.claude/skills/
# Should show 15 symlinks (_adr, _architecture, ..., _testing)
# Each should point to ~/Henry_Bud_GitHub/python-ai-skills/_*/
```

If any of the steps shows a problem — go back to the corresponding installation step.
