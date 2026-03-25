# Git Conventions

> Rules for commit formatting and working with git.

---

## Commit Message Format

```
TASK-NNN: <type>: <description>
```

### Types (type)

| Type | When |
|------|------|
| `feat` | New functionality |
| `fix` | Bug fix |
| `refactor` | Refactoring without behavior change |
| `docs` | Documentation changes |
| `test` | Adding or modifying tests |
| `ci` | CI/CD changes |
| `chore` | Miscellaneous (dependencies, configs) |

### Examples

```
TASK-001: feat: add user authentication via JWT
TASK-003: fix: handle timeout in HTTP client
TASK-007: docs: add backlog and workflow process
TASK-012: refactor: extract validation to separate module
```

---

## Rules

| Rule | Description |
|------|-------------|
| Language | English (commit messages). Documentation — Russian |
| Task ID | Mandatory at the beginning of the message |
| Header | First line ≤ 72 characters — brief "what was done" |
| Imperative | Use imperative mood: "add", not "added" |
| Body | **MANDATORY**. Separated by a blank line after the header. Detailed description: what changed, why, which files are affected, what decisions were made |

---

## Commit Body (description)

> **Goal:** from `git log` alone, the full project development history can be reconstructed without reading the code.

The commit body should answer these questions:

1. **What was done** — what specific changes were made (files, modules, functions)
2. **Why** — what problem it solves, which backlog task it addresses
3. **How** — key decisions and approach (not the entire code, but the essence)
4. **What is affected** — list of changed/created/deleted files with explanations

### Commit Atomicity

- A commit should be **small** — minimal number of files, one logical change
- If a task affects many files — split into multiple commits by logical groups
- Each commit should leave the project in a working state
- One commit = one idea that can be understood from `git log`

Examples of splitting a large task:
```
TASK-007: docs: add workflow and backlog process
TASK-007: docs: add planning format and git conventions
TASK-007: docs: update ADR and completion report templates with Task ID
TASK-007: docs: add CHANGELOG.md and update routing table
```

### Body Format

```
TASK-NNN: <type>: <brief header>

<Detailed description: what, why, how>

Changes:
- <file/module>: <what was done and why>
- <file/module>: <what was done and why>
```

### Example

```
TASK-007: docs: add mandatory documentation pipeline

Add 6-step documentation pipeline that every task must follow:
backlog → planning → ADR → changelog → completion report → commit.

Introduce TASK-NNN / PLAN-NNN / ADR-NNN numbering system
with cross-references between all artifacts.
Extract planning format from global CLAUDE.md into process/planning.md (DRY).

Changes:
- process/workflow.md: end-to-end 6-stage pipeline with checklist
- process/backlog.md: task template with TASK-NNN numbering
- process/planning.md: plan format (extracted from ~/.claude/CLAUDE.md)
- process/git-conventions.md: commit format with Task ID
- CHANGELOG.md: created in project root
- process/adr.md: added Task ID field
- process/completion-report.md: added Task block (ID, plan, ADR)
- CLAUDE.md: added workflow to the routing table
```
