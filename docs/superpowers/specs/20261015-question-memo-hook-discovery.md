---
feature: question-memo-hook
bd_id: python-ai-skills-r1f.3
date: 2026-10-15
status: draft
risk: medium
risk_justification: one new hook module that runs on every user prompt in every project on this machine (global settings.json), but it is advisory only (exit 0, no decision field, about 1,440 characters of context, measured 2026-10-15 after FR-2a), degrades to silence when the section is missing, and changes no contract, API or schema.
evidence: strong
evidence_justification: UserPromptSubmit contract quoted from code.claude.com/docs/en/hooks (fetched 2026-10-15); settings.json.template parsed with python3 json; pattern hook and its test read in full; the four best-* SKILL.md files grepped for confidence and question wording; memo size measured with wc -c on a draft; prompts per session counted over the 60 most recent transcripts of this project directory; Codex chain cap quoted from learn.chatgpt.com/docs/agent-configuration/agents-md; the Codex prompt-input probe itself was blocked by the sandbox (recorded as unverified).
open_questions: []
---

# Discovery: question header and numbers rule delivered by a UserPromptSubmit memo hook (python-ai-skills-r1f.3)

## Intent

The user wants two communication behaviours (bd `python-ai-skills-r1f`, description and acceptance criteria):
1. Every question to the user opens with three lines: **План:** (all tasks in order, 1-3 lines), **Сейчас:** (which task and
   which step or question of how many), **Цель вопроса:** (what the question decides).
2. Every number has a unit; every percentage names its base (N of M) and what it is compared with; a confidence percentage in a
   recommendation is phrased as "my estimate of the probability that the option <meets acceptance criteria X without rework>".
   Scope (bd r1f design note 2026-10-15): chat replies AND every text written for the user - reports, bd issue text, CHANGELOG,
   docs - in any language.

## Constraints - decisions the user already made (bd r1f notes and design, bd r1f.3 description; not reopened here)

1. The rule text lives ONCE, as a new section in `claude-home/CLAUDE.md`.
2. Delivery BEFORE the answer: a new `UserPromptSubmit` hook cuts that section out of `claude-home/CLAUDE.md` at run time (no copy)
   and returns it as `additionalContext`. Pattern: `claude-home/hooks/task-level-inject.sh` + `claude-home/hooks/test_task_level_inject.py`.
   Memo short (about 15 lines). Wired in `claude-home/settings.json.template` -> `UserPromptSubmit`.
3. NO post-hoc Stop check of the header (a Stop check makes the model write a second message).
4. `best-recommend`, `best-questions`, `best-research` SKILL.md point to the section; `best-recommend` must say what its confidence
   percentage is a probability of (`best-rank` already says "probability of acceptance" - see Q2 for the mismatch found).
5. The same hook may later deliver a per-project glossary (bd `python-ai-skills-du5`) - noted, not designed for (YAGNI).
6. Codex runs no hooks; its only delivery is the text in `claude-home/CLAUDE.md` through `~/.codex/AGENTS.md`.

Constraint check against facts: 1, 2, 3, 5, 6 hold. Constraint 4 is literally true (`best-rank/SKILL.md:6,19,29` say
"probability of acceptance" / "вероятность принятия 0-100%") but that meaning - the user accepting the option - differs from the
meaning the new rule fixes - the option meeting acceptance criteria X without rework. Recorded as Q2, not a blocker.

## Hook contract - official docs (code.claude.com/docs/en/hooks, fetched 2026-10-15; quotes verbatim)

Input: "In addition to the common input fields, UserPromptSubmit hooks receive the `prompt` field containing the submitted text."
Example input fields: `session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`, `prompt`; plus
`session_title` "when the session has a custom title". Pasted text arrives expanded, possibly between `<pasted_content id="...">`
lines.

Output: "There are two ways to add context to the conversation on exit code 0: Plain text stdout ... JSON with `additionalContext`".
"Neither channel produces a visible transcript entry. Plain stdout and the `additionalContext` value are each injected as a system
reminder that starts with the hook's name; Claude reads both." Placement: "UserPromptSubmit and UserPromptExpansion: alongside the
submitted prompt". Blocking: "`decision` | `"block"` stops the prompt before it reaches Claude. Omit to allow the prompt to proceed";
exit 2 "Blocks the prompt, so it never reaches Claude." `UserPromptSubmit` "can't replace the prompt; it only injects
`additionalContext` alongside it". JSON shape: `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "..."}}`.

