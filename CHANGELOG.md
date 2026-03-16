# Changelog

Формат: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Версионирование: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 15 SKILL.md файлов с frontmatter (name, description) (TASK-001)
- quality-cascade использует context: fork для глубокого ревью (TASK-001)
- init-project skill с интерактивными вопросами (TASK-001)
- Архитектурный документ: docs/2026-03-15-skills-file-convention-architecture.md (TASK-001)
- Пайплайн документации: workflow, backlog, planning, git-conventions (TASK-001)
- Гибридная триггерная модель для _adr и _report (TASK-001)
- CHANGELOG.md (TASK-001)
- Ретроспективный docworkflow: backlog, ADR, completion report (TASK-001)
- python-pipeline плагин: 8-фазная оркестрация разработки (TASK-002)
- 4 специализированных агента: py-quality, py-security, py-test-writer, py-doc-manager (TASK-002)
- Plugin manifest `.claude-plugin/plugin.json` (TASK-002)
- Routing Table для автоматического выбора skill'ов по контексту (TASK-002)
- Ретроспективный docworkflow: backlog, completion report (TASK-002)

### Fixed
- Pipeline: железные правила для Lead — запрет подмены агентов и переопределения severity (TASK-003)
- Pipeline: gate-чеклисты между фазами 3.5→4, 5→6 и в Phase 8 (TASK-003)
- Pipeline: Phase 5 требует ровно 3 агента в одном сообщении (TASK-003)
- Pipeline: Phase 6 — BLOCKER/CRITICAL исправляются всегда, не optional (TASK-003)
- Pipeline: обязательное одобрение плана пользователем перед Phase 4 — абсолютный BLOCKER (TASK-004)

### Changed
- Все 26 .md файлов реорганизованы из плоской структуры в skill-папки (TASK-001)
- Все 15 skill'ов переименованы с префиксом `_` (TASK-001)
- 6 skill'ов получили интуитивные имена: _workflow→_docworkflow, _quality-cascade→_code-quality, _create-adr→_adr, _completion-report→_report, _init-project→_init, _http-clients→_http (TASK-001)
- CLAUDE.md переписан как каталог skill'ов + workflow (v3.2) (TASK-001)
