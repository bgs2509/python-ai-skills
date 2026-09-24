# RTK - Rust Token Killer

**Usage**: Token-optimized CLI proxy (60-90% savings on dev operations)

## Meta Commands (always use rtk directly)

```bash
rtk gain              # Show token savings analytics
rtk gain --history    # Show command usage history with savings
rtk discover          # Analyze Claude Code history for missed opportunities
rtk proxy <cmd>       # Execute raw command without filtering (for debugging)
```

## Installation Verification

```bash
rtk --version         # Should show: rtk X.Y.Z
rtk gain              # Should work (not "command not found")
which rtk             # Verify correct binary
```

⚠️ **Name collision**: If `rtk gain` fails, you may have reachingforthejack/rtk (Rust Type Kit) installed instead.

## Hook-Based Usage

All other commands are automatically rewritten by the Claude Code hook.
Example: `git status` → `rtk git status` (transparent, 0 tokens overhead)

## `rtk diff` — Implementation Trait (NOT a bug)

`rtk diff` is a token-optimized condenser, not a verification tool — by design:
- it MAY report "Files are identical" for files that do differ (observed on a 1-line JSON change)
- it ALWAYS exits 0, even when differences are printed

Since the hook rewrites `diff` → `rtk diff`, plain `diff` inherits both traits.
**Never use `diff` as a verification gate.** For byte-exact comparison use:

```bash
cmp file_a file_b       # byte-exact, exit 1 on difference (not rewritten)
rtk proxy diff a b      # native diff, unfiltered
```

Refer to CLAUDE.md for full command reference.

## `rtk find` — excluded from rewriting (false empty results)

`rtk find` skips files that `.gitignore` hides and directories listed in rtk's
`[filters].ignore_dirs` (`.venv`, `node_modules`, `target`, `vendor`, ...), and it
still **exits 0** — so "nothing found" may be false. Verified 2026-09-24 (rtk 0.35.0):
in a repo with `a/` in `.gitignore`, `rtk find . -name '*syn*'` listed 1 of 2 files;
`rtk find . -name pyvenv.cfg` answered `0 for 'pyvenv.cfg'` next to an existing
`.venv/pyvenv.cfg`. In Sinayara-Isuzu this produced a wrong "snapshot never downloaded"
conclusion (bd `python-ai-skills-abh`).

**Fix in place:** `find` is listed in `[hooks] exclude_commands` of
`claude-home/rtk/config.toml` (linked to `~/.config/rtk/config.toml` by
`make install-symlinks`), so the hook leaves `find` native. Rules:

- An empty result from `rtk find` (typed explicitly) is **not** evidence of absence.
- Plain `find` is native again; `rtk proxy find ...` is equivalent.

Checked and **not** affected on the same fixture: `rtk grep` (lists gitignored and
`.venv` matches), `rtk ls`, `rtk read` (`cat`), `rtk wc`. `rtk tree` hides dot-dirs
such as `.venv` exactly like native `tree` without `-a`.
