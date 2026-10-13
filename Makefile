.PHONY: install-symlinks install-symlinks-force test

# Link this repo's Claude config (skills, agents, commands, global instructions)
# into ~/.claude. Idempotent and portable — safe to re-run. Bootstrap on a new
# machine: clone the repo, then `make install-symlinks`.
install-symlinks:
	@bash scripts/install-claude-symlinks.sh

# Same, but replaces existing REAL directories with symlinks — use when migrating
# a machine that still has real skill/config dirs (content is canonical in repo).
install-symlinks-force:
	@bash scripts/install-claude-symlinks.sh --force

# Every test suite in the repo — the full sweep. The commit-time gate runs only
# scoped suites (see .pre-commit-config.yaml): hooks on claude-home/hooks/,
# scripts on claude-home/scripts/, the principles guard on any *.md.
test:
	@python3 -m pytest claude-home/hooks/test_block_no_verify.py \
	                   claude-home/hooks/test_delegation_pool_nudge.py \
	                   claude-home/hooks/test_git_finish_router.py \
	                   claude-home/hooks/test_skill_finish_guard.py \
	                   claude-home/hooks/test_principles_inject.py \
	                   claude-home/hooks/test_principles_ssot.py \
	                   claude-home/housekeeping/test_housekeeping.py \
	                   claude-home/scripts/test_model_run.py \
	                   claude-home/scripts/test_model_stats.py \
	                   claude-home/scripts/test_skill_stats.py \
	                   claude-home/scripts/test_git_finish_state.py -q
