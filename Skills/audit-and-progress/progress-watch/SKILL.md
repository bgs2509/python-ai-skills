---
name: progress-watch
description: >
  Watch a long-running process that nobody is staring at — a background Bash job,
  a subagent, a `claude -p` run, a training run, a CI build — and report its
  progress on a fixed interval (default 10 minutes) in exactly four short lines:
  check time, progress since start, estimated remainder, expected result. Owns its
  own schedule (CronCreate) and stops itself when the process finishes, crashes, or
  the probe itself breaks. Strictly read-only: it never touches, throttles, signals,
  or restarts what it watches.
  TRIGGER when: user asks to check on a running process every N minutes, says
  "каждые 10 минут проверяй прогресс", "следи за фоновым процессом", "check the
  build every 5 min", or a long job was just started in the background and the user
  wants periodic short updates.
  SKIP when: the user wants a single notification the moment something happens (use
  the Monitor tool or a background Bash `until` loop), the job is expected to finish
  within a minute, or the request is to change/stop the process rather than observe it.
argument-hint: "[target: file | pid | task id | command] [--every 10m] [--once] [--stop]"
---

# /progress-watch — periodic four-line progress report

> **Utility skill. Report-first, read-only, self-terminating.**
> It does NOT auto-transition to other skills. It owns exactly one scheduled job
> per watched target and deletes that job itself when watching is over.

## Arguments

1. `target` — what to watch. Free-form; resolved in Phase 0.
2. `--every <N>m|<N>h` — probe interval. Default `10m`. Minimum `1m` (cron granularity).
3. `--once` — probe once, report, do not schedule anything.
4. `--stop` — delete this target's scheduled job and report the last known state.
5. `--iteration` — internal: set only by the scheduled prompt, never typed by the user.

## Phase 0 — Bootstrap (first call, no `--iteration`)

0. **Choose the session.** A check runs inside the session that scheduled it, and every
   request re-reads that session's whole context. Measured 2026-10-13 over 145 checks: two
   requests per check, median 494k tokens of context each — about 1.1M tokens per check,
   almost none of it the watch itself. When the target does not need this session's
   `TaskList` (a file, a PID, a CI run, a GPU), say this in one line and offer the cheap form:
   a fresh session on the cheap tier — `claude --model haiku`, then
   `/progress-watch <target> --every <N>`. Continue here when the user prefers, or when the
   target is a subagent of this session (its liveness is visible only here).

1. **Resolve the target** into a probe. Recognised kinds:
   - *log file / output file* — a path that grows. Probe: `stat -c '%s %Y' <path>`.
   - *background Bash task* — the output-file path returned when the task was started. Same probe as a log file.
   - *process* — a PID or a command pattern. Probe: `ps -o etime=,stat= -p <pid>` or `pgrep -cf '<pattern>'`.
   - *subagent / local agent task* — liveness only, via `TaskList`. **Never** read its output file (see Hard rules).
   - *remote build / CI run* — one bounded CLI call, e.g. `gh run list --limit 1 --json status,conclusion`.
   - *GPU training* — `nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader`.
   If the target cannot be resolved into one whitelisted probe, **ask one question and stop**. Do not guess a probe.

2. **Establish the baseline**, four values:
   - `since` — ISO-8601 local timestamp of this moment,
   - `baseline` — the metric's current value,
   - `total` — the total amount of work if, and only if, it is *measured* (step count in the plan, file count in the queue, `--json` field). Otherwise the literal string `unknown`.
   - `expect` — what the finished run is supposed to leave behind (artifact path, exit code, DB row count).

3. **Report immediately** in the four-line format below (first report: deltas are zero).

4. **Schedule itself** — unless `--once`. Call `CronCreate` directly (this skill owns its
   schedule; it does not delegate to another skill) with:
   - `cron`: an offset minute list, not `*/N` — e.g. for 10 minutes use
     `3,13,23,33,43,53 * * * *`; for 5 minutes `2,7,12,17,22,27,32,37,42,47,52,57 * * * *`.
     Offsetting away from `:00`/`:30` is the scheduler's own documented preference.
   - `recurring: true`
   - `prompt`: a plain re-entry text — **not** a `/progress-watch` call, which would paste
     this whole file into the session on every check. It carries the state and the rules a
     check needs:
     ```
     progress-watch check pw-<slug> (do not invoke the progress-watch skill).
     State: target=<...> since=<ISO> baseline=<value> total=<value|unknown> expect=<...>.
     Run ONE Bash call: timeout 10 ionice -c3 nice -n19 <probe>; timeout 10 ionice -c3 nice -n19 <liveness>
     Previous value = the one in your last pw-<slug> report. Classify: running | застой (unchanged 3 checks, keep watching) | завершено (process gone, expect present) | крах (gone without expect, or tail shows Traceback/Error/FAILED/Killed/OOM) | probe broken (non-zero or 124).
     Answer in exactly four Russian lines: "<HH:MM> (+<elapsed> от старта)" / "Прогресс: ..." / "Осталось: ..." (with total=unknown write "Осталось: не вычислимо — общий объём неизвестен") / "Ожидаем: <expect>".
     On завершено, крах, or probe broken twice in a row: CronList, CronDelete the job whose prompt contains pw-<slug>, then the final summary.
     Never stop or signal the watched work, never read a subagent's output file, never write in its directory.
     ```
   `<slug>` is a short unique name for this target. The marker is how the skill finds
   its own job later; state lives in this prompt text, so it survives context compaction.
   Jobs created before 2026-10-13 still re-enter as `/progress-watch --iteration ...`; that
   form keeps working (Phase 1 below).

