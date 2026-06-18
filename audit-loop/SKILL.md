---
name: audit-loop
description: >
  5-round cross-review loop: codex audits claude's fixes, claude analyzes
  codex report, detects stagnation, auto-applies decisions at confidence ≥70%,
  asks via /best-questions when <70%, produces a detailed final report.
  TRIGGER: user invokes /audit-loop in a dev-workflow project after a
  series of bugfixes and wants a cross-review by codex.
  SKIP: not a dev-workflow project, life-project, codex CLI missing.
argument-hint: "[--max-rounds=5] [--start-round=N] [--finish] [--abort] [--resume] [--dry-run]"
---

# /audit-loop — Codex × Claude Cross-Review Loop

> Apply **only** to dev-projects governed by `do-feature` (presence of `docs/superpowers/`, `docs/development-plan.xml`). Refuse with a clear error in life-projects and plain repos.

## What it does

One skill = up to 5 audit rounds. Each round:
1. **Codex** audits the whole repo read-only — finds issues remaining after Claude's fixes, including repeated ones.
2. **Claude** (this agent) reads the report, applies fixes via GRACE skills, updates docs, auto-applies at confidence ≥70%, batches questions via a single `/best-questions` session at <70%.
3. Stagnation detector compares rounds by `(module_id, category, kind)`.
4. On round 5 — final report + auto-applied review section + Beads-issue creation prompt for any open findings.

## Atomicity & rollback (transaction model)

Each round is a transaction.

### Round start
```bash
git tag "audit-loop/R${N}/start" HEAD
echo "$(date -Iseconds)" > docs/audit-loop/.round-${N}.startedat
```

### Round abort / failure / user `--abort`
The skill prints rollback instructions and stops. **Never** auto-rollback without explicit user consent.
```
✗ Round ${N} aborted. To rollback uncommitted/partial fixes:
   git reset --hard audit-loop/R${N}/start
   git tag -d audit-loop/R${N}/start    # only if discarding the round
To resume the round in place: /audit-loop --resume
```

**Lock cleanup is mandatory on every exit path.** Before printing the abort message and returning control, the skill MUST call `python3 ~/.claude/skills/audit-loop/lib/lock.py release`. Exit paths that release the lock:
1. Normal cycle finish (after round 5 / `--finish`)
2. `--abort` flag
3. Round-completion-gate failure
4. Codex parse failure / non-zero exit
5. Round timeout hard-pause (Step 7b)
6. Kill-switch (`stop` / `pause` / `abort` mid-step)
7. Pre-flight failure **after** `lock.py acquire` succeeded

If the skill crashes before release runs, `lib/lock.py` auto-overwrites the stale lock on the next acquire (PID liveness check via `os.kill(pid, 0)`) — so a missed release is recoverable, not fatal.

### Round commit policy
- Each AUTO-applied finding produces **one commit** with conventional commits + MODULE_ID scope:
  - Code change: `fix(<MODULE_ID>): <kind> — auto-applied conf=<NN>% [audit-loop R${N}]`
  - Doc-only change: `docs(<MODULE_ID>): <kind> — auto-applied [audit-loop R${N}]`
  - Refactor: `refactor(<MODULE_ID>): <kind> — auto-applied [audit-loop R${N}]`
- Each ASKED finding (after user choice in batch QA) → one commit with the same template, suffixed `[audit-loop R${N} qa]`.
- Each ADR creation → `docs(adr): ADR-NNN — <topic> [audit-loop R${N}]`.
- Round close (after gate passes) → `chore(audit-loop): R${N} closed — <C>c/<M>m/<Min>min, <fixed> fixed`.
- Cycle close → `chore(audit-loop): cycle <YYYYMMDD> — N rounds, X critical closed, Y open`.
- Never `git push` automatically (policy-level rule).

## Idempotency & resume

`/audit-loop` invocation logic:

1. If `docs/audit-loop/state.json` does NOT exist → start fresh, `current_round=1`.
2. If `state.json` exists and last round completed (gate passed, round-close commit present) → start `current_round = last_n + 1` (or finish if last_n == max_rounds).
3. If `state.json` exists and last round NOT completed → **prompt user**:
   ```
   Found incomplete round ${N} from <ISO timestamp>.
   Options:
     [r] resume in place — continue findings-loop from where we stopped
     [s] restart round  — git reset --hard audit-loop/R${N}/start, redo round
     [a] abort cycle    — keep state, exit; rollback manually if needed
   ```
4. `--start-round=N` overrides detection (manual recovery only).
5. `--abort` writes `state.aborted=true`, exits without rollback.
6. `--resume` is shorthand for option `r` above.