Size: "A hook's `additionalContext`, `systemMessage`, and `initialUserMessage` strings, and its plain stdout, are capped at 10,000
characters"; "Claude Code measures each string on its own, even when several hooks run for the same event"; over the limit the text
goes to a file with "a preview of up to the first 2,000 characters" and "Claude Code doesn't ask Claude to read the file".

Timeout: "Defaults: 600 for `command` ... Claude Code lowers the `command`, `http`, and `mcp_tool` default to 30 on UserPromptSubmit"
(seconds); per handler `"timeout": <seconds>`.

Matcher: "`UserPromptSubmit`, `PostToolBatch`, `Stop`, ... | no matcher support | always fires on every occurrence."

Several hooks: "All matching hooks run in parallel. If you define the same handler in more than one settings file, it runs once."
"When several hooks return `additionalContext` for the same event, Claude receives all of the values." Ordering is not stated.

When it fires: "When a prompt is submitted, before Claude processes it. Also fires on turns Claude Code starts on its own" - a
scheduled task or `/loop` iteration, a background subagent reporting back, a message from another session. Not stated in the docs:
whether it fires for a typed slash command (the separate `UserPromptExpansion` event "Runs when a user-typed command expands into a
prompt"), inside subagents (the docs say settings hooks "also run inside subagents" for tool events only), or in `-p` mode.
`systemMessage`: "Warning message shown to the user"; the UserPromptSubmit section says only "All JSON output fields are available."

## Existing wiring (claude-home/settings.json.template, parsed 2026-10-15)

Events present: SessionStart, PreCompact, PreToolUse, PostToolUse, Stop, UserPromptSubmit. `UserPromptSubmit` has one group
(`matcher: "*"`, ignored for this event per docs) with two handlers, both `timeout: 3` (seconds):
1. Inline counter: `wc -l` of `transcript_path`, prints `{"systemMessage": "⚡ Сообщений в сессии: N"}` - user-visible, no context.
2. `'{{CLAUDE_HOME}}/hooks/git-finish-router.sh'`: `additionalContext` naming `git-finish` on a free-text "git finish"; silent
   on `/git-finish*` (`git-finish-router.sh:29` - evidence that the prompt text of a slash command reaches the hook) and otherwise.
`Stop` has one handler: `explanation-terms.sh` (`timeout: 10` s). A third `UserPromptSubmit` handler emitting `additionalContext`
conflicts with neither: the counter uses `systemMessage`, the router is silent on most prompts, and the docs deliver all values.

Pattern hook `claude-home/hooks/task-level-inject.sh` (33 lines): `FILE="${TASK_LEVELS_FILE:-$(dirname "$0")/../CLAUDE.md}"`
(line 20; installed layout `<claude home>/hooks/<hook>` next to `<claude home>/CLAUDE.md`, both symlinks into the repo);
`awk '/^## /{inside = /^## Dev-project workflow/} inside'` (line 24) cuts from the exact `## ` heading to the next `## `; `jq -n`
builds `hookSpecificOutput` with a framing line "Task levels from <file> (the only copy)"; `exit 0` on every path. Its test
(`test_task_level_inject.py`, 10 tests) runs `bash <hook>` with `env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent",
"TASK_LEVELS_FILE": ...}` (line 35), uses a `tmp_path / "CLAUDE.md"` fixture with PREVIOUS/NEXT markers, and asserts silence on a
missing file, a file without the section, a directory, malformed JSON and empty stdin.

## Structure of claude-home/CLAUDE.md (351 lines, 38,044 bytes)

24 headings; `## ` sections in order: Language (l.7), Output Formatting (13), Project Classification (29), Dev-project workflow (37),
Skill Hierarchy (53), Commit Convention (62), Naming (72), Documentation Retrieval Policy (82), Anti-Hallucination Protocol (90),
Explanation Protocol (105), First-Contact Protocol (146), Pre-commit Policy (166), Git Push Policy (178), Security (195),
Tooling Preferences (215), Model Routing (223), Preferences (233), User Adaptation (262), Memory System Update (274),
Python Development (284), RTK (292, with three `###`).

Duplication check (grep for единиц, процент, базу, N of M, План:, Сейчас:, Цель вопроса, уверенност, вероятност over `claude-home/CLAUDE.md`
and `CLAUDE-APPENDIX.md`): no existing rule covers units, percentage bases or a question header. Output Formatting (l.13-27) covers
lists, paragraphs, emphasis and the no-tables rule; Explanation Protocol (l.105-144) covers terms, images, roles, selection rules,
sources and order. The only percentage-adjacent text is "Trust = 0 %" (l.231, 252). A new section therefore adds no duplicate.
The section must carry its own `## ` heading, because the awk cut keys on `## ` (a `###` under Output Formatting would be cut only
together with the whole Output Formatting section). Natural position: directly after Output Formatting (before l.29), keeping the
communication rules adjacent and the file's simple-to-complex order. Appendix: `CLAUDE-APPENDIX.md` mirrors the section list with
"Почему" rationale (headings l.6-82); a rationale paragraph for the new section belongs there, not in the hook.

## Current skill wording (repo root skill dirs)

- `best-recommend/SKILL.md` (59 lines): l.29 "Проценты — это ранжирование уверенности, не обязаны суммироваться в 100%"; l.33
  "Источник к каждому проценту ... 1-2 предложениями «почему именно столько»"; l.41-43 template `**N% Вариант A** — {почему ...;
  источник}`. It names a source per percentage but never says what the percentage is a probability OF - the gap constraint 4 closes.
- `best-research/SKILL.md` (112 lines): l.60 scale "85–100% — сильный фаворит; 50–84% — рабочий с оговорками; 20–49% — слабый;
  0–19% — почти нет"; l.95-100 rules (no tables, user language); l.33 "файлы CLAUDE.md уже в контексте — не перечитывай их".
  A scale, not a meaning.
- `best-questions/SKILL.md` (81 lines): l.27 and l.38 define the per-question block "Контекст → Что сейчас в коде → Что нужно решить →
  Варианты (pros/cons) → Рекомендация (% по формату best-recommend)"; l.66-74 skill-specific rules. No Plan/Now/Goal header today.
- `best-rank/SKILL.md` (72 lines): l.6 "score every option 0–100% as its probability of acceptance", l.19 and l.29 "вероятность
  принятия 0–100%". Already a meaning, but see Q2.
- `best-approach/SKILL.md` (51 lines): l.5 "recommend with confidence %"; delegates the format to best-recommend. Not named in r1f.3.
- `do-feature`: USER APPROVAL gates at Steps 3, 5, 10 (`do-feature/SKILL.md:24,28`; `reference.md:128` "Approve FR/NFR and scope?")
  and the Research Subagent Pattern (`SKILL.md:146-150`, orchestrator asks "question + options + one-line why") are also questions to
  the user. bd r1f description lists "do-feature gates, needs-input prompts" in scope; r1f.3 names only the three best-* skills (Q3).
- `superpowers:brainstorming` asks questions too but is a plugin skill the repo cannot edit; the hook reaches it anyway.

## Cost of the memo (measured 2026-10-15)

- Draft section with both rules and the scope line: 10 lines, 753 characters -> estimate 215 tokens at 3.5 characters per token
  and 251 tokens at 3.0 characters per token (Russian and English mixed; labelled estimate). With the hook's framing line (about
  150 characters) roughly 900 characters -> about 260-300 tokens per prompt. The 10,000-character cap is 11 times larger.
  For comparison the section task-level-inject cuts is 2,599 bytes, and `claude-home/CLAUDE.md` loaded at session start is 38,044 bytes.
