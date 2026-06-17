# python-ai-skills

A collection of 15 skills, 5 specialized agents, and a 9-phase development pipeline for Python 3.11+ projects in Claude Code. Enforces code quality, security, testing, and documentation standards throughout the entire development lifecycle.

## Features

- **15 skills** covering the full development spectrum:
  - Code quality (`_code-quality`) — 17 principles: DRY, KISS, YAGNI, SOLID, SRP, LoD, Fail Fast
  - Security (`_security`) — OWASP Top 10 checklist, input validation, secrets management
  - Testing (`_testing`) — 3-level test strategy, pytest, AAA pattern, coverage target >= 90%
  - Error handling (`_error-handling`) — AppException hierarchy, HTTP mapping, retry strategies
  - Database (`_database`) — Repository pattern, Alembic migrations, transactions, N+1 prevention
  - HTTP clients (`_http`) — httpx AsyncClient, timeout, retry, Circuit Breaker
  - Caching (`_caching`) — Redis, Cache-Aside, TTL, invalidation, graceful degradation
  - Docker (`_docker`) — multi-stage Dockerfile, Compose, health checks, graceful shutdown
  - Architecture (`_architecture`) — DDD, Hexagonal, monolith vs microservices
  - Logging (`_logging`) — structlog, JSON, Correlation ID, 11 Log-Driven Design principles
  - Linters (`_linters`) — Ruff, Mypy, Bandit, pre-commit hooks, CI pipeline
  - Documentation workflow (`_docworkflow`) — TASK -> REQ -> PLAN -> ADR -> CHANGELOG -> REPORT -> COMMIT
  - ADR generator (`_adr`) — Architecture Decision Records with context, alternatives, consequences
  - Completion report (`_report`) — post-implementation summary with review and test results
  - Project init (`_init`) — interactive new project scaffolding

- **5 specialized agents** (via Claude Code Agent Teams):
  - `py-quality` — code quality review against 17 principles
  - `py-security` — security audit using OWASP Top 10
  - `py-test-writer` — automated test generation (pytest, AAA, fixtures)
  - `py-doc-manager` — documentation pipeline (backlog, plans, ADRs, changelogs, reports)
  - `py-supervisor` — post-hoc audit of pipeline compliance

- **9-phase development pipeline** (`/pipeline`):
  1. INTAKE — task analysis, skill routing
  2. REQUIREMENTS — FR/NFR formulation and approval
  3. EXPLORATION — codebase analysis
  4. PLANNING — implementation design with mandatory review
  5. IMPLEMENTATION — code writing with skill guidance
  6. QUALITY GATE — parallel review by 3 agents (quality + security + tests)
  7. FIX — resolve blockers and warnings
  8. DOCUMENTATION — changelog, completion report
  9. COMMIT + AUDIT — commit with checklist, post-hoc supervisor audit

- **Routing Table** — automatic skill selection based on task context (DB work, HTTP integrations, CI/CD, Docker, etc.)

## Technologies Used

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — CLI, Agent Teams, Skills system, Plugin architecture
- **Python 3.11+** — target runtime for all skills
- **Ruff** — fast Python linter and formatter (referenced in `_linters`)
- **Mypy** — static type checking (referenced in `_linters`)
- **Bandit** — security-focused static analysis (referenced in `_linters`, `_security`)
- **pytest** — testing framework (referenced in `_testing`)
- **httpx** — async HTTP client (referenced in `_http`)
- **Redis** — caching backend (referenced in `_caching`)
- **Docker** / **Docker Compose** — containerization (referenced in `_docker`)
- **structlog** — structured logging (referenced in `_logging`)
- **Alembic** — database migrations (referenced in `_database`)
- **Pydantic Settings** — configuration and secrets management (referenced in `_security`)

## Installation

### Prerequisites

- Claude Code CLI installed (`claude --version`)
- Git installed (`git --version`)

### Steps

1. **Clone the repository**

   ```bash
   git clone <repository-url> python-ai-skills
   cd python-ai-skills
   ```

2. **Install symlinks into `~/.claude`**

   ```bash
   make install-symlinks
   ```

   This links every skill, agent, command, and the global instruction files
   (`CLAUDE.md`, `RTK.md`, `rules/`, `output-styles/`) into `~/.claude`.
   Idempotent — safe to re-run after adding or removing a skill. The repo is the
   single source of truth; `~/.claude` holds only symlinks back to it.

3. **Restart Claude Code**

   ```bash
   exit
   claude
   ```

## Usage

### Full pipeline

Run the complete 9-phase development pipeline for a task:

```
/pipeline <task description>
```

The pipeline orchestrates all phases automatically — from task intake through code review, testing, documentation, and commit.

### Individual skills

Invoke any skill directly as a slash command:

```
/_code-quality    # Code quality review (17 principles)
/_security        # Security audit (OWASP Top 10)
/_testing         # Test strategy and generation
/_database        # Database patterns and migrations
/_docker          # Containerization guidance
/_http            # HTTP client patterns
/_caching         # Caching strategies
/_logging         # Structured logging setup
/_linters         # Linter configuration
/_architecture    # Architecture design
/_error-handling  # Exception hierarchy
/_docworkflow     # Documentation pipeline
/_adr             # Architecture Decision Record
/_report          # Completion report
/_init            # New project scaffolding
```

### Agents

Specialized agents are available through Claude Code Agent Teams:

- `py-quality` — review files for code quality issues
- `py-security` — security vulnerability scan
- `py-test-writer` — generate and run tests
- `py-doc-manager` — manage documentation artifacts
- `py-supervisor` — audit pipeline compliance

## Result

Using python-ai-skills provides:

- **Standardized development** — consistent code quality, security, and architecture across all Python projects
- **Automated code review** — parallel quality and security audits with severity classification (Must Fix / Should Fix / Optional)
- **Automated test generation** — pytest tests following AAA pattern with coverage targets
- **Full documentation trail** — every task produces TASK, REQ, PLAN, CHANGELOG entry, and Completion Report
- **Compliance audit** — post-hoc verification that all pipeline phases were followed correctly
- **Knowledge codification** — 15 skills encode best practices (SOLID, OWASP, DDD) as reusable, versionable artifacts
- **Gated workflow** — mandatory approvals at requirements and plan stages prevent wasted implementation effort

## License

Private project.

## Version

1.3.0
