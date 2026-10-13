# Revision Plan — Skills, Pipelines and Always-Loaded Instructions

- **Date:** 2026-10-13
- **Status:** DRAFT, second pass 2026-10-13 — decisions recorded per item; not yet executed. No skill, instruction or setting has been changed.
- **bd issue:** none yet (an epic is created after approval).
- **Goal:** cut token spend and wall-clock time of skills, pipelines and always-loaded instructions
  without losing quality; make subagents run on economical models.
- **Evidence tags used below:**
  - `[measured]` — computed in this session by a script over `~/.claude/projects/**/*.jsonl`.
  - `[verified]` — checked in this session against the primary source (official page, arXiv
    abstract, or the Claude Code 2.1.296 binary).
  - `[GLM-report]` — from a `model-run.sh --role researcher` report (`glm-5.3-high`), cited sources
    listed there, **not re-checked by the parent session**.
  - `[estimate]` — arithmetic on the numbers above with the stated assumptions.
  - `[hypothesis]` — not measured, needs an experiment.

---

## 1. Evidence base (what this session established)

### 1.1 Data available

| Fact | Value | Tag |
|------|-------|-----|
| Transcripts on disk | 1,889 main + 344 subagent files, 2.1 GB | measured |
| Period covered | 2026-09-09 … 2026-10-13 (35 days); six months is NOT available | measured |
| Why | `cleanupPeriodDays: 30` in `~/.claude/settings.json` | verified |
| Main-session API calls | 33,232 | measured |

### 1.2 Spend totals (35 days)

| Metric | Value | Tag |
|--------|-------|-----|
| All tokens | 13.94 B | measured |
| of which cache reads | 13.48 B (97 %) | measured |
| without cache reads | 0.46 B; output 43 M | measured |
| API-equivalent cost (Anthropic models only, GLM/qwen excluded) | ≈ $6,505 | measured × verified prices |
| Main sessions on Opus 5 / Opus 5.5 | ≈ $4,705 (72 %) | measured |
| — Opus 5.5 main: cache **writes** $1,013 vs cache reads $906 | writes cost more than reads | measured |
| Subagents, all models | ≈ $1,194 (18 %) | measured |
| — Fable 5.1 subagents | $351 for only 1,309 calls ($275 of it cache writes) | measured |
| — Sonnet 5 / 5.5 subagents | $659, 13,480 calls | measured |
| — Haiku 4.5 subagents | $1, 42 calls | measured |

> Cost is "API-equivalent": the account may be on a subscription, so the real price is quota share.
> Ratios between items stay valid either way.

### 1.3 Skills by spend (attribution windows)

Window rule: a skill owns API calls from its invocation until the next human-typed message (**low**)
or until the next skill / end of session (**high**). Subagent transcripts go to the skill active in
the parent when the subagent started. Built-in commands (`/clear`, `/model`, …) excluded.

| Skill | Calls | Sessions | Tokens low–high | Non-cache-read low–high | Tag |
|-------|-------|----------|-----------------|-------------------------|-----|
| best-questions | 65 | 45 | 427–2,378 M | 7.6–52 M | measured |
| do-feature | 34 | 29 | 732–1,809 M (482 M subagents) | 20–44 M | measured |
| progress-watch | 145 cron firings | 10 | 421–823 M | 6–13 M | measured |
| git-finish | 73 | 58 | 455–761 M | 9–20 M | measured |
| best-approach | 31 | 24 | 73–678 M | 1.1–15.7 M | measured |
| superpowers:writing-plans | 7 (+~20 inside subagents) | 7 | 90–119 M | 2.5–2.8 M | measured |

Never invoked in the period: `do-multiagent`, `do-autopilot`, `full-audit`, `audit-loop`, almost all
`_*` skills. `[measured]`

Limitations of the attribution: exclusive (a nested skill takes over the window); skill calls made
inside subagents are not counted as calls (their tokens go to the parent skill). `[measured]`

### 1.4 Skill groups (reference graph of `SKILL.md` files)

1. **Independent** — no references to other skills: `progress-watch`, `grace-refresh`; effectively
   `git-commit`, `git-branch` (they mention others only in SKIP routing).
2. **Independent with conditional hand-offs** — `git-finish` (may call `grace-refresh`,
   `beads-sync`, `git-commit`, …).
3. **Nested family** — `best-questions` / `best-approach` / `best-rank` → `best-research` →
   `best-recommend`.
4. **Orchestrators (pipelines)** — `do-feature` (references 12 skills), `do-autopilot`,
   `do-multiagent` (both built on `do-feature`).
5. **Skills that spawn subagents** (text search in `*/SKILL.md`): `do-feature`, `do-autopilot`,
   `do-multiagent`, `audit-loop`, `grace-setup-subagents`, `progress-watch`. `grace-*` skills in other
   directories may be missing from this search.

### 1.5 Always-loaded context

| Item | Size | Tag |
|------|------|-----|
| `claude-home/CLAUDE.md` (global, every project) | 40,881 chars, 453 lines | measured |
| `python-ai-skills/CLAUDE.md` | 13,908 chars, 222 lines | measured |
| `ai-steward/CLAUDE.md` (bot spec, loads in every dev session under `ai-steward/`) | 9,616 chars, 266 lines | measured |
| `RTK.md` + `rules/python-dev.md` + user profile | 6,646 chars | measured |
| Descriptions of the 47 repo skills (skill listing) | 21,761 chars | measured |
| Largest global sections | Explanation Protocol 6.4 k, Model Routing 6.2 k, Security 2.9 k chars | measured |
| Official target | "target under 200 lines per CLAUDE.md file" | verified (code.claude.com/docs/en/memory) |
| Imports | "don't reduce its context cost, because imported files also load at launch" | verified |
| Path-scoped rules | `.claude/rules/*.md` with `paths:` frontmatter load only for matching files | verified |
| Skill listing | every listed skill's description is in context every turn; `/skill-doctor` audits it | GLM-report; keys `skill-doctor`, `skillOverrides`, `name-only`, `disable-model-invocation` exist in binary — verified |

