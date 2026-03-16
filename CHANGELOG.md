# Changelog

Формат: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Версионирование: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- 6 skill'ов переименованы для интуитивности: _workflow→_docworkflow, _quality-cascade→_code-quality, _create-adr→_adr, _completion-report→_report, _init-project→_init, _http-clients→_http
- Обновлены все cross-references, symlinks, CLAUDE.md (v3.2), архитектурный документ

### Changed
- Все 15 skill'ов переименованы с префиксом `_` (вызов: `/_quality-cascade` и т.д.)
- Обновлены cross-references, symlinks, CLAUDE.md (v3.1), архитектурный документ
- create-adr и completion-report: гибридная триггерная модель (авто + ручной fallback)
- workflow: чеклист напоминает вызвать create-adr/completion-report если не сработали автоматически
- Миграция на Claude Code Skills: 15 skill'ов с SKILL.md + reference.md структурой
- CLAUDE.md переписан как каталог skill'ов + workflow-правила (v3.0)
- Все 26 .md файлов реорганизованы из плоской структуры в skill-папки

### Added
- 15 SKILL.md файлов: quality-cascade, error-handling, security, logging, testing, database, architecture, linters, docker, http-clients, caching, workflow, create-adr, completion-report, init-project
- quality-cascade использует context: fork для глубокого ревью
- init-project skill с интерактивными вопросами для нового проекта
- Документ архитектурного решения: docs/2026-03-15-skills-file-convention-architecture.md
- Пайплайн обязательной документации: workflow, backlog, planning, git-conventions (TASK-001)
- CHANGELOG.md (TASK-001)
