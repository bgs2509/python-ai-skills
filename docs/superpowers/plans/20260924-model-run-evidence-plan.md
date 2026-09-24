# model-run.sh: truthful outcomes and kept evidence — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**bd issues:** `python-ai-skills-tlo` (phase 1) · `python-ai-skills-2fu` (phase 2)
**Discovery:** `docs/superpowers/specs/20260924-model-run-evidence-discovery.md`
**Design:** `docs/superpowers/specs/20260924-model-run-evidence-design.md`

**Goal:** Stop `model-run.sh` from mislabelling a successful (exit 0) answer as a failure, keep the
evidence of every attempt that ran and was not `ok`, let a caller reject an unusable answer via
`--expect`, and record what the 2026-09-24 capability sweep found about model capabilities.

**Architecture:** `classify()` gates text-pattern checks on a non-zero exit code (phase 1). Phase 2
adds a machine-local `model-outputs/` directory next to the journal with age-based retention, a
9th/8th journal field pair (`out_path`/`out_bytes`), a new `check_failed` outcome for an empty or
`--expect`-missing answer, registry `capabilities.web_search` per model, and a `--help` that prints
the whole header instead of a fixed line range. `model-stats.py` needs no code change — its
generic per-outcome counting already covers a new outcome value.

**Tech Stack:** bash (`model-run.sh`, unchanged interpreter), jq 1.7, GNU coreutils (`mktemp --suffix`,
`wc`, `date`, `timeout`), GNU grep, GNU findutils `find` (new, for retention), Python 3 stdlib
(`model-stats.py` + both test files). No new runtime dependency (NFR-1).

## Global Constraints

- Journal and penalties are machine-local runtime state, never committed (`model-registry.json`
  `state_files`, `claude-home/CLAUDE.md` line 95).
- `model-registry.json` is the single home for per-model parameters; skills and prompts must not
  restate them.
- stdout and stderr of a delegate are merged into one capture file (`model-run.sh:156`); any
  stream-based distinction is out of scope.
- `measured_seconds` in the registry is documentation only — `model-run.sh` never reads it.
- NFR-1: no new runtime dependency beyond stock Ubuntu (bash, jq, GNU coreutils/grep, GNU
  findutils `find`); Python 3 stdlib only for `model-stats.py` and its tests.
- NFR-2: all 126 existing tests in `make test` stay green; new behaviour is covered by
  `test_model_run.py`/`test_model_stats.py` using the synthetic-registry fixture — no real model,
  network, or quota.
- NFR-3: kept outputs and the journal stay machine-local under the user's home directory, never
  committed, never cited by absolute path in committed documents.
- NFR-4: the journal stays append-only, one line per attempt; schema changes are additive so
  existing lines still parse.
- NFR-5: the journal line contains only facts (path, bytes, outcome) — never the output text
  itself.
- NFR-6: growth of kept outputs is bounded by an age-based retention rule.
- Out of scope: delegates running Bash without sandbox; the codex configuration warning; keeping
  outputs of `ok` attempts; any change to which models serve which role or their order.

## Context-Window Fit

**Phase 1** touches 2 files: `claude-home/scripts/model-run.sh` (185 lines) and
`claude-home/scripts/test_model_run.py` (276 lines), plus a `CHANGELOG.md` bullet. Well under one
context window.