- Frequency: over the 60 most recent transcripts of this project directory (`~/.claude/projects/-home-bgs-...-python-ai-skills/*.jsonl`),
  user prompts per session (string `user` messages not starting with `<`, sidechains excluded): median 1, p90 15, max 25, 261 in total.
  Many single-prompt files are non-interactive runs, so the median understates interactive sessions.
- Per session: the reminder is inserted at the prompt position and stays in the transcript, so every later request re-reads it.
  At p90 (15 prompts) about 15 x 300 = 4,500 tokens are resident by session end - about 1.8 % of the 246k-token request size
  do-feature measured for its own runs (`do-feature/SKILL.md` Pre-dispatch item 0). Added API tokens per prompt: about 300 input
  tokens, mostly cache-read after the first request of a turn.
- Each extra UserPromptSubmit hook also costs one `bash` + `awk` + `jq` process start per prompt; the two existing handlers already
  pay this and the template caps them at 3 s.

## Test harness facts

- `make test` (Makefile l.20-34) lists every hook test file explicitly; a new `test_*.py` under `claude-home/hooks/` is collected by
  `make test` only when added to that list. Pre-commit `hook-regression-tests` (`.pre-commit-config.yaml` l.41-46) runs
  `pytest claude-home/hooks/ -q` on commits touching `claude-home/hooks/`, so the commit gate would collect it regardless.