Direct cost of the global `CLAUDE.md` alone `[estimate]`: ≈ 10–12 k tokens × ≈ 50 k API calls
(main + subagents, if subagents load it) ≈ 0.5 B cache-read tokens ≈ 3.5 % of all tokens; in money
≈ $100–150 of reads plus cache writes on every new session/compaction (≈ 1,900 sessions × 10–12 k ×
$5–8/MTok ≈ $100–180). Total ≈ 4–5 % of spend for one file. The listing + other files roughly double that.

### 1.6 Models

| Fact | Value | Tag |
|------|-------|-----|
| Prices $/MTok in / out / cache read | Fable 5.1 10 / 50 / 0.25; Opus 5.5 4 / 20 / 0.20; Opus 5 5 / 25 / 0.50; Sonnet 5.5 2 / 10 / 0.10; Sonnet 5 2 / 10 / 0.20; Haiku 5.5 (≤100 k prompt) 0.10 / 0.50 / 0.01, (>100 k) 0.50 / 2.50 / 0.05; Haiku 4.5 1 / 5 / 0.10 | verified (pricing page) |
| Haiku 5.5 | released 2026-10-07, `claude-haiku-5-5`, 1 M context, positioned for subagents; tokenizer counts ~30 % more tokens than Haiku 4.5; clearly below Sonnet 5.5 on Terminal-Bench (39.2 % vs 70.6 %) | GLM-report (model id in binary — verified) |
| `Agent` tool `model` param, 460 launches | sonnet 230, omitted (inherits parent, mostly Opus) 100, fable 74, opus 49, haiku 7 | measured |
| `subagent_type` | general-purpose 348, do-feature-clean 34, fork 32, Explore 14 | measured |
| Subagent model controls | `CLAUDE_CODE_SUBAGENT_MODEL`, `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` | verified (binary); resolution order GLM-report |
| Current setting | `CLAUDE_CODE_SUBAGENT_MODEL` not set; `"model": "opus"` | verified |
| Advisor | `advisorModel` field present: opus-5-5 in 34,791 records, fable-5-1 in 4,961 | measured |
| Advisor cost visibility | NOT visible in `usage.iterations` (only `message`, `fallback_message`) | measured |
| Advisor mechanics | reads the full conversation each consultation, uncached; `/advisor off`, `CLAUDE_CODE_DISABLE_ADVISOR_TOOL` | GLM-report (env var exists in binary — verified) |
| Subagent cache TTL | `subagentPromptCacheTtl` / `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL`, values `5m`/`1h`; subscription default 1 h main / 5 m subagents | key verified; defaults GLM-report |

### 1.7 External findings

| Source | Finding | Tag |
|--------|---------|-----|
| arXiv 2602.11988 "Evaluating AGENTS.md" | context files do not generally raise success rate; +20 % inference cost; agents follow instructions well; repo overviews do not help; useful for non-standard practices; evaluate any tuning rigorously | verified (abstract). Developer-written files +2.4 % (not significant), LLM-generated −0.5…−2 % — GLM-report. ETH affiliation not on the page |
| Matt Pocock `writing-for-agents` | every always-loaded word costs every turn; decide a rule's value by running without it; prohibitions pull the forbidden behaviour into context — phrase the positive; avoid "sediment" | GLM-report; `CODING_STANDARDS.md` split NOT found in the repo |
| Karpathy / ASD-STE100 | controlled English for human-readable explanations; skill `danyuchn/asd-ste100-skill` rewrites agent-consumed text | GLM-report |
| claude-code-templates | `hooks/subagents-explore-only` (SubagentStart `additionalContext`), `security/subagent-read-only-guard` (PreToolUse, detects subagents by `agent_id`), preset `model/sonnet-opus-advisor-haiku-subagents` | GLM-report (`SubagentStart`, `agent_id` exist in binary — verified) |
| You Should Know (`cc-plugin-you-should-know@builtin`) | side agent watching the session; cost not published | GLM-report (id in binary — verified) |
| prompt-cache-control mod | cache meter for the main loop only | GLM-report |
| Managed Agents dynamic workflows (`multiagent_20261001`) | API product, multi-agent uses 3–10× tokens; "70 planted bugs" number not found in any source | GLM-report |

### 1.8 Second pass (2026-10-13): tests and decisions

| Fact | Value | Tag |
|------|-------|-----|
| Billing basis | Anthropic Max 5x subscription (registry `quota`); $ figures are API-equivalent quota share | verified (registry) |
| A/B Haiku 5.5 vs Sonnet 5.5 | 4 tasks via `claude -p` in this repo, read-only tools: (1) explain `model-run.sh` penalty logic with file:line, (2) hooks with/without tests, (3) find 2 planted bugs, (4) per-call arithmetic with a trap answer (`_report`). Both models 4/4 correct; Sonnet went deeper on task 1 (noticed no model sets `penalize_on_timeout`) | measured, graded by the parent against known answers |
| A/B cost and time | Haiku 5.5 $0.012–0.019 per task, 9–17 s; Sonnet 5.5 $0.27–0.33, 11–19 s (15–23× cost ratio) | measured (`total_cost_usd`, `duration_ms`) |
| Fresh-session baseline | 66–67 k input tokens for a one-turn `claude -p` task in this repo | measured |
| Nested `claude -p` | needs sandbox bypass (network to `api.anthropic.com` and the credentials file) | measured |
| Subagent idle gaps | 16,961 gaps: 16,844 < 5 min, 109 of 5–60 min, 8 ≥ 60 min; long gaps follow `SubagentHandback`, `SendMessage`, long Bash (tests, wait loops, `model-run.sh`) | measured |
| Registry | `reviewer` role = `gpt-sol-xhigh` (`gpt-5.6-sol`, `xhigh`) → `glm-5.3-high` → `opus-xhigh`; reviewer runs took 739 s and 793 s; `haiku` entry still has a 200 k window (Haiku 4.5); `fable-medium` quota marked "scarce" | verified (registry, journal) |
| `ai-steward/` inventory | root holds only `CLAUDE.md`, an empty `.worktrees/` and user folders; 67 `planner.json` files in the tree, all with empty `items`, 16 tracked in git | measured |
| Russian analog of ASD-STE100 | none official. Rosstandart has been developing a national GOST R on plain language since 2022 (no number yet); ISO 24495-1 (plain-language principles, published 2023 per GLM — iso.org returned 403 to the parent); editorial systems without machine rules: Ilyakhov's "Инфостиль"/Главред, Nora Gal | GOST R status verified (ru.wikipedia "Простой_язык"); rest GLM-report |

