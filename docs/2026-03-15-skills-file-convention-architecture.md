# Variant C: File Convention SKILL.md + reference.md

**Date:** 2026-03-15
**Context:** Choosing an architecture for reusing python-ai-skills standards across 10-20+ projects via Claude Code Skills.
**Status:** IMPLEMENTED 2026-03-16 (15 skills, 26 reference files, symlinks in ~/.claude/skills/, hybrid triggers).

## Approach Overview

The `python-ai-skills` repository is a **skill collection**. Each directory in it is a ready-made skill following the convention: `SKILL.md` contains the short version (L0+L1), `reference.md` — the full version (L2). Claude loads `SKILL.md` on invocation, and reads `reference.md` via the `Read` tool **only when details are needed**. No additional code, servers, or dependencies.

```
~/python-ai-skills/                    # Git repo = skill collection (15 skills)
├── _code-quality/
│   ├── SKILL.md                       # Short principles (~50 lines, context: fork)
│   └── reference/                     # Multiple reference files
│       ├── quality-cascade.md
│       ├── code-standards.md
│       └── naming.md
├── _error-handling/
│   ├── SKILL.md
│   └── reference.md                   # Single reference file
└── ...

~/.claude/skills/                      # Symlinks → python-ai-skills (15 total)
├── _code-quality → ~/python-ai-skills/_code-quality
├── _error-handling → ~/python-ai-skills/_error-handling
└── ...
```

---

## How Loading Works (3 Phases)

### Phase 1: Metadata (session start)

At session start, Claude loads **only `name` and `description`** of each skill.

- Cost: ~100 tokens per skill
- 15 skills (implemented) = ~1,500 tokens (negligible)
- 50 skills = ~5,000 tokens (still low)
- Budget: 2% of context window (can be overridden via `SLASH_COMMAND_TOOL_CHAR_BUDGET`)

Claude sees **what is available**, but does not load content.

