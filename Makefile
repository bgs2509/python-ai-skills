.PHONY: install-symlinks install-symlinks-force

# Link this repo's Claude config (skills, agents, commands, global instructions)
# into ~/.claude. Idempotent and portable — safe to re-run. Bootstrap on a new
# machine: clone the repo, then `make install-symlinks`.
install-symlinks:
	@bash scripts/install-claude-symlinks.sh

# Same, but replaces existing REAL directories with symlinks — use when migrating
# a machine that still has real skill/config dirs (content is canonical in repo).
install-symlinks-force:
	@bash scripts/install-claude-symlinks.sh --force
