# TASK-008: Fix Installation Documentation — Skills vs Plugin

## Status: Done

## Priority: High

## Description

When installing the plugin on a new machine, skills (`/_docworkflow`, `/_code-quality`, etc.) are not visible as slash commands. Reason: the plugin registers only commands and agents, while skills are a separate mechanism via symlinks in `~/.claude/skills/`.

The documentation `docs/plugin-install.md` did not describe this step, leading to `Unknown skill: _docworkflow` error.

## Changes

- Rewrote the "Architecture" section — separation of plugin vs skills
- Added step 4: creating `~/.claude/skills/` symlinks
- Added error 4: `Unknown skill` with diagnostics and resolution
- Updated the diagnostics section: skills symlink verification

## Related Artifacts

- docs/plugin-install.md
