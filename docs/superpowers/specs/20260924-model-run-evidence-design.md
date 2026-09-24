---
feature: model-run-evidence
bd_id: python-ai-skills-2fu
related_bd_ids:
  - python-ai-skills-tlo
date: 2026-09-24
status: design
discovery: docs/superpowers/specs/20260924-model-run-evidence-discovery.md
risk: medium
risk_justification: Unchanged from discovery - three modules (model-run.sh, model-stats.py tests, model-registry.json), one new machine-local directory, additive journal keys; no public API break, no auth surface.
evidence: strong
evidence_justification: Every design choice cites file:line of the current code or a local command run on 2026-09-24 (GNU grep 3.11, GNU findutils 4.9.0, GNU coreutils 9.4 mktemp, jq 1.7).
open_questions: []
context7_verified: []
technology_stack:
  - bash (runner, unchanged)
  - jq 1.7 (journal line, registry reads - already used)
  - GNU coreutils (mktemp --suffix, wc, date, timeout - already used except --suffix)
  - GNU grep (already used by classify; now also for --expect)
  - GNU findutils find (new for the runner - retention)
  - Python 3 stdlib (model-stats.py, tests)
decisions:
  - D-1 (FR-1): exit-code gate - text patterns are consulted only when exit is non-zero; exit 0 goes to the answer checks.
  - D-2 (FR-3/FR-4/NFR-6): kept outputs in $(dirname JOURNAL)/model-outputs, override MODEL_OUTPUTS; files created there by mktemp from the start; retention by find inside model-run.sh on every real run, days from registry policy.output_retention_days (14).
  - D-3 (FR-5/FR-6): flag --expect REGEX (grep -E, case-sensitive, validated at startup, rejected if it matches the task file); one new outcome check_failed for both empty output and regex miss; never penalised.
  - D-4 (FR-7): model-stats.py code unchanged; new tests pin rendering of check_failed and tolerance of new keys.
  - D-5 (FR-8): models.<name>.capabilities = {web_search - bool} on all ten models, provenance in top-level capabilities_source; latency explained in one _comment line, no new number.
  - D-6 (FR-9): task-57 re-run through the phase-2 runner with an anchored --expect; acceptance verified by the main session with curl; journal lines recorded in a bd comment with out_path reduced to its file name.
phases:
  - id: phase-1
    bd_id: python-ai-skills-tlo
    covers: [FR-1, FR-2]
    committable_alone: true
  - id: phase-2
    bd_id: python-ai-skills-2fu
    covers: [FR-3, FR-4, FR-5, FR-6, FR-7, FR-8, FR-9, FR-10, NFR-6]
---

# Design — model-run.sh: truthful outcomes and kept evidence

> Step 4 of do-feature for bd `python-ai-skills-2fu` (+ `python-ai-skills-tlo`).
> FR/NFR/risks/constraints live in the discovery file named in the frontmatter and are referenced
> here by id only.

`context7_verified: []` — the design uses no third-party library: bash, jq, GNU coreutils/grep/
findutils and Python stdlib only. Non-obvious tool behaviour was verified by local runs
(section 3.5) instead of Context7.

## 1. Decision points

### D-1. How classify() uses the exit code (FR-1, FR-2)

Facts: classify greps the capture for overflow and unavailability words before looking at the
exit code (`model-run.sh:91-97`); stdout and stderr are merged (`model-run.sh:156`).

1. **A1 — exit-code gate.** `124 → timeout`; non-zero → overflow words / unavailability words /
   `error` as today; exit 0 → answer checks (phase 1: straight to `ok`).
   - KISS: one reordering, no new file. Explicit: "text refines a failure, never overrides a
     success" becomes the literal code shape. Testability: pure function of (code, file, check).
   - Cost: R-1 (a wrapper that exits 0 on a real outage) — accepted in discovery.
2. **A2 — capture stderr separately, grep stderr only.** Rejected: changes what reaches `--out`
   (today it gets both streams), and rests on the unverified assumption that every runner writes
   errors to stderr and answers to stdout (discovery 1.4 p.2). Violates scope and Fail-Fast on an
   unverified premise.
3. **A3 — gate only the unavailability words on non-zero exit.** Rejected: an exit-0 answer that
   mentions "maximum context" would still be relabelled `context_overflow` — FR-1 names both
   outcomes.

