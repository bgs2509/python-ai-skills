# Changelog

Формат: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Версионирование: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
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
