.PHONY: install-symlinks

# Link this repo's Claude config (skills, agents, commands, global instructions)
# into ~/.claude. Idempotent and portable — safe to re-run. Bootstrap on a new
# machine: clone the repo, then `make install-symlinks`.
install-symlinks:
	@bash scripts/install-claude-symlinks.sh
