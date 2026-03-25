# TASK-006: Pipeline Agent Context Optimization

## Status: Done

## Priority: Critical

## Description

Pipeline agents (py-quality, py-security, py-test-writer, py-doc-manager) were reading 2-4 skill files at startup, loading 4,000-12,000 tokens of knowledge into context. This led to missed instructions, incomplete reports, and slow performance.

Solution: "Critical rules inline, details on demand" pattern — critical rules (severity, report format, top-5 checks) are embedded directly in agent files, references to skill files are preserved for details.

Additionally: a Unified Severity Mapping table was added to pipeline.md for severity alignment across agents.

## Related Artifacts

- CHANGELOG.md (Unreleased)
- Report: docs/reports/2026-03-17-agent-context-optimization.md
