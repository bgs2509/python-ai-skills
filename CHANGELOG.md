# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-03-25

### Changed
- Translated entire project from Russian to English (~66 files: skills, references, agents, commands, docs, changelog, CLAUDE.md)
- Updated language standards: all documentation and code comments now in English
- Bumped version to 1.3.0

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
