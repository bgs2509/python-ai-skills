---
feature: model-run-evidence
bd_id: python-ai-skills-2fu
related_bd_ids:
  - python-ai-skills-tlo
date: 2026-09-24
status: approved
risk: medium
risk_justification: Three modules touched (model-run.sh, model-stats.py, model-registry.json) plus a new machine-local state directory and an additive journal-schema change consumed by a second module; reversible, no public-API break, no security/auth surface.
evidence: strong
evidence_justification: Every claim is cited file:line from the repo, the live journal and the bd issues; all four open questions resolved by the user at the Step 3 gate (2026-09-24).
open_questions: []
decisions:
  - OQ-1 -> option 1 (user, 2026-09-24): kept outputs in one flat machine-local directory next to the journal, declared in the registry's state_files, 14-day age retention (precedent JOB_MAX_AGE_DAYS=14). Retention is IN scope (NFR-6).
  - OQ-2 -> option 1: empty exit-0 output is always a non-ok outcome; the caller regex is an optional stricter check.
  - OQ-3 -> option 1: the new outcome is never penalised.
  - OQ-4 -> option 3: structured capability key only (qwen38 has no web search); latency stays in the journal.
functional_requirements:
  - id: FR-1
    text: classify() maps an attempt to unavailable or context_overflow on output text only when the exit code is non-zero; an exit-0 attempt is never reclassified by words in the model's answer.
  - id: FR-2
    text: Regression test - a model that exits 0 and whose answer contains "quota" and "429" yields outcome ok, the answer reaches --out, no penalty is written; the existing non-zero-exit true-positive tests stay green.
  - id: FR-3
    text: The captured output of every attempt that actually ran and did not end ok (timeout, unavailable, error, runtime context_overflow, and the new check-failed outcome) is kept in a machine-local location instead of being deleted.
  - id: FR-4
    text: The journal line of an attempt carries the path of the kept output and its size in bytes; ok attempts and pre-flight context_overflow skips carry null.
  - id: FR-5
    text: The caller may pass an answer check (a regex that must match the output); an output that fails the check is a new non-ok outcome, the attempt is journalled as such, and the run continues to the next model of the role.
  - id: FR-6
    text: An attempt classified by the new outcome is not penalised (see OQ-3).
  - id: FR-7
    text: model-stats.py counts and renders the new outcome and tolerates journal lines with and without the new optional keys.
  - id: FR-8
    text: The registry records that qwen38 has no working web search as a structured capability; observed latency stays in the journal (read via model-stats.py), not in the registry (OQ-4 decision).
  - id: FR-9
    text: task-57 is re-run through model-run.sh --role executor; at least one executor model returns a card quoting a fetched 57.mskobr.ru page with its URL, and the journal line is recorded in the bd issue.
  - id: FR-10
    text: The header help text of model-run.sh (printed by --help) lists the new flag and the new outcome.
non_functional_requirements:
  - id: NFR-1
    text: No new runtime dependency beyond what a stock Ubuntu has - bash, jq, GNU coreutils, grep, awk (already used) and GNU findutils (find, for retention) for the runner; Python 3 stdlib only for model-stats.py.
  - id: NFR-2
    text: All 126 existing tests in `make test` stay green; new behaviour is covered by tests in test_model_run.py and test_model_stats.py using the synthetic-registry fixture (no real model, network or quota).
  - id: NFR-3
    text: Kept outputs and the journal remain machine-local under the user's home directory, never committed, never cited by absolute path in committed documents.
  - id: NFR-4
    text: The journal stays append-only, one line per attempt; schema changes are additive so existing lines still parse.
  - id: NFR-5
    text: The journal line contains only facts (path, bytes, outcome) - never the output text itself, so no task or model content can leak through the journal.
  - id: NFR-6
    text: Growth of kept outputs is bounded by an age-based retention rule.