State invariant: every `rounds[N]` entry has either `completed_at` (success) or `aborted_at` (skipped / manually closed).

## Kill-switch / pause protocol

Inside a long step (codex running, batch QA mid-question), if user types **stop** / **pause** / **abort**:

1. Mark current step as interrupted in `state.json` (`rounds[N].interrupted_at`).
2. If codex is still running → kill the background process (`kill <pid>` from the `Bash run_in_background` handle).
3. Release lock: `python3 ~/.claude/skills/audit-loop/lib/lock.py release`.
4. Print rollback instructions (see Round abort above).
5. Do NOT auto-rollback. User decides via `--resume` / `--abort` / manual `git reset`.

## MCP integration (targeted, not carpet bombing)

### Context7 — extended triggers

Call `mcp__context7__resolve-library-id` → `query-docs` (in this order) **mandatory** in each of 4 cases:

1. **First contact** — third-party library first encountered in current cycle session
2. **Version bump** — library version in `pyproject.toml` / `uv.lock` differs from when the touched code was written (check via `git log` of the manifest)
3. **Library error** — finding contains exception/traceback referencing a third-party library
4. **Auto-apply on library API** — confidence rubric requires Context7 evidence for the +20 factor

**Skip** Context7 for: stdlib, pytest, project-internal modules, obvious bugs unrelated to library API.

Persist Context7 documents **inline** in `round-N.md` under issue-id (traceability + DRY for next rounds).

### Sequential-thinking — only two points

Call `mcp__sequential-thinking__sequentialthinking` **only** at:

1. **Stagnation handling** (round ≥2 with ≥50% repeated criticals): formal decomposition of "why fixes don't close the root". Structure: (a) what exactly repeats, (b) root-cause hypotheses, (c) why prior fix didn't work, (d) alternative approaches.
2. **Final report (round 5)**, "Why errors didn't end" section — **only if** at least one stagnation episode happened in the cycle. Otherwise: "N/A, no stagnation".

**Do not** use sequential-thinking for routine round-completion-gate, ordinary findings, or confidence calculation. The 5-factor rubric already provides structure.

### Reasoning trace persistence

Sequential-thinking output → `state.json.rounds[N].stagnation_reasoning` (next rounds read it to avoid re-thinking — DRY).

## Progress reporting (mandatory at every step)

### Step boundaries

Before a step:    `▶ R{N}/5 · {step-name} · started`
After a step:     `✓ R{N}/5 · {step-name} · {one-line summary} · {duration}s`
On failure:       `✗ R{N}/5 · {step-name} · FAILED: {reason}`

`step-name` ∈ {`pre-flight`, `pre-round-hooks`, `codex-audit`, `parse+stagnation`, `findings-loop`, `batch-qa`, `round-completion-gate`, `round-md`, `final-report`}.

### Codex live-monitoring (mandatory)

Codex may run 2–10 minutes. Run it via background + Monitor, NOT synchronously:

1. Start with `Bash run_in_background=true`:
   ```bash
   codex exec -s read-only --cd "$PWD" "$PROMPT" \
     > docs/audit-loop/round-${N}.codex.log 2>&1
   ```
2. Open `Monitor` on `docs/audit-loop/round-${N}.codex.log`.
3. Every ~15 seconds print heartbeat: `⏳ codex running · {elapsed}s · last: {truncated 80 chars}`
4. On clean exit — parse JSON (with fallback, see Codex output validation), proceed.
5. On non-zero exit — `✗` marker with log tail.

### Findings table (after codex-audit)

```
Findings R{N} · {C}c / {M}m / {Min}min · stagnation: yes/no
- [critical] M-PREPROC · src/foo.py:42 · missing-await · repeated=yes
- [critical] M-VOICE   · src/bar.py:88 · race-condition · repeated=no
- [medium]   M-PREPROC · src/foo.py:120 · duplicate-validation · repeated=no
...
```

### Per-finding markers

Auto-apply (confidence ≥70%):
```
→ R{N} · fnd-7 [critical M-PREPROC] · grace-fix · confidence 82% · AUTO
✓ R{N} · fnd-7 · applied · commit abc1234
```
Batched-ask (confidence <70%): collect during findings-loop, ask all at once in `batch-qa` step.
```
? R{N} · fnd-12 [medium M-VOICE] · confidence 55% · queued for batch-qa
```
Defer / document:
```
↪ R{N} · fnd-9 · DEFERRED → ADR-NNN
```

### Round summary block (mandatory after gate)

Template + rules: `reference/round-summary.md`. Data is a projection of `state.json` — no duplication.

### Final report announcement

