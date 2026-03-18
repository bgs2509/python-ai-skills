# Changelog

Формат: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Версионирование: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- docs/plugin-install.md: добавлен шаг создания симлинков `~/.claude/skills/` — без него скиллы не видны как slash-команды (TASK-008)
- docs/plugin-install.md: добавлена ошибка 4 `Unknown skill: _docworkflow` с диагностикой (TASK-008)
- docs/plugin-install.md: переписана секция «Архитектура» — разделение плагин vs скиллы (TASK-008)

### Added
- py-supervisor агент: post-hoc аудит compliance пайплайна (TASK-007)
- Pipeline Phase 9 AUDIT: автоматическая проверка артефактов после коммита (TASK-007)
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

### Removed
- _docker: правила `no-new-privileges`, `cap_drop: ALL`, `read_only: true` — ломали nginx/postgres через запрет `setgid()` (TASK-005)
- _docker: упоминание "security hardening" из описания skill'а (TASK-005)

### Fixed
- Pipeline: железные правила для Lead — запрет подмены агентов и переопределения severity (TASK-003)
- Pipeline: gate-чеклисты между фазами 3.5→4, 5→6 и в Phase 8 (TASK-003)
- Pipeline: Phase 5 требует ровно 3 агента в одном сообщении (TASK-003)
- Pipeline: Phase 6 — BLOCKER/CRITICAL исправляются всегда, не optional (TASK-003)
- Pipeline: обязательное одобрение плана пользователем перед Phase 4 — абсолютный BLOCKER (TASK-004)

### Changed
- Agents: критичные правила встроены inline в py-quality, py-security, py-test-writer, py-doc-manager — убрано обязательное чтение 2-4 skill-файлов на старте (TASK-006)
- Pipeline Phase 5: добавлена Unified Severity Mapping — единая таблица Must Fix / Should Fix / Optional (TASK-006)
- Pipeline Phase 6: severity-правила используют Unified Severity Mapping вместо разрозненных терминов (TASK-006)
- Pipeline Phase 5: промпты агентов упрощены — убрано "Read skill first" (TASK-006)
- Все 26 .md файлов реорганизованы из плоской структуры в skill-папки (TASK-001)
- Все 15 skill'ов переименованы с префиксом `_` (TASK-001)
- 6 skill'ов получили интуитивные имена: _workflow→_docworkflow, _quality-cascade→_code-quality, _create-adr→_adr, _completion-report→_report, _init-project→_init, _http-clients→_http (TASK-001)
- CLAUDE.md переписан как каталог skill'ов + workflow (v3.2) (TASK-001)