**Chosen: A1** (dominant — only option satisfying FR-1 without changing `--out` content).

### D-2. Where kept outputs live, their names, and retention (FR-3, FR-4, NFR-3, NFR-6)

Path scheme:

1. **P1 — derived default `$(dirname "$JOURNAL")/model-outputs`, override `MODEL_OUTPUTS`.**
   Next to the journal by construction (OQ-1). Existing tests set `MODEL_JOURNAL` to `tmp_path`
   (`test_model_run.py:41-48`), so every existing test is isolated with no fixture change — no
   stray files in the real `~/.claude`.
2. **P2 — fixed default `$HOME/.claude/model-outputs` + `MODEL_OUTPUTS`.** Rejected: the 12
   existing tests produce non-ok attempts (`test_model_run.py:94-242`) and would write into the
   real home unless every call site learns the new variable — a silent Testability trap.
3. **P3 — read the path from registry `state_files`.** Rejected: `state_files` is documentation
   only today (`model-run.sh:20-22` never reads it); making one entry live and two not is
   inconsistent (Explicit/SSoT).

**Chosen: P1.** `state_files.outputs` documents the default, as `journal`/`penalties` do.

File creation and naming: the capture file is created **in the outputs directory from the start**
(replacing `mktemp` in `/tmp`, `model-run.sh:154`):

```bash
tmp_out=$(mktemp --suffix=.out "$OUTPUTS/$(date +%Y%m%dT%H%M%S)-${MODEL//[^A-Za-z0-9._-]/_}-XXXXXX")
```

- Name = local start time + model key + random 6 chars: sortable, readable, collision-free across
  concurrent runs. Session and attempt are already on the journal line that points to the file.
- Mode 0600 (verified, 3.5) — outputs may contain task text (R-2).
- On `ok`: moved to `--out` or printed and removed, as today (`model-run.sh:166`). On any other
  attempt that ran: kept. No move for non-ok means no cross-filesystem copy.
- Rejected alternative: keep `/tmp` capture and `mv` only non-ok files — two paths for one file,
  and a crash of the runner loses the evidence it was meant to keep.

Retention:

1. **R-a — inside model-run.sh, every real (non-dry) run, before the first attempt:**
   `find "$OUTPUTS" -maxdepth 1 -type f -name '*.out' -mmin +$((DAYS*1440)) -delete`.
   - SRP / ownership: the component that creates the state expires it — same as penalties expire
     inside the runner (`model-run.sh:62-66`).
   - Works on every machine that produces outputs; growth happens only when the runner runs, so
     the bound holds exactly where needed.
   - `-maxdepth 1 -name '*.out'` keeps a mis-set `MODEL_OUTPUTS` from deleting anything else;
     `-mmin` avoids `-mtime`'s whole-day rounding (3.5).
   - Testable in `test_model_run.py` with `os.utime`.
2. **R-b — a rule in housekeeping.py.** Rejected: its schedule is per-machine and manual
   (`housekeeping.service:2-4` systemd on the laptop, cron+wrapper on vpn-2 per
   `housekeeping-wrapper.sh:1`); a machine without it never prunes. It would also duplicate the
   directory path as a second constant next to `JOBS_DIR` (`housekeeping.py:51`) — DRY/SSoT.
   Housekeeping tests are not in the commit-time gate (`.pre-commit-config.yaml` has no
   housekeeping hook).
3. **R-c — both.** Rejected: YAGNI, two owners of one lifecycle.

**Chosen: R-a.** Days live in the registry: `policy.output_retention_days: 14` (precedent
`JOB_MAX_AGE_DAYS = 14`, `housekeeping.py:41`), read with `jq '.policy.output_retention_days // 14'`.

### D-3. The caller's answer check and the new outcome (FR-5, FR-6)

Flag name and semantics:

1. **`--expect REGEX`** — POSIX ERE via `grep -qE -- "$EXPECT"`, case-sensitive, line-based,
   applied to the whole capture. Reads as "I expect the answer to contain…".
2. `--check` — rejected: collides in meaning with the built-in empty check; unclear what is
   checked. `--require` — rejected: reads like a dependency flag.
3. Case-insensitive default — rejected: Explicit; a caller who needs it writes `[Uu]rl`.

Two fail-fast validations at startup (exit 2, `die`, before any model runs):

