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
