# ADR-001: File Convention SKILL.md + reference.md

## Task
TASK-001

## Status
Accepted

## Context
Need to reuse python-ai-skills standards across 10-20+ projects via Claude Code.
Requirements: minimal tokens, zero dependencies, live reload on editing,
git versioning.

## Considered Alternatives

### Variant A: MCP Server with Tiering
- Pros: explicit L0/L1/L2 control, semantic search
- Cons: requires server code, dependencies, MCP responses are duplicated in history

### Variant B: MCP with FTS5
- Pros: full-text search, scales to 100+ documents
- Cons: SQLite + embedding, setup complexity, server overhead

### Variant C: File Convention SKILL.md + reference.md
- Pros: zero code, best token savings (-66%), live reload, git native
- Cons: no semantic search, manual split into short/full version

### Variant D: OpenViking
- Pros: memory between sessions, per-project profiling
- Cons: 5-7 hours setup, external dependency

## Decision
Chose Variant C because it provides the best token savings with zero
infrastructure complexity. reference.md is read via Read tool and is not duplicated
in message history (unlike MCP responses).

## Consequences
- Easier: adding a skill = creating a folder + SKILL.md + symlink
- Easier: updating = editing an .md file (live reload)
- Harder: with 30+ skills, false positives in automatic selection are possible
- Limitation: no semantic search — Claude selects skills only by description

Full analysis: [docs/2026-03-15-skills-file-convention-architecture.md](../2026-03-15-skills-file-convention-architecture.md)
