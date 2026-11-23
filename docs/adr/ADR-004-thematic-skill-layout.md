# ADR-004: Thematic skill layout with flat client installations

## Status

Accepted (user approval; bd `python-ai-skills-9pq`).

## Context

The repository had 50 skill folders at its root. Fifteen public names also started with an underscore, which does not conform to the [Agent Skills specification](https://agentskills.io/specification). The repository is the shared source for Claude Code, Codex, and Pi; moving a source file must not change its installed command a second time.

## Considered alternatives

- Four broad topics: low implementation cost, but unrelated utilities would share a category and the GRACE family would be harder to browse.
- Seven topics at a fixed depth: preserves existing skill families and lets the installer exclude nested test fixtures with a single glob.
- Topics with subcategories: more navigation and discovery rules than the current collection needs.

## Decision

Use `Skills/<topic>/<name>/SKILL.md` and package supporting files with their skill. One skill belongs to one topic, chosen by its main purpose:

- `python-development`: Python design, implementation, quality checks, and project initialization.
- `development-workflows`: development orchestration and its planning and reporting artifacts.
- `grace`: the GRACE skill family.
- `decision-support`: `best-*` and `explain`.
- `git-and-sync`: Git, Beads, and repository synchronization.
- `audit-and-progress`: audits, progress observation, and progress visualization.
- `business`: customer specifications and vacancy analysis.

Folders are the inventory. Do not copy skill definitions or create a separate registry. The installer validates the inventory and links each skill directly to the flat `skills/<name>/` directory in each enabled client. Category names never enter invocation names. Repository-wide `agents/`, `commands/`, `claude-home/`, `docs/`, and `scripts/` stay separate.

## Upgrade and rollback

The name migration landed first (`538f04a`); the only nonliteral rename is `_init` to `python-init`, leaving Claude Code's built-in `/init` free. Update consumers of old commands and paths, then run `make install-symlinks` from the same checkout and restart the clients (or reload Pi). Do not use `--force` to resolve a skill collision: inspect the reported entry first. Existing sessions may still contain instructions with the old names.

To roll back **only the directory layout**, return the same checkout to the compatible flat layout at `538f04a` and run `make install-symlinks`; that installer recognizes links from the thematic layout. Restart clients and check that all expected links resolve. Do not use a different checkout for rollback unless deliberately migrating the paths, since the ownership checks protect links that point elsewhere.

To roll back **both** changes, save local work, return the same checkout to the old-name revision, and reinstall; also retire the new-name links that did not exist in that revision. Remove only links whose targets match the exact source directories for the 15 renamed skills in this checkout. Do not remove a real directory, a third-party link, or similarly named files. Restart clients and verify the resulting inventory again.