```
═══ AUDIT-LOOP COMPLETE ═══
rounds: 5 · total findings: {total}
closed: {closed} · open: {open} · documented: {adr-count}
GRACE skills used: grace-fix×N, grace-refactor×N, grace-refresh×N, /qa×N
auto-applied (review needed): {count}
📊 Full report: docs/reports/YYYYMMDD_audit-loop.md
```

### Output rules
1. One marker — one line. No paragraphs.
2. Don't duplicate `state.json` into chat. Markers are UX; `state.json` is SSoT.
3. Don't go silent for >30 seconds. Heartbeat is mandatory in long steps.
4. Failure visible immediately — `✗` marker before any abort.

## Pre-flight (mandatory, abort otherwise)

```bash
test -d docs/superpowers || { echo "ERROR: not a dev-workflow project"; exit 1; }
test -f docs/development-plan.xml || { echo "ERROR: missing development-plan.xml"; exit 1; }
command -v codex >/dev/null || { echo "ERROR: codex CLI not installed"; exit 1; }
# Pre-commit is a load-bearing gate — hard ERROR, not WARN.
test -f .pre-commit-config.yaml -o -x .git/hooks/pre-commit || { echo "ERROR: pre-commit hooks missing — install before audit-loop"; exit 1; }
for s in grace-fix grace-refactor grace-refresh best-questions _code-quality _adr; do
  test -d ~/.claude/skills/$s || { echo "ERROR: missing skill $s"; exit 1; }
done
git diff --quiet HEAD || { echo "WARN: working tree dirty — commit or stash before audit-loop"; }
mkdir -p docs/audit-loop docs/reports
# Per-project config (optional override of defaults).
test -f docs/audit-loop/config.toml || cp ~/.claude/skills/audit-loop/config.toml.template docs/audit-loop/config.toml
# Concurrency lock — fails if another audit-loop holds the repo.
python3 ~/.claude/skills/audit-loop/lib/lock.py acquire || exit 2
```

If pre-flight fails — DO NOT start the cycle. Tell the user the cause.

**Config**: `docs/audit-loop/config.toml` (per-project) overrides defaults from `config.toml.template`. Thresholds (70/30 gate, 60% Context7-less ceiling, 50% stagnation, 60min/180min round timeouts, prompt_version) are read from there — do not hard-code in chat.

**Lock release**: on normal finish, `--abort`, `--finish`, or fatal error, call `python3 ~/.claude/skills/audit-loop/lib/lock.py release`. Stale locks (dead PID) auto-overwrite on next acquire.

## State schema

Full schema + invariants: `reference/state-schema.md`. SSoT at `docs/audit-loop/state.json` (versioned in git). Key invariants: fingerprint = `sha1(module_id|category|kind)[:8]`; every round entry has `completed_at` XOR `aborted_at`; `prompt_version` frozen on R1, mismatch on R{N>1} → abort.

## Per-round protocol

### Step 1. Pre-round hooks

```bash
git status --short > docs/audit-loop/round-${N}-gitstatus.txt
pre-commit run --all-files > docs/audit-loop/round-${N}-hooks.txt 2>&1 || true
```

If hooks fail — these are the **first issues** for the round, surfaced before content audit.

### Step 2. Run codex

Full prompt (security clauses, inputs, output schema): `reference/codex-prompt.md`. Pass via heredoc to `codex exec -s read-only --cd "$PWD"`. Save exit code, stderr, log path to `state.json.rounds[N]`.

### Step 3. Codex output validation + parse

```bash
python3 ~/.claude/skills/audit-loop/lib/codex_parse.py docs/audit-loop/round-${N}.json
```

The helper: parses raw output (3 fallbacks: direct → strip fences → first balanced `{...}`), validates schema (`round`, `summary`, `findings[].severity ∈ {critical,medium,minor}`), adds `fingerprint = sha1(module_id|category|kind)[:8]` per finding, rewrites the file in-place. Exit 0 on success, 2 on unparseable → `✗ codex output unparseable`, round aborts. User can `--resume` or `--abort`.

### Step 4. Stagnation detection

```bash
python3 ~/.claude/skills/audit-loop/lib/stagnation.py \
  docs/audit-loop/round-${N}.json \
  docs/audit-loop/round-$((N-1)).json \
  "$(jq -r '.thresholds.stagnation_overlap // 0.5' docs/audit-loop/config.toml 2>/dev/null || echo 0.5)"
```

Outputs JSON: `{stagnation, repeated, prev_critical, repeated_fingerprints}`. Persist into `state.json.rounds[N].stagnation_with_prev`. R1 always returns `stagnation=false`.