**Phase 2** touches 5 files: `claude-home/scripts/model-run.sh`, `claude-home/scripts/test_model_run.py`,
`claude-home/scripts/model-stats.py`, `claude-home/scripts/test_model_stats.py`,
`claude-home/model-registry.json`, plus `claude-home/CLAUDE.md` and `CHANGELOG.md` for the final
docs task. Combined ~1000 lines of source/tests (design section 4: "Both phases fit one context
window: 5 source/test files, ~1000 lines total"). Broken into 8 small tasks (2-9) below so each
individual task's diff plus the file it touches fits comfortably within any executing tier's
window, including the narrowest (haiku, 200K tokens).

---

## Phase 1 — bd `python-ai-skills-tlo` (FR-1, FR-2)

### Task 1: Gate `classify()` text patterns on a non-zero exit code

**Files:**
- Modify: `claude-home/scripts/model-run.sh` (the `classify()` function, currently lines 86-99)
- Modify: `claude-home/scripts/test_model_run.py` (add two tests after
  `test_first_healthy_model_wins_and_is_journalled`, currently ending at line 91)
- Modify: `CHANGELOG.md` (`### Fixed` section under `## [Unreleased]`)

**Interfaces:**
- Consumes: nothing (first task).
- Produces: `classify(code, out_file)` — unchanged 2-arg contract, but exit 0 now always yields
  `ok` regardless of the answer's text. Every later task in this plan that edits `classify()`
  (Task 4) must reproduce this exact function body as its own edit's `old_string`.

- [ ] **Step 1: Write the two failing regression tests**

Open `claude-home/scripts/test_model_run.py`. Find this exact block (the end of the first test
function):

```python
    lines = journal_lines(env)
    assert len(lines) == 1, "only the attempt that ran should be journalled"
    assert lines[0]["model"] == "good"
    assert lines[0]["outcome"] == "ok"
    assert lines[0]["role"] == "executor"
    assert lines[0]["ctx_chars"] > 0
```

Replace it with the same text plus two new test functions appended after it:

```python
    lines = journal_lines(env)
    assert len(lines) == 1, "only the attempt that ran should be journalled"
    assert lines[0]["model"] == "good"
    assert lines[0]["outcome"] == "ok"
    assert lines[0]["role"] == "executor"
    assert lines[0]["ctx_chars"] > 0


def test_exit_zero_answer_mentioning_quota_is_ok(env):
    """Regression: exit 0 must not be relabelled by quota/429 words in the answer.

    Evidence: ~/.claude/model-journal.jsonl, 2026-09-22 19:44-19:48, session b2b75c8a —
    five consecutive exit-0 answers were mislabelled unavailable and their models penalised.
    """
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo 'quota 429 rate limit'")},
            {"executor": {"models": ["good"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]))
    assert result.returncode == 0, result.stderr
    assert env["out"].read_text().strip() == "quota 429 rate limit"
    assert journal_lines(env)[0]["outcome"] == "ok"
    assert json.loads(env["penalties"].read_text()) == {}


def test_exit_zero_answer_mentioning_context_window_is_ok(env):
    """Regression: exit 0 must not be relabelled by overflow words in the answer."""
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo 'maximum context'")},
            {"executor": {"models": ["good"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]))
    assert result.returncode == 0, result.stderr
    assert env["out"].read_text().strip() == "maximum context"
    assert journal_lines(env)[0]["outcome"] == "ok"
```

- [ ] **Step 2: Run the two new tests, verify they fail**

Run: `python3 -m pytest claude-home/scripts/test_model_run.py::test_exit_zero_answer_mentioning_quota_is_ok claude-home/scripts/test_model_run.py::test_exit_zero_answer_mentioning_context_window_is_ok -v`

Expected: both FAIL on `assert result.returncode == 0` (actual: `1`). Today's `classify()` greps
the whole capture for pattern words *before* checking the exit code, so an exit-0 answer
containing "quota 429 rate limit" is mislabelled `unavailable` and one containing "maximum
context" is mislabelled `context_overflow`; with only one candidate model in each registry, the
role is then exhausted and the script exits 1 instead of 0.

- [ ] **Step 3: Reorder `classify()` — text patterns only refine a non-zero exit**

In `claude-home/scripts/model-run.sh`, find this exact block:

```bash
# Classify an attempt from its exit code and captured output. Order matters:
# context overflow and quota messages can both accompany a non-zero exit.
classify() {
  local code="$1" out_file="$2"
  [ "$code" -eq 124 ] && { echo timeout; return; }
  if grep -qiE 'prompt is too long|context (length|window) exceeded|too many tokens|maximum context' "$out_file" 2>/dev/null; then
    echo context_overflow; return
  fi
  if grep -qiE 'rate.?limit|quota|usage limit|429|50[0-9] (server|error)|overloaded|authentication|unauthorized|invalid api key|connection (refused|reset)|could not connect' "$out_file" 2>/dev/null; then
    echo unavailable; return
  fi
  [ "$code" -eq 0 ] && { echo ok; return; }
  echo error
}
```

Replace with:

```bash
# Classify an attempt from its exit code and captured output. Text patterns
# refine a non-zero exit; they never override a zero one (exit 0 -> ok).
classify() {
  local code="$1" out_file="$2"
  [ "$code" -eq 124 ] && { echo timeout; return; }
  if [ "$code" -ne 0 ]; then
    if grep -qiE 'prompt is too long|context (length|window) exceeded|too many tokens|maximum context' "$out_file" 2>/dev/null; then
      echo context_overflow; return
    fi
    if grep -qiE 'rate.?limit|quota|usage limit|429|50[0-9] (server|error)|overloaded|authentication|unauthorized|invalid api key|connection (refused|reset)|could not connect' "$out_file" 2>/dev/null; then
      echo unavailable; return
    fi
    echo error; return
  fi
  echo ok
}
```

- [ ] **Step 4: Run the full test_model_run.py suite, verify it passes**

Run: `python3 -m pytest claude-home/scripts/test_model_run.py -v`

Expected: 14 passed (12 pre-existing + 2 new). In particular confirm the three true-positive tests
still pass unchanged: `test_unavailable_model_is_penalised_and_next_one_answers`,
`test_reported_overflow_is_detected_from_output`, `test_exhausted_role_exits_nonzero` — each of
these exits non-zero, so the reordering does not change their outcome.

- [ ] **Step 5: Add the CHANGELOG entry**

In `CHANGELOG.md`, find:

```markdown
### Fixed
- `claude-home/scripts/model-run.sh` journalled every attempt as `session: "unknown"`
```

Replace with (inserting a new bullet before the existing one):

```markdown
### Fixed
- `claude-home/scripts/model-run.sh` `classify()` mislabelled a successful (exit 0) answer as `unavailable` or `context_overflow` when the text merely mentioned quota/429 or "maximum context" — five consecutive healthy models were penalised for an hour after answering correctly (`~/.claude/model-journal.jsonl`, 2026-09-22 19:44-19:48, session `b2b75c8a`, five lines `outcome=unavailable, exit=0`). Text patterns are now consulted only when the exit code is non-zero; an exit-0 answer always classifies `ok`. Two regression tests added: an exit-0 answer containing "quota 429 rate limit" or "maximum context" now yields `ok`, reaches `--out`, and writes no penalty (bd `python-ai-skills-tlo`)
- `claude-home/scripts/model-run.sh` journalled every attempt as `session: "unknown"`
```

- [ ] **Step 6: Commit**

```bash
git add claude-home/scripts/model-run.sh claude-home/scripts/test_model_run.py CHANGELOG.md
git commit -m "fix(model-run): gate text patterns on non-zero exit"
```

This closes the phase-1 scope (FR-1, FR-2) and is independently committable — bd `python-ai-skills-tlo`
can be closed after this task without waiting for phase 2.

---

## Phase 2 — bd `python-ai-skills-2fu` (FR-3..FR-10, NFR-6)

### Task 2: Machine-local outputs directory with age-based retention

**Files:**
- Modify: `claude-home/scripts/model-run.sh` (after `PENALTY_SECONDS=...`, currently lines 52-57)
- Modify: `claude-home/scripts/test_model_run.py` (the `registry()` helper, `journal_lines()`
  helper, and `test_dry_run_touches_nothing`)

**Interfaces:**
- Consumes: the phase-1 shape of `model-run.sh` from Task 1.
- Produces: shell variables `OUTPUTS` (the kept-outputs directory, default
  `$(dirname "$JOURNAL")/model-outputs`, override `MODEL_OUTPUTS`) and `RETENTION_DAYS` (from
  registry `policy.output_retention_days`, default 14), both set before the model loop starts.
  Task 3 consumes `$OUTPUTS` to place the capture file. Test helper `outputs_dir(env)` and the
  `registry(..., policy=...)` keyword are produced for reuse by every later task's tests.

- [ ] **Step 1: Extend the `registry()` test helper to accept a policy override**

In `claude-home/scripts/test_model_run.py`, find:

```python
def registry(models, roles, penalty_seconds=3600):
    return {
        "version": 1,
        "roles": roles,
        "models": models,
        "policy": {"penalty_seconds": penalty_seconds},
    }
```

Replace with:

```python
def registry(models, roles, penalty_seconds=3600, policy=None):
    base_policy = {"penalty_seconds": penalty_seconds}
    if policy:
        base_policy.update(policy)
    return {
        "version": 1,
        "roles": roles,
        "models": models,
        "policy": base_policy,
    }
```

- [ ] **Step 2: Add an `outputs_dir()` test helper**

Find:

```python
def journal_lines(env):
    if not env["journal"].exists():
        return []
    return [json.loads(line) for line in env["journal"].read_text().splitlines() if line.strip()]
```

Replace with:

```python
def journal_lines(env):
    if not env["journal"].exists():
        return []
    return [json.loads(line) for line in env["journal"].read_text().splitlines() if line.strip()]


def outputs_dir(env):
    """Default kept-outputs location: next to the journal (no MODEL_OUTPUTS override)."""
    return env["journal"].parent / "model-outputs"
```

- [ ] **Step 3: Write the failing retention test and extend the dry-run test**

Find:

```python
def test_dry_run_touches_nothing(env):
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo SHOULD_NOT_RUN")},
            {"executor": {"models": ["good"]}},
        ),
    )
    result = run(env, "--role", "executor", "--dry-run")
    assert result.returncode == 0
    assert "good" in result.stdout
    assert not env["journal"].exists() or journal_lines(env) == []
    assert not env["out"].exists()
```

Replace with:

```python
def test_dry_run_touches_nothing(env):
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo SHOULD_NOT_RUN")},
            {"executor": {"models": ["good"]}},
        ),
    )
    result = run(env, "--role", "executor", "--dry-run")
    assert result.returncode == 0
    assert "good" in result.stdout
    assert not env["journal"].exists() or journal_lines(env) == []
    assert not env["out"].exists()
    assert not outputs_dir(env).exists(), "a dry run must not create the outputs directory"


def test_old_outputs_are_pruned_young_and_foreign_files_kept(env):
    """Retention runs on every real (non-dry) invocation, days from the registry."""
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo ANSWER")},
            {"executor": {"models": ["good"]}},
            policy={"output_retention_days": 14},
        ),
    )
    outputs = outputs_dir(env)
    outputs.mkdir()
    old_out = outputs / "old.out"
    young_out = outputs / "young.out"
    old_txt = outputs / "old.txt"
    for f in (old_out, young_out, old_txt):
        f.write_text("x")
    old_time = time.time() - 15 * 86400
    young_time = time.time() - 13 * 86400
    os.utime(old_out, (old_time, old_time))
    os.utime(old_txt, (old_time, old_time))
    os.utime(young_out, (young_time, young_time))

    run(env, "--role", "executor", "--out", str(env["out"]))

    assert not old_out.exists(), "a 15-day .out file must be pruned"
    assert young_out.exists(), "a 13-day .out file must survive 14-day retention"
    assert old_txt.exists(), "pruning must only touch *.out files"
```

- [ ] **Step 4: Run the new tests, verify the pruning test fails**

Run: `python3 -m pytest claude-home/scripts/test_model_run.py -k "pruned or dry_run" -v`

Expected: `test_old_outputs_are_pruned_young_and_foreign_files_kept` FAILS on
`assert not old_out.exists()` — nothing in `model-run.sh` touches `$OUTPUTS` yet, so the aged file
is never pruned. `test_dry_run_touches_nothing` PASSES already (nothing creates the directory
before this task's implementation either) — this assertion is a forward-looking regression guard
that becomes meaningful once Step 5 adds the `mkdir`, not a RED signal on its own.

- [ ] **Step 5: Add the outputs directory and retention pruning**

In `claude-home/scripts/model-run.sh`, find:

```bash
CTX_CHARS=$(wc -c < "$TASK" | tr -d ' ')
CTX_TOKENS=$(awk -v c="$CTX_CHARS" -v r="$CHARS_PER_TOKEN" 'BEGIN{printf "%d", c/r}')
PENALTY_SECONDS=$(jq -r '.policy.penalty_seconds // 3600' "$REGISTRY")

mkdir -p "$(dirname "$JOURNAL")"
[ -f "$PENALTIES" ] || echo '{}' > "$PENALTIES"
```

Replace with:

```bash
CTX_CHARS=$(wc -c < "$TASK" | tr -d ' ')
CTX_TOKENS=$(awk -v c="$CTX_CHARS" -v r="$CHARS_PER_TOKEN" 'BEGIN{printf "%d", c/r}')
PENALTY_SECONDS=$(jq -r '.policy.penalty_seconds // 3600' "$REGISTRY")
OUTPUTS="${MODEL_OUTPUTS:-$(dirname "$JOURNAL")/model-outputs}"
RETENTION_DAYS=$(jq -r '.policy.output_retention_days // 14' "$REGISTRY")

mkdir -p "$(dirname "$JOURNAL")"
[ -f "$PENALTIES" ] || echo '{}' > "$PENALTIES"

# Kept outputs are machine-local evidence of non-ok attempts (NFR-3). Pruned
# here, on every real run, so the component that creates the state expires
# it — same ownership pattern as the penalty expiry below.
if [ "$DRY" -eq 0 ]; then
  mkdir -p "$OUTPUTS"
  find "$OUTPUTS" -maxdepth 1 -type f -name '*.out' -mmin "+$((RETENTION_DAYS * 1440))" -delete
fi
```

- [ ] **Step 6: Run the full suite, verify all pass**

Run: `python3 -m pytest claude-home/scripts/test_model_run.py -v`

Expected: 15 passed (14 from Task 1 + 1 new).

- [ ] **Step 7: Commit**

```bash
git add claude-home/scripts/model-run.sh claude-home/scripts/test_model_run.py
git commit -m "feat(model-run): add a machine-local outputs directory with age-based retention"
```

---

### Task 3: Capture in place, keep non-ok outputs, journal `out_path`/`out_bytes`

**Files:**
- Modify: `claude-home/scripts/model-run.sh` (the `journal()` function, currently lines 76-84;
  and the per-attempt body inside the model loop, currently lines 154-181)
- Modify: `claude-home/scripts/test_model_run.py` (append 5 tests after
  `test_shipped_registry_is_valid_and_self_consistent`)

**Interfaces:**
- Consumes: `$OUTPUTS` from Task 2.
- Produces: `journal()` now takes 9 positional args (`model pool runner seconds outcome exit
  attempt out_path out_bytes`); the journal line gains `out_path` (absolute path string or
  `null`) and `out_bytes` (integer or `null`). Every attempt that ran and was not `ok` keeps its
  capture file under `$OUTPUTS`; `ok` and pre-flight `context_overflow` carry `null`/`null`. Task 4
  and Task 9 rely on `out_path` pointing at a real, readable file for every non-`ok` outcome.

- [ ] **Step 1: Write the five failing tests**

In `claude-home/scripts/test_model_run.py`, find the exact tail of the last function in the file:

```python
    for tier, name in shipped["tiers"].items():
        if tier.startswith("_"):  # documentation key, not a tier
            continue
        assert name in known, f"tier {tier} references unknown model {name}"
```

Replace with the same text plus five new tests appended after it:

```python
    for tier, name in shipped["tiers"].items():
        if tier.startswith("_"):  # documentation key, not a tier
            continue
        assert name in known, f"tier {tier} references unknown model {name}"


def test_timeout_output_is_kept_and_journalled(env):
    write_registry(
        env,
        registry(
            {"slow": model("echo PARTIAL; sleep 5", timeout_seconds=1)},
            {"executor": {"models": ["slow"]}},
        ),
    )
    run(env, "--role", "executor", "--out", str(env["out"]))

    line = journal_lines(env)[0]
    assert line["outcome"] == "timeout"
    kept = Path(line["out_path"])
    assert kept.exists()
    assert kept.read_text().strip() == "PARTIAL"
    assert line["out_bytes"] == kept.stat().st_size
    assert kept.parent == outputs_dir(env)


def test_error_and_unavailable_outputs_are_kept(env):
    write_registry(
        env,
        registry(
            {
                "broken": model("cat >/dev/null; echo 'Error: rate limit exceeded' >&2; exit 1"),
                "buggy": model("cat >/dev/null; echo 'boom' >&2; exit 3"),
            },
            {"executor": {"models": ["broken", "buggy"]}},
        ),
    )
    run(env, "--role", "executor", "--out", str(env["out"]))

    lines = journal_lines(env)
    assert [line["outcome"] for line in lines] == ["unavailable", "error"]
    for line in lines:
        kept = Path(line["out_path"])
        assert kept.exists(), f"{line['outcome']} output must be kept"
        assert line["out_bytes"] > 0


def test_ok_and_preflight_overflow_carry_null_paths(env):
    write_registry(
        env,
        registry(
            {
                "tiny": model("cat >/dev/null; echo NEVER", context_tokens=1),
                "roomy": model("cat >/dev/null; echo FITS", context_tokens=1000000),
            },
            {"executor": {"models": ["tiny", "roomy"]}},
        ),
    )
    run(env, "--role", "executor", "--out", str(env["out"]))

    lines = journal_lines(env)
    assert lines[0]["outcome"] == "context_overflow"
    assert lines[0]["out_path"] is None
    assert lines[0]["out_bytes"] is None
    assert lines[1]["outcome"] == "ok"
    assert lines[1]["out_path"] is None
    assert lines[1]["out_bytes"] is None


def test_outputs_default_next_to_journal(env):
    """No MODEL_OUTPUTS override: the kept file must land next to the journal, not in /tmp."""
    write_registry(
        env,
        registry(
            {"buggy": model("cat >/dev/null; echo boom >&2; exit 3")},
            {"executor": {"models": ["buggy"]}},
        ),
    )
    run(env, "--role", "executor", "--out", str(env["out"]))
    kept = Path(journal_lines(env)[0]["out_path"])
    assert kept.parent == outputs_dir(env)
    assert kept.parent == env["journal"].parent / "model-outputs"


def test_journal_line_has_no_output_text(env):
    marker = "SUPER_SECRET_TASK_MARKER_12345"
    write_registry(
        env,
        registry(
            {"buggy": model(f"cat >/dev/null; echo '{marker}' >&2; exit 3")},
            {"executor": {"models": ["buggy"]}},
        ),
    )
    run(env, "--role", "executor", "--out", str(env["out"]))
    raw_journal = env["journal"].read_text()
    assert marker not in raw_journal
    kept = Path(journal_lines(env)[0]["out_path"])
    assert marker in kept.read_text()
```

- [ ] **Step 2: Run the new tests, verify they fail**

Run: `python3 -m pytest claude-home/scripts/test_model_run.py -k "kept or null_paths or default_next_to_journal or no_output_text" -v`

Expected: all 5 FAIL, mostly with `KeyError: 'out_path'` (the journal line has no such key yet) —
`journal()` still writes only the original 12 keys, and the loop still `rm -f`'s every non-`ok`
capture file.

- [ ] **Step 3: Extend `journal()` with `out_path`/`out_bytes`**

Find:

```bash
journal() { # model pool runner seconds outcome exit attempt
  jq -nc --arg ts "$(date -Is)" --arg role "$ROLE" --arg model "$1" --arg pool "$2" \
     --arg runner "$3" --argjson ctx_chars "$CTX_CHARS" --argjson ctx_tokens "$CTX_TOKENS" \
     --argjson seconds "$4" --arg outcome "$5" --argjson exit "$6" --argjson attempt "$7" \
     --arg session "$SESSION" \
     '{ts:$ts,role:$role,model:$model,pool:$pool,runner:$runner,ctx_chars:$ctx_chars,
       ctx_tokens:$ctx_tokens,seconds:$seconds,outcome:$outcome,exit:$exit,
       attempt:$attempt,session:$session}' >> "$JOURNAL"
}
```

Replace with:

```bash
journal() { # model pool runner seconds outcome exit attempt out_path out_bytes
  jq -nc --arg ts "$(date -Is)" --arg role "$ROLE" --arg model "$1" --arg pool "$2" \
     --arg runner "$3" --argjson ctx_chars "$CTX_CHARS" --argjson ctx_tokens "$CTX_TOKENS" \
     --argjson seconds "$4" --arg outcome "$5" --argjson exit "$6" --argjson attempt "$7" \
     --arg session "$SESSION" --arg out_path "${8:-}" --arg out_bytes "${9:-}" \
     '{ts:$ts,role:$role,model:$model,pool:$pool,runner:$runner,ctx_chars:$ctx_chars,
       ctx_tokens:$ctx_tokens,seconds:$seconds,outcome:$outcome,exit:$exit,
       attempt:$attempt,session:$session,
       out_path:(if $out_path == "" then null else $out_path end),
       out_bytes:(if $out_bytes == "" then null else ($out_bytes | tonumber) end)}' >> "$JOURNAL"
}
```

`${8:-}`/`${9:-}` are required, not cosmetic: under `set -uo pipefail` a bare `$8` on a call with
only 7 args raises "unbound variable" (verified locally: `bash -c 'set -u; f(){ echo $8; }; f a'`
fails with exactly that message; `${8:-}` does not). The pre-flight `context_overflow` call site
(`journal "$MODEL" "$pool" "$runner" 0 context_overflow 0 "$attempt"`) passes only 7 args and
needs no edit — the missing 8th/9th default to `""` and become `null`.

- [ ] **Step 4: Capture in place and keep every non-ok output**

Find this exact block (the per-attempt body inside the `for MODEL in $CANDIDATES` loop):

```bash
  tmp_out=$(mktemp)
  t0=$(date +%s.%N)
  timeout "$timeout_s" bash -c "$CMD" < "$TASK" > "$tmp_out" 2>&1
  code=$?
  t1=$(date +%s.%N)
  secs=$(awk -v a="$t0" -v b="$t1" 'BEGIN{printf "%.2f", b-a}')

  outcome=$(classify "$code" "$tmp_out")
  journal "$MODEL" "$pool" "$runner" "$secs" "$outcome" "$code" "$attempt"

  case "$outcome" in
    ok)
      if [ -n "$OUT" ]; then mv "$tmp_out" "$OUT"; else cat "$tmp_out"; rm -f "$tmp_out"; fi
      printf 'model-run: %s answered in %ss\n' "$MODEL" "$secs" >&2
      exit 0 ;;
    unavailable)
      set_penalty "$MODEL" unavailable
      printf 'model-run: %s unavailable, penalised %ss\n' "$MODEL" "$PENALTY_SECONDS" >&2 ;;
    timeout)
      [ "$penalize_timeout" = "true" ] && set_penalty "$MODEL" timeout
      printf 'model-run: %s timed out after %ss\n' "$MODEL" "$timeout_s" >&2 ;;
    context_overflow)
      printf 'model-run: %s reported context overflow\n' "$MODEL" >&2 ;;
    *)
      printf 'model-run: %s failed (exit %s)\n' "$MODEL" "$code" >&2 ;;
  esac
  rm -f "$tmp_out"
done
```

Replace with:

```bash
  tmp_out=$(mktemp --suffix=.out "$OUTPUTS/$(date +%Y%m%dT%H%M%S)-${MODEL//[^A-Za-z0-9._-]/_}-XXXXXX")
  t0=$(date +%s.%N)
  timeout "$timeout_s" bash -c "$CMD" < "$TASK" > "$tmp_out" 2>&1
  code=$?
  t1=$(date +%s.%N)
  secs=$(awk -v a="$t0" -v b="$t1" 'BEGIN{printf "%.2f", b-a}')

  outcome=$(classify "$code" "$tmp_out")

  out_path=""
  out_bytes=""
  if [ "$outcome" != "ok" ]; then
    out_path="$tmp_out"
    out_bytes=$(wc -c < "$tmp_out" | tr -d ' ')
  fi

  journal "$MODEL" "$pool" "$runner" "$secs" "$outcome" "$code" "$attempt" "$out_path" "$out_bytes"

  case "$outcome" in
    ok)
      if [ -n "$OUT" ]; then mv "$tmp_out" "$OUT"; else cat "$tmp_out"; rm -f "$tmp_out"; fi
      printf 'model-run: %s answered in %ss\n' "$MODEL" "$secs" >&2
      exit 0 ;;
    unavailable)
      set_penalty "$MODEL" unavailable
      printf 'model-run: %s unavailable, penalised %ss (output kept: %s)\n' "$MODEL" "$PENALTY_SECONDS" "$tmp_out" >&2 ;;
    timeout)
      [ "$penalize_timeout" = "true" ] && set_penalty "$MODEL" timeout
      printf 'model-run: %s timed out after %ss (output kept: %s)\n' "$MODEL" "$timeout_s" "$tmp_out" >&2 ;;
    context_overflow)
      printf 'model-run: %s reported context overflow (output kept: %s)\n' "$MODEL" "$tmp_out" >&2 ;;
    *)
      printf 'model-run: %s failed (exit %s, output kept: %s)\n' "$MODEL" "$code" "$tmp_out" >&2 ;;
  esac
done
```

Note the trailing `rm -f "$tmp_out"` that used to run for every outcome is gone entirely: `ok`
handles its own cleanup inside the `case`, and every other outcome now falls through the loop
with its file intact.

- [ ] **Step 5: Run the full suite, verify all pass**

Run: `python3 -m pytest claude-home/scripts/test_model_run.py -v`

Expected: 20 passed (15 from Task 2 + 5 new).

- [ ] **Step 6: Commit**

```bash
git add claude-home/scripts/model-run.sh claude-home/scripts/test_model_run.py
git commit -m "feat(model-run): keep the output of every non-ok attempt and record its path/size in the journal"
```

---

### Task 4: `--expect REGEX` flag and the `check_failed` outcome

**Files:**
- Modify: `claude-home/scripts/model-run.sh` (arg-parsing loop, validation block, `classify()`,
  the per-attempt `case` statement)
- Modify: `claude-home/scripts/test_model_run.py` (append 4 tests after
  `test_journal_line_has_no_output_text`)

**Interfaces:**
- Consumes: `classify()` and the per-attempt loop body from Task 3.
- Produces: CLI flag `--expect REGEX` (POSIX ERE via `grep -E`), shell variable `$EXPECT` (empty
  string when absent), outcome `check_failed` (exit 0, empty answer or `--expect` miss; never
  penalised — no `set_penalty` call in its `case` branch). Task 6 documents this outcome in
  `policy.no_penalty_on` (documentation only — `model-run.sh` never reads that field). Task 9
  consumes `--expect` directly.

- [ ] **Step 1: Write the four failing tests**

In `claude-home/scripts/test_model_run.py`, find the exact tail of
`test_journal_line_has_no_output_text` (the last function in the file after Task 3):

```python
    run(env, "--role", "executor", "--out", str(env["out"]))
    raw_journal = env["journal"].read_text()
    assert marker not in raw_journal
    kept = Path(journal_lines(env)[0]["out_path"])
    assert marker in kept.read_text()
```

Replace with the same text plus four new tests appended after it:

```python
    run(env, "--role", "executor", "--out", str(env["out"]))
    raw_journal = env["journal"].read_text()
    assert marker not in raw_journal
    kept = Path(journal_lines(env)[0]["out_path"])
    assert marker in kept.read_text()


def test_expect_miss_is_check_failed_and_next_model_answers(env):
    write_registry(
        env,
        registry(
            {
                "vague": model("cat >/dev/null; echo NO URL"),
                "precise": model("cat >/dev/null; echo '=== URL ==='"),
            },
            {"executor": {"models": ["vague", "precise"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]), "--expect", "^=== URL ===$")
    assert result.returncode == 0, result.stderr
    assert env["out"].read_text().strip() == "=== URL ==="

    outcomes = [line["outcome"] for line in journal_lines(env)]
    assert outcomes == ["check_failed", "ok"]
    assert json.loads(env["penalties"].read_text()) == {}


def test_empty_exit_zero_output_is_check_failed(env):
    write_registry(
        env,
        registry(
            {"mute": model("cat >/dev/null")},
            {"executor": {"models": ["mute"]}},
        ),
    )
    run(env, "--role", "executor", "--out", str(env["out"]))
    line = journal_lines(env)[0]
    assert line["outcome"] == "check_failed"
    assert line["out_bytes"] == 0


def test_invalid_expect_regex_is_usage_error(env):
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo ANSWER")},
            {"executor": {"models": ["good"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]), "--expect", "(")
    assert result.returncode == 2
    assert "valid extended regex" in result.stderr
    assert not env["journal"].exists() or journal_lines(env) == []


def test_expect_matching_task_text_is_usage_error(env):
    env["task"].write_text("please answer with === URL === at the end\n")
    write_registry(
        env,
        registry(
            {"good": model("cat >/dev/null; echo ANSWER")},
            {"executor": {"models": ["good"]}},
        ),
    )
    result = run(env, "--role", "executor", "--out", str(env["out"]), "--expect", "=== URL ===")
    assert result.returncode == 2
    assert "matches the task text" in result.stderr
```

- [ ] **Step 2: Run the new tests, verify they fail**

Run: `python3 -m pytest claude-home/scripts/test_model_run.py -k "expect or check_failed" -v`

Expected: all 4 FAIL. `--expect` is not yet a recognised flag, so every invocation dies with
`model-run: unknown argument: --expect` (exit 2) before reaching any model:
`test_expect_miss_is_check_failed_and_next_model_answers` fails on `returncode == 0` (actual `2`);
`test_invalid_expect_regex_is_usage_error` and `test_expect_matching_task_text_is_usage_error`
already get exit 2 but for the wrong reason, so they fail on the stderr-text assertion
(`"valid extended regex"` / `"matches the task text"` is not in `"unknown argument: --expect"`).
`test_empty_exit_zero_output_is_check_failed` fails independently of `--expect`: today's
`classify()` returns `ok` unconditionally on exit 0, so an empty answer is still `ok`, not
`check_failed`.

- [ ] **Step 3: Add the `--expect` flag and its startup validation**

Find:

```bash
ROLE=""; TASK=""; OUT=""; DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --role)    ROLE="${2:-}"; shift 2 ;;
    --task)    TASK="${2:-}"; shift 2 ;;
    --out)     OUT="${2:-}";  shift 2 ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done
```

Replace with:

```bash
ROLE=""; TASK=""; OUT=""; EXPECT=""; DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --role)    ROLE="${2:-}"; shift 2 ;;
    --task)    TASK="${2:-}"; shift 2 ;;
    --out)     OUT="${2:-}";  shift 2 ;;
    --expect)  EXPECT="${2:-}"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done
```

Then find:

```bash
[ -n "$ROLE" ] || die "--role is required"
[ -n "$TASK" ] || die "--task is required"
[ -f "$TASK" ] || die "task file not found: $TASK"
[ -f "$REGISTRY" ] || die "registry not found: $REGISTRY"
command -v jq >/dev/null 2>&1 || die "jq is required"
```

Replace with:

```bash
[ -n "$ROLE" ] || die "--role is required"
[ -n "$TASK" ] || die "--task is required"
[ -f "$TASK" ] || die "task file not found: $TASK"
[ -f "$REGISTRY" ] || die "registry not found: $REGISTRY"
command -v jq >/dev/null 2>&1 || die "jq is required"

if [ -n "$EXPECT" ]; then
  grep -qE -- "$EXPECT" </dev/null
  [ $? -eq 2 ] && die "--expect is not a valid extended regex: $EXPECT"
  grep -qE -- "$EXPECT" "$TASK" && die "--expect matches the task text; it would pass on an echoed prompt"
fi
```

(Verified locally: `grep -qE -- '(' </dev/null` exits 2 on GNU grep 3.11; a regex with no match
against `/dev/null` exits 1, so only exit 2 means "invalid regex".)

- [ ] **Step 4: Add the empty-output and `--expect` checks to `classify()`**

Find:

```bash
classify() {
  local code="$1" out_file="$2"
  [ "$code" -eq 124 ] && { echo timeout; return; }
  if [ "$code" -ne 0 ]; then
    if grep -qiE 'prompt is too long|context (length|window) exceeded|too many tokens|maximum context' "$out_file" 2>/dev/null; then
      echo context_overflow; return
    fi
    if grep -qiE 'rate.?limit|quota|usage limit|429|50[0-9] (server|error)|overloaded|authentication|unauthorized|invalid api key|connection (refused|reset)|could not connect' "$out_file" 2>/dev/null; then
      echo unavailable; return
    fi
    echo error; return
  fi
  echo ok
}
```

Replace with:

```bash
classify() {
  local code="$1" out_file="$2"
  [ "$code" -eq 124 ] && { echo timeout; return; }
  if [ "$code" -ne 0 ]; then
    if grep -qiE 'prompt is too long|context (length|window) exceeded|too many tokens|maximum context' "$out_file" 2>/dev/null; then
      echo context_overflow; return
    fi
    if grep -qiE 'rate.?limit|quota|usage limit|429|50[0-9] (server|error)|overloaded|authentication|unauthorized|invalid api key|connection (refused|reset)|could not connect' "$out_file" 2>/dev/null; then
      echo unavailable; return
    fi
    echo error; return
  fi
  grep -q '[^[:space:]]' "$out_file" || { echo check_failed; return; }
  if [ -n "$EXPECT" ] && ! grep -qE -- "$EXPECT" "$out_file"; then echo check_failed; return; fi
  echo ok
}
```

- [ ] **Step 5: Give `check_failed` its own message in the per-attempt `case`**

Find:

```bash
    context_overflow)
      printf 'model-run: %s reported context overflow (output kept: %s)\n' "$MODEL" "$tmp_out" >&2 ;;
    *)
```

Replace with:

```bash
    context_overflow)
      printf 'model-run: %s reported context overflow (output kept: %s)\n' "$MODEL" "$tmp_out" >&2 ;;
    check_failed)
      printf 'model-run: %s answer failed the check (output kept: %s)\n' "$MODEL" "$tmp_out" >&2 ;;
    *)
```

(`check_failed` deliberately calls no `set_penalty` — FR-6/NFR: the model works, only the answer
does not fit this task.)

- [ ] **Step 6: Run the full suite, verify all pass**

Run: `python3 -m pytest claude-home/scripts/test_model_run.py -v`

Expected: 24 passed (20 from Task 3 + 4 new).

- [ ] **Step 7: Commit**

```bash
git add claude-home/scripts/model-run.sh claude-home/scripts/test_model_run.py
git commit -m "feat(model-run): add --expect and the check_failed outcome for unusable answers"
```

---

### Task 5: `--help` prints the full header, listing `--expect` and `check_failed`

**Files:**
- Modify: `claude-home/scripts/model-run.sh` (the header comment, lines 1-18; the `-h|--help` case
  arm)
- Modify: `claude-home/scripts/test_model_run.py` (append 1 test after
  `test_expect_matching_task_text_is_usage_error`)

**Interfaces:**
- Consumes: nothing new (help text is read-only documentation of Tasks 2-4's behaviour).
- Produces: `--help` output that scales with header length (no more fixed `sed -n '2,20p'` range).

- [ ] **Step 1: Write the failing test**

In `claude-home/scripts/test_model_run.py`, find the exact tail of
`test_expect_matching_task_text_is_usage_error` (the last function in the file after Task 4):

```python
    result = run(env, "--role", "executor", "--out", str(env["out"]), "--expect", "=== URL ===")
    assert result.returncode == 2
    assert "matches the task text" in result.stderr
```

Replace with the same text plus a new test appended after it:

```python
    result = run(env, "--role", "executor", "--out", str(env["out"]), "--expect", "=== URL ===")
    assert result.returncode == 2
    assert "matches the task text" in result.stderr


def test_help_lists_expect_and_check_failed():
    result = subprocess.run(
        ["bash", str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "--expect" in result.stdout
    assert "check_failed" in result.stdout
    assert "set -uo" not in result.stdout
```

- [ ] **Step 2: Run the new test, verify it fails**

Run: `python3 -m pytest claude-home/scripts/test_model_run.py::test_help_lists_expect_and_check_failed -v`

Expected: FAIL on `assert "--expect" in result.stdout` — today's header (printed by
`sed -n '2,20p' "$0"`) predates this feature and neither mentions `--expect` nor `check_failed`.

- [ ] **Step 3: Rewrite the header comment**

Find:

```bash
#!/usr/bin/env bash
# model-run.sh — run a task on the first usable model of a role.
#
# The caller decides ONE thing: which role the task needs. Everything else
# (which model, which launch flags, how long to wait, what to do on failure,
# what to record) is decided here, deterministically, from the registry.
#
#   model-run.sh --role executor --task task.txt [--out result.md]
#
# Outcomes per attempt, written to the journal one line each:
#   ok               — model answered, exit 0. Run stops, result is in --out.
#   unavailable      — quota exhausted / 5xx / auth / network. Penalised (see registry).
#   context_overflow — task does not fit this model's window. NOT penalised.
#   timeout          — exceeded the model's timeout. NOT penalised by default.
#   error            — anything else (bad flag, crash). NOT penalised.
#
# Exit: 0 when some model answered, 1 when the role was exhausted.
set -uo pipefail
```

Replace with:

```bash
#!/usr/bin/env bash
# model-run.sh — run a task on the first usable model of a role.
#
# The caller decides ONE thing: which role the task needs. Everything else
# (which model, which launch flags, how long to wait, what to do on failure,
# what to record) is decided here, deterministically, from the registry.
#
#   model-run.sh --role executor --task task.txt [--out result.md] [--expect REGEX]
#
# --expect REGEX — extended regex (grep -E) the answer must contain; a miss
#   or an empty answer becomes check_failed instead of ok. Rejected at
#   startup (exit 2) if the regex is invalid or matches the task file itself.
#
# Outcomes per attempt, written to the journal one line each:
#   ok               — model answered, exit 0, non-empty, --expect matched.
#   unavailable      — quota exhausted / 5xx / auth / network. Penalised (see registry).
#   context_overflow — task does not fit this model's window. NOT penalised.
#   timeout          — exceeded the model's timeout. NOT penalised by default.
#   check_failed     — exit 0 but empty or missed --expect. NOT penalised.
#   error            — anything else (bad flag, crash). NOT penalised.
#
# Non-ok attempts that ran keep their output under $MODEL_OUTPUTS (default:
# next to the journal); the journal line's out_path/out_bytes point to it.
#
# Exit: 0 when some model answered, 1 when the role was exhausted.
set -uo pipefail
```

- [ ] **Step 4: Replace the fixed `sed` range with a header-length-agnostic `awk`**

Find:

```bash
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
```

Replace with:

```bash
    -h|--help) awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0"; exit 0 ;;
```

This prints every `#`-prefixed line starting at line 2 (skipping the shebang) and stops at the
first non-comment line — the current header ends at line 17 (`# Exit: 0 when ...`), with
`set -uo pipefail` as line 18, so the cutoff is automatic and length-independent.

- [ ] **Step 5: Run the full suite, verify all pass**

Run: `python3 -m pytest claude-home/scripts/test_model_run.py -v`

Expected: 25 passed (24 from Task 4 + 1 new).

- [ ] **Step 6: Commit**

```bash
git add claude-home/scripts/model-run.sh claude-home/scripts/test_model_run.py
git commit -m "feat(model-run): rewrite --help to print the full header and list --expect/check_failed"
```

---

### Task 6: Registry — `capabilities.web_search`, `check_failed` policy, retention days

**Files:**
- Modify: `claude-home/model-registry.json` (all six sections below)
- Modify: `claude-home/scripts/test_model_run.py` (extend
  `test_shipped_registry_is_valid_and_self_consistent` in place — no new test function)

**Interfaces:**
- Consumes: nothing from earlier tasks (registry fields here are documentation-only; `model-run.sh`
  never reads `capabilities`, `no_penalty_on`, or `penalize_on` at runtime — verified against the
  full script in Tasks 1-5, which reads only `pool`, `runner`, `model_arg`, `effort`,
  `context_tokens`, `timeout_seconds`, `cmd_template`, `penalize_on_timeout`, and
  `policy.penalty_seconds`/`policy.output_retention_days`).
- Produces: `models.<name>.capabilities.web_search` (bool, all ten models), top-level
  `capabilities_source`, `policy.output_retention_days` (already read by Task 2's
  `RETENTION_DAYS=$(jq -r '.policy.output_retention_days // 14' ...)`), `policy.no_penalty_on`
  including `check_failed`, `state_files.outputs`.

- [ ] **Step 1: Extend the registry self-consistency test**

In `claude-home/scripts/test_model_run.py`, find the exact tail of
`test_shipped_registry_is_valid_and_self_consistent`:

```python
    for tier, name in shipped["tiers"].items():
        if tier.startswith("_"):  # documentation key, not a tier
            continue
        assert name in known, f"tier {tier} references unknown model {name}"
```

Replace with:

```python
    for tier, name in shipped["tiers"].items():
        if tier.startswith("_"):  # documentation key, not a tier
            continue
        assert name in known, f"tier {tier} references unknown model {name}"
    for name, spec in shipped["models"].items():
        assert isinstance(spec.get("capabilities", {}).get("web_search"), bool), (
            f"model {name} is missing capabilities.web_search"
        )
    assert shipped["models"]["qwen38"]["capabilities"]["web_search"] is False
    assert "check_failed" in shipped["policy"]["no_penalty_on"]
    assert isinstance(shipped["policy"]["output_retention_days"], int)
    assert shipped["policy"]["output_retention_days"] > 0
```

- [ ] **Step 2: Run it, verify it fails**

Run: `python3 -m pytest claude-home/scripts/test_model_run.py::test_shipped_registry_is_valid_and_self_consistent -v`

Expected: FAIL on `assert isinstance(spec.get("capabilities", {}).get("web_search"), bool)` for
`opus-xhigh` (the first model in the file) — no model has a `capabilities` key yet, so
`.get("capabilities", {}).get("web_search")` is `None`, not a `bool`.

- [ ] **Step 3: Add the `_comment` line, `capabilities_source`, and bump `updated`**

In `claude-home/model-registry.json`, find:

```json
  "_comment": [
    "SSoT for WHICH MODEL implements a role, with launch parameters and fallback order.",
    "It is NOT the SSoT for which role/tier a do-feature step needs — that stays in",
    "do-feature/SKILL.md (Model Routing Matrix), which by its own wording routes by TIERS,",
    "not model names. Matrix answers 'this step needs tier X'; this file answers",
    "'tier/role X is served by these models, in this order, with these parameters'.",
    "Numbers come from docs/research/model-passports-2026-09.md (measured 2026-09-22).",
    "Consumed by claude-home/scripts/model-run.sh. Edit here, never in a skill."
  ],
  "version": 1,
  "updated": "2026-09-22",
  "source": "docs/research/model-passports-2026-09.md",
```

Replace with:

```json
  "_comment": [
    "SSoT for WHICH MODEL implements a role, with launch parameters and fallback order.",
    "It is NOT the SSoT for which role/tier a do-feature step needs — that stays in",
    "do-feature/SKILL.md (Model Routing Matrix), which by its own wording routes by TIERS,",
    "not model names. Matrix answers 'this step needs tier X'; this file answers",
    "'tier/role X is served by these models, in this order, with these parameters'.",
    "Numbers come from docs/research/model-passports-2026-09.md (measured 2026-09-22).",
    "Consumed by claude-home/scripts/model-run.sh. Edit here, never in a skill.",
    "measured_seconds = ~2k-token single prompt incl. CLI startup (passport). Multi-turn tool/web tasks take far longer: read model-stats.py, not this field."
  ],
  "version": 1,
  "updated": "2026-09-24",
  "source": "docs/research/model-passports-2026-09.md",
  "capabilities_source": "bd python-ai-skills-2fu comment 2026-09-24: real runs of all ten models, web search checked by a live PyPI query.",
```

- [ ] **Step 4: Add `capabilities.web_search` to every model**

Apply these ten edits (each `old_string` is unique in the file because the following `notes` text
differs per model):

`opus-xhigh` — find:
```json
      "quota": "Anthropic Max 5x — scarce, 5h rolling window",
      "notes": "Fastest measured position at every context size."
```
replace:
```json
      "quota": "Anthropic Max 5x — scarce, 5h rolling window",
      "capabilities": {"web_search": true},
      "notes": "Fastest measured position at every context size."
```

`fable-medium` — find:
```json
      "quota": "Anthropic Max 5x — scarce",
      "notes": "Twice the per-token price of opus and slower at high effort; keep for work that explicitly needs it."
```
replace:
```json
      "quota": "Anthropic Max 5x — scarce",
      "capabilities": {"web_search": true},
      "notes": "Twice the per-token price of opus and slower at high effort; keep for work that explicitly needs it."
```

`sonnet-low` — find:
```json
      "quota": "Anthropic Max 5x — scarce, separate weekly Sonnet cap",
      "notes": "Refused a word-salad test fixture under the AUP classifier; generate fixtures as coherent prose."
```
replace:
```json
      "quota": "Anthropic Max 5x — scarce, separate weekly Sonnet cap",
      "capabilities": {"web_search": true},
      "notes": "Refused a word-salad test fixture under the AUP classifier; generate fixtures as coherent prose."
```

`haiku` — find:
```json
      "quota": "Anthropic Max 5x",
      "notes": "Smallest Anthropic window. Fails with 'Prompt is too long' above ~170k tokens of usable context."
```
replace:
```json
      "quota": "Anthropic Max 5x",
      "capabilities": {"web_search": true},
      "notes": "Smallest Anthropic window. Fails with 'Prompt is too long' above ~170k tokens of usable context."
```

`glm-5.3-high` — find:
```json
      "unavailable_mcp": ["claude_ai_Claude_Docs", "claude_ai_Gmail", "claude_ai_Google_Calendar", "claude_ai_Google_Drive"],
      "notes": "claude-glm remaps tiers: --model fable reaches glm-5.3. Reasoning cannot be disabled; only low/high/max exist."
```
replace:
```json
      "unavailable_mcp": ["claude_ai_Claude_Docs", "claude_ai_Gmail", "claude_ai_Google_Calendar", "claude_ai_Google_Drive"],
      "capabilities": {"web_search": true},
      "notes": "claude-glm remaps tiers: --model fable reaches glm-5.3. Reasoning cannot be disabled; only low/high/max exist."
```

`glm-4.7` — find:
```json
      "unavailable_mcp": ["claude_ai_Claude_Docs", "claude_ai_Gmail", "claude_ai_Google_Calendar", "claude_ai_Google_Drive"],
      "notes": "claude-glm remaps --model sonnet to glm-4.7. Window is ~205k, not 1M."
```
replace:
```json
      "unavailable_mcp": ["claude_ai_Claude_Docs", "claude_ai_Gmail", "claude_ai_Google_Calendar", "claude_ai_Google_Drive"],
      "capabilities": {"web_search": true},
      "notes": "claude-glm remaps --model sonnet to glm-4.7. Window is ~205k, not 1M."
```

`gpt-sol-xhigh` — find:
```json
      "quota": "ChatGPT Plus — 10-100 Sol messages / 5h, shared with ChatGPT Work",
      "notes": "Slowest-but-strongest Codex position."
```
replace:
```json
      "quota": "ChatGPT Plus — 10-100 Sol messages / 5h, shared with ChatGPT Work",
      "capabilities": {"web_search": true},
      "notes": "Slowest-but-strongest Codex position."
```

`gpt-terra-high` — find:
```json
      "quota": "ChatGPT Plus — 25-200 Terra messages / 5h",
      "notes": "Best balance measured in the Codex pool."
```
replace:
```json
      "quota": "ChatGPT Plus — 25-200 Terra messages / 5h",
      "capabilities": {"web_search": true},
      "notes": "Best balance measured in the Codex pool."
```

`gpt-luna-low` — find:
```json
      "quota": "ChatGPT Plus — 250-2000 Luna messages / 5h",
      "notes": "Fastest non-Anthropic position at small and medium context."
```
replace:
```json
      "quota": "ChatGPT Plus — 250-2000 Luna messages / 5h",
      "capabilities": {"web_search": true},
      "notes": "Fastest non-Anthropic position at small and medium context."
```

`qwen38` — find:
```json
      "quota": "none — costs machine time only",
      "notes": "Smallest window of any channel and 10-24x slower than every subscription pool. Batch work only. The only channel where code never leaves own infrastructure."
```
replace:
```json
      "quota": "none — costs machine time only",
      "capabilities": {"web_search": false},
      "notes": "Smallest window of any channel and 10-24x slower than every subscription pool. Batch work only. The only channel where code never leaves own infrastructure."
```

- [ ] **Step 5: Update the `policy` block**

Find:

```json
  "policy": {
    "penalty_seconds": 3600,
    "penalty_scope": "whole model",
    "penalize_on": ["unavailable"],
    "no_penalty_on": ["context_overflow", "timeout"],
    "_policy_comment": [
      "unavailable = quota exhausted, gateway 5xx, auth failure, network down: the model is",
      "genuinely unusable for a while, so a 1h circuit breaker avoids pointless retries.",
      "context_overflow is not a fault — the model is fine, the task does not fit; jump to a",
      "model with a bigger window instead of punishing this one.",
      "timeout is NOT penalised by default: qwen legitimately takes 190 s, and penalising",
      "slowness would evict the free pool permanently. Set penalize_on_timeout per model to",
      "override."
    ]
  },
```

Replace with:

```json
  "policy": {
    "penalty_seconds": 3600,
    "penalty_scope": "whole model",
    "penalize_on": ["unavailable"],
    "no_penalty_on": ["context_overflow", "timeout", "check_failed"],
    "output_retention_days": 14,
    "_policy_comment": [
      "unavailable = quota exhausted, gateway 5xx, auth failure, network down: the model is",
      "genuinely unusable for a while, so a 1h circuit breaker avoids pointless retries.",
      "context_overflow is not a fault — the model is fine, the task does not fit; jump to a",
      "model with a bigger window instead of punishing this one.",
      "timeout is NOT penalised by default: qwen legitimately takes 190 s, and penalising",
      "slowness would evict the free pool permanently. Set penalize_on_timeout per model to",
      "override.",
      "check_failed = exit 0 but the answer is empty or misses the caller's --expect regex: the model works, the answer does not fit this task. Never penalised; the output is kept."
    ]
  },
```

- [ ] **Step 6: Document the outputs directory in `state_files`**

Find:

```json
  "state_files": {
    "_comment": "Runtime state, machine-local. NEVER committed: it is state, not configuration.",
    "journal": "~/.claude/model-journal.jsonl",
    "penalties": "~/.claude/model-penalties.json"
  }
```

Replace with:

```json
  "state_files": {
    "_comment": "Runtime state, machine-local. NEVER committed: it is state, not configuration.",
    "journal": "~/.claude/model-journal.jsonl",
    "penalties": "~/.claude/model-penalties.json",
    "outputs": "~/.claude/model-outputs/ (kept outputs of non-ok attempts; pruned by model-run.sh after policy.output_retention_days)"
  }
```

- [ ] **Step 7: Validate the JSON and run the full suite**

Run: `python3 -m json.tool claude-home/model-registry.json > /dev/null && echo "valid JSON"`

Expected: `valid JSON` (this is also what the `settings-template-json`-style check in the pre-commit
config would demand, though that specific hook only fires on `settings.json.template` — this is a
manual sanity check for the registry itself).

Run: `python3 -m pytest claude-home/scripts/test_model_run.py -v`

Expected: 25 passed (unchanged count — Step 1 extended an existing test function, it did not add a
new one).

- [ ] **Step 8: Commit**

```bash
git add claude-home/model-registry.json claude-home/scripts/test_model_run.py
git commit -m "feat(model-registry): record web_search capability per model and the check_failed/retention policy"
```

---

### Task 7: `model-stats.py` — pin generic handling of `check_failed` and new keys

**Files:**
- Modify: `claude-home/scripts/test_model_stats.py` (append 2 tests after
  `test_cli_text_output_mentions_each_model`)
- Modify: `claude-home/scripts/model-stats.py` (module docstring only — no logic change)

**Interfaces:**
- Consumes: the journal schema from Task 3 (`out_path`/`out_bytes`, possibly absent on older
  lines) and the outcome name from Task 4 (`check_failed`).
- Produces: nothing new for later tasks — this is the terminal consumer of the journal schema in
  this plan.

Design decision D-4 (S1, `docs/superpowers/specs/20260924-model-run-evidence-design.md` section
1): `model-stats.py` needs **no code change**. Outcomes are counted into a generic
`defaultdict(int)` (`model-stats.py:84`) and rendered as sorted `k=v` pairs (`:147`); every journal
key is read with `.get()` (`:76-79`), so a line with or without `out_path`/`out_bytes` parses the
same way; `check_failed` attempts have real `seconds` and are not `context_overflow`, so they
already enter the latency picture the same as any other timed outcome. This task therefore has no
RED step in the usual sense — the two tests below are expected to **pass on the first run**,
because they pin behaviour the code already has.

- [ ] **Step 1: Write the two tests**

In `claude-home/scripts/test_model_stats.py`, find the exact tail of
`test_cli_text_output_mentions_each_model` (the last function in the file):

```python
def test_cli_text_output_mentions_each_model(tmp_path, capsys):
    journal = tmp_path / "j.jsonl"
    write_journal(journal, [entry(), entry(model="qwen38", pool="local", role="batch", seconds=190)])
    model_stats.main(["--journal", str(journal), "--penalties", str(tmp_path / "none.json")])
    text = capsys.readouterr().out
    assert "glm-4.7" in text and "qwen38" in text
    assert "active penalties: none" in text
```

Replace with the same text plus two new tests appended after it:

```python
def test_cli_text_output_mentions_each_model(tmp_path, capsys):
    journal = tmp_path / "j.jsonl"
    write_journal(journal, [entry(), entry(model="qwen38", pool="local", role="batch", seconds=190)])
    model_stats.main(["--journal", str(journal), "--penalties", str(tmp_path / "none.json")])
    text = capsys.readouterr().out
    assert "glm-4.7" in text and "qwen38" in text
    assert "active penalties: none" in text


def test_check_failed_is_counted_and_rendered(tmp_path):
    journal = tmp_path / "j.jsonl"
    write_journal(journal, [entry(outcome="ok"), entry(outcome="check_failed", seconds=5)])
    stats = model_stats.summarize(model_stats.read_journal(journal, None))
    assert stats["by_model"]["glm-4.7"]["outcomes"] == {"ok": 1, "check_failed": 1}
    assert stats["by_pool"]["zai"] == {"calls": 2, "ok": 1}
    text = model_stats.render(stats, {})
    assert "check_failed=1" in text


def test_lines_with_and_without_new_keys_both_parse(tmp_path):
    journal = tmp_path / "j.jsonl"
    old_line = entry(outcome="ok")  # no out_path/out_bytes, as written before this feature
    new_line = entry(outcome="check_failed", seconds=3)
    new_line["out_path"] = "/home/user/.claude/model-outputs/x.out"
    new_line["out_bytes"] = None
    write_journal(journal, [old_line, new_line])
    rows = model_stats.read_journal(journal, None)
    assert len(rows) == 2
    stats = model_stats.summarize(rows)
    assert stats["total_attempts"] == 2
    assert stats["by_model"]["glm-4.7"]["outcomes"] == {"ok": 1, "check_failed": 1}
```

- [ ] **Step 2: Run the two new tests, confirm they pass immediately**

Run: `python3 -m pytest claude-home/scripts/test_model_stats.py -k "check_failed or new_keys" -v`

Expected: 2 passed, no code change required — this confirms design decision D-4 in practice, not
just on paper.

- [ ] **Step 3: Name `check_failed` in the module docstring**

In `claude-home/scripts/model-stats.py`, find:

```python
"""model-stats.py — read the model journal and answer four questions.

  1. Which models actually ran, how often, and how did they end?
  2. How fast were they really (median and p90, not the passport guess)?
  3. How much work stayed off the scarce Anthropic pool?
  4. Which models are penalised right now?

Facts only: every number here is counted from journal lines written by
model-run.sh. Nothing is scored, judged, or estimated.

  model-stats.py [--journal PATH] [--penalties PATH] [--since HOURS] [--json]
"""
```

Replace with:

```python
"""model-stats.py — read the model journal and answer four questions.

  1. Which models actually ran, how often, and how did they end?
  2. How fast were they really (median and p90, not the passport guess)?
  3. How much work stayed off the scarce Anthropic pool?
  4. Which models are penalised right now?

Facts only: every number here is counted from journal lines written by
model-run.sh. Nothing is scored, judged, or estimated. Outcome names are
whatever model-run.sh writes (ok, unavailable, context_overflow, timeout,
check_failed, error) — this module counts and renders them generically and
never special-cases one, so a new outcome value needs no change here.

  model-stats.py [--journal PATH] [--penalties PATH] [--since HOURS] [--json]
"""
```

- [ ] **Step 4: Run the full `model-stats.py` suite, confirm it still passes**

Run: `python3 -m pytest claude-home/scripts/test_model_stats.py -v`

Expected: 14 passed (12 pre-existing + 2 new). The docstring edit changes no behaviour.

- [ ] **Step 5: Commit**

```bash
git add claude-home/scripts/test_model_stats.py claude-home/scripts/model-stats.py
git commit -m "test(model-stats): pin check_failed counting/rendering and tolerance of new journal keys"
```

---

### Task 8: Documentation, full test sweep, pre-commit

**Files:**
- Modify: `claude-home/CLAUDE.md` (the "delegating by role" paragraph, currently lines 356-360)
- Modify: `CHANGELOG.md` (`### Added` section under `## [Unreleased]`)

**Interfaces:**
- Consumes: the finished behaviour of Tasks 2-7 (this task only describes it).
- Produces: nothing consumed by a later task in this plan — Task 9 is operational, not code.

- [ ] **Step 1: Update the "delegating by role" paragraph**

In `claude-home/CLAUDE.md`, find (verified at lines 356-360 in this session):

```markdown
**Rule (delegating by role):** to hand work to another pool, call the runner instead of assembling a command by hand:
```bash
~/.claude/scripts/model-run.sh --role executor --task task.txt --out result.md
```
It picks the first usable model of that role, applies the registry timeout, skips models under an active penalty, distinguishes *unavailable* (quota/5xx/auth → 1-hour penalty on the whole model) from *context overflow* (no penalty — jump to a wider window) and from *slow* (no penalty — slowness is a passport property, not a fault), and appends one facts-only line per attempt to `~/.claude/model-journal.jsonl`. The journal and `~/.claude/model-penalties.json` are machine-local runtime state and are never committed.
```

Replace with:

```markdown
**Rule (delegating by role):** to hand work to another pool, call the runner instead of assembling a command by hand:
```bash
~/.claude/scripts/model-run.sh --role executor --task task.txt --out result.md
```
It picks the first usable model of that role, applies the registry timeout, skips models under an active penalty, distinguishes *unavailable* (quota/5xx/auth → 1-hour penalty on the whole model) from *context overflow* (no penalty — jump to a wider window) and from *slow* (no penalty — slowness is a passport property, not a fault), and appends one facts-only line per attempt to `~/.claude/model-journal.jsonl`. Pass `--expect REGEX` to reject an empty or off-target answer as `check_failed` (never penalised, next model tried); every non-`ok` attempt keeps its output under `~/.claude/model-outputs/` (age-pruned), path and size on the journal line. The journal and `~/.claude/model-penalties.json` are machine-local runtime state and are never committed.
```

- [ ] **Step 2: Add the CHANGELOG entries**

In `CHANGELOG.md`, find:

```markdown
## [Unreleased]

### Added
```

Replace with (inserting two new bullets right after `### Added`, before the existing git-finish
bullet):

```markdown
## [Unreleased]

### Added
- `claude-home/scripts/model-run.sh`: kept the output of every attempt that ran and was not `ok` (timeout, unavailable, context_overflow, error, check_failed) under `$MODEL_OUTPUTS` (default: next to the journal, `~/.claude/model-outputs/`), instead of `rm -f`'ing it — a 2026-09-24 timeout on `glm-4.7` (420 s, session `618791ff`) had discarded the one file that could explain the cause. The capture file is created there from the start (named `<start-time>-<model>-<random>.out`, mode 0600); the journal line gains `out_path`/`out_bytes` (null for `ok` and pre-flight `context_overflow`). Retention: files older than `policy.output_retention_days` (14, precedent `housekeeping.py`'s `JOB_MAX_AGE_DAYS`) are pruned by `find` at the start of every real run; `--dry-run` neither creates the directory nor prunes (bd `python-ai-skills-2fu`)
- `claude-home/scripts/model-run.sh`: new `--expect REGEX` flag and `check_failed` outcome — the caller states what a usable answer must contain (POSIX ERE, `grep -E`); an empty answer or a miss is `check_failed`, never penalised, and the run tries the next model of the role instead of reporting an empty card as `ok` (the 2026-09-24 `gpt-terra-high` line on task-57 had exit 0 and no usable content). `--expect` is rejected at startup (exit 2) if the regex is invalid or matches the task text itself, since stdout/stderr are merged and an echoed prompt would otherwise pass. `--help` now prints the full header (was a fixed `sed` range that clipped code lines) and lists the flag and outcome. `claude-home/model-registry.json`: records `capabilities.web_search` (bool) for all ten models — the only limitation found is `qwen38` (search returns an echoed query, 0 URLs; page fetch works) — and adds `check_failed` to `policy.no_penalty_on` plus `policy.output_retention_days: 14`. `claude-home/scripts/model-stats.py` needed no code change (outcomes are counted and rendered generically); 2 new tests in `test_model_stats.py` pin that (bd `python-ai-skills-2fu`)
```

- [ ] **Step 3: Run the full project test sweep**

Run: `make test`

Expected: all suites pass — `test_block_no_verify.py`, `test_delegation_pool_nudge.py`,
`test_housekeeping.py`, `test_model_run.py` (25 tests), `test_model_stats.py` (14 tests). The bd
`python-ai-skills-2fu` notes record a pre-feature baseline of 126 passed; this plan adds 2 tests in
Task 1 and 13 across Tasks 2-4 and 7 to `test_model_run.py`/`test_model_stats.py` (2+1+5+4+1+2 =
15), so 141 passed is the expected total — treat any failure or error as a blocker, not a passing
count different from 141 as automatically wrong (re-derive the count from `-q` output rather than
trusting this arithmetic blindly).

- [ ] **Step 4: Stage and run the pre-commit gate on the changed docs**

```bash
git add claude-home/CLAUDE.md CHANGELOG.md
pre-commit run --files claude-home/CLAUDE.md CHANGELOG.md
```

Expected: `gitleaks-staged` passes (no secret patterns in either file); `settings-template-json`,
`hook-regression-tests`, and `scripts-regression-tests` are skipped (their `files:` regexes do not
match `claude-home/CLAUDE.md` or `CHANGELOG.md`). Exit 0.

- [ ] **Step 5: Commit**

```bash
git commit -m "docs(model-run): document kept outputs, --expect and capabilities"
```

This closes the TDD scope of bd `python-ai-skills-2fu` (FR-3 through FR-8, FR-10, NFR-6). FR-9
remains — Task 9 below.

---

### Task 9: FR-9 — re-run task-57, verify, record (operational, run by the orchestrator)

This task is **not** a worker subagent task: it runs a real delegate against real pools and quota,
verifies facts against a live external site, and writes a bd comment. It has no RED/GREEN cycle
and touches no file in this repository. Run it in the main session, after Task 8 is committed.

**Why re-run at all:** `glm-4.7` has already timed out on this exact task twice before this
feature existed — `~/.claude/model-journal.jsonl` lines
`{"ts":"2026-09-24T10:47:48+03:00", ..., "outcome":"timeout","exit":124,"seconds":420.49,"session":"618791ff-4287-4958-aa4f-bd6ebcfff430"}`
and
`{"ts":"2026-09-24T11:34:00+03:00", ..., "outcome":"timeout","exit":124,"seconds":420.50,"session":"618791ff-4287-4958-aa4f-bd6ebcfff430"}`
(verified directly against the journal file in this session). Both discarded their output under
the old code. If `glm-4.7` times out a third time here, Tasks 2-3 mean the timeout's capture file
is now kept — read it (`out_path` on that journal line) before concluding the cause is still
unknown; root-causing the 420 s itself stays LATER-scoped per the design, but a non-empty file to
read is new evidence this run produces that the two September runs could not.

- [ ] **Step 1: Note the session id and start time**

```bash
echo "session=$CLAUDE_CODE_SESSION_ID"
date -Is
```

Record both — they are the filter used in Step 6 to pull only this run's journal lines.

- [ ] **Step 2: Write the task file to a session-local, uncommitted directory**

The exact task text is bd `python-ai-skills-2fu`'s NOTES field, from "Задача:" up to and including
the line ending "...которые ты реально открыл." (the NOTES field also holds later do-feature
process notes, which must be excluded). Reproduced verbatim below, verified against `bd show
python-ai-skills-2fu` in this session:

```bash
WORKDIR=$(mktemp -d)
cat > "$WORKDIR/task-57.txt" <<'TASK_EOF'
Задача: проверить факты о московской школе № 57 по официальным источникам и вернуть готовую Markdown-карточку. Файлы НЕ редактировать, git-команды НЕ выполнять. Ответ — только текст карточки.

ПРАВИЛА (обязательны):

1. Ничего не выдумывать. Каждая цифра и каждый факт — только со ссылкой на КОНКРЕТНУЮ страницу, которую ты реально открыл (WebFetch) в этой работе. Знания из памяти источником не являются.
2. Нет источника — писать «не собрано». Пустое поле лучше правдоподобного.
3. Уровни источников: 1 — официальный сайт школы (правила приёма, контакты), 2 — официальный Telegram/VK, на который ссылается сайт школы, 3 — агрегаторы/СМИ (только если нет 1–2), 4 — отзывы (не использовать).
4. Источники противоречат — записать оба значения с обеими ссылками и пометкой «расхождение».
5. Формат факта: - **<поле>:** <значение> — [источник](<URL>), ур. <1-4>, проверено 2026-09-24

ЧТО ПРОВЕРИТЬ (текущие данные карточки, могут быть неверны):

• сайт школы; адрес здания, где учатся 8 классы; ОДНА ближайшая станция метро (только если указана на официальном сайте);
• в какие классы идёт набор; профили 8 класса;
• объявлен ли набор в 8 класс на 2027/2028 учебный год (только по прямому тексту на официальном сайте);
• даты приёма, если опубликованы (указать, к какому году они относятся).
Подсказка из прошлой проверки: официальный сайт — https://57.mskobr.ru/ (страницы /roditelyam/algoritm-postuplenia/profilnye-klassy, /proekty/nashi-proekty/priemnaya-kampaniya, /o-nas/kontakty-podrazdelenij).

## ФОРМАТ ОТВЕТА — ровно такой файл:

## название: "Школа № 57"
статус: кандидат
регион: Москва
тип: государственная
вуз: null
набор_в_8_2027: <да|нет|неизвестно>
классы_набора: [<числа>]
профили_8: [<строки в кавычках>]
стоимость_руб_в_мес: 0
курс_usd: null
курс_дата: null
оплата: бесплатно
рейтинги: []
сайт:
проверено: 2026-09-24

# Школа № 57

| Этап 0: факты перепроверены по официальным источникам 2026-09-24.

## Основное

## Приём в 8 класс

## Результаты

Не собрано.

## Связь с вузом

Нет.

## Преподаватели

Не собрано.

## Условия

Не собрано.

## Отзывы

Не собрано.

## Сроки

См. [[сроки]].
<даты приёма, найденные на официальном сайте, — списком со ссылками, с указанием года>

В конце, после карточки, строка === URL === и список всех URL, которые ты реально открыл.
TASK_EOF
echo "written: $WORKDIR/task-57.txt"
```

`$WORKDIR` is never committed (NFR-3) — it lives under the system temp directory, not this repo.

- [ ] **Step 3: Run in the background**

A single attempt can legitimately take up to 420 s (`glm-4.7`'s `timeout_seconds`) before the role
falls back to `gpt-terra-high` (480 s) and then `sonnet-low` (300 s) — up to ~20 minutes worst
case. Use the Bash tool's background-run option, or:

```bash
nohup /home/bgs/ai-steward/Gena_Beeline_Local/python-ai-skills/claude-home/scripts/model-run.sh \
  --role executor \
  --task "$WORKDIR/task-57.txt" \
  --out "$WORKDIR/card-57.md" \
  --expect '^=== URL ===$' \
  > "$WORKDIR/run.log" 2>&1 &
RUN_PID=$!
echo "pid=$RUN_PID workdir=$WORKDIR"
```

If this repo checkout is a worktree rather than the main clone, call the worktree's own
`claude-home/scripts/model-run.sh` path — `~/.claude/scripts/` is a symlink into the main checkout
and would run pre-Task-9 code.

- [ ] **Step 4: Wait for completion**

```bash
wait "$RUN_PID"
echo "exit=$?"
```

(Or, if launched via the Bash tool's background option, wait for its completion notification
instead of polling.)

- [ ] **Step 5: Read the result and pick facts to verify**

```bash
cat "$WORKDIR/card-57.md"
sed -n '/^=== URL ===$/,$p' "$WORKDIR/card-57.md"
```

If the role was exhausted (no model produced a card matching `--expect`), that is itself a valid,
reportable outcome — do not force a success; record what happened (Step 8) and tell the user FR-9's
acceptance criterion 1 was not met on this attempt.

If a card was produced: pick 1-2 concrete facts the card attributes to a `57.mskobr.ru` URL (a
class-profile name, a building address, an admission date) — this is a judgement step, since the
exact facts depend on what the model returned and cannot be scripted blindly.

- [ ] **Step 6: Verify with curl against the live site (Trust = 0% — the regex match alone is not acceptance)**

For each `57.mskobr.ru` URL listed after `=== URL ===`:

```bash
curl -s "<url>"
```

Confirm the fetched page's text actually contains the fact(s) chosen in Step 5. A model can list a
URL it never meaningfully used (the 2026-09-24 `gpt-terra-high` card had only web-search calls, no
page fetch, per bd comment 08:43) — the card claiming a URL is not itself proof.

- [ ] **Step 7: Build the bd comment, path reduced to file name only**

```bash
COMMENT_FILE=$(mktemp)
{
  echo "## FR-9 re-run of task-57, $(date -Is)"
  echo
  echo "Journal lines (session $CLAUDE_CODE_SESSION_ID), out_path reduced to file name (NFR-3):"
  echo '```'
  jq -c --arg s "$CLAUDE_CODE_SESSION_ID" \
    'select(.session == $s) | .out_path |= (if . then (. | split("/") | last) else . end)' \
    ~/.claude/model-journal.jsonl
  echo '```'
  echo
  echo "Card summary: <one or two lines on what the winning model returned, or 'role exhausted' if none did>"
  echo "Curl verification: <which 57.mskobr.ru URL(s) were fetched and which quoted fact(s) matched>"
} > "$COMMENT_FILE"
bd comments add python-ai-skills-2fu -f "$COMMENT_FILE"
```

(`bd comments add <issue-id> -f <file>` verified via `bd comments add --help` in this session.)

- [ ] **Step 8: Do not close the bd issues here**

Closing `python-ai-skills-tlo`/`python-ai-skills-2fu` is do-feature's Finish step (13), after
Review — out of scope for this plan (Writing Plans is step 9). Report Task 9's outcome to the user
and stop.

---

## Self-Review Checklist

**FR coverage:**
- [x] FR-1 (exit-code gate) -> Task 1, Step 3
- [x] FR-2 (regression test + existing true positives stay green) -> Task 1, Steps 1, 2, 4
- [x] FR-3 (kept output of every non-ok attempt) -> Task 2 (directory), Task 3 (capture-in-place,
  keep-not-delete)
- [x] FR-4 (journal `out_path`/`out_bytes`, null for `ok`/pre-flight overflow) -> Task 3
- [x] FR-5 (`--expect`, `check_failed`, fallback continues) -> Task 4
- [x] FR-6 (`check_failed` never penalised) -> Task 4, Step 5 (no `set_penalty` call in that
  branch); Task 6 documents it in `no_penalty_on` and the extended registry test asserts it
- [x] FR-7 (`model-stats.py` counts/renders new outcome, tolerates old/new keys) -> Task 7
- [x] FR-8 (registry `capabilities.web_search`, latency not conflated) -> Task 6
- [x] FR-9 (re-run task-57, verify, record) -> Task 9
- [x] FR-10 (`--help` lists the flag and outcome) -> Task 5

**NFR coverage:**
- [x] NFR-1 (no new runtime dependency) -> verified by inspection while writing this plan: every
  new bash construct (`mktemp --suffix`, `find -mmin -delete`, an additional `grep -qE`) uses
  binaries already invoked elsewhere in the same script or stock GNU coreutils/findutils/grep;
  `model-stats.py`'s new tests import nothing beyond what the file already imports
  (`json`, `time`, `pathlib.Path`, already present)
- [x] NFR-2 (126 existing tests stay green + new tests) -> Task 8, Step 3 (`make test`)
- [x] NFR-3 (machine-local, never committed, never absolute-path-cited) -> Task 2 (default under
  `$HOME/.claude`, test isolation via `tmp_path`), Task 9 Step 7 (bd comment reduces `out_path` to
  file name)
- [x] NFR-4 (append-only, additive schema) -> Task 3 (`journal()` still uses `>>`; `${8:-}`/`${9:-}`
  default absent args to `null`); Task 7's `test_lines_with_and_without_new_keys_both_parse`
- [x] NFR-5 (journal never carries output text) -> Task 3's `test_journal_line_has_no_output_text`;
  the `--expect` regex itself is never passed to `journal()` (Task 4)
- [x] NFR-6 (bounded retention) -> Task 2 (`find -mmin +N -delete`) and its pruning test

**Design test list (design section 3, tests 1-18) -> plan tasks:**
- [x] 1, 2 -> Task 1 · 3 (existing true positives stay green) -> Task 1, Step 4
- [x] 4, 5, 6 -> Task 3 · 7, 8, 9, 10 -> Task 4 · 11, 12 -> Task 2 · 13, 14 -> Task 3 · 15 -> Task 5
- [x] 16 -> Task 6 · 17, 18 -> Task 7

**Placeholder scan:** grepped this plan's intent for "TBD", "TODO", "fill in", "handle edge cases",
"similar to Task N" — none present; every step that changes a file gives its literal `old_string`/
`new_string` or literal command; Task 9's two narrative placeholders (`<one or two lines on what
the winning model returned...>`, `<which 57.mskobr.ru URL(s)...>`) are inside a bd-comment template
whose content is inherently only knowable after the live run happens — they are prompts for the
orchestrator to fill with real observations at execution time, not deferred implementation.

**Type/signature consistency across tasks:**
- [x] `classify(code, out_file)` — 2-arg contract unchanged from Task 1 through Task 4; each task's
  `old_string` for this function reproduces exactly the previous task's resulting body
- [x] `journal(...)` — 7 positional args through Task 2, extended to 9 in Task 3
  (`out_path`, `out_bytes`); the one other call site (pre-flight `context_overflow`) is
  intentionally left at 7 args, relying on `${8:-}`/`${9:-}` defaults, and this is called out
  explicitly in Task 3 rather than silently assumed
- [x] `registry(models, roles, penalty_seconds=3600, policy=None)` test helper — extended once, in
  Task 2, and used with the new `policy=` kwarg only from Task 2 onward; earlier positional-only
  call sites are unaffected (backward compatible)
- [x] `outputs_dir(env)` test helper — defined once in Task 2, reused as-is in Tasks 2 and 3

**Dependency order:** Task 1 before all of phase 2 (phase 2's `classify()` edits build on phase 1's
shape). Task 2 before Task 3 (`$OUTPUTS` must exist before capture-in-place uses it). Task 3 before
Task 4 (the per-attempt `case` block Task 4 edits is the one Task 3 produced). Task 4 before
Task 9 (`--expect` must exist to use it operationally). Task 6 has no code dependency on Tasks 2-5
(registry fields are documentation-only) but is ordered after them because its CHANGELOG/self-
review narrative refers to the finished behaviour. Task 7 depends only on Task 3/4's journal shape.
Task 8 last among the TDD/doc tasks (documents the finished whole). Task 9 last overall (needs
everything committed and working).

## Execution record (2026-09-24)

- Phase 1: `ddf0dc6`. Deviation: the CHANGELOG bullet of Task 1 was skipped by the worker (write scope given by the controller omitted CHANGELOG.md) and added in Task 8 (`d8f81aa`).
- Phase 2: `9c41c1a`, `2cce8fc`, `f137245`, `af1afe7`, `df2b1cd`, `7d3b773`, `d8f81aa` — as planned.
- Step 12 review fixes, not in this plan, applied inline by the controller with TDD: `e057cef` (value flags, outputs dir, retention validation, failed --out move), `f4e7d4d` (docs wording, FR-8 text).
- Task 9: done; results in the bd comment on `python-ai-skills-2fu`. 57.mskobr.ru content pages are JS-rendered (≈590 chars of HTML text), so only the weak form of acceptance 1 is reachable.
