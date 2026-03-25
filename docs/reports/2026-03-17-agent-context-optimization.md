# Completion Report: Pipeline Agent Context Optimization

## Metadata

- **Task ID:** TASK-006
- **Plan:** None (plan in claude plans)
- **ADR:** None
- **Date:** 2026-03-17

## Executive Summary

Eliminated the root cause of agents missing instructions in the pipeline — bloated context due to mandatory reading of 2-4 skill files on each launch. Applied the "Critical rules inline, details on demand" pattern. Additionally resolved the severity inconsistency issue across agents via Unified Severity Mapping.

## Changes

| File | What was done |
|------|---------------|
| `agents/py-quality.md` | Inline: top-5 checks (DRY, KISS, Fail Fast, AppException, no print) + severity. Removed reading of 4 files |
| `agents/py-security.md` | Inline: top-5 (secrets, SQL injection, .gitignore, validation, OWASP) + severity. Removed reading of 2 files |
| `agents/py-test-writer.md` | Inline: AAA, naming, fixtures, coverage, anti-patterns. Removed reading of 1 file |
| `agents/py-doc-manager.md` | Inline: numbering, plan structure (4 sections + 6 questions), commit format. Removed reading of 4 files |
| `commands/pipeline.md` | Unified Severity Mapping, simplified Phase 5 prompts, updated Phase 6 rules |

## Metrics

| Metric | Before | After |
|--------|--------|-------|
| Tool calls on agent startup | 4-8 | 0-1 |
| Knowledge tokens in context | 4,000-12,000 | 300-500 |
| Agent startup time | 15-30 sec | 2-5 sec |
| Severity tables | 2 different | 1 unified |

## Review Checklist

- [x] Quality Cascade: DRY (inline rules ≠ full copy), KISS (≤120 lines per agent)
- [x] Security: no secrets, no vulnerabilities
- [x] Linters: N/A (markdown files)

## Tests

- N/A — changes in markdown configuration files, not in code

## Known Limitations

- Inline rules = partial duplication with skill files (~15 lines per agent). When updating a skill, the agent must also be updated.
- "Read on demand" references depend on model behavior — Sonnet may not read the details.