### Step 5. Findings-loop (Claude processes each finding)

For each finding, in order critical → medium → minor:

1. **Read referenced file** via Read tool at `file:line`.
2. **Pick GRACE skill** by category:
   - `category=bug` → `grace-fix`
   - `category=principle` or refactor needed → `grace-refactor`
   - `category=contract` → edit MODULE_CONTRACT + `grace-refresh`
   - `category=test` → `superpowers:test-driven-development`
   - multiple independent fixes → `superpowers:dispatching-parallel-agents`
3. **Verify via Context7** for library decisions (per triggers above). No Context7 evidence → confidence ceiling 60%.
4. **Compute confidence** (5 factors × 20%):
   ```
   confidence = 0
   + 20 if context7_evidence else 0
   + 20 if no_quality_principle_violated else 0
   + 20 if precedent_in_project else 0
   + 20 if grace_graph_unaffected_or_refreshed else 0
   + 20 if reversible (single file/function, no migration) else 0
   - 10 per disputed factor
   - category_penalty (from prior anti-abuse)
   ```
   Minimum 3 factors with **concrete refs** (file:line, doc URL, grace-graph node) — otherwise reject confidence and route to batch-qa.
5. **Per-fingerprint budget gate** (before confidence check):
   ```bash
   python3 ~/.claude/skills/audit-loop/lib/budget.py <fingerprint> <limit>
   ```
   If `over_budget=true` (fingerprint already appeared in ≥`max_rounds_per_fingerprint` prior rounds without closing) → **auto-defer**: skip grace-fix, append to `state.json.rounds[N].deferred` with `reason: "budget exhausted after N rounds"`, surface in final report's Beads-creation list. Marker: `↪ R{N} · fnd-X · BUDGET-EXHAUSTED → auto-defer`. Rationale: prevents infinite loops on truly hard issues; user decides via Beads triage.

6. **Decision gate 70/30**:
   - `confidence ≥ 70%` → apply, then **before commit** print diff preview:
     ```
     → R{N} · fnd-7 · AUTO conf=82% · diff preview:
     <git diff --stat>
     <git diff (≤40 lines, truncate with marker if larger)>
     ```
     Then commit per Round commit policy. Record in `auto_applied` with breakdown.
   - `confidence < 70%` → **queue for batch-qa** (see Step 6). Do not apply yet.