1. `grep -qE -- "$EXPECT" </dev/null` returns 2 → invalid regex (verified: GNU grep exit 2).
2. The regex matches the **task file** → die "--expect matches the task text; it would pass on an
   echoed prompt". Reason: streams are merged (`model-run.sh:156`), and whether a runner echoes
   the prompt is unverified. Verified on the task-57 text: unanchored `=== URL ===` and
   `https?://57\.mskobr\.ru` each match it once; anchored `^=== URL ===$` does not (3.5).

Outcome name — **`check_failed`**:

- One plain snake_case name that says what happened and matches the wording discovery already
  uses (FR-3 "the new check-failed outcome").
- Rejected `rejected` (who rejected?), `empty` (only one of two causes), `bad_answer` (a judgement,
  not a fact — model-stats is "facts only", `model-stats.py:9-10`).

Empty output and regex miss → **one outcome**:

- Handling is identical for both: not penalised (OQ-3), output kept, next model tried. Existing
  outcomes are split by handling/cause class, and here the cause class is the same ("process
  succeeded, answer unusable").
- The two cases stay distinguishable from facts already on the line: `out_bytes` and the kept
  file. Two outcomes — rejected: YAGNI, one more name in help, registry policy and stats.
- "Empty" = no non-whitespace character: `! grep -q '[^[:space:]]'`. Caveat, stated in `--help`:
  since stderr is merged, runner noise makes output non-empty, so the regex is the real guard.

### D-4. model-stats.py (FR-7)

Facts: outcomes are counted into a generic dict (`model-stats.py:84`) and rendered generically as
sorted `k=v` pairs (`model-stats.py:147`); pool/role count only `ok` (`:92-94`); all keys are
read with `.get` (`:76-79`); latency uses any non-zero `seconds` except `context_overflow`
(`:87-88`) — `check_failed` attempts really ran, so their seconds belong in the latency picture.

1. **S1 — no code change, new tests pin the behaviour.** DRY/YAGNI: the generic path already does
   what FR-7 asks.
2. S2 — dedicated per-outcome columns. Rejected: a fixed column set breaks on the next outcome.
3. S3 — report kept-file count/bytes from `out_bytes`. Rejected: not requested; `ls` on the
   directory answers it.

**Chosen: S1.** Only the module docstring gains one line naming `check_failed` if the reviewer
wants it; no logic change.

### D-5. Registry: capability key and the policy block (FR-8)

Capability shape (OQ-4 decided "structured key only"):

1. **C1 — `"capabilities": {"web_search": true|false}` on all ten models**, plus top-level
   `"capabilities_source"` naming the 2026-09-24 measurement (bd `python-ai-skills-2fu`
   comment: search works on 9 of 10, `qwen38` returns only an echo of the query).
   - Explicit: absent key cannot be misread as "has it"; the measurement covers all ten, so the
     data exists.
   - A map, not a flat key: the LATER capability-aware skip can add keys without a new shape.
2. C2 — `web_search: false` on `qwen38` only. Rejected: absence becomes ambiguous
   ("has it" vs "not measured") for the LATER skip logic.
3. C3 — negative list `"lacks": ["web_search"]`, mirroring `unavailable_mcp` (`model-registry.json:100`).
   Rejected: same ambiguity as C2.

`web_fetch` is not recorded: for codex it is site-dependent (opens pypi.org, fails on
57.mskobr.ru), which is not a boolean; FR-8 does not ask for it.

Latency (OQ-4: latency stays in the journal): no new number. One line added to the top-level
`_comment`: "`measured_seconds` = ~2k-token single prompt incl. CLI startup (passport); multi-turn
tool/web tasks take far longer — read `model-stats.py`, not this field." One place, applies to
every model (DRY), satisfies "does not conflate". `timeout_seconds` of `glm-4.7` (420,
`model-registry.json:110`) is **not** changed — the cause of the 420 s runs is LATER.

Policy block: `check_failed` added to `no_penalty_on`, `output_retention_days: 14` added, one
`_policy_comment` line explaining `check_failed`.

### D-6. Re-run of task-57 (FR-9)

1. Task text = bd `python-ai-skills-2fu` NOTES from "Задача:" up to "…которые ты реально
   открыл." (the NOTES field also holds later do-feature notes, which must be cut off). Written to
   a session job directory, never committed.
2. Command (run in background — up to ~15 min: glm-4.7 has timed out at 420 s twice):
   ```bash
   <repo>/claude-home/scripts/model-run.sh --role executor --task task-57.txt \
       --out card-57.md --expect '^=== URL ===$'
   ```
   If executed from a worktree, call the worktree's script path — `~/.claude/scripts` points to the
   main checkout.
3. Acceptance is **not** proven by the regex: a model can list a URL it never opened (the
   2026-09-24 terra card had only web-search calls, bd comment 08:43). The main session checks:
   the card has a `57.mskobr.ru` URL after `=== URL ===`; `curl` of that URL contains at least one
   quoted value (Trust = 0%).
4. Record: `bd comments add python-ai-skills-2fu` with every journal line of that session
   (`jq -c 'select(.session==…)'`), `out_path` reduced to the file name (NFR-3), plus the curl
   verification result.

## 2. Chosen design

### 2.1 CLI surface

```text
model-run.sh --role ROLE --task FILE [--out FILE] [--expect REGEX] [--dry-run] [-h|--help]
```

- `--expect REGEX` — new; ERE, case-sensitive; exit 2 if invalid or if it matches the task file.
- `--help` prints the header comment up to the first non-comment line (replaces the fixed
  `sed -n '2,20p'`, `model-run.sh:38`, which today also prints code lines 18-20 and would cut a
  longer header). Header gains the `--expect` usage line and the `check_failed` outcome (FR-10).

Environment variables:

- existing: `MODEL_REGISTRY`, `MODEL_JOURNAL`, `MODEL_PENALTIES`, `MODEL_RUN_SESSION`,
  `MODEL_CHARS_PER_TOKEN` (`model-run.sh:20-27`)
- new: `MODEL_OUTPUTS` — default `$(dirname "$JOURNAL")/model-outputs`

Exit codes unchanged: 0 answered, 1 role exhausted, 2 usage error (now also bad `--expect`).

### 2.2 classify() after both phases

```bash
classify() {   # code out_file
  local code="$1" out_file="$2"
  [ "$code" -eq 124 ] && { echo timeout; return; }
  if [ "$code" -ne 0 ]; then
    grep -qiE '<overflow words>'     "$out_file" && { echo context_overflow; return; }
    grep -qiE '<unavailable words>'  "$out_file" && { echo unavailable; return; }
    echo error; return
  fi
  # phase 2 only:
  grep -q '[^[:space:]]' "$out_file" || { echo check_failed; return; }
  if [ -n "$EXPECT" ] && ! grep -qE -- "$EXPECT" "$out_file"; then echo check_failed; return; fi
  echo ok
}
```

Pattern lists are unchanged (`model-run.sh:91, :94`).

### 2.3 Outcome table

| outcome | when | penalised | output kept | out_path/out_bytes |
|---|---|---|---|---|
| ok | exit 0, non-empty, `--expect` matches (or absent) | no | no (goes to `--out`) | null / null |
| check_failed (new) | exit 0 and (empty or `--expect` miss) | never | yes | path / bytes |
| timeout | exit 124 | only if `penalize_on_timeout` | yes | path / bytes |
| unavailable | exit ≠ 0 + unavailability words | yes (`penalty_seconds`) | yes | path / bytes |
| context_overflow (runtime) | exit ≠ 0 + overflow words | no | yes | path / bytes |
| context_overflow (pre-flight) | task tokens > window, not run | no | — | null / null |
| error | exit ≠ 0, no words matched | no | yes | path / bytes |

Rule in one line: *every attempt that ran and was not `ok` keeps its output* — runtime
`context_overflow` included (FR-3 lists four outcomes; one uniform rule is simpler and the file is
the evidence for tuning the overflow regex).

### 2.4 Journal line schema diff (additive, NFR-4, NFR-5)

Twelve existing keys unchanged (`model-run.sh:81-83`). Two added:

```diff
 {ts, role, model, pool, runner, ctx_chars, ctx_tokens, seconds, outcome, exit, attempt, session,
+ out_path,   # string: absolute path of the kept file | null
+ out_bytes}  # integer: size in bytes (wc -c) | null
```

- `journal()` takes two more positional args; empty string → `null` via
  `(if $p == "" then null else $p end)` / `($b | tonumber)` (verified, 3.5).
- Absolute path: the journal is machine-local; a bare name would be ambiguous under
  `MODEL_OUTPUTS`. Committed documents cite the file name only (NFR-3).
- The expect regex itself is **not** journalled (NFR-5: it is caller/task text).

### 2.5 File layout

```text
~/.claude/
├── model-journal.jsonl
├── model-penalties.json
└── model-outputs/                          # new, 0700 via mkdir -p under umask, files 0600
    └── 20260924T112701-glm-4.7-Ab3xYz.out  # <start local time>-<model>-<random>.out
```

### 2.6 Retention

At startup of a non-dry run, after arg validation:

```bash
mkdir -p "$OUTPUTS"
find "$OUTPUTS" -maxdepth 1 -type f -name '*.out' -mmin +$(( RETENTION_DAYS * 1440 )) -delete
```

`--dry-run` neither creates the directory nor prunes (keeps `test_dry_run_touches_nothing`
meaningful).

### 2.7 Registry diff

```diff
   "_comment": [
     ...
+    "measured_seconds = ~2k-token single prompt incl. CLI startup (passport). Multi-turn tool/web tasks take far longer: read model-stats.py, not this field."
   ],
+  "capabilities_source": "bd python-ai-skills-2fu comment 2026-09-24: real runs of all ten models, web search checked by a live PyPI query.",
   "models": {
-    "opus-xhigh": { ..., "notes": "..." },
+    "opus-xhigh": { ..., "capabilities": {"web_search": true}, "notes": "..." },
     ... same for fable-medium, sonnet-low, haiku, glm-5.3-high, glm-4.7,
         gpt-sol-xhigh, gpt-terra-high, gpt-luna-low: {"web_search": true}
+    "qwen38": { ..., "capabilities": {"web_search": false}, ... }
   },
   "policy": {
     "penalty_seconds": 3600,
+    "output_retention_days": 14,
     "penalize_on": ["unavailable"],
-    "no_penalty_on": ["context_overflow", "timeout"],
+    "no_penalty_on": ["context_overflow", "timeout", "check_failed"],
     "_policy_comment": [ ...,
+      "check_failed = exit 0 but the answer is empty or misses the caller's --expect regex: the model works, the answer does not fit this task. Never penalised; the output is kept."
     ]
   },
   "state_files": {
     ...
+    "outputs": "~/.claude/model-outputs/ (kept outputs of non-ok attempts; pruned by model-run.sh after policy.output_retention_days)"
   }
-  "updated": "2026-09-22",
+  "updated": "<date of phase-2 commit>",
```

### 2.8 model-stats.py diff

No logic change (D-4). Tests only.

### 2.9 Documentation touched

- `claude-home/CLAUDE.md` "delegating by role" paragraph (`:358-360`): mention `--expect` and that
  non-ok outputs are kept — one sentence.
- `do-feature/SKILL.md:89`: no change needed (invocation still valid).
- `CHANGELOG.md` Unreleased: Fixed (tlo), Added (kept outputs, `--expect`, `check_failed`,
  capabilities).

## 3. Tests mapped to FR/NFR

All in the existing synthetic-registry fixture (`test_model_run.py:27-71`); `registry()` helper
gains an optional `policy` override. No real model/network (NFR-2).

### 3.1 Phase 1 — `test_model_run.py`

1. `test_exit_zero_answer_mentioning_quota_is_ok` — model `cat >/dev/null; echo 'quota 429 rate limit'`
   exit 0 → outcome `ok`, text in `--out`, penalties `{}` → **FR-1, FR-2**.
2. `test_exit_zero_answer_mentioning_context_window_is_ok` — `echo 'maximum context'` exit 0 → `ok`
   → **FR-1** (overflow half).
3. Existing `test_unavailable_model_is_penalised_and_next_one_answers`,
   `test_reported_overflow_is_detected_from_output`, `test_exhausted_role_exits_nonzero` stay green
   → **FR-2** true positives.

### 3.2 Phase 2 — `test_model_run.py`

4. `test_timeout_output_is_kept_and_journalled` — `echo PARTIAL; sleep 5`, timeout 1 → file under
   `tmp_path/model-outputs` exists, contains `PARTIAL`, line has `out_path` = that file and
   `out_bytes` = its size → **FR-3, FR-4** (bd acceptance 3).
5. `test_error_and_unavailable_outputs_are_kept` → **FR-3**.
6. `test_ok_and_preflight_overflow_carry_null_paths` → **FR-4**.
7. `test_expect_miss_is_check_failed_and_next_model_answers` — first model prints `NO URL`, second
   prints `=== URL ===`; `--expect '^=== URL ===$'` → outcomes `[check_failed, ok]`, second answer
   in `--out`, penalties `{}` → **FR-5, FR-6** (bd acceptance 2).
8. `test_empty_exit_zero_output_is_check_failed` — `cat >/dev/null` only → `check_failed`,
   `out_bytes` 0 → **FR-5** (OQ-2).
9. `test_invalid_expect_regex_is_usage_error` — `--expect '('` → exit 2, journal absent → **FR-5**.
10. `test_expect_matching_task_text_is_usage_error` → **FR-5**.
11. `test_old_outputs_are_pruned_young_and_foreign_files_kept` — `.out` aged 15 d removed, `.out`
    aged 13 d and `.txt` aged 15 d kept; `output_retention_days` from the synthetic registry →
    **NFR-6**.
12. `test_dry_run_touches_nothing` extended: outputs directory not created → **NFR-6** safety.
13. `test_outputs_default_next_to_journal` — no `MODEL_OUTPUTS` set; kept file lands in
    `dirname(MODEL_JOURNAL)/model-outputs` → **NFR-3** (isolation, machine-local).
14. `test_journal_line_has_no_output_text` — output contains a marker string; the journal file does
    not → **NFR-5**.
15. `test_help_lists_expect_and_check_failed` — `--help` stdout contains `--expect` and
    `check_failed`, no `set -uo` line → **FR-10**.
16. `test_shipped_registry_is_valid_and_self_consistent` extended: every model has
    `capabilities.web_search` bool; `qwen38` is `false`; `check_failed` in `no_penalty_on`;
    `output_retention_days` is a positive int → **FR-8, FR-6**.

### 3.3 Phase 2 — `test_model_stats.py`

17. `test_check_failed_is_counted_and_rendered` — `outcomes == {"ok":1,"check_failed":1}`, text
    contains `check_failed=1`, `by_pool.ok == 1` → **FR-7**.
18. `test_lines_with_and_without_new_keys_both_parse` — one old 12-key line, one with
    `out_path`/`out_bytes` (one null) → both counted → **FR-7, NFR-4**.

### 3.4 Not a pytest

- **FR-9** — recorded run (D-6), evidence in bd.
- **NFR-1** — reviewed in the diff: no new interpreter or package.
- **NFR-2** — `make test` count = 126 + new tests, all green.

### 3.5 Verified tool behaviour (local runs, 2026-09-24)

1. `mktemp --suffix=.out DIR/…-XXXXXX` creates a mode `600` file (`mktemp --help`: "Files are
   created u+rw … minus umask").
2. `/usr/bin/grep -qE -- '('` → exit 2 (GNU grep 3.11); no match → exit 1.
3. GNU `find -maxdepth 1 -type f -name '*.out' -mmin +20160 -delete` removed a 15-day `.out`,
   kept a 13-day `.out` and a 15-day `.txt` (findutils 4.9.0). `man find`: for `-atime/-mtime`
   "any fractional part is ignored", hence `-mmin`.
4. jq 1.7: `if $p=="" then null else $p end` and `$b|tonumber` yield `null` / `12` as intended.
5. Non-interactive bash resolves `grep`/`find` to GNU binaries; the interactive shell of this
   machine aliases them to `ugrep`/`bfs`, which does not affect the runner (it runs as
   `bash script`, not `bash -i`).
6. Task-57 text: `=== URL ===` → 1 match, `https?://57\.mskobr\.ru` → 1, `^=== URL ===$` → 0.

## 4. Phasing

1. **Phase 1 — tlo (FR-1, FR-2).** Only `classify()` reorder (A1 without the phase-2 checks) +
   tests 1-3 + CHANGELOG Fixed. Committable and closable alone:
   `fix(model-run): gate text patterns on non-zero exit`.
2. **Phase 2 — 2fu.** In order, each step with its tests:
   1. Outputs directory, capture-in-place, journal keys, retention (tests 4-6, 11-14).
   2. `--expect`, `check_failed`, empty check, `--help` (tests 7-10, 15).
   3. Registry diff + registry test (test 16).
   4. model-stats tests (17-18); docs + CHANGELOG.
   5. `make test` green, then the FR-9 run (D-6), then bd comment.

Both phases fit one context window: 5 source/test files, ~1 000 lines total.
