# python-ai-skills — Claude Code Skills

project_type: dev

> A collection of skills for high-quality Python 3.11+ application development.
> Each skill is a folder with `SKILL.md` (short version) + `reference.md` (full version).
> The `_` prefix distinguishes custom skills from built-in ones.

---

## Skill Catalog

| Skill | Command | Description |
|-------|---------|-------------|
| _code-quality | `/_code-quality` | 17 quality principles (DRY, KISS, YAGNI, SOLID); not security/tests/linters |
| _error-handling | `/_error-handling` | Exception hierarchy, HTTP mapping, retry; not logging or HTTP-client transport |
| _security | `/_security` | OWASP Top 10, validation, secrets; not general quality or linter setup |
| _logging | `/_logging` | Structured logging, Correlation ID, sanitization; not exception design |
| _testing | `/_testing` | 3 test levels, coverage ≥90%, pytest; not linters or quality review |
| _database | `/_database` | Repository pattern, migrations, transactions; not caching or HTTP |
| _architecture | `/_architecture` | DDD, Hexagonal, monolith vs microservices; not a single tech choice (_adr) |
| _linters | `/_linters` | Ruff, Mypy, Bandit, pre-commit, CI; not tests or principle-level review |
| _docker | `/_docker` | Dockerfile, Compose, health checks; not CI/lint config |
| _http | `/_http` | httpx, timeout, retry, Circuit Breaker; not server errors or caching |
| _caching | `/_caching` | Redis, TTL, invalidation, graceful degradation; not source-of-truth DB |
| _docworkflow | `/_docworkflow` | Docs pipeline backlog → commit for TASK-NNN legacy projects; not do-feature/GRACE projects, not final report only (_report) |
| _adr | `/_adr` | Architecture Decision Record generator; not a full docs pipeline |
| _report | `/_report` | Feature completion report; not mid-work docs (_docworkflow) |
| _init | `/_init` | New project initialization (slash-only, no model auto-invoke) |
| py-supervisor | (agent) | Post-hoc pipeline compliance audit |

> **SSoT for invocation:** the `TRIGGER`/`SKIP` lines in each `SKILL.md` frontmatter are the single source of truth for when a skill fires. The `not …` hints above are a compact routing aid, not a duplicate of those lines.

### Workflow, GRACE & utility skills (33)

- **Orchestrators:** `do-feature` (shipped code: full mode for task level 1, `--lite` for level 2 — levels in `claude-home/CLAUDE.md`), `do-autopilot` (draft → executable chain), `do-multiagent` (parallel team over bead graph)
- **best-\* family:** `best-research` (analysis engine, SSoT), `best-recommend` (recommendation format atom), `best-approach` / `best-rank` / `best-questions` (thin wrappers)
- **grace-\* (14):** `grace-init`, `grace-plan`, `grace-execute`, `grace-multiagent-execute`, `grace-refresh`, `grace-reviewer`, `grace-refactor`, `grace-fix`, `grace-ask`, `grace-status`, `grace-verification`, `grace-explainer`, `grace-cli`, `grace-setup-subagents`
- **git & sync:** `git-commit`, `git-branch`, `git-finish` (closes the session: docs and plans always first → merge → delete → push → uppercase verdict), `project-sync`, `projects-sync`, `beads-sync`
- **audit:** `full-audit` (deterministic code+docs audit), `audit-loop` (5-round codex cross-review)
- **monitoring:** `progress-watch` (four-line progress report on an interval, self-terminating, read-only), `plan-progress-page` (proportional HTML progress page of a plan, published as an Artifact)
- **misc:** `customer-tz` (customer-facing TZ from raw input)

> The catalog table above covers only the `_*` quality skills; this grouped list covers the rest. Full inventory = every repo dir with a `SKILL.md` (48 total); `make install-symlinks` links them all.

---

## When to Use Each Skill