- `settings-render-tests` (`.pre-commit-config.yaml` l.34-39) runs `scripts/test_install_claude_symlinks.py`;
  `test_every_hook_path_is_one_shell_word` (l.57-64) renders the template under a `CLAUDE_HOME` with a space and asserts each hook
  path is one shell word and `is_file()` - the template entry must use the existing form `'{{CLAUDE_HOME}}/hooks/<name>.sh'` and the
  file must exist in `claude-home/hooks/`.
- `settings-template-json` validates the template as JSON on every template change.
- Baseline recorded in bd r1f.3 notes: `make test` 473 of 473 passed; `ruff check claude-home/hooks/` 1 pre-existing error
  (F401 in `test_big_read_nudge.py:22`).
- Isolation pattern: tests never touch `~/.claude`; `HOME=/nonexistent`, `PATH=/usr/bin:/bin`, file path through an env variable,
  default path tested through a copied hook under `tmp_path/claude-home/hooks/`.

## Functional requirements

- FR-1 A new `## ` section in `claude-home/CLAUDE.md` holds the question header rule (three lines План / Сейчас / Цель вопроса, in
  that order, before every question to the user). Source: bd r1f acceptance criteria and notes (variant B), constraint 1.
- FR-2 The same section holds the numbers rule - unit on every number, base (N of M) and comparison point on every percentage -
  and states the scope (chat and every text written for the user, any language). Source: bd r1f design note 2026-10-15, r1f.3 description.
- FR-2a The same section is the single source of the option-scoring rule for every recommendation (all best-* skills, do-feature
  questions, any other question with options): each option carries two scores written `X% / Y%` - X = probability that the user
  chooses this option, Y = probability that the option meets the task's acceptance criteria without rework (independent per option).
  The X values of all listed options plus one extra line «Свой вариант / ни один — N%» sum to 100 %. Auto-select only when the
  top option's X exceeds the next line's X (the «свой вариант» line counts as a competitor) by at least 20 percentage points AND
  the top option's Y is at least 80 %; every other case goes to the user. Source: user decisions 2026-10-15 (Q2 after
  /best-approach, variant 3 modified; follow-up on the «свой вариант» line); answers bd `python-ai-skills-ao1`.
- FR-3 A new `UserPromptSubmit` hook in `claude-home/hooks/` reads stdin JSON, cuts the section from `claude-home/CLAUDE.md`
  (default `$(dirname "$0")/../CLAUDE.md`, env override) at run time, prints `{"hookSpecificOutput": {"hookEventName":
  "UserPromptSubmit", "additionalContext": "<framing line + section>"}}`, and exits 0; it prints nothing when the file or the section
  is missing or stdin is malformed. Source: constraint 2; pattern `task-level-inject.sh:20-33`; docs contract quoted above.
- FR-4 The hook is wired in `claude-home/settings.json.template` -> `UserPromptSubmit` as a third `command` handler with the
  `'{{CLAUDE_HOME}}/hooks/<name>.sh'` form and `timeout: 3` (seconds) like its neighbours. Source: constraint 2; template facts;
  `test_every_hook_path_is_one_shell_word`.
- FR-5 `best-recommend/SKILL.md`, `best-rank/SKILL.md`, `best-questions/SKILL.md`, `best-research/SKILL.md` drop their own
  definitions of the percentage (`best-recommend:29` "need not sum to 100", `best-rank:6,19,29` "probability of acceptance",
  `best-research:60` scale) and point to the section by heading; their output templates show `X% / Y%`. Source: constraint 4; FR-2a.