---

## 2. Plan

Order: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7. Every change to a skill, instruction or setting goes through
`do-feature` with its approval gates; every change is re-measured after 7 days with the step-0 tool.

Impact scale: **Quality** (↑ better / ↓ worse / = neutral), **Tokens & cost**, **Time** (wall clock
of a task). Each estimate names its assumption.

### Step 0 — Measurement toolkit

**What:** move the session's attribution script into the repo (next to
`claude-home/scripts/model-stats.py`) and extend it:

1. per-invocation median / p90 tokens and API-equivalent $ per skill;
2. model mix of subagents per skill;
3. cost of always-loaded context (instructions + skill listing) per call;
4. idle gaps between consecutive subagent requests (input for step 3e);
5. a way to see advisor spend (see open questions);
6. baseline `/doctor prompt-audit` and `/skill-doctor` reports.

Plus: raise `cleanupPeriodDays` (e.g. 120–200) so future revisions have more than 30 days of data.

- **Pros:** every later step becomes measurable; zero Anthropic tokens to run (pure Python, 14 s on 2.1 GB).
- **Cons / risks:** attribution windows are approximate (exclusive, human-message boundary); longer
  retention grows `~/.claude/projects` (2.1 GB per ~35 days now → several GB).
- **Impact:** Quality = (no behaviour change). Tokens: −0 directly, enables everything else.
  Time: none.
