# Updating the python-pipeline Plugin

> Instructions for AI and user. Execute **after every change** to skills, commands, agents, or plugin.json.

---

## Why This Is Needed

Claude Code caches plugins in `~/.claude/plugins/cache/local-plugins/python-pipeline/`.
The cache is tied to the **version** from `.claude-plugin/plugin.json`, not to file contents.
Without a version bump, changes in source files **are not applied**.

---

## Update Procedure

### Step 1. Bump the version

File: `.claude-plugin/plugin.json`, field `version`.

Versioning scheme (SemVer):

| Change type | Example | When |
|-------------|---------|------|
| Patch | `1.0.0` → `1.0.1` | Fixes, minor text edits |
| Minor | `1.0.0` → `1.1.0` | New skill, command, pipeline phase |
| Major | `1.0.0` → `2.0.0` | Breaking changes in format/structure |

### Step 2. Commit changes

```bash
git add -A
git commit -m "chore: bump plugin version to X.Y.Z"
```

### Step 3. Update the plugin cache

```bash
claude plugins update python-pipeline@local-plugins
```

The plugin name **must** include the `@local-plugins` suffix. Without it — "not found" error.

### Step 4. Restart Claude Code

The current session uses the cache loaded at startup. The new cache will only be picked up after a restart.

---

## Emergency Update (without version bump)

If you need to apply changes without bumping the version:

```bash
rm -rf ~/.claude/plugins/cache/local-plugins/python-pipeline
```

Then restart Claude Code. The cache will be recreated from source.

**Drawback:** metadata in `~/.claude/plugins/installed_plugins.json` will remain outdated (old SHA, old date). Functionally the plugin works, but metadata is dirty.

---

## Common Errors

| # | Symptom | Cause | Solution |
|---|---------|-------|----------|
| 1 | AI uses outdated skills, does not see new phases/templates | Cache contains old plugin version, changes in source files are not applied | Perform full update procedure (steps 1-4) |
| 2 | `Plugin "python-pipeline" not found` | `@local-plugins` suffix not specified | Use full name: `python-pipeline@local-plugins` |
| 3 | `already at the latest version` but files changed | Version in `plugin.json` not bumped — CLI compares only version, not contents | Bump version in `.claude-plugin/plugin.json` (step 1) |
| 4 | After `claude plugins update` changes are still not visible | Current Claude Code session loaded old cache at startup | Restart Claude Code (step 4) |
| 5 | After `rm -rf` cache + restart, `installed_plugins.json` shows old SHA and date | `rm -rf` + restart restores files but does not update metadata | Cosmetic issue. For clean metadata — bump version and run `claude plugins update` |
| 6 | `claude plugins update` without arguments — `missing required argument` | CLI requires explicit plugin name | Specify full name: `claude plugins update python-pipeline@local-plugins` |

---

## Rule for AI

When committing changes in this project — **always**:
1. Bump version in `.claude-plugin/plugin.json`
2. Remind the user to execute steps 3-4