- FR-9 The user profile `~/ai-steward/Gena_Beeline_Local/CLAUDE.md` item 3 ("варианты с уверенностью выше 80% выбираются
  автоматически") and the auto-memory `best-questions-auto-select-80.md` are replaced by a pointer to the section. Source: FR-2a (one SSoT).
- FR-6 A pytest file beside the hook, following `test_task_level_inject.py` (section delivered, only that section, silence on
  missing file / missing section / directory / malformed input, default path next to the hooks dir), added to the Makefile `test`
  list. Source: existing contract (Makefile l.20-34, `.pre-commit-config.yaml` l.41-46).
- FR-7 No Stop hook checks the header or the numbers after the answer. Source: constraint 3.
- FR-8 CHANGELOG `Unreleased` entry (Added). Source: project `CLAUDE.md` -> Changelog rule.

## Non-functional requirements

- NFR-1 Memo size: the section stays at about 20 lines or fewer (target under 2,000 characters; grown from ~15 lines by FR-2a),
  5 times below the 10,000-character cap, so the whole text is always inline. Source: constraint 2 ("short ~15 lines") plus FR-2a; docs cap quote.
- NFR-2 Hook runtime well under its 3 s timeout (awk over a 38 KB file plus one jq call). Source: template convention `timeout: 3`;
  docs default 30 s.
- NFR-3 Advisory only: exit 0 on every path, no `decision`, no stderr noise, never blocks or alters a prompt. Source: pattern hooks
  (`task-level-inject.sh:15`, `git-finish-router.sh:17`); docs ("exit 2 blocks the prompt").
- NFR-4 No copy of the rule text anywhere but the section: the hook, the tests and the skills carry only the heading name (the tests
  use a synthetic fixture). Source: constraint 1; `_code-quality/principles.md` SSoT via Preferences rule.
- NFR-5 Section wording is project-neutral and language-neutral: the hook fires in every project on this machine (global settings,
  79 projects per the user profile), `dev` and `life` alike, and on auto-started turns. Source: docs ("always fires on every
  occurrence"); rule scope decision ("any language", every text).
- NFR-6 Codex path intact: `~/.codex/AGENTS.md -> .../claude-home/CLAUDE.md` (ls 2026-10-15) delivers the section at Codex session
  start; the installer keeps that link (`scripts/install-claude-symlinks.sh:70-78`). Source: constraint 6.

## Risks and mitigations

1. Heading renamed or section moved -> the hook is silent by design (pattern `test_file_without_the_section_is_silent`), nobody
   notices. Mitigation: a guard test that reads the real `claude-home/CLAUDE.md` and asserts the heading exists (precedent
   `test_principles_ssot.py:54` reads the real file) - Q4.
2. Duplicate delivery: the section is in context from session start (CLAUDE.md) and again on every prompt - about 300 tokens per
   prompt, about 4,500 tokens resident at p90 (15 prompts). Accepted by the user decision; mitigation is NFR-1 (keep it short).
3. Fires everywhere: `life` projects, auto-started turns (scheduled tasks, `/loop`, background subagent reports, cross-session
   messages). Mitigation: NFR-5 wording; no opt-out is designed (YAGNI) - an env opt-out like `DELEGATION_NUDGE=off`
   (`delegation-pool-nudge.sh:35`) exists as a precedent if needed later.
4. Subagents: not stated in the docs whether UserPromptSubmit fires on a subagent's initial prompt; only 2 debug logs exist on this
   machine and neither contains a `Hooks: UserPromptSubmit` line, so no evidence either way. Subagents never talk to the user: a
   miss costs nothing, a hit costs about 300 tokens per subagent. Hypothesis, LATER to measure.
5. Slash commands: not stated in the docs; `git-finish-router.sh:29` branches on a `/git-finish` prefix, which implies the prompt
   text of a typed slash command reaches UserPromptSubmit hooks - desirable, since `/best-questions` is the main consumer.
   Hypothesis; verify once live (type `/best-questions` and check the debug log for the hook's `Hooks: UserPromptSubmit` line).
6. Interaction with the `explanation-terms` Stop hook: it scans the last assistant message for hyphenated Latin words and single
   backticked Latin words, with non-assistant text (user messages, tool results, tool inputs; `explanation-terms.py:170-200`) as
   evidence. The header words are Cyrillic. A unit written as a single backticked Latin word (`ms`, `KiB`) that appears nowhere in
   the session or repo would draw a one-line correction request. Mitigation: the section's examples of units are Cyrillic or plain
   (not backticked); a system reminder injected by the memo hook is non-assistant text, so its own words count as evidence (hypothesis
   on how the transcript stores hook reminders).
7. Codex chain cap: learn.chatgpt.com (fetched 2026-10-15) - "Codex builds an instruction chain when it starts", global file first,
   and it "stops adding files once the combined size reaches" `project_doc_max_bytes` "(32 KiB by default)"; `~/.codex/config.toml`
   sets no `project_doc_*` key (grep empty). `claude-home/CLAUDE.md` is 38,044 bytes, above 32,768 bytes already today. Whether
   Codex truncates the global file or drops the project file after it is unverified: `codex debug prompt-input` failed inside the
   Bash sandbox with `Error: Read-only file system (os error 30)` (codex-cli 0.160.0). A section placed after Output Formatting
   (about 2 KB into the file) survives a tail truncation; the project `AGENTS.md` may not. Q5.
8. Three parallel handlers on one event: ordering of the delivered contexts is unspecified in the docs; the counter's `systemMessage`
   is a separate channel. No functional conflict found.
9. `best-rank` names a different probability ("acceptance" by the user) than the rule's phrase ("meets acceptance criteria X
   without rework") - two meanings for the same `%` across sibling skills. Q2.
10. Compliance is not measurable automatically: constraint 3 forbids the Stop check, so acceptance rests on observation in a fresh
    session. A read-only transcript scan (precedent `claude-home/scripts/skill-stats.py`) could count assistant messages that end a
    turn with a question and start with «План:» - LATER.

## Scope

- IN: the new `## ` section in `claude-home/CLAUDE.md` (question header, numbers rule, two-score rule FR-2a; plus a short
  "Почему" paragraph in `CLAUDE-APPENDIX.md`, the file's convention); the hook script, its pytest file (incl. the guard test on the
  real file) and the Makefile `test` entry; the `settings.json.template` handler; pointers and `X% / Y%` templates in
  `best-recommend`, `best-rank`, `best-questions`, `best-research`; the profile item and the auto-memory replaced by pointers (FR-9);
  the CHANGELOG entry; a `codex debug prompt-input` run outside the sandbox recording which sections Codex loads (Q5); a live check
  in a fresh session (header present on the first question; `claude --debug` log shows the hook run).
- OUT: any Stop hook or other post-hoc check (constraint 3); the per-project glossary delivery (bd `python-ai-skills-du5`); an
  opt-out switch; editing plugin skills (`superpowers:brainstorming`); the `do-autopilot` 3x-rule (separate rule, unchanged); any push.
- LATER: measure whether UserPromptSubmit fires in subagents and for typed slash commands (risk 4, 5); a compliance scan over
  transcripts (risk 10); a journal of predicted X versus the user's actual choice to measure calibration (Brier score); fixing the
  Codex chain cap if Q5 shows truncation; pointers in `do-feature` gate text and `best-approach` (Q3); the glossary extension (bd du5).

## Best-practice check

No web search beyond the two official documentation pages was needed: the mechanism (run-time section cut, additionalContext,
exit 0) is already the repo's documented pattern (`task-level-inject.sh`, `delegation-pool-nudge.sh`, `git-finish-router.sh`), and
the project's own rule (`python-ai-skills/CLAUDE.md` -> "Live immediately has one exception") names the hook route for rules that
must reach running sessions, with the measured case of 14 of 17 sessions predating a rule added an hour earlier.

## Resolved questions (user and auto-select decisions, 2026-10-15)

- Q1 auto-selected: a new `## ` section right after Output Formatting, before Project Classification.
- Q2 user decision after /best-approach: the two-score rule FR-2a replaces every per-skill meaning of the percentage, `best-rank` included.
- Q2 follow-up, user decision: the «Свой вариант / ни один — N%» line is part of the 100 % and counts as a competitor for the 20-point gap.
- Q2 follow-up, auto-selected: the SSoT of the two-score rule is the new `claude-home/CLAUDE.md` section (delivered by the hook,
  read by Codex); skills, the profile and the auto-memory point to it.
- Q3 user decision: pointers in `best-recommend`, `best-questions`, `best-research` (FR-5 adds `best-rank` because of Q2);
  `do-feature` gate text and `best-approach` LATER.
- Q4 auto-selected: a guard test reads the real `claude-home/CLAUDE.md` and asserts the heading exists.
- Q5 auto-selected: run `codex debug prompt-input` outside the sandbox during Execution and record which sections Codex loads; no code.
