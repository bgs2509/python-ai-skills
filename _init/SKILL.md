---
name: _init
description: >
  Initialize a new Python project for Claude Code. Creates CLAUDE.md, CHANGELOG.md,
  docs/ structure. Invoke when starting a new project.
disable-model-invocation: true
---

# Project Initialization

> Setting up a new Python project for use with Claude Code and python-ai-skills.

## Required Questions for the User

Before creating files, ask these questions:

1. **Project name** — what is the project called?
2. **Architecture type** — monolith or microservices?
3. **Framework** — FastAPI, Django, CLI, library?
4. **Database** — PostgreSQL, SQLite, no database?
5. **Cache** — Redis, no cache?
6. **Description** — 1-2 sentences: what does the project do?

## Files to Create

### 1. CLAUDE.md (in project root)

```markdown
# {Project Name}

## Description
{Description from user's answer}

## Architecture
- Type: {monolith/microservices}
- Framework: {FastAPI/Django/...}
- DB: {PostgreSQL/SQLite/none}
- Cache: {Redis/none}

## Standards
This project follows python-ai-skills standards (global skills).
```

### 2. CHANGELOG.md

```markdown
# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Project initialization
```

### 3. docs/ Structure

```
docs/
├── backlog/     # Tasks (TASK-NNN)
├── plans/       # Implementation plans
├── adr/         # Architecture Decision Records
└── reports/     # Completion reports
```

### 4. .claude/settings.local.json (if it doesn't exist)

```json
{
  "permissions": {
    "allow": []
  }
}
```

## After Creation

Inform the user:
- Which files were created
- Which skills are available globally (list the main ones)
- How to invoke a skill: `/_code-quality`, `/_adr`, etc.