7. **Post-fix actualization** (preventive, mandatory after **any** applied fix — irrespective of category):
   - Bounded diff: `git diff --name-only HEAD~1 HEAD` (just this fix's commit, not all round commits)
   - If any touched file contains `START_MODULE_CONTRACT` or affects MODULE_MAP exports → run `grace-refresh` immediately
   - If a test file (`tests/**`) or log marker (`logger.info("[Module][...]")`) was touched → run `grace-refresh --verify`
   - If MODULE_CONTRACT header changed (added/removed exports, modified DEPENDS) → also run `grace lint` to confirm `docs/knowledge-graph.xml` consistent
   - All calls **before** moving to the next finding
8. **Anti-abuse**:
   - If an auto-applied issue from R{N-1} repeats in R{N} → that category gets penalty -20 for the rest of the cycle (persisted in `category_penalties`).
   - If confidence ≥70% lacks 3+ evidenced factors → reject, route to batch-qa.

### Step 6. Batch-qa (single /best-questions session per round)

After findings-loop completes, if `asked` queue is non-empty:

1. Build a single `/best-questions` invocation with all queued findings as questions.
2. Each question presents: finding summary, options ranked by confidence, evidence refs.
3. User answers all in one session — no per-finding interruption avalanche.
4. For each answer, apply the chosen option, commit per policy, record in `state.json.rounds[N].asked`.
5. Run post-fix actualization (Step 5.6) for each applied fix.

### Step 7. Stagnation handling

If `stagnation_with_prev=true`:

1. Print list of repeated findings with rounds-of-appearance.
2. Invoke `mcp__sequential-thinking__sequentialthinking` for root-cause decomposition (see MCP section).
3. Persist reasoning into `state.json.rounds[N].stagnation_reasoning`.
4. **Advise** (no auto-call): "Stagnation detected — recommend extending batch-qa with: «fix root cause vs document in ADR» for these issues".
5. User chooses next-round behaviour (continue, finish, abort).

### Step 7b. Round timeout policy

Track `started_at` per round. Before each finding-loop iteration check elapsed wall-clock against `config.toml.timeouts`:

- elapsed > `round_soft_warn_seconds` (default 3600s / 60min) → print `⚠ R{N} elapsed {M}min — consider /audit-loop --pause` and continue.
- elapsed > `round_hard_pause_seconds` (default 10800s / 180min) → auto-pause: mark `interrupted_at`, save state, release lock, print rollback instructions, exit. User resumes via `/audit-loop --resume`.

Rationale: prevents runaway rounds when codex+grace-fix loops on a hard finding without progress.

### Step 8. Round completion gate

Round considered complete **only when ALL** pass:
- `pre-commit run --all-files` — exit 0
- `grace-refresh` — exit 0 (or skip if module boundaries untouched)
- `grace-refresh --verify` — exit 0 (or skip)
- `git diff --name-only audit-loop/R${N}/start..HEAD` intersects `docs/` if module boundaries / tests / log markers touched
- `docs/audit-loop/round-${N}.md` exists with rationales for all decisions
- `state.json.rounds[N].completed_at` set
- Round-close commit present (`chore(audit-loop): R${N} closed — ...`)

If any condition fails — round NOT complete; tell user what to fix. DO NOT advance to next round.

### Step 9. Round-N markdown report

Write `docs/audit-loop/round-${N}.md` per template in `reference/round-md-template.md`. Sections: Codex summary, Auto-applied, Asked, Deferred, Hooks state, Context7 docs cited.

## Round 5 — final report

Write `docs/reports/YYYYMMDD_audit-loop.md` per template in `reference/final-report.md`. Includes cycle metadata, per-round trend, cycle metrics, stagnation analysis, GRACE skills usage, auto-applied review list (with `revert_finding.py` instructions), opt-in Beads creation prompt, ADRs, recommendations.

## Skill commands

- `/audit-loop` — start new cycle (R1) or resume current (per Idempotency rules)
- `/audit-loop --start-round=N` — manual recovery: force start at round N
- `/audit-loop --resume` — explicit resume of an interrupted round
- `/audit-loop --abort` — close cycle without rollback (sets `aborted=true`)
- `/audit-loop --finish` — early completion at current round, generate final report
- `/audit-loop --max-rounds=N` — override default 5 (use sparingly)
- `/audit-loop --dry-run` — codex audit + parse + stagnation only; **no** grace-fix, **no** commits, **no** state mutation. Findings table is printed to chat; `round-${N}.json` written to `docs/audit-loop/dry-run/` instead of the real path. Useful for: first-time use on a repo, smoke-testing the skill, previewing what codex will flag before paying the fix cost.

## Principles (gate, not aspiration)

Blocking for any decision in the cycle:

1. **DRY** — repetition in N places → single solution, not N local fixes
2. **KISS** — function >50 lines / nesting >4 → critical
3. **SSoT** — two places of one truth → critical, unify
4. **SRP** — class >500 lines / mixed concerns → critical
5. **SOTA** — every library/pattern → Context7 evidence or confidence ≤60%

See `_code-quality` skill (17 principles) — invoked explicitly when evaluating findings.

## Constraints

- NOT applicable in life-projects (Health, Budget, Family, Hobby, Home, Study, Career)
- Does NOT work without dev-workflow infrastructure
- Does NOT auto-transition to other workflow skills (only GRACE worker skills inside a round)
- Does NOT run `git push` (policy-level rule)
- Auto-Beads-creation is **opt-in per cycle** via final-report prompt — never silent

## After round 5 (or `--finish`)

1. Save final report.
2. Cycle-close commit: `chore(audit-loop): cycle <YYYYMMDD> — N rounds, X critical closed, Y open`.
3. Release lock: `python3 ~/.claude/skills/audit-loop/lib/lock.py release`.
4. Print final report path + cycle stats summary.
5. Return control to user. DO NOT auto-start a new cycle.

## Dry-run mode (`--dry-run`)

Disables all side effects after Step 4. Exact behavior:

| Step | Normal mode | Dry-run |
|------|-------------|---------|
| Pre-flight | runs, acquires lock | runs, **no lock** |
| Pre-round hooks | runs | runs |
| Codex audit | runs | runs |
| Parse + stagnation | persists to `round-${N}.json` | persists to `dry-run/round-${N}.json` |
| Findings-loop | grace-fix + commit per finding | **skipped** — only prints findings table |
| Batch-qa | runs | **skipped** |
| Round gate, round-md, state.json | written | **not written** |

Exit message: `DRY-RUN complete · {C}c/{M}m/{Min}min · no changes made · see docs/audit-loop/dry-run/round-1.json`. Idempotent — repeated dry-runs overwrite the dry-run output without touching real state.

## Smoke-test fixture

`~/.claude/skills/audit-loop/test/fixture/` — minimal dev-workflow project for end-to-end validation without touching a real repo. See `test/fixture/README.md`.
