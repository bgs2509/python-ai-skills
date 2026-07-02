# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- `do-feature`: resolved 3 critical round-2 audit findings — (1) circular risk-classifier dependency: risk is now classified twice (preliminary by the orchestrator in the new Pre-dispatch Protocol before Step 2, final in the Discovery artifact) with upward-only escalation; (2) Step 2 preflight STOP gates were unreachable inside the research subagent: preflight (pre-commit check, lint baseline, Sentrux baseline) is now explicitly orchestrator-owned and runs inline before the dispatch; (3) monolithic 447-line SKILL.md split per ADR-001 convention into a control-logic SKILL.md + `reference.md` with the per-step details; A/B routing evidence moved to `docs/adr/ADR-002-model-routing-ab-validation.md`
- `do-feature`: resolved 8 medium round-2 audit findings — (1) Discovery no longer runs `/best-approach` solution research (duplicated Step 4 Brainstorming's job before the requirements gate); Discovery is now problem-space only; (2) Step 13 `grace-refresh` is now targeted (scoped to modules touched since the last Step 11 phase-boundary sync) instead of unconditional full; (3) Step 12 review is now scoped to cross-phase deltas/integration seams/FR-NFR coverage instead of re-reviewing code already passed by Step 11's per-phase `grace-reviewer`; (4) Step 2/4 XML outputs annotated "auto-generated — do NOT write manually" to stop contradicting the Auto-Generated XML Rule; (5) Model Routing Matrix rewritten in tier language (strong/mid/cheap) with a revalidation rule for lineup changes (follow-up: `python-ai-skills-4f4`, revalidate on Claude 5); (6) added `context7_verified:` frontmatter key to `design.md`, written in Steps 4/7, read by the Step 10 evidence check; (7) inlined a one-line `3x-rule` definition in `SKILL.md ## Flags` (full protocol still in `do-autopilot`); (8) added explicit commit authority rule — invoking `do-feature` grants authority for the workflow's own commits (Step 11/13), never for `git push`

### Added
- `git-branch`: standalone pure-instruction skill that discovers ALL branches and triages each — protected/active (current HEAD, worktree-checked-out = adjacent session), merged→safe-delete, abandoned (with age), junk (throwaway name + stale). Report-first; deletes only after confirmation; `-d` over `-D`; unpushed-commits data-loss guard; never `git push --delete` (reports the command instead)
- `do-multiagent`: team-lead orchestrator running a TEAM of subagents over a bead dependency graph in parallel git worktrees, each via `do-feature --auto-approve`. Accepts free-form work/draft (decompose→approve) or an existing bead queue; upfront `best-questions` fork-analysis; controller-owned serialised merge queue; controller is sole `bd` writer; Trust=0% independent re-verify per branch before merge; parallel only across disjoint write-scope (shared-file beads grouped into one session)
- best-* skill family matryoshka: `best-recommend` (recommendation atom) and `best-research` (analysis engine, SSoT of the shared core), with `best-approach`/`best-rank`/`best-questions` as thin wrappers
- `scripts/install-claude-symlinks.sh` + `make install-symlinks`: idempotent, portable installer linking all skills/agents/commands/global instructions into `~/.claude`
- `claude-home/`: SSoT for global Claude config (`CLAUDE.md`, `RTK.md`, `rules/`, `output-styles/`, `hooks/`, `scripts/`)
- `claude-home/settings.json.template`: portable `settings.json` rendered at install time (`{{CLAUDE_HOME}}` placeholder); installer validates JSON and backs up before overwriting

### Changed
- Renamed `smart-commit`→`git-commit` (split branch hygiene out into the new `git-branch` skill); propagated across `beads-sync`, `project-sync`, `do-feature`, `do-autopilot`, `do-feature-clean`, global `CLAUDE.md` skill hierarchy
- Renamed orchestrator skills into the `do-*` executor family: `feature-workflow`→`do-feature`, `superautocoder`→`do-autopilot`; agent `feature-workflow-clean`→`do-feature-clean`. The methodology/concept (a "feature-workflow project/infrastructure") is now phrased "dev-workflow" to avoid the awkward "do-feature project". Propagated across global `CLAUDE.md`, `rules/python-dev.md`, `settings.json.template` (SessionStart hook), `audit-loop`, `customer-tz`, `best-approach`
- Centralized all global skills, agents, and instruction files into this repo; `~/.claude` now holds only symlinks back (single source of truth)
- Renamed skills: `best-explain`→`best-recommend`, `best-option`→`best-rank`, `questions-answers`→`best-questions` (propagated across feature-workflow, superautocoder, audit-loop)
- Skill distribution switched from the `python-pipeline` plugin to the symlink model
- Centralized `hooks/` + `scripts/` and `settings.json` (V3): hook-script paths made portable (`$(dirname "$0")`, `$HOME`); `settings.json` rendered from template with absolute per-machine hook paths; machine-specific `enabledPlugins`/`extraKnownMarketplaces` moved to `settings.local.json` (deep-merged by Claude); dropped stale `python-pipeline`/`local-plugins` references

### Removed
- Retired the `python-pipeline` plugin: deleted `.claude-plugin/plugin.json`, `docs/plugin-install.md`, `docs/plugin-update.md`
- Dropped the `best-explain` risky-ops communication contract; removed its pointers from git-commit/beads-sync/project-sync/projects-sync

## [1.3.0] - 2026-03-25

### Changed
- Translated entire project from Russian to English (~66 files: skills, references, agents, commands, docs, changelog, CLAUDE.md) (TASK-009)
- Updated language standards: all documentation and code comments now in English (TASK-009)
- Bumped version to 1.3.0 (TASK-009)

### Fixed
- docs/plugin-install.md: added skills symlinks step `~/.claude/skills/` — without it skills are not visible as slash commands (TASK-008)
- docs/plugin-install.md: added error 4 `Unknown skill: _docworkflow` with diagnostics (TASK-008)
- docs/plugin-install.md: rewritten "Architecture" section — separation of plugin vs skills (TASK-008)

### Added
- py-supervisor agent: post-hoc pipeline compliance audit (TASK-007)
- Pipeline Phase 9 AUDIT: automatic artifact verification after commit (TASK-007)
- 15 SKILL.md files with frontmatter (name, description) (TASK-001)
- quality-cascade uses context: fork for deep review (TASK-001)
- init-project skill with interactive questions (TASK-001)
- Architecture document: docs/2026-03-15-skills-file-convention-architecture.md (TASK-001)
- Documentation pipeline: workflow, backlog, planning, git-conventions (TASK-001)
- Hybrid trigger model for _adr and _report (TASK-001)
- CHANGELOG.md (TASK-001)
- Retrospective docworkflow: backlog, ADR, completion report (TASK-001)
- python-pipeline plugin: 8-phase development orchestration (TASK-002)
- 4 specialized agents: py-quality, py-security, py-test-writer, py-doc-manager (TASK-002)
- Plugin manifest `.claude-plugin/plugin.json` (TASK-002)
- Routing Table for automatic skill selection by context (TASK-002)
- Retrospective docworkflow: backlog, completion report (TASK-002)

### Removed
- _docker: rules `no-new-privileges`, `cap_drop: ALL`, `read_only: true` — broke nginx/postgres by blocking `setgid()` (TASK-005)
- _docker: mention of "security hardening" from skill description (TASK-005)

### Fixed
- Pipeline: strict rules for Lead — prohibit agent substitution and severity overrides (TASK-003)
- Pipeline: gate checklists between phases 3.5→4, 5→6 and in Phase 8 (TASK-003)
- Pipeline: Phase 5 requires exactly 3 agents in one message (TASK-003)
- Pipeline: Phase 6 — BLOCKER/CRITICAL always fixed, not optional (TASK-003)
- Pipeline: mandatory user plan approval before Phase 4 — absolute BLOCKER (TASK-004)

### Changed
- Agents: critical rules embedded inline in py-quality, py-security, py-test-writer, py-doc-manager — removed mandatory reading of 2-4 skill files at startup (TASK-006)
- Pipeline Phase 5: added Unified Severity Mapping — single Must Fix / Should Fix / Optional table (TASK-006)
- Pipeline Phase 6: severity rules use Unified Severity Mapping instead of scattered terms (TASK-006)
- Pipeline Phase 5: agent prompts simplified — removed "Read skill first" (TASK-006)
- All 26 .md files reorganized from flat structure into skill folders (TASK-001)
- All 15 skills renamed with `_` prefix (TASK-001)
- 6 skills received intuitive names: _workflow→_docworkflow, _quality-cascade→_code-quality, _create-adr→_adr, _completion-report→_report, _init-project→_init, _http-clients→_http (TASK-001)
- CLAUDE.md rewritten as skill catalog + workflow (v3.2) (TASK-001)
