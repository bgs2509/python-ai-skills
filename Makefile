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

# Full sweep: claude-home suites plus the skill suites under audit-loop/,
# full-audit/ and project-sync/. One pytest call per suite: full-audit/ and
# project-sync/ carry their own pytest.ini, so they run from their dir (a
# combined call would apply one suite's ini to every path).
# The commit-time gate runs only scoped suites (see .pre-commit-config.yaml): hooks on claude-home/hooks/,
# scripts on claude-home/scripts/, the principles guard on any *.md.
test:
	@python3 -m pytest claude-home/hooks/test_block_no_verify.py \
	                   claude-home/hooks/test_delegation_pool_nudge.py \
	                   claude-home/hooks/test_git_finish_router.py \
	                   claude-home/hooks/test_skill_finish_guard.py \
	                   claude-home/hooks/test_principles_inject.py \
	                   claude-home/hooks/test_task_level_inject.py \
	                   claude-home/hooks/test_principles_ssot.py \
	                   claude-home/housekeeping/test_housekeeping.py \
	                   claude-home/scripts/test_model_run.py \
	                   claude-home/scripts/test_model_stats.py \
	                   claude-home/scripts/test_skill_stats.py \
	                   claude-home/scripts/test_git_finish_state.py \
	                   scripts/test_install_claude_symlinks.py -q
	@python3 -m pytest audit-loop/tests -q
	@cd full-audit && python3 -m pytest
	@cd project-sync && python3 -m pytest