constraints:
  - Journal and penalties are machine-local runtime state, never committed (model-registry.json state_files, CLAUDE.md line 95).
  - model-registry.json is the single home for per-model parameters; skills and prompts must not restate them (claude-home/CLAUDE.md "choosing WHICH model").
  - stdout and stderr of a delegate are merged into one capture file (model-run.sh line 156); any stream-based distinction is a design change, not a given.
  - measured_seconds in the registry is documentation only - model-run.sh reads pool, runner, model_arg, effort, context_tokens, timeout_seconds, cmd_template, penalize_on_timeout (lines 107-114) and nothing else.
  - Out of scope by prior decision - delegates running Bash without sandbox; the codex config warning.
dependencies:
  - model-stats.py reads journal keys model, pool, role, outcome, seconds (lines 75-95) and counts ok per pool/role (line 92).
  - test_model_run.py (12 tests) pins today's classification via cmd_template models; test_model_stats.py (12 tests) pins the journal summary.
  - test_delegation_pool_nudge.py asserts only that the hook text contains "model-run.sh" (lines 42, 112); flag names are not asserted.
  - CLAUDE.md lines 358-362 and do-feature/SKILL.md line 89 document the runner's outcomes and invocation for humans.
  - housekeeping.py prunes ~/.claude/jobs/<id>/ by age (JOB_MAX_AGE_DAYS=14, line 41) - the only existing retention rule for machine-local state.
risks:
  - id: R-1
    risk: Gating text patterns on non-zero exit hides a real outage whose wrapper exits 0.
    mitigation: The answer then reaches --out where the caller sees the error text; the caller check (FR-5) moves the run on without a wrong penalty; exit and outcome stay in the journal for a later sweep.
  - id: R-2
    risk: Kept outputs grow unbounded or hold task text the caller considers sensitive.
    mitigation: Machine-local only, age-based retention (NFR-6), never cited by absolute path.
  - id: R-3
    risk: A new outcome value is miscounted by an older reader.
    mitigation: model-stats.py is the only reader; updated and tested in the same change; its ok counting is unaffected.
  - id: R-4
    risk: A timed-out claude -p run leaves an empty kept file because the answer is buffered until the end.
    mitigation: The journal records the byte size (FR-4) so the reader knows before opening; tracing the 420 s cause stays LATER.
  - id: R-5
    risk: An over-strict caller regex turns every model into the new outcome and exhausts the role.
    mitigation: Exit 1 "exhausted" already exists (model-run.sh lines 184-185); every answer is kept (FR-3), so nothing is lost.
  - id: R-6
    risk: Refreshing glm-4.7 timing mixes two measurements (2k-token single prompt vs multi-turn web task).
    mitigation: OQ-4 - keep the two figures apart; only timeout_seconds matters at runtime.
  - id: R-7
    risk: The task-57 acceptance run depends on live pools and on 57.mskobr.ru being reachable for the chosen runner.
    mitigation: Acceptance asks for at least one executor model; the run is recorded evidence, never a pytest.
scope:
  in:
    - FR-1 to FR-10 above, phased tlo (FR-1, FR-2) then 2fu (FR-3 to FR-10) on the shared file model-run.sh
  out:
    - Delegates running Bash without sandbox (separate decision)
    - The codex configuration warning
    - Keeping outputs of ok attempts (the caller already receives them via --out)
    - Any change to which models serve which role or their order
  later:
    - model-run.sh consulting a capability field to skip a model unfit for the task
    - Tracing why glm-4.7 spent 420 s on task-57 (needs a tool-trace run, not the captured stdout)
    - A command to clear or inspect a penalty without waiting for the clock
---

# Discovery — model-run.sh: truthful outcomes and kept evidence

> Problem-space research for bd `python-ai-skills-tlo` (P1) and `python-ai-skills-2fu` (P2).
> One pass because both change `claude-home/scripts/model-run.sh`. No solution design here —
> that is Step 4.

## 1. Intent

### 1.1 Literal ask

1. **tlo:** stop `classify()` from labelling an exit-0 answer `unavailable` because the answer
   text mentions quota or HTTP 429; add a regression test.
2. **2fu:** keep the output of non-ok attempts and point to it from the journal; let the caller
   supply an answer check whose miss is a new non-ok outcome that continues the fallback chain;
   teach `model-stats.py` the outcome; record `qwen38` has no web search and refresh `glm-4.7`
   timing; re-run task-57.