5. Tell the user the interval and how to stop it (`/progress-watch --stop <slug>`). One line.

## Phase 1 — Probe (every check)

Run **at most two** wrapped commands — one probe, one liveness check — in **one** Bash call,
so a check costs one tool round-trip. Wrap every one:

```bash
timeout 10 ionice -c3 nice -n19 <command>
```

`timeout` bounds a hung probe (it exits 124), `ionice -c3` puts it on idle disk priority,
`nice -n19` on lowest CPU priority — so the probe cannot compete with the process it watches.

Then classify the state:

1. **running** — metric moved since the previous check.
2. **stalled** — metric unchanged for 3 consecutive checks. Report it as a fact
   ("без изменений 30 мин"), do NOT stop: a long phase looks identical to a hang.
3. **finished** — the process is gone AND the `expect` artifact exists (or the exit code is known).
4. **crashed** — the process is gone without the artifact, or the log tail matches
   `Traceback|Error|FAILED|assert|Killed|OOM|Segmentation`. Check the tail with
   `tail -n 3`, never by reading the file.
5. **probe-broken** — the probe command itself failed (non-zero, or 124 from `timeout`).

**finished**, **crashed** → emit the final summary, then stop (see below).
**probe-broken** twice in a row → stop, and say plainly that watching ended because the
probe broke, not because the process did. A broken probe must never be reported as progress.

## Report format (Russian, exactly four lines)

```
14:03 (+40 мин от старта)
Прогресс: 1 847 строк (+312 за 10 мин, +1 847 с начала)
Осталось: ~25 мин (12/19 шагов, темп 31 стр/мин)
Ожидаем: отчёт в docs/reports/, код возврата 0
```

Rules for the four lines:
1. No preamble, no closing sentence, no markdown table. Four lines, nothing else.
2. Line 3 is the honest one. With `total=unknown` write exactly:
   `Осталось: не вычислимо — общий объём неизвестен`, plus the observed rate if there is one.
   Never convert an unmeasured guess into minutes or per cent.
3. State that is not `running` gets one extra word on line 1: `застой`, `завершено`, `крах`.
4. The final summary (on finish or crash) replaces line 3 with the total duration and
   line 4 with where the result actually is.

## Stopping

1. `CronList` — the listing shows each job's id and its prompt text.
2. Find the job whose prompt contains this target's `--marker=pw-<slug>`.
3. `CronDelete` with that id.
4. If no job matches, say so and ask the user to stop it manually — do not delete a job
   you did not identify.

## Probe whitelist

Only these, always wrapped as above:

1. `stat -c '%s %Y' <path>` — size and mtime without reading the file.
2. `tail -n 3 <path>` — last lines only.
3. `grep -c '<pattern>' <path>` — only when the file is under ~50 MB by `stat`; otherwise `tail -n 200 <path> | grep -c`.
4. `ps -o etime=,stat= -p <pid>` / `pgrep -cf '<pattern>'` — liveness and elapsed time.
5. `git --no-optional-locks status --porcelain` / `git -C <dir> --no-optional-locks log --oneline -1` — the flag keeps the probe off the git index lock.
6. `nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader`.
7. One bounded remote status call (`gh run list --limit 1 --json ...`), never more often than every 30 seconds — the default 10-minute interval satisfies this with room to spare.
8. `TaskList` / `CronList` — tool-level, no shell.

Anything outside this list: ask first, then add it here in the same change.

## Hard rules (never)

1. **Never stop or signal the watched work** — no `TaskStop`, no `kill`, no `pkill`, no restart.
2. **Never read a subagent's output file.** It is a symlink to the full JSONL conversation transcript and will overflow the context. Liveness for agent tasks comes from `TaskList`.
3. **Never write anything in the process's working directory** — no redirects (`>`, `>>`, `tee`), no `git add/commit/checkout`, no touch files, no scratch output.
4. **Never `wc -l` a large or growing log.** Size comes from `stat`.
5. **Never query the watched process's database** (SQLite, Dolt, Postgres) — a read can still take a lock. Measure its files instead. *(If a DB read is genuinely the only signal, ask first.)*
6. **Never open the process's stdin** and never run an interactive command.
7. **Never exceed two commands and ~15 lines of output per check.** This is a background observer; if the observer is expensive it is broken. When the watched work is itself a Claude run on the same account, every probe spends from the same token pool — brevity is speed for the watched process too.
8. **Never assert a remainder without a measured total** (Hard rule form of line 3 above).

## Notes

- The schedule is session-only, lives in memory, and dies with the session. Recurring jobs also auto-expire (7 days per the scheduler's own description). Say this once at bootstrap, not on every check.
- Scheduled jobs fire only while the session is idle, so a check can never interrupt work in progress; it can only arrive late. A late check is reported with its real timestamp, never back-dated.
- Each check's four lines cost context. Over a long watch that adds up — which is the second reason the format is fixed at four lines.