| Task | Skills |
|------|--------|
| Writing code | _code-quality, _error-handling |
| Code review | _code-quality, _security, _linters |
| Database work | _database, _error-handling |
| HTTP integrations | _http, _caching |
| CI setup | _linters |
| Deployment | _docker, _security |
| Testing | _testing |
| New project | _init, _architecture |
| Architecture decision | _architecture, _adr |
| Feature completed | _report; _docworkflow (TASK-NNN legacy projects only) |
| Pipeline audit | py-supervisor |
| Starting a task | pick the task level (`claude-home/CLAUDE.md` → Dev-project workflow): do-feature for levels 1–2; _docworkflow (TASK-NNN legacy projects) |

---

## Required Workflow

### Verify Before Act (BEFORE every code change)

| Action | Check BEFORE executing |
|--------|------------------------|
| Creating a file | File does NOT exist |
| Editing | Read current content first |
| Deleting | Check all dependencies and references |
| Writing code | No similar code exists (DRY) |
| Adding a feature | It is needed NOW (YAGNI) |

### Changelog

- Format: [Keep a Changelog](https://keepachangelog.com/)
- Sections: Added, Changed, Deprecated, Removed, Fixed, Security
- Every change → entry in `Unreleased`

### Skill Distribution (symlinks)

This repo is the **SSoT** for the global Claude config. `~/.claude` links back via symlinks — there is no plugin install step.

- Bootstrap / after structural changes: `make install-symlinks` (idempotent, safe to re-run).
- New machine: clone the repo, then `make install-symlinks` — as a **non-root** user (`bypassPermissions` refuses root). Prerequisites and what the installer does not carry (plugins, MCP servers, project memory, `bd bootstrap`): `README.md` → Installation.
- Cross-machine sync: `/project-sync` (code via GitHub) + re-run the installer on each machine to regenerate links.
- `settings.json` is **rendered** from `claude-home/settings.json.template` (it needs absolute per-machine hook paths, so it is generated, not symlinked). `extraKnownMarketplaces` lives in `~/.claude/settings.local.json` — never committed, deep-merged by Claude on top. `hooks/` and `scripts/` are symlinked like everything else.
- **Runtime-owned keys.** `model` (written by `/model`), `enabledPlugins` (written by `claude plugin enable` — it targets `settings.json`, and the copy in `settings.local.json` is ignored), `autoMode` (written by `/auto-mode-setup` and the Auto mode tab of `/permissions`; the classifier reads it only from `~/.claude/settings.json`), `modelSettings` and `voiceEnabled` are carried over from the live file on every render and masked in the drift guard. Do not put them in the template; change `autoMode` through `/permissions` or by editing the live file, then check with `claude auto-mode config`.
- Skills are linked into `~/.codex/skills/` as well, from the repo directly. Same list, one SSoT.
- `claude-home/model-registry.json` is symlinked too (which model serves which role/tier, with launch flags and timeouts). The runtime state it drives — `~/.claude/model-journal.jsonl` and `~/.claude/model-penalties.json` — is machine-local and never committed. Read the journal with `~/.claude/scripts/model-stats.py`.
- The bootstrap `pre-commit` hook is installed into this checkout too (`.git/hooks/` is not versioned). Quality gate: `.pre-commit-config.yaml` — gitleaks staged scan, template JSON validity, settings render test (hook paths under a `CLAUDE_HOME` with a space), hook regression suite. Full sweep: `make test`.

> No version bump or `claude plugins update` is needed — edits to any skill/agent/command/instruction are **live immediately** through the symlink. Adding or removing a skill/agent/command → re-run `make install-symlinks`. After editing `settings.json.template`, re-run the installer to re-render.

> **"Live immediately" has one exception, and it bites.** Skills, agents and commands are read when invoked, so an edit reaches even a running session. `CLAUDE.md` is read **at session start** — a session already running never learns a rule you add now. Measured 2026-09-22: 14 of 17 active sessions predated a rule added an hour earlier and could not have followed it. If a new rule must reach live sessions, deliver it as a **hook** (`PreToolUse` + `hookSpecificOutput.additionalContext` — see `claude-home/hooks/delegation-pool-nudge.sh`), not as a paragraph in `CLAUDE.md`.

---

## Multi-machine consistency (moved from the global CLAUDE.md, 2026-10-13)

**Rule:** The SSoT instruction file is `python-ai-skills/claude-home/CLAUDE.md` (in git). `~/.claude/CLAUDE.md` is a symlink to it; `~/.claude/AGENTS.md` links to that link, and `~/.codex/AGENTS.md` links straight to the repo file (both made by `make install-symlinks`). Keep the global rules in this one file: Codex reads `~/.codex/AGENTS.md` as a single file, expands no `@`-imports and ignores `~/.claude/rules/` (so `RTK.md` and `rules/python-dev.md` were folded in, bd `python-ai-skills-lvt.1`). Cross-machine identity is provided by git + `make install-symlinks`.

**Rule:** Shared config (`settings.json`, `config.toml`) MUST be identical across machines.

**Rule:** Machine-specific settings live in `~/.claude/settings.local.json` and `~/.codex/config.toml` profiles (not synced).

**Exception (verified 2026-08-31):** `enabledPlugins` does NOT work from `settings.local.json` — `claude plugin enable` writes it into `~/.claude/settings.json`, and only that copy is honoured. Three plugins marked enabled in the local file loaded as disabled for months. Enable plugins with `claude plugin enable <name> --scope user`, never by hand-editing the local file; `install-claude-symlinks.sh` carries the key over on every render (see also `model`, written by `/model`).

**Rule:** Secrets (`.credentials.json`, `.env`) — never in git; per-machine only.

**Rule:** All repo skills (48 as of 2026-10-15; SSoT is the set of repo dirs with a `SKILL.md`) are symlinked into BOTH `~/.claude/skills/` and `~/.codex/skills/` by `make install-symlinks` — one SSoT, no per-tool copies.

**Exception:** Anthropic-proprietary skills (currently `pptx`) live in `~/.claude/skills/` as real directories OUTSIDE the repo SSoT: their license forbids copying/redistribution, so they are never committed, never linked into `~/.codex/`, and not counted above. They are managed by Claude Code itself and may need reinstall after a `~/.claude` rebuild. Linking straight from the repo (never `~/.codex/skills/<n>` → `~/.claude/skills/<n>`) keeps Codex working when `~/.claude` is rebuilt. Set `CODEX_HOME` to a path with no `skills/` dir to opt a machine out.

---

## Language Standards

| What | Language | Example |
|------|----------|---------|
| Documentation (all pipeline artifacts) | English | TASK, REQ, PLAN, ADR, reports, CHANGELOG |
| Code comments | English | `# Check session TTL` |
| Commit messages | English | `feat(M-SYNC): add user sender service` |
| File names, variables, functions | English | `user_sender.py`, `def send_outreach()` |

> **Rule**: all documentation generated by this project's skills must be in English.
> All content in this project is in English.

---

**Version**: 3.7

## Non-Interactive Shell Commands

**ALWAYS use non-interactive flags** with file operations to avoid hanging on confirmation prompts.

Shell commands like `cp`, `mv`, and `rm` may be aliased to include `-i` (interactive) mode on some systems, causing the agent to hang indefinitely waiting for y/n input.

**Use these forms instead:**
```bash
# Force overwrite without prompting
cp -f source dest           # NOT: cp source dest
mv -f source dest           # NOT: mv source dest
rm -f file                  # NOT: rm file

# For recursive operations
rm -rf directory            # NOT: rm -r directory
cp -rf source dest          # NOT: cp -r source dest
```

**Other commands that may prompt:**
- `scp` - use `-o BatchMode=yes` for non-interactive
- `ssh` - use `-o BatchMode=yes` to fail instead of prompting
- `apt-get` - use `-y` flag
- `brew` - use `HOMEBREW_NO_AUTO_UPDATE=1` env var

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:970c3bf2 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:
   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   bd dolt push
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->

<!-- BEGIN BEADS CODEX SETUP: generated by bd setup codex -->
## Beads Issue Tracker

Use Beads (`bd`) for durable task tracking in repositories that include it. Use the `beads` skill at `.agents/skills/beads/SKILL.md` (project install) or `~/.agents/skills/beads/SKILL.md` (global install) for Beads workflow guidance, then use the `bd` CLI for issue operations.

### Quick Reference

```bash
bd ready                # Find available work
bd show <id>            # View issue details
bd update <id> --claim  # Claim work
bd close <id>           # Complete work
bd prime                # Refresh Beads context
```

### Rules

- Use `bd` for all task tracking; do not create markdown TODO lists.
- Run `bd prime` when Beads context is missing or stale. Codex 0.129.0+ can load Beads context automatically through native hooks; use `/hooks` to inspect or toggle them.
- Keep persistent project memory in Beads via `bd remember`; do not create ad hoc memory files.

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.
<!-- END BEADS CODEX SETUP -->

> The sections below are hand-written and MUST stay outside the managed
> `BEADS INTEGRATION` and `BEADS CODEX SETUP` blocks above: `bd init` and `bd setup codex` rewrite everything between
> their markers (`bd setup claude` skips the `CLAUDE.md` symlink) and would silently delete them. `Agent Context Profiles` and
> `Session Completion` are NOT hand-written — `bd` regenerates them inside the
> block, so they must not be duplicated out here.

## Commit Authority (resolves the Beads-block conflict)

The Beads block declares a `Conservative` default: "do not run git commits …
unless explicitly asked". The global CLAUDE.md "Commit Convention" says the
opposite: "Commit without user confirmation when work is atomic and verified".

**Resolution (user decision 2026-08-31): the global rule wins for commits.**

- **Commit** without asking once the work is atomic AND verified by a command
  whose output can be quoted. Commit-time hooks are the quality gate; a failing
  hook means fix the cause, never bypass it.
- **Push** stays untouched: `git push` of code only on explicit request
  (global CLAUDE.md → "Git Push Policy"). `bd dolt push` remains allowed at
  session close.
- Everything else in the Beads block still applies — this overrides only its
  commit clause, not its push or sync clauses.

## Task Tracking Scope (resolves the TodoWrite/TaskCreate conflict)

The Beads block says "do NOT use TodoWrite, TaskCreate, or markdown TODO
lists", while the harness itself emits reminders to use its task list every
session — a rule the platform breaks automatically.

**Resolution (user decision 2026-08-31): split by durability.**

- **`bd` is the single source of truth for work tracking.** Anything that must
  outlive the session — issues, status, dependencies, links to commits and
  branches — lives in beads. Markdown TODO lists stay prohibited.
- **The harness task list is a within-session scratchpad**, showing progress
  during long sessions. It records nothing and never substitutes for `bd`.
  Using it is optional; not using it is not a violation.

## Memory Scoping (Beads vs auto-memory)

The Beads block above says "do NOT use MEMORY.md files". That prohibition is scoped to **project/task knowledge only** — it does not apply to the harness auto-memory:

- **Project and workflow insights** (architecture decisions, task context, codebase gotchas) → `bd remember` / `bd memories` — they must travel with the Dolt workspace across machines.
- **User-level facts** (preferences, feedback, communication style, decision thresholds) → harness auto-memory (`~/.claude/projects/<project>/memory/`) — outside the repo, loaded into every session, endorsed by the global CLAUDE.md "Memory System Update" section.

Each system owns its zone (SSoT). Do not delete or refuse the auto-memory `MEMORY.md` on the basis of the Beads block.