### 1.2 Real goal

`model-run.sh` is the only channel that moves bulk work off the scarce Anthropic pool
(`claude-home/CLAUDE.md:358-360`; `do-feature/SKILL.md:89`). A runner that discards answers,
penalises five healthy models for an hour, or reports an empty card as success makes delegation
untrustworthy — and an untrusted runner stops being used, which defeats the cost-discipline design
the journal was built to measure (`claude-home/CLAUDE.md:362`).

### 1.3 What the code does today (evidence)

1. `classify()` greps the **whole** capture file for unavailability words before looking at the
   exit code (`model-run.sh:94-97`); `ok` is reached only when no pattern matched (`:97`).
2. stdout and stderr are merged into one file (`model-run.sh:156`: `> "$tmp_out" 2>&1`), so
   "grep only stderr" is not possible without a structural change.
3. Every non-ok attempt ends with `rm -f "$tmp_out"` (`model-run.sh:180`); a timeout (`exit 124`,
   `:90`; GNU `timeout --help`: "124 if COMMAND times out") therefore leaves nothing to read.
4. `ok` means exit 0 and no pattern hit — nothing checks that the output is non-empty or has the
   shape the task demanded (`model-run.sh:97, :164-168`).
5. The journal line has twelve keys: `ts, role, model, pool, runner, ctx_chars, ctx_tokens,
   seconds, outcome, exit, attempt, session` (`model-run.sh:76-84`).
6. The penalty is written for the whole model for `policy.penalty_seconds` (3600, registry
   `:162`) with no command to undo it (`model-run.sh:68-74`).

Live evidence, `~/.claude/model-journal.jsonl` (12 lines at the time of writing):

1. 2026-09-22 19:44–19:48, session `b2b75c8a`: five consecutive lines
   `outcome=unavailable, exit=0` — `glm-4.7` 274.03 s, `gpt-terra-high` 43.37 s, `sonnet-low`
   25.61 s, `qwen38` 133.62 s, `gpt-luna-low` 51.73 s. Five answers lost; `~/.claude/model-penalties.json`
   still lists all five with `reason: unavailable` (expired 2026-09-22 20:44 local, so no cleanup
   is needed, but the hour was lost).
2. 2026-09-24 10:47, session `618791ff`: `glm-4.7` `outcome=timeout, exit=124, 420.49 s` — output
   deleted; then `gpt-terra-high` `outcome=ok, exit=0, 56.16 s` — the card was empty (bd 2fu).

### 1.4 Unconscious assumptions

1. **"The exit code is truthful."** Exit 0 is *necessary* for a usable answer, not *sufficient*
   (the 2026-09-24 `gpt-terra-high` line); and exit 0 plus a quota word is *not* an outage (the
   five 2026-09-22 lines). Text patterns can refine a non-zero exit; they cannot override a zero one.
2. **"stderr is separable."** It is not today (`model-run.sh:156`). Whether the wrappers put the
   answer on stdout and noise on stderr is *unverified* for every runner (hypothesis).
3. **"The caller knows a good answer."** For task-57 the task text itself demanded a trailing
   `=== URL ===` line (bd 2fu NOTES). The caller writes the task, so the caller can state the
   check; the registry is per-model, not per-task, and is the wrong home for it.
4. **"A penalty can be undone."** It cannot, except by the clock (`model-run.sh:62-74`).

### 1.5 Unsaid needs

1. **Bounded retention** for kept outputs — the only existing precedent for machine-local state
   pruning is `housekeeping.py` (`~/.claude/jobs/<id>/`, `JOB_MAX_AGE_DAYS = 14`, `:41`).
2. **Size in the journal line** — a timed-out `claude -p` may leave an empty file because the
   final answer is written at the end; a byte count tells the reader whether opening it is worth it.
3. **Additive schema** — `model-stats.py` reads keys with `.get` (`:76-79`), so new optional keys
   are safe; a new *outcome value* only needs counting and rendering (`:84, :147`).