- **To clarify in the project:**
  1. Is `cleanupPeriodDays` in `settings.json.template` or runtime-owned? (template render rules.)
  2. Disk budget on the laptop for transcripts.
  3. Whether subagents actually load `CLAUDE.md` (check a subagent transcript's first request size).
  4. Where advisor tokens are recorded, if anywhere (other JSONL fields, `/usage`, `/cost`).
  5. Which built-in commands to exclude (list from `/help`).
- **To research online:**
  1. Claude Code docs: transcript JSONL schema, advisor usage reporting.
  2. Whether `/doctor prompt-audit` output is machine-readable.
- **Acceptance:** script reproduces this session's numbers (±1 %), tests pass, `make test` green.
- **Done (2026-10-13):** `claude-home/scripts/skill-stats.py` (17 tests) and `cleanupPeriodDays: 180` in the template, bd `python-ai-skills-8of.1`. First-request context measured on 1,879 main sessions: median 70.6 k, p90 83.5 k tokens.
- **Decision (2026-10-13):** Do it first. Raise `cleanupPeriodDays` to 180 (six months, the period originally asked for). Add one metric: baseline context of a fresh session (66–67 k tokens measured, §1.8).
- **Still open:** disk budget (~2.1 GB per 35 days → ~11 GB for 180 days). Resolved: `cleanupPeriodDays` is template-owned; `claude-home/housekeeping/housekeeping.py` now reads it instead of its own 30-day constant.

### Step 1 — Pilot on an independent skill: `progress-watch`

**What:** run the full method on one skill: baseline → read 3 firings (max / median / min cost,
reading delegated to GLM via `model-run.sh --role executor`) → hypotheses with expected numbers →
change via `do-feature` → re-measure after 7 days → write the method as a checklist.

Current baseline `[measured]`: 145 firings, ≈ 2.9 M tokens per firing (≈ 42 k non-cache-read);
cost is dominated by re-reading the host session's context on every cron firing.

Hypotheses `[hypothesis]`:
1. run the check in a separate small session (or `claude -p` on Haiku 5.5) instead of the host session;
2. shrink `SKILL.md` (9.2 k chars) and its 1,056-char description;
3. fewer tool calls per firing.

- **Pros:** independent, read-only, many repetitions (fast statistics), a mistake breaks nothing.
- **Cons / risks:** the method learned on a read-only skill may not transfer to pipelines; a
  separate session loses the host session's context (the report may become less informed).
- **Impact:** Quality = or slightly ↓ (less context for the report). Tokens: hypothesis 1 could cut
  per-firing cost by an order of magnitude `[estimate: 2.9 M host-context reads → tens of k]`.
  Time: the host session is no longer blocked by monitoring turns.
- **To clarify in the project:**
  1. Where exactly the cost goes inside one firing (context size at firing, number of calls).
  2. Why `progress-watch` is in the "spawns subagents" list and which model those subagents use.
  3. How CronCreate firings are executed (inside the host session or separately).
- **To research online:**
  1. Claude Code `CronCreate` / `/loop` execution model and cost guidance.
  2. Whether a scheduled prompt can run on a different model than the session.
- **Acceptance:** median tokens per firing down by the target agreed in the hypothesis step, with
- **Decision (2026-10-13):** Run the pilot right after step 0. First hypothesis to test: move each firing into a separate `claude -p` run on Haiku 5.5 (Haiku 5.5 handled read-only tasks correctly in §1.8).
- **Still open:** Does the progress report need the host session's context, or only the watched process's files/logs?
  report quality checked on 5 firings.

### Step 2 — Always-loaded instructions (`CLAUDE.md` ×3, `RTK.md`, rules, skill listing)

Applies to: global `claude-home/CLAUDE.md`, `python-ai-skills/CLAUDE.md`, `ai-steward/CLAUDE.md`,
`RTK.md`, `rules/python-dev.md`, descriptions of all skills. 941 lines of `CLAUDE.md` vs an official
target of < 200 lines per file.

General method (from arXiv 2602.11988 and `writing-for-agents`): a rule stays only if removing it
changes behaviour on a fixed task set; instructions are followed, so every rule costs extra steps.

#### 2a. Remove rules that do not change behaviour

- **What:** for each section, A/B run a fixed task set with and without it; drop no-op rules.
- **Pros:** direct context reduction on every call; per arXiv, fewer induced steps (the +20 % cost
  comes from agents obeying instructions).
- **Cons / risks:** A/B runs cost tokens; small samples are noisy; a rule may matter only in rare
  situations a task set does not cover (e.g. security rules — keep those regardless).
- **Impact:** Quality = if done carefully, ↓ risk on rare cases. Tokens: up to −4–5 % from the global
  file alone `[estimate, §1.5]` plus fewer induced steps (unknown, arXiv suggests up to 20 %).
  Time: fewer steps per task.
- **To clarify in the project:** which rules are already enforced by hooks
  (`anti-hallucination.sh`, `explanation-terms.sh`, `delegation-pool-nudge.sh`, …) and which are
  pure text; which incidents each rule was added for (`CLAUDE-APPENDIX.md` rationale, CHANGELOG).
- **To research online:** how others build an instruction A/B harness for Claude Code
  (`claude -p` with/without `claudeMdExcludes`); the full arXiv paper sections on which instruction
  categories cost most (GLM-report: "Testing" category).
- **Acceptance:** task set passes with equal quality; lines and per-call tokens down.
- **Decision (2026-10-13):** Do it with the `claude -p` A/B harness built in §1.8, extended from 4 to ~10 tasks; 2e is folded into this step.
- **Still open:** Task-set composition and the quality judge (parent session vs the `reviewer` role).

#### 2b. Move partial-scope rules out of the always-loaded file

- **What:** rules needed only in some work go to `.claude/rules/*.md` with `paths:`, into the skill
  that needs them, or behind a pointer to `CLAUDE-APPENDIX.md`. Candidates: Plan Sizing, GRACE core
  principles, Semantic Markup, Documentation SSoT table, most of Model Routing (the registry is its
  SSoT already), Multi-machine consistency.
- **Pros:** official mechanism; rules still apply where needed; global file shrinks the most.
- **Cons / risks:** `paths:` triggers on file access, not on topic — a rule about planning has no
  file path; pointer wording decides whether the agent ever reads the target (Pocock); risk of
  rules silently not loading.
- **Impact:** Quality = if pointers are right, ↓ if they are not. Tokens: the largest single cut of
  always-loaded text `[estimate: global file could fall from 41 k to ~15–20 k chars]`. Time: =.
- **To clarify in the project:** which sections are topic-scoped vs file-scoped; whether
  `~/.claude/rules/` (user level) is supported for global rules; Codex compatibility — the same file
  is `~/.codex/AGENTS.md`, does Codex understand `paths:` rules?
- **To research online:** Claude Code docs on user-level rules directory; Codex `AGENTS.md`
  scoping; Pocock's "pointer wording" guidance in full.
- **Acceptance:** each moved rule demonstrably loads in a task that needs it (test transcript).
- **Decision (2026-10-13):** Do it. Candidates: Plan Sizing, GRACE principles, Semantic Markup, Documentation SSoT table, Model Routing details (registry is SSoT), Multi-machine consistency.
- **Still open:** Does Codex honour `.claude/rules/` with `paths:` (same file is `~/.codex/AGENTS.md`)? Is a user-level rules directory supported?

#### 2c. Hard rules → hooks

- **What:** rules of the form "never do X" become `PreToolUse` hooks, and the text shrinks to one line.
- **Pros:** enforcement independent of the model's attention (official guidance); text shrinks.
- **Cons / risks:** hooks add latency and maintenance; false positives block legitimate work.
- **Impact:** Quality ↑ (rules hold more reliably). Tokens: small −. Time: + a few ms per tool call.
- **To clarify in the project:** inventory of existing hooks vs the rules they cover; which
  remaining rules are mechanically checkable (push, `--no-verify`, secret files…).
- **To research online:** hook latency guidance; examples of rule→hook conversions.
- **Acceptance:** regression suite of hooks passes; rule text replaced by a pointer.
- **Decision (2026-10-13):** Do it, starting with an inventory: rule → existing hook → text that can shrink to one line.
- **Still open:** None beyond the inventory.

#### 2d. `ai-steward/CLAUDE.md` bot spec

- **What:** move the `planner.json` spec, user table and project templates out of the file that
  loads into every dev session under `ai-steward/` (into the bot's own docs or a life-project rule).
- **Pros:** −9.6 k chars from every dev session in this tree; zero quality risk for dev work.
- **Cons / risks:** the Telegram bot's sessions need that spec — it must still load there; the file
  belongs to the bot's deployment (`/opt/ai-steward/`), changes must not break it.
- **Impact:** Quality = (dev) / must stay = (bot). Tokens: ≈ −2–3 k tokens per call in dev
  sessions. Time: =.
- **To clarify in the project:** how the bot launches Claude Code (cwd per user/project?), whether
  bot sessions would still see a moved spec; who else edits this file.
- **To research online:** nothing.
- **Acceptance:** a bot session still validates `planner.json`; dev sessions no longer load the spec.
- **Decision (2026-10-13, executed):** user confirmed. Deleted `ai-steward/CLAUDE.md` (not in any git repo; the README of `claude_bot` points to a template copy that does not exist), the empty `ai-steward/.worktrees/`, 51 untracked `planner.json` files, and 15 tracked ones with one commit per repo (`chore(planner): remove unused ai-steward bot planner file`). User profiles `Dari/`, `Marat/`, `Tania/`, `Gena_MTS/`, `Gena_Beeline_Local/` `CLAUDE.md` are kept (user decision).
- **Still open:** `Sinayara-Isuzu/planner.json` remains: the project's `no-commit-to-branch` pre-commit hook blocks commits to `master`; the file was restored, to be removed through that project's branch workflow.

#### 2e. Positive phrasing instead of prohibitions

- **What:** rewrite "do NOT X" rules as "do Y" where possible (Pocock: prohibitions make the
  forbidden behaviour more available).
- **Pros:** may raise adherence; often shorter.
- **Cons / risks:** claim is from one author, not measured here; some rules are inherently
  prohibitions (security).
- **Impact:** Quality ↑? `[hypothesis]`. Tokens: small −. Time: =.
- **To clarify in the project:** count of "NOT/НЕ/НИКОГДА" rules and which have incidents behind them.
- **To research online:** evidence for the negation effect in LLM instruction following
  (studies beyond Pocock).
- **Acceptance:** A/B on rules with known violation history.
- **Decision (2026-10-13):** Folded into 2a: test positive vs negative phrasing only on rules with a known violation history.
- **Still open:** None.

#### 2f. Skill listing

- **What:** shorten descriptions (21.8 k chars for 47 repo skills; the longest: `git-finish` 1,168,
  `progress-watch` 1,056, `do-multiagent` 1,020, `do-autopilot` 1,003); set `name-only` visibility
  (`skillOverrides`) or `disable-model-invocation` for skills never auto-invoked (all unused `_*`,
  `do-autopilot`, `do-multiagent`, `full-audit`, `audit-loop` — they are slash-invoked).
- **Pros:** listing is paid every turn in every project; unused skills cost now and give nothing.
- **Cons / risks:** shorter descriptions → worse auto-routing; `name-only` skills are never picked
  automatically; TRIGGER/SKIP lines are the repo's SSoT for routing.
- **Impact:** Quality = / slight ↓ routing. Tokens: −a share of ~5 k tokens per call `[estimate:
  21.8 k chars ≈ 5 k tokens]`. Time: =.
- **To clarify in the project:** total listing size including plugin and built-in skills (measure a
  real first request); which skills are invoked by the model vs only by slash.
- **To research online:** `/skill-doctor` and `skillOverrides` docs (exact syntax, Codex effect).
- **Acceptance:** routing tests (the repo's hook regression suite / TRIGGER checks) pass.
- **Done (2026-10-13):** `skillOverrides` `name-only` for the 29 repo skills never invoked in 35 days (`_init` already hidden), bd `python-ai-skills-8of.3`. Measured with `/context`: Skills 10k → 9.6k tokens. The earlier estimate (21.8k chars ≈ 5k tokens) was wrong — Claude Code lists shortened descriptions, 20-380 tokens per repo skill, and about half the listing is built-in and plugin skills. Real saving ≈ 0.4k tokens per request (~1 % of the fresh-session baseline).
- **Decision (2026-10-13):** Do it: `name-only` (via `skillOverrides`) for slash-only skills — `do-autopilot`, `do-multiagent`, `full-audit`, `audit-loop`, unused `_*`; shorten descriptions over ~600 chars.
- **Still open:** Measure the real listing size including plugin and built-in skills (part of 2h).

#### 2g. ASD-STE100 (Simplified Technical English) for English instruction text

- **What:** experiment: rewrite one English section in ~80 % STE style and compare adherence.
- **Pros:** shorter, one instruction per sentence; LLMs know the standard.
- **Cons / risks:** the standard is English; user-facing answers are Russian, so it does not apply to
  the Explanation Protocol's output; third-party skill (`npx skills add` sends telemetry).
- **Impact:** Quality ? `[hypothesis]`. Tokens: small −. Time: =.
- **To clarify in the project:** which sections are pure English instructions.
- **To research online:** the "58 % cheaper" claim (third-party blog, unverified); STE skill contents.
- **Acceptance:** A/B on one section only; keep only if adherence ≥ baseline.
- **Decision (2026-10-13):** No Russian analog of ASD-STE100 exists (§1.8). Russian answers keep the Explanation Protocol, which already encodes the useful rules (one term per concept, no images, lists over prose). STE stays an optional low-priority experiment for English instruction text only.
- **Still open:** None.

#### 2h. Baseline context of every fresh session (new)

- **What:** break down the 66–67 k tokens a fresh `claude -p` session in this repo carries before any
  work (§1.8): system prompt, built-in tool schemas, MCP servers (three browser toolsets are
  configured: `playwright`, `chrome-devtools`, `claude-in-chrome`), instructions, skill listing; turn
  off MCP servers a project does not use.
- **Pros:** this baseline is paid by every subagent and every session start; it is larger than all
  `CLAUDE.md` files together.
- **Cons / risks:** a disabled server is missing when a task needs it; per-project MCP config adds
  maintenance.
- **Impact:** Quality = . Tokens: every subagent start is cheaper; the size of the cut is unknown
  until the breakdown. Time: = .
- **To clarify in the project:** run `/context` in a fresh session; which MCP servers each project uses.
- **To research online:** Claude Code docs on deferred tools and per-project MCP scoping.
- **Acceptance:** baseline tokens of a fresh session measured before and after.
- **Measured (2026-10-13, `claude -p "/context"` in this repo, after the `ai-steward/CLAUDE.md` removal):** ~43k tokens before the first message — memory files 24.8k (global `CLAUDE.md` 16.4k, `python-ai-skills/CLAUDE.md` 5.2k, `RTK.md` 1.6k), deferred system tools 14.5k, skills 9.6k, MCP 4.7k, system prompt 2.4k. Transcripts show a 70.6k median first request in interactive sessions; the gap is likely SessionStart hook output (superpowers, `bd prime`) — hypothesis, not yet measured. Conclusion: the global `CLAUDE.md` is the single largest controllable item (step 2a/2b).
- **Decision (2026-10-13):** add as a step-2 item; measure first.
- **Still open:** the breakdown itself.

### Step 3 — Subagent model routing

Context: subagents ≈ $1,194 / 35 days; 174 of 460 launches on a senior model (Opus, Fable, or
inherited); Haiku nearly unused; GLM unreachable via `Agent` by design.

#### 3a. Default subagent model

- **What:** set `CLAUDE_CODE_SUBAGENT_MODEL` (candidate: `haiku` → Haiku 5.5, or `sonnet`) **without**
  `_FORCE`, so explicit per-launch and per-agent pins keep working; trial in one project first.
- **Pros:** fixes the 100 inherit-from-Opus launches in one line.
- **Cons / risks:** Haiku 5.5 is weaker on agentic coding; prompts >100 k tokens cost 5× more on
  Haiku 5.5; a model different from the parent loses cache reuse with the parent (forks reuse it).
- **Impact:** Quality ↓ risk on complex subagent tasks. Tokens & cost: inherited launches move from
  Opus 5.5 ($4/$20) to Haiku 5.5 ($0.10/$0.50) — up to −95 % on those launches `[estimate]`.
  Time: Haiku is faster per turn (GLM-report: "up to 2.5× faster").
- **To clarify in the project:** which tasks the 100 inherited launches performed; template vs
  runtime ownership of `env` in `settings.json`; does it affect `do-feature-clean` and forks.
- **To research online:** exact resolution order in the official sub-agents doc; whether
  `CLAUDE_CODE_SUBAGENT_MODEL` applies to Explore and built-in agents.
- **Acceptance:** 7-day share of subagent $ on senior models falls; no quality regressions in step-1/7 task set.
- **Done (2026-10-13):** template `env.CLAUDE_CODE_SUBAGENT_MODEL=sonnet`, bd `python-ai-skills-8of.4`. Measured: `general-purpose` obeys the variable, built-in `Explore` ignores it and runs on the session model.
- **Decision (2026-10-13):** Set `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` (Sonnet 5.5) now, without `_FORCE`: a safe default for launches of unknown purpose, 2× cheaper than Opus 5.5 and 5× cheaper than Fable 5.1. Read-only work gets `haiku` explicitly via 3b. Switch the default to `haiku` only if 3d shows most unspecified launches are read-only.
- **Still open:** Is `env` in `settings.json` rendered from the template (edit the template, re-run the installer)?

#### 3b. Explicit model per task type in the 6 spawning skills

- **What:** in `do-feature`, `do-autopilot`, `do-multiagent`, `audit-loop`,
  `grace-setup-subagents`, `progress-watch` — name the model per role (explore → Haiku 5.5,
  implement → Sonnet 5.5, review/architecture → Opus 5.5), referencing `model-registry.json` instead
  of repeating names.
- **Pros:** routing becomes deterministic and reviewable; aligns with the registry SSoT.
- **Cons / risks:** registry roles are for `model-run.sh` pools — a mapping for the `Agent` tool
  needs a new registry section; too-cheap models on implementation hurt quality.
- **Impact:** Quality = with correct mapping. Tokens: largest subagent saving `[estimate: Sonnet
  subagents $659 → explore part on Haiku 5.5 ≈ −80–90 % of that part]`. Time: ↓ for exploration.
- **To clarify in the project:** how each skill currently phrases subagent launches; whether
  `grace-execute` / `grace-multiagent-execute` also spawn; the registry schema.
- **To research online:** Anthropic guidance on Haiku 5.5 as a subagent for coding.
- **Acceptance:** each spawning skill names a model per role; journal shows the mix.
- **Done (2026-10-13):** mapping lives in `model-registry.json` → `agent_work_types`; `delegation-pool-nudge.sh` renders it on every launch without `model` (91 of 126 launches happen outside skills, so a hook reaches them and skill text does not). Inside `do-feature` the tier matrix already matched the user's mapping.
- **Decision (2026-10-13):** Mapping by work type: Discovery, Brainstorming, architecture and contracts → **Fable 5.1** (user decision); code exploration, search, log/transcript reading, digests → **Haiku 5.5** (§1.8 A/B); writing code and tests → **Sonnet 5.5**; code review → a GPT model through `codex` via the existing `reviewer` role (`gpt-sol-xhigh` = `gpt-5.6-sol`, effort `xhigh`). To protect Fable's scarce quota, Fable directs and Haiku explorers do the reading.
- **Still open:** (1) ~~GPT-6 for review~~ — resolved 2026-10-13: user chose `gpt-5.6-sol` with effort `xhigh` (registry `gpt-sol-xhigh`, already first in the `reviewer` role). (2) Review through Codex takes ~12–13 min per run (journal: 739 s, 793 s) — acceptable inside `do-feature` Step 12? (3) Fable effort level (registry: `fable-medium`) and fallback when the Fable quota runs out (Opus `xhigh`?). (4) Where the Agent-tool mapping lives — a new registry section, so model names stay in one place.

#### 3c. Read-only guard for exploration subagents

- **What:** a `SubagentStart` instruction plus a `PreToolUse` guard (by `agent_id`) that keeps
  exploration subagents read-only — scoped per agent type, NOT global (do-multiagent writers need
  write access in worktrees).
- **Pros:** makes Haiku-on-exploration safe; a cheap model cannot damage files.
- **Cons / risks:** third-party template code (review before adopting, or write our own); a
  deny-by-default classifier blocks legitimate reads; MCP tools not covered.
- **Impact:** Quality ↑ (safety). Tokens = . Time: + a `python3` process per guarded call.
- **To clarify in the project:** which subagent types write files; can the guard key on
  `subagent_type`; overlap with existing hooks.
- **To research online:** hook input schema for `SubagentStart` and `agent_id`/agent type fields.
- **Acceptance:** guard test suite: writer agents unaffected, explorers blocked on writes.
- **Done (2026-10-13):** decided not to build a custom guard — read-only work goes to `Explore`, which has no Edit/Write tools; the hook reminds that `Explore` needs an explicit `model`.
- **Decision (2026-10-13):** Do it with our own hook (not the third-party script), scoped to read-only agent types only (Explore and named explorer agents); writer agents (`do-multiagent`, `do-feature-clean`) keep write access.
- **Still open:** Which hook input field carries the agent type (`agent_id` is confirmed in the binary; the type field is not yet checked).

#### 3d. Fable and inherited launches audit

- **What:** read the 74 `fable` and 100 inherited launches (sampled, GLM reading) and classify
  which needed a senior model.
- **Pros:** Fable subagents cost $351 for 1,309 calls — highest $/call; cheap to audit.
- **Cons / risks:** judging "needed" is subjective; small sample.
- **Impact:** Quality = . Tokens: if half move to Sonnet 5.5: ≈ −$150 / 35 days `[estimate]`. Time = .
- **To clarify in the project:** which skill/session launched them (step-0 tool).
- **To research online:** nothing.
- **Acceptance:** written classification + rule added to 3b mapping.
- **Done (2026-10-13):** 126 launches from main sessions classified by description (`Agent` calls with `model` omitted or `fable`; the earlier "100 inherited" also counted launches made inside subagents and 32 `fork` launches, which must inherit to reuse the parent cache). **Fable, 76:** 29 from `do-feature` (top tier: Discovery / GRACE Plan); of the other 47 — ~15 GRACE plans and contracts, ~15 plan audits and plan updates, 9 blind-judge evaluations, 3 design comparisons: consistent with the user's rule. Exceptions: 2 decision-recording write tasks (→ Sonnet) and 1 whole-branch review (→ `reviewer` role). **Inherited, 50:** ~15 read-only (`Explore`, recon, inventories, checks → Haiku), ~20 research and dossier writing (→ Sonnet or the GLM `researcher` role), 5 mechanical reformatting (→ Haiku or GLM), the rest code changes and service agents.
- **Decision (2026-10-13):** confirms 3a (default Sonnet) and the 3b mapping; adds two rules to 3b — decision-recording writes go to Sonnet, branch reviews go to the `reviewer` role.
- **Still open:** none.

#### 3e. Subagent prompt-cache TTL

- **What:** measure idle gaps between subagent requests (step 0) and decide `subagentPromptCacheTtl`
  `5m` vs `1h`.
- **Pros:** may cut subagent cache re-writes (Fable subagents: $275 of $351 is writes).
- **Cons / risks:** 1 h writes cost 2× base input vs 1.25× for 5 m — loses money if subagents
  rarely idle 5–60 min; "1h" ignored in subscription overage (GLM-report).
- **Impact:** Quality = . Tokens: cost ±, decided by data. Time = .
- **To clarify in the project:** idle-gap distribution per skill.
- **To research online:** the DannyMac180 gist's method (reuse the idea in our script); Boris
  Cherny's post (x.com returned 402 to the researcher).
- **Acceptance:** computed verdict from our own transcripts.
- **Decision (2026-10-13):** Closed: keep the default 5-minute subagent cache. Measured: 16,844 of 16,961 gaps between consecutive subagent requests (99.3 %) are under 5 minutes. Long gaps come from resumed subagents (`SubagentHandback`, `SendMessage`) and long commands inside the subagent (test runs, wait loops, `model-run.sh`). Fable's cache-write cost comes from every new subagent writing its starting context, not from idling.
- **Still open:** Revisit only if agent-team usage grows (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set; teammates live longer).

### Step 4 — New models and model roles

#### 4a. Evaluate Haiku 5.5 on our tasks

- **What:** fixed task set (code exploration, transcript digest, output verification, `bd` triage)
  on Haiku 5.5 vs Sonnet 5.5; compare correctness, tokens, seconds; add results to
  `docs/research/model-passports-*` and Haiku 5.5 to `model-registry.json`.
- **Pros:** 20× cheaper than Sonnet 5.5 on in/out, 10× on cache reads (≤100 k prompts).
- **Cons / risks:** ~30 % more tokens per text (GLM-report); 5× price over 100 k; weaker on agentic
  coding; no published comparison with Sonnet 5 / Opus 5.5.
- **Impact:** Quality: per task class, measured. Tokens: the largest per-call lever available.
  Time: faster turns.
- **To clarify in the project:** which registry roles could include Haiku 5.5; how the passports
  doc rated Haiku 4.5.
- **To research online:** independent Haiku 5.5 benchmarks on coding agents; tokenizer change details.
- **Acceptance:** passport entry with measured quality and speed.
- **Decision (2026-10-13):** Adopt Haiku 5.5 for read-only subagent work: 4 of 4 tasks answered correctly, same as Sonnet 5.5, at 15–23× lower cost and slightly faster (§1.8). Not adopted for writing code — not tested yet. Update the registry `haiku` entry (it still describes Haiku 4.5: 200 k window).
- **Still open:** Test code writing and long multi-step agentic tasks; repeat each task 3× for variance; keep subagent prompts under 100 k tokens (Haiku 5.5 price ×5 above that).

#### 4b. Advisor cost and setting

- **What:** find where advisor spend is recorded; decide on/off and advisor model (Opus 5.5 vs
  Fable 5.1).
- **Pros:** possibly a large hidden cost (full conversation, uncached, per consultation —
  GLM-report); one setting to change.
- **Cons / risks:** the advisor may be what keeps quality high on hard tasks; removing it blind is risky.
- **Impact:** Quality ↓ risk if removed. Tokens: unknown until measured. Time: each consultation
  adds latency.
- **To clarify in the project:** consultations per session; whether `advisor_message` records exist
  (the string is in the binary).
- **To research online:** official `code.claude.com/docs/en/advisor` (re-read by the parent);
  billing of advisor tokens on subscription.
- **Acceptance:** advisor $ per 35 days known; decision recorded.
- **Decision (2026-10-13):** Pending measurement: no decision until advisor spend is visible.
- **Still open:** Where advisor usage is recorded: the A/B `claude -p` JSON listed only the main model in `modelUsage` — either the advisor was not consulted or it is reported elsewhere.

#### 4c. Main-session model: Sonnet 5.5 + Opus advisor + Haiku subagents

- **What:** trial the preset (main `sonnet`, `advisorModel: opus`, subagents `haiku`) in a few
  routine projects for a week; keep Opus for architecture work by choice via `/model`.
- **Pros:** main sessions are 72 % of spend; Sonnet 5.5 is half of Opus 5.5 and 2.5–5× cheaper than
  Opus 5 per token.
- **Cons / risks:** the biggest quality risk in the plan; the advisor adds uncached reads; the
  orchestrator is a human choice per session (CLAUDE.md rule).
- **Impact:** Quality ↓ risk on complex work. Tokens & cost: up to ≈ −40–50 % of main-session $
  `[estimate]`. Time: Sonnet turns are faster.
- **To clarify in the project:** which projects are routine; how to compare quality (bugs found in
  review, re-work rate).
- **To research online:** experience reports with this preset; the preset's exact JSON (GLM-report
  has it).
- **Acceptance:** a week of trial with no rise in re-work; $ per task down.
- **Decision (2026-10-13):** Not adopted as a global default. Main-session model stays a per-task human choice: Fable for Discovery/architecture (user decision), Opus for complex implementation, Sonnet 5.5 trial for routine projects.
- **Still open:** Which projects count as routine for the Sonnet trial, and the quality metric (re-work rate, review findings).

### Step 5 — `git-finish` (independent with conditional hand-offs)

- **What:** per-invocation profile; the 17.6 k-char `SKILL.md` and 1,168-char description; which
  conditional hand-offs fire; whether docs/plans update steps re-read large files.
- **Pros:** 73 calls in 58 sessions — frequent and predictable; procedure-like, suits a script for
  the mechanical part.
- **Cons / risks:** touches git state (merge, delete, push) — changes need careful tests.
- **Impact:** Quality = . Tokens: the low bound 455 M — mostly host-context re-reads `[measured]`;
  a shorter skill and a scripted mechanical part reduce calls. Time: ↓ with scripting.
- **To clarify in the project:** call count per run; which steps are deterministic (scriptable).
- **To research online:** nothing specific.
- **Acceptance:** median tokens per run down; regression tests of the skill pass.
- **Decision (2026-10-13):** Do it after the pilot: shorten the skill and move deterministic steps into a script.
- **Still open:** Which steps are deterministic enough to script.

### Step 6 — `best-*` family (nested)

- **What:** measure a wrapper call including nested `best-research` / `best-recommend`; find rules
  loaded twice; check whether web/Context7 research is delegated to the `researcher` role.
- **Pros:** `best-questions` is the most expensive skill on the high bound (2.4 B).
- **Cons / risks:** the family is the user's decision tool — quality loss is costly; the high bound
  includes the work that follows decisions, not only the skill.
- **Impact:** Quality = . Tokens: delegating research to GLM moves reading off the Anthropic pool.
  Time: GLM research is slower (258–560 s in this session) — fits only when the user is not waiting.
- **To clarify in the project:** what share of a `best-questions` window is research vs dialogue;
  duplication between the four `SKILL.md` files.
- **To research online:** nothing specific.
- **Acceptance:** per-question tokens down with the same recommendation quality.
- **Decision (2026-10-13):** Delegate source reading to the GLM `researcher` role only where nobody waits for the answer; in interactive `best-questions` keep the dialogue in-session and use Haiku explorers for code reading.
- **Still open:** Share of a `best-questions` window spent on research vs dialogue (step-0 tool).

### Step 7 — `do-feature` pipeline (and unused `do-autopilot` / `do-multiagent`)

- **What:** per-run cost by pipeline stage; hand-off data between stages; repeated reads of the
  same files; model per stage (registry roles); 482 M subagent tokens and 34 `do-feature-clean`
  launches.
- **Pros:** the highest low-bound cost (732 M); stage-level routing is where cheap models fit best
  (exploration, drafting tests, docs).
- **Cons / risks:** most complex to measure; gates involve the user, so windows split; changes
  affect every dev project.
- **Impact:** Quality = with correct routing. Tokens: large, unknown until staged. Time: parallel
  stages and cheap models cut wall clock.
- **To clarify in the project:** stage markers in transcripts (to attribute by stage); which
  stages re-read the same files; why `do-autopilot` / `do-multiagent` were not used (keep, shrink
  description, or retire).
- **To research online:** Anthropic guidance on multi-agent token cost (blog: 3–10× vs single agent).
- **Acceptance:** per-run cost by stage known; at least two stages re-routed with equal quality.
- **Decision (2026-10-13):** Route stages by the 3b mapping: Discovery/Brainstorming/GRACE plan → Fable; exploration → Haiku; execution → Sonnet; review → `reviewer` role (Codex). Keep `do-autopilot` / `do-multiagent` but list them `name-only` (2f).
- **Still open:** Stage markers in transcripts for per-stage attribution; whether to retire `do-autopilot` / `do-multiagent` after 90 more days without use (user decision).

---

## 3. Considered and deferred

| Item | Reason | Revisit when |
|------|--------|--------------|
| You Should Know (`cc-plugin-you-should-know@builtin`) | adds a side agent = extra spend, unquantified | after steps 0–4, as a quality experiment |
| prompt-cache-control mod | main-loop observability only; third-party code in the UI; step-0 script covers the need | if live cache monitoring is wanted |
| Managed Agents dynamic workflows | API product, not Claude Code; multiplies tokens | if a product needs it |
| `CODING_STANDARDS.md` split (from the post) | not found in Pocock's repo; 2b covers the idea | — |

## 4. Cross-cutting open questions

1. ~~Real billing basis~~ — resolved: Anthropic Max 5x subscription; $ = API-equivalent quota share.
2. Do subagents load the full `CLAUDE.md` and skill listing? (decides the size of step 2's effect on subagents.)
3. Advisor spend visibility (4b).
4. Codex shares the same `AGENTS.md` — every step-2 change must be checked against Codex behaviour.
5. A/B harness: a fixed task set and a quality metric reused by steps 1, 2, 4, 7.