**Source:** [Skills — Where skills live](https://code.claude.com/docs/en/skills.md#where-skills-live)

### Phase 2: SKILL.md (on invocation)

When a skill is invoked (manually `/_code-quality` or automatically by description), Claude reads the full `SKILL.md` from disk.

- Cost: 300-5,000 tokens (depends on size)
- Recommendation: up to 500 lines
- Re-read every time (no cache between invocations)
- File changes are visible immediately (live reload)

### Phase 3: Supporting files (on demand)

If `SKILL.md` references `reference.md`, Claude reads it via `Read` **only if the task requires details**.

- Cost: 0 tokens until read
- Claude decides on its own — whether reference.md is needed for the current task
- File is read via Read tool, **not duplicated** in every context message (unlike MCP responses)

**This is the key advantage of Variant C:** reference.md read via Read = one-time load. MCP response = included in history and forwarded in every message.

**Source:** [Skills — Add supporting files](https://code.claude.com/docs/en/skills.md#add-supporting-files)

---

## Skill Structure

### Minimal Example

```yaml
# ~/python-ai-skills/_code-quality/SKILL.md
---
name: _code-quality
description: 17 Python code quality principles. Use during review, refactoring, and writing new code.
---

## Principles (short version)

1. **DRY** — no logic duplication
2. **SRP** — one class/function = one responsibility
3. **LoD** — don't reach into others' internals (a.b.c.d — bad)
4. **KISS** — simple solution is better than complex
5. **Fail Fast** — validate at entry, guard clauses
...

**Red flags:** except pass, god class >300 lines, magic numbers

Full text with examples and anti-patterns: see [reference.md](reference.md)
```

### reference.md

```markdown
# Quality Cascade — Full Version

## Principle 1: DRY

### Description
...

### Violation Examples
...

### How to Fix
...

## Principle 2: SRP
...
```

### Implemented Structure Variants

**Single reference file** (full version = one file):
```
_error-handling/
├── SKILL.md              # Short version (~40 lines)
└── reference.md          # Full version (~110 lines)
```

**reference/ folder** (multiple topic-specific files):
```
architecture/
├── SKILL.md              # DDD + Hexagonal short
└── reference/
    ├── ddd.md            # Layers, entities, Value Objects
    ├── hexagonal.md      # Ports, adapters, DI
    ├── monolith.md       # Monolith specifics
    └── microservices.md  # Microservices specifics
```

**No reference** (template/generator entirely in SKILL.md):
```
init-project/
└── SKILL.md              # Interactive initialization with questions
```

**Source:** [Best practices — Pattern 2: Domain-organized](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#pattern-1-high-level-guide-with-references)

---

## Description Behavior — How Claude Selects Skills

Description is the **only thing** that determines auto-loading. Claude uses **semantic matching** (not regex, not keywords) via its language model.

### Rules for Good Descriptions

```yaml
# ✅ Good — specific, with triggers
description: >
  17 Python code quality principles (DRY, SRP, LoD, KISS).
  Use during code review, refactoring, writing new modules.

# ❌ Bad — too abstract
description: Helps with code quality
```

### What to Include in Description

1. **WHAT it does** — "17 Python code quality principles"
2. **WHEN to use** — "during review, refactoring, writing new code"
3. **Keywords** — "DRY, SRP, LoD, KISS" (help semantic matching)
4. **TRIGGER conditions** (for auto-invocation) — "TRIGGER when: choosing between technologies, user compares options"

### TRIGGER Pattern in Description

For skills that should fire automatically, a TRIGGER block is added to the description:

```yaml
description: >
  ADR creation. Template with context, alternatives, decision.
  TRIGGER when: choosing between technologies/libraries, choosing an architectural pattern,
  user compares options.
```

This does not guarantee automatic invocation, but significantly increases the likelihood. If auto-invocation does not trigger, the workflow reminds to invoke the skill manually.

**Implemented for:** create-adr, completion-report.

### Limitations

- Maximum 1,024 characters
- No XML tags
- Write in third person ("Checks code...", not "I check...")

**Source:** [Best practices — Writing effective descriptions](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#writing-effective-descriptions)

---

## Token Consumption — Detailed Calculation

### Base Sizes

| Component | Lines | Tokens |
|-----------|-------|--------|
| Description (1 skill) | 2-3 | ~100 |
| SKILL.md body (short version) | 30-50 | ~300-500 |
| reference.md (full version) | 150-500 | ~1,500-5,000 |

### Scenario: 15 skills (implemented), 20-message session

**Code review (5 requests) — 3 skills with details needed:**
- Descriptions of all 15: ~1,500 tokens (always loaded)
- SKILL.md × 3: 900-1,500 tokens
- reference.md × 1-3: 1,500-5,000 tokens (Claude decides how many are needed)
- **Total: 3,400-7,500 tokens per request**

**Writing code (10 requests) — background context, details not needed:**
- Descriptions: ~1,500 tokens
- SKILL.md × 0-2 (auto-loaded): 0-600 tokens
- reference.md: not read
- **Total: 1,000-1,600 tokens per request**

**Simple questions (5 requests) — skills not needed:**
- Descriptions: ~1,500 tokens
- Everything else: 0
- **Total: 1,000 tokens per request**

### Comparison with Other Variants

| Metric | No tiering | Variant C | MCP (A/B/D) |
|--------|-----------|-----------|-------------|
| Average per session | ~100,000 | ~34,000 | ~46,000 |
| Savings | — | **66%** | 54% |
| Wasted tokens | 40-60% | 10-20% | 10-20% |

**Why C is more economical than MCP:** reference.md read via Read = data in one message. MCP response = included in tool_result and **forwarded in every subsequent request** until compressed.

---

## Strengths

### 1. Zero Code, Zero Dependencies

No MCP server, embedding provider, or database. Only .md files in `~/python-ai-skills/` + symlinks in `~/.claude/skills/`. Works on any machine with Claude Code.

### 2. Best Token Savings (-66%)

Paradoxically, the simplest variant saves the most. Reason: `reference.md` is read via `Read` tool and is not duplicated in message history, unlike MCP responses.

### 3. Live Reload

Changed `SKILL.md` or `reference.md` — Claude sees changes on the next invocation. No need to restart a server, re-index a database, or reload a session.

### 4. Git Versioning

All skills are regular .md files. Can be stored in git, PRs made, rolled back, change history tracked.

### 5. Transparency

You can see what Claude loaded — every Read tool call is displayed in chat. Unlike auto-loading with `user-invocable: false`, where it is unclear what was loaded and when.

### 6. Quick Start

Creation time: ~1 Claude Code session (15 skills + 26 reference files, including migration from flat structure). For comparison: MCP variants = 4-6 hours, OpenViking = 5-7 hours.

### 7. Description Scalability

With 15 skills (implemented) descriptions = ~1,500 tokens (<1% of context). With 100 skills = ~10,000 tokens (~2%). The system works up to 100+ skills without degradation.

---

## Weaknesses

### 1. No Semantic Search

Claude selects skills only by description (LLM semantic matching). With 30+ skills with similar descriptions, Claude may select the wrong skill or miss the right one.

**Mitigation:** Write maximally specific descriptions with trigger keywords. Avoid overlapping descriptions.

### 2. No Guarantee That reference.md Will/Won't Be Read

Claude **decides on its own** whether reference.md is needed. This can lead to:
- **Overspending:** Claude reads reference.md when SKILL.md would have been sufficient
- **Under-loading:** Claude does not read reference.md when details are needed

**Mitigation:** Clear instructions in SKILL.md: "For code review, ALWAYS read reference.md. For writing new code — the principles above are sufficient."

### 3. Manual Split into L0/L1/L2

You need to manually decide what goes in SKILL.md (short version) and what in reference.md (full version). For 15 skills from python-ai-skills (26 files) this was done in one Claude Code session.

**Status:** Completed 2026-03-16. Update incrementally when adding new skills.

### 4. No Memory Between Sessions (for skills)

Skills do not remember what worked and what did not. Each session starts from scratch.

**Mitigation:** Claude Code has its own memory system (`~/.claude/projects/*/memory/`). This is unrelated to skills, but covers the memory need.

### 5. No Automatic Profiling by Project Type

A skill does not know whether the project is a monolith or microservice. You need to either:
- Explicitly invoke `/_code-quality`
- Or rely on the project's CLAUDE.md (where the architecture type is specified)

**Mitigation:** Specify architecture type in the project's CLAUDE.md. A skill can contain the instruction: "Read the project's CLAUDE.md, find the architecture type, apply the corresponding rules."

### 6. Writing to python-ai-skills from Another Project Requires a $PWD Policy Exception

To create/edit skills from a target project (where context has accumulated) you need to allow writing to `~/python-ai-skills/` — this is an exception to the LOCAL-ONLY policy.

**Solution:** A whitelist exception was added to global `~/.claude/CLAUDE.md` (IMPLEMENTED 2026-03-16):

```markdown
##### Exceptions for writing outside $PWD

Writing outside $PWD is allowed ONLY:
- Path: `~/Henry_Bud_GitHub/python-ai-skills/**`
- Operations: creating and editing .md files
- Prohibited: deletion, renaming, writing non-.md files
- This list is FINAL — add new exceptions only after explicit user request
```

This is not "diluting" the policy, but a conscious decision: `python-ai-skills` is skill infrastructure (analogous to `.gitconfig`), not a "foreign project".

### 7. Claude May Auto-load an Unnecessary Skill (or Not Load a Needed One)

If the description is too broad — false positives. If too narrow — Claude won't invoke automatically when needed.

**Mitigation (suppressing auto-invocation):**
- `disable-model-invocation: true` — manual invocation only (implemented: init-project)
- Narrow, specific descriptions

**Mitigation (enhancing auto-invocation):**
- TRIGGER conditions in description with specific situations (implemented: create-adr, completion-report)
- Fallback via workflow: reminder to invoke manually before commit

---

## Skill Priorities

When names conflict (same skill at multiple levels):

| Priority | Level | Path |
|----------|-------|------|
| 1 (highest) | Enterprise | Managed by admin |
| 2 | Personal | `~/.claude/skills/<name>/SKILL.md` |
| 3 | Project | `.claude/skills/<name>/SKILL.md` |
| 4 (lowest) | Plugin | `<plugin>/skills/<name>/SKILL.md` |

A project skill can **override** a global one with the same name. This allows having a global `_code-quality` and a project-level `_code-quality` with additions.

**Source:** [Skills — Where skills live](https://code.claude.com/docs/en/skills.md#where-skills-live)

---

## Dynamic Content (!`command`)

Skills support preprocessing — executing shell commands **before** sending to Claude:

```yaml
---
name: project-stats
description: Current project statistics
---

## Current State
- Python files: !`find . -name "*.py" | wc -l`
- Lines of code: !`find . -name "*.py" -exec wc -l {} + | tail -1`
- Last commit: !`git log --oneline -1`
```

Claude receives the **result**, not the command. Useful for skills that need to know the project state.

**Source:** [Skills — Inject dynamic context](https://code.claude.com/docs/en/skills.md#inject-dynamic-context)

---

## context: fork + Reference Files

When using `context: fork`, the skill runs in an isolated subagent context. **Implemented** in the `_code-quality` skill:

```yaml
---
name: _code-quality
description: >
  17 Python code quality principles (DRY, KISS, YAGNI, SOLID, SSoT, LoD, Fail Fast).
  Use during code review, refactoring, writing new modules.
  Checks code-standards and naming conventions.
context: fork
agent: Explore
---

# Quality Cascade — 17 Quality Principles
...
Full principles: see [reference/quality-cascade.md](reference/quality-cascade.md)
```

The subagent **can** read reference files via Read — supporting files work normally in forked context.

**Source:** [Skills — Run skills in a subagent](https://code.claude.com/docs/en/skills.md#run-skills-in-a-subagent)

---

## python-ai-skills Structure

The `~/python-ai-skills/` repository is the single source of truth for all skills. Deployment to `~/.claude/skills/` via symlinks.

```
~/python-ai-skills/                    # Git repo (source of truth) — IMPLEMENTED 2026-03-16
├── _code-quality/                      # context: fork, agent: Explore
│   ├── SKILL.md                       # 17 principles — short checklist
│   └── reference/
│       ├── quality-cascade.md         # Full principles with anti-patterns
│       ├── code-standards.md          # Typing, docstrings, metrics
│       └── naming.md                  # Naming conventions
│
├── _error-handling/
│   ├── SKILL.md                       # Exception hierarchy, retry
│   └── reference.md                   # Full HTTP ↔ exception mapping
│
├── _security/
│   ├── SKILL.md                       # OWASP Top 10 + mandatory rules
│   └── reference/
│       ├── security.md                # Full security rules
│       └── secrets-management.md      # Pydantic Settings, .env.example, rotation
│
├── _logging/
│   ├── SKILL.md                       # Log-Driven Design, key principles
│   └── reference.md                   # AI-Readable Logging, structlog config
│
├── _testing/
│   ├── SKILL.md                       # 3 test levels, coverage ≥90%
│   └── reference.md                   # AAA pattern, fixtures, mocks
│
├── _database/
│   ├── SKILL.md                       # Repository pattern, key rules
│   └── reference.md                   # Alembic, transactions, N+1, connection pooling
│
├── _architecture/
│   ├── SKILL.md                       # DDD + Hexagonal, monolith/microservices choice
│   └── reference/
│       ├── ddd.md                     # Layers, entities, Value Objects
│       ├── hexagonal.md               # Ports, adapters, DI
│       ├── monolith.md                # Modular boundaries, shared database
│       └── microservices.md           # Isolation, communication, tracing
│
├── _linters/
│   ├── SKILL.md                       # Ruff, Mypy, Bandit, pre-commit
│   └── reference/
│       ├── linters.md                 # Full tool configuration
│       └── ci-cd.md                   # CI pipeline, coverage gate
│
├── _docker/
│   ├── SKILL.md                       # Multi-stage, security, health checks
│   └── reference/
│       ├── docker.md                  # Dockerfile, Compose, .dockerignore
│       └── production.md              # Graceful shutdown, monitoring
│
├── _http/
│   ├── SKILL.md                       # httpx, timeout, Circuit Breaker
│   └── reference.md                   # Retry, logging, error handling
│
├── _caching/
│   ├── SKILL.md                       # Redis, TTL, graceful degradation
│   └── reference.md                   # Patterns, invalidation, naming
│
├── _docworkflow/
│   ├── SKILL.md                       # 6-phase pipeline, checklist
│   └── reference/
│       ├── workflow.md                # Full documentation pipeline
│       ├── backlog.md                 # TASK-NNN template
│       ├── planning.md                # Plan format
│       └── git-conventions.md         # Commit format
│
├── _adr/                               # Hybrid trigger: auto + manual
│   ├── SKILL.md                       # ADR template, creation rules
│   └── reference.md                   # Full template and statuses
│
├── _report/                            # Hybrid trigger: auto + manual
│   ├── SKILL.md                       # Report template, rules
│   └── reference.md                   # Full template with metrics
│
├── _init/
│   └── SKILL.md                       # Interactive initialization (disable-model-invocation)
│
├── docs/
│   └── 2026-03-15-skills-file-convention-architecture.md
│
├── CLAUDE.md                          # Skill catalog + workflow (v3.1)
└── CHANGELOG.md

~/.claude/skills/                      # Symlinks (deployment) — CREATED 2026-03-16
├── _code-quality → ~/python-ai-skills/_code-quality
├── _error-handling → ~/python-ai-skills/_error-handling
├── _security → ~/python-ai-skills/_security
├── _logging → ~/python-ai-skills/_logging
├── _testing → ~/python-ai-skills/_testing
├── _database → ~/python-ai-skills/_database
├── _architecture → ~/python-ai-skills/_architecture
├── _linters → ~/python-ai-skills/_linters
├── _docker → ~/python-ai-skills/_docker
├── _http → ~/python-ai-skills/_http
├── _caching → ~/python-ai-skills/_caching
├── _docworkflow → ~/python-ai-skills/_docworkflow
├── _adr → ~/python-ai-skills/_adr
├── _report → ~/python-ai-skills/_report
└── _init → ~/python-ai-skills/_init
```

### Deploying Symlinks

Symlinks are created manually (no script). When adding a new skill — one command:

```bash
# Creating all symlinks (one-time)
mkdir -p ~/.claude/skills
for skill_dir in ~/Henry_Bud_GitHub/python-ai-skills/_*/; do
    [ -f "$skill_dir/SKILL.md" ] && ln -sfn "$skill_dir" "$HOME/.claude/skills/$(basename "$skill_dir")"
done

# Adding a new skill (with _ prefix)
ln -sfn ~/Henry_Bud_GitHub/python-ai-skills/_new-skill ~/.claude/skills/_new-skill
```

**Status:** 15 symlinks created 2026-03-16.

---

## Cross-project Workflow: Creating Skills from a Target Project

### Problem

Context for a new skill accumulates in the target project (e.g., `claude_bot`), but skills live in `~/python-ai-skills/`. Without a $PWD policy exception, it is impossible to write a skill from the target project.

### Solution

A whitelist exception for `~/python-ai-skills/` was added to global `~/.claude/CLAUDE.md`. This allows from any project:

1. **Create a new skill** — when a reusable pattern is identified during work
2. **Update an existing skill** — when a better approach is found in the target project
3. **Add reference materials** — when examples have accumulated

### Workflow

```
Project claude_bot                     ~/python-ai-skills/
┌─────────────────────┐                ┌─────────────────────┐
│ Working on code     │                │                     │
│ Identify pattern    │ ── write ──→   │ _error-handling/     │
│ Context is here     │                │   SKILL.md (new)    │
│                     │                │   reference.md      │
└─────────────────────┘                └─────────────────────┘
                                              │
                                         symlink in
                                       ~/.claude/skills/
                                              │
                                              ▼
                                       Available in ALL
                                       projects instantly
```

### Workflow Recommendations

- **Create a skill when the pattern is confirmed** — not after first use, but when it has repeated 2-3 times
- **Start with SKILL.md** — short version (30-50 lines). Add reference.md later when examples accumulate
- **Commit to python-ai-skills separately** — remember that writing to another repo does not create a commit automatically. After the session, go to `~/python-ai-skills/` and commit changes

---

## When to Switch to Another Variant

| Signal | Action |
|--------|--------|
| Claude often loads the wrong skill | Refine descriptions. If that doesn't help → MCP with search (Variant B) |
| Skills grew to 30+ | Consider MCP with FTS5 (Variant B) |
| Claude always reads reference.md | SKILL.md is not informative enough — expand the short version |
| Claude never reads reference.md | reference.md is redundant — can be removed |
| Need memory between sessions (for skills) | Use Claude Code memory or consider OpenViking |
| Token cost is critical | Variant A (MCP tiering) — gives explicit L0/L1/L2 control |

---

## Implementation Decisions (2026-03-16)

The section below documents key decisions made during implementation. The original plan above is preserved for context.

### Differences from Original Plan

| Aspect | Plan | Implementation | Reason |
|--------|------|---------------|--------|
| Number of skills | 8 (mentioned "10 core") | **15** | All 26 original files covered through grouping |
| Original files | Not defined | Moved to reference (git mv) | Variant D — SSoT, no duplication |
| CLAUDE.md | Not mentioned | Skill catalog + workflow (v3.1) | Variant B — entry point + navigation |
| deploy-skills.sh | Script in repo | Manual symlinks | KISS — 15 commands once |
| security/reference/ | auth.md, injection.md, validation.md | security.md + secrets-management.md | Files from plan did not exist |
| context: fork | Described, not applied | quality-cascade | Only skill for deep review |
| init-project | Empty placeholder | Interactive with questions | Standardizing project setup |
| process/ files | 2 files (adr, completion-report) | 6 files → 3 skills + workflow | workflow.md, backlog.md, planning.md, git-conventions.md added |
| Trigger model | Deferred | Hybrid: auto (TRIGGER in description) + manual fallback (workflow) | Balance: won't forget, but no false positives |
| Naming | No prefix | `_` prefix for all skills | Visual distinction of custom skills from built-in |

### Additional Skills (not in plan)

| Skill | Source | Why added |
|-------|--------|----------|
| database | development/database.md | Independent topic: Repository, migrations, N+1 |
| architecture | architecture/*.md (4 files) | Fundamental patterns: DDD, Hexagonal, monolith/microservices |
| linters | quality/linters.md + ci-cd.md | Largest file (221 lines), CI pipeline |
| docker | operations/docker.md + production.md | Containerization + production requirements |
| http-clients | integrations/http-clients.md | HTTP client, Circuit Breaker — independent topic |
| caching | integrations/caching.md | Redis, TTL — independent topic |
| workflow | process/*.md (4 files) | Documentation pipeline: 6 phases |

### Reference File Structure

Two variants depending on the number of reference files:

- **Single file** → `reference.md` (error-handling, logging, testing, database, http-clients, caching, create-adr, completion-report)
- **Multiple files** → `reference/` folder (quality-cascade, security, architecture, linters, docker, workflow)

### Trigger Model for create-adr and completion-report (decided 2026-03-16)

**Model: hybrid (auto + manual fallback)**

- Both skills **do not have** `disable-model-invocation` — Claude can invoke them automatically
- Description contains specific TRIGGER conditions for automatic firing
- If auto-trigger does not fire — the workflow SKILL.md reminds to invoke them manually before commit
- create-adr: trigger on technology choice, architectural patterns, option comparison
- completion-report: trigger on feature completion, readiness to commit

---

## Sources

- [Claude Code — Extend Claude with skills](https://code.claude.com/docs/en/skills.md)
- [Claude API — Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Claude Code — Manage costs effectively](https://code.claude.com/docs/en/costs.md)
- [Claude Code — Features overview](https://code.claude.com/docs/en/features-overview.md)