4. **A `--help` that matches** — the header comment lists the outcomes and is what `--help`
   prints (`model-run.sh:10-15, :38`).

### 1.6 Blind spots

1. `measured_seconds` is never read at runtime (`model-run.sh:107-114`); "refreshing" it changes
   nothing unless `timeout_seconds` changes.
2. The passport figure for `glm-4.7` (19.2 s) is a ~2k-token single prompt with CLI startup
   included (`docs/research/model-passports-2026-09.md:193-196, :207`); the journal's 30–360 s are
   multi-turn web tasks. Different measurements, not a stale one.
3. The registry has no capability slot; the only per-model limitation key is `unavailable_mcp`
   (`model-registry.json:100, :112`).
4. Pre-flight `context_overflow` lines carry `seconds=0, exit=0` (`model-run.sh:123`) and never
   have an output file — every new key must allow null.
5. The bd comment records that `claude -p` delegates run under `bypassPermissions` with
   `WebSearch`/`WebFetch` allowed (`settings.json.template`, verified by parsing) — so the 420 s
   is not a permission wait; its cause is unknown and stays LATER.

### 1.7 Stakeholders

Callers of `model-run.sh`:

1. Orchestrator sessions following `claude-home/CLAUDE.md:358`.
2. `do-feature/SKILL.md:89` outward-dispatch fork.
3. `claude-home/hooks/delegation-pool-nudge.sh:73` (names the runner in hook text;
   `test_delegation_pool_nudge.py:42, :112` assert only the string `model-run.sh`).
4. `claude-home/scripts/test_model_run.py` (12 tests, synthetic registry via `cmd_template`).

Consumers of the journal and penalties:

1. `claude-home/scripts/model-stats.py` (+ 12 tests) — per-model outcomes, latency, penalties.
2. `claude-home/CLAUDE.md:360-362` and `CHANGELOG.md:10-13` — human description of outcomes.
3. Humans reading the JSONL directly (as both bd issues did).
4. `model-run.sh` itself — `penalty_active` (`:62-66`).

Consumers of the registry:

1. `model-run.sh:49, :104-114`.
2. `test_model_run.py:266-276` — roles→models and tiers→models self-consistency.
3. `claude-home/CLAUDE.md` "Plan Sizing" quotes `context_tokens` values.
4. `docs/research/model-passports-2026-09.md` is the declared `source` (`model-registry.json:13`).

## 2. Requirements

Functional (FR-1..FR-10), non-functional (NFR-1..NFR-6), constraints, dependencies and risks are
in the frontmatter above (single source; `requirements.xml` is generated from it).

Grouping by issue:

1. **tlo (phase 1):** FR-1, FR-2.
2. **2fu (phase 2):** FR-3 to FR-10.

## 3. Scope

**IN:** FR-1..FR-10 and the NFR-6 retention rule (moved from LATER at the Step 3 gate), phased as above on the shared file.

**OUT:** delegates running Bash without sandbox; codex config warning; keeping outputs of `ok`
attempts; any change to role membership or order.

**LATER:** capability-aware skipping in `model-run.sh`; tracing the 420 s `glm-4.7` run with a
tool trace; a penalty clear/inspect command.

## 4. Open questions

Four, listed in the frontmatter with options and a recommendation each (OQ-1 location and
retention of kept outputs; OQ-2 empty exit-0 output; OQ-3 penalty for the new outcome;
OQ-4 registry form for capability and latency). To be resolved with the user before the Step 3 gate.

## 5. Notes for the orchestrator

1. Preflight recorded in bd 2fu notes: `make test` 126 passed (re-confirmed 2026-09-24, 17.65 s);
   pre-commit via `.pre-commit-config.yaml` (scripts suite runs on `claude-home/scripts/`
   changes); no `.sentrux/rules.toml`; no `knowledge-graph.xml`.
2. No WebSearch used: the failure-classification pattern (exit code first, text second) is
   already the project's own precedent in `classify()` ordering (`model-run.sh:86-99`) and in the
   registry policy comment (`model-registry.json:166-174`); GNU `timeout` semantics verified via
   `timeout --help`.
