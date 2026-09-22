# Model Passports — Rating for do-feature Routing (Variant 2, Phase A)

- **bd issue:** `python-ai-skills-bt9` (blocks `python-ai-skills-4f4` — Routing Matrix revalidation)
- **Date collected:** 2026-09-22
- **Method:** Variant 2 ("passport + speed"), approved by user. Phase A (this document) = passport data
  from documentation, no measurements. Phase B = minimal-cost speed experiments (plan at the end).
- **User decisions:** all models included, no cutoffs; model x reasoning-mode = separate rating position;
  Anthropic effort/thinking/fast modes and GLM modes included for symmetry; experiments must NOT consume
  a significant share of subscription quotas; result delivered as this standalone document (not an ADR,
  not a Routing Matrix edit — the matrix update is a later step under `python-ai-skills-4f4`).

---

## 1. Criteria (agreed list)

**A. Passport (from documentation — this document):**
1. Context window (nominal) and max output tokens
2. Connection method into the pipeline (Agent tool / shell function / codex CLI) and whether a
   do-feature step can invoke it automatically
3. Subscription cost and quota: request/token allowance, reset window
4. Reasoning modes available and their quota cost

**B. Measured (Phase B, one standardized run):**
5. Speed: tokens/sec and time-to-first-token at small (~5k), medium (~50k), large (~150k+) context
6. Quality stability at a nearly-full context window (same task at empty vs. near-full context)

**C. Quality (Phase C if needed, benchmark tasks from own projects):**
7. Code correctness (do generated tests/linters pass)
8. Instruction adherence: GRACE contracts, semantic markup, commit format
9. Review quality: real defects found vs. invented
10. Russian-language explanation quality (for user-facing steps)

**D. Operational:**
11. Channel stability (known blockers, quota exhaustion patterns)
12. Privacy: does code leave the machine
13. Parallelism: concurrent calls the pool tolerates (matters for Execution workers)

---

## 2. Passport data by pool

### 2.1 Anthropic — Claude subscription Max 5x ($100/mo)

Connection: native `claude` CLI; the **only** pool reachable via the Agent tool from do-feature
(structural constraint — Agent tool dispatches Anthropic tiers only).

| Model | Context | Max output | API price in/out ($/MTok) | Reasoning modes |
|---|---|---|---|---|
| claude-fable-5 | 1M | 128K | 10 / 50 | thinking always on; effort low/medium/high/xhigh/max |
| claude-opus-5 | 1M | 128K | 5 / 25 | adaptive thinking on by default; disabled allowed only at effort <= high; effort low..max; **fast mode** (research preview, ~2.5x output speed, priced 10/50) |
| claude-sonnet-5 | 1M | 128K | 3 / 15 (intro 2/10 until 2026-08-31) | adaptive default; effort low..max; new tokenizer ~30% more tokens per same text |
| claude-haiku-4-5 | 200K | 64K | 1 / 5 | thinking via `budget_tokens` (legacy scheme); no effort parameter |

Source: `claude-api` skill model table (cached 2026-06-24; verifiable live via Models API
`client.models.retrieve`). API prices shown as relative cost weights — subscription usage is metered
by sessions, not per-token billing.

**Subscription limits (Max 5x, $100/mo):** 5-hour rolling session window at ~5x Pro capacity
(~225 prompts/window derived estimate; Anthropic publishes the multiplier, not counts) + two weekly
caps (one all-models, one Sonnet-only). Claude Code 5h limits were doubled on 2026-05-06.
Sources: [userightai](https://www.userightai.com/claude-max-limits),
[ccforeveryone](https://ccforeveryone.com/guides/claude-code-limits-and-pricing),
[morphllm](https://www.morphllm.com/claude-code-usage-limits).

### 2.2 Z.ai GLM — Coding Plan (~$20/mo tier)

Connection: `claude-glm` shell function (`~/.bashrc:162`) — swaps `ANTHROPIC_BASE_URL` to
`https://api.z.ai/api/anthropic` and remaps tiers: `fable`->glm-5.3[1m], `opus`->glm-5.3-flash,
`sonnet`/`haiku`->glm-4.7. NOT reachable via Agent tool; invoke via
`bash -ic "claude-glm -p --model <tier> ..."` (precedent: `Sensedar-Spark/scripts/run_markup_queue.sh`).

| Model | Context | Max output | Notes | Reasoning modes |
|---|---|---|---|---|
| glm-5.3 (`[1m]` profile) | 1M | 128K | MoE 753B total / ~40B active | reasoning always on, cannot disable; efforts **low / high / max** (max = default) |
| glm-5.3-flash | 1M | (not verified) | MoE 320B / 18B active; hybrid sparse+linear attention | efforts not verified — assume same family scheme, **hypothesis** |
| glm-4.7 | ~205K (204,800) | 131,072 | previous generation | modes not verified — **hypothesis** |

Sources: [Z.AI docs GLM-5.3](https://docs.z.ai/guides/llm/glm-5.3),
[Z.AI docs GLM-5.3-Flash](https://docs.z.ai/guides/vlm/glm-5.3-flash),
[OpenRouter GLM-4.7](https://openrouter.ai/z-ai/glm-4.7),
[layer3labs GLM-5.3](https://www.layer3labs.io/guides/glm-5-3-explained).

**Subscription limits (Coding Plan):** Lite tier lists at **$18/mo** (user reported $20 — likely the
Lite tier at an older/rounded price; Pro is $72, Max is $160 — verify which tier the account has in
the Z.ai dashboard). Lite: ~80 prompts per 5-hour cycle, ~400/week. Quota multipliers exist for newer
models (observed 3x peak / 2x off-peak for 5.2-era models; 5.3 multiplier not verified). 5-hour window
resets 5h after consumption; weekly resets every 7 days from activation. Reset was previously observed
on Beijing time (global CLAUDE.md note).
Sources: [Z.AI FAQ](https://docs.z.ai/devpack/faq),
[aipricing.guru](https://www.aipricing.guru/z-ai-subscription-pricing/),
[digitalapplied](https://www.digitalapplied.com/blog/glm-coding-plan-worth-it-2026-value-analysis).

### 2.3 OpenAI GPT — ChatGPT Plus ($20/mo) via Codex CLI

Connection: `codex` CLI (`codex exec -m <model>`); default model `gpt-5.6-sol`,
`model_reasoning_effort = "high"` (`~/.codex/config.toml`). NOT reachable via Agent tool.

| Model | Context | Max output | API price in/out ($/MTok) | Role per OpenAI |
|---|---|---|---|---|
| gpt-6-astra | 1,050,000 (922K input ceiling) | 128K | (not verified) | most capable; default in picker; in Codex sessions effective window ~258K by default (1M configurable) |
| gpt-5.6-sol | 1,050,000 | 128K | 5 / 30 | flagship of 5.6 family; hardest coding/agents |
| gpt-5.6-terra | 1,050,000 | 128K | 2.50 / 15 | balanced mid-tier |
| gpt-5.6-luna | 1,050,000 | 128K | 1 / 6 | fast and cheap; near GPT-5.5 on several tests |
| gpt-5.5 | 1,050,000 (922K in / 128K out) | 128K | (not verified) | previous generation |

Reasoning levels (from the Codex picker, verified by user screen): **Low (default) / Medium / High /
Extra high / Max / Ultra** — "Max and Ultra consume usage limits faster".

Sources: [OpenAI GPT-6 Astra](https://openai.com/index/gpt-6-astra/),
[OpenAI GPT-5.6](https://openai.com/index/gpt-5-6/),
[getunblocked Codex context](https://getunblocked.com/blog/codex-context-window/),
[OpenAI API GPT-5.5](https://developers.openai.com/api/docs/models/gpt-5.5),
[mindstudio 5.6 tiers](https://www.mindstudio.ai/blog/what-is-gpt-5-6-sol-terra-luna-explained).

**Subscription limits (Plus $20/mo):** 5-hour rolling window for Codex (restored ~2026-08-25) +
weekly limits; Codex and ChatGPT Work share one agentic pool. Reported Plus ranges per 5h:
Sol 10-100, Terra 25-200, Luna 250-2,000 messages (consumption varies with model, context size,
reasoning effort, local vs cloud).
Sources: [9to5mac](https://9to5mac.com/2026/08/24/openai-restores-5-hour-codex-and-work-limits-for-chatgpt-plus-users/),
[simplemetrics](https://simplemetrics.xyz/chatgpt-codex-limits-2026/),
[Codex pricing](https://chatgpt.com/codex/pricing/).

### 2.4 Local — spark-1 gateway (free)

Connection: `claude-spark-qwen38` shell function (`~/.bashrc:198`) -> LiteLLM at
`https://spark1.clevertry.com/baa846f2`, auth via `ANTHROPIC_AUTH_TOKEN` (Bearer).

| Model | Context | Cost | Privacy | Status |
|---|---|---|---|---|
| qwen38-27b | 122,880 (function profile) | free (machine time only) | code never leaves own infra — the only such channel | **BLOCKED**: LiteLLM returns 500 — the model's Jinja template rejects the second `role=system` message that Claude Code sends (bd `llm-asw`, 2026-09-20) |

User decision (2026-09-22, interpreted from "ДА" on the fix-or-exclude question): **fix the blocker
before speed measurements**. The fix lives on the spark-1 side, not in the shell function. Passport
data collection is unaffected.

Note: the spark-1 gateway also hosts `gemma-4-26b` and `bge-m3` (global CLAUDE.md), but no shell
function wires them into Claude Code — out of scope for this rating.

---

## 3. Rating grid (model x mode positions)

Per user decision every model x reasoning-mode pair is a separate position:

| Pool | Positions |
|---|---|
| Anthropic | fable x5 efforts; opus-5 x5 efforts + fast mode (= 6); sonnet-5 x5 efforts; haiku-4.5 x1 = **17** |
| GLM | glm-5.3 x3 efforts (low/high/max); glm-5.3-flash x3 (hypothesis); glm-4.7 x1 (modes unverified) = **7** |
| Codex | 5 models x 6 levels = **30** |
| Local | qwen38-27b x1 = **1** |
| **Total** | **55 positions** |

---

## 4. Known operational facts (criterion D)

1. **Channel stability:** qwen38-27b blocked (500, above). Z.ai quota exhaustion observed in practice
   (resets on Beijing time). Codex Plus 5h window restored 2026-08.
2. **Privacy:** only qwen38-27b keeps code on own infrastructure.
3. **Automation:** only Anthropic models are dispatchable via the Agent tool inside do-feature steps;
   GLM and Codex require shell-out wrappers; this is a routing constraint, not a quality property.

---

## 5. Phase B plan — speed measurements at minimal quota cost

Constraint (user): do NOT consume a significant share of monthly quotas.

1. One standardized prompt (fixed text, ~200-token answer cap) per position.
2. Context tiers: small (~2k) for ALL 55 positions; medium (~50k) ONLY for the shortlist that survives
   passport screening (expected <= 12 positions); large (~150k) ONLY for the final <= 6 candidates.
3. Estimated cost: 55 small calls =~ 55 prompts total spread across three pools =~ well under one
   5-hour window on each subscription; medium/large tier adds ~18 calls.
4. Measure: wall-clock to first token and total, output tokens/sec; record model+mode+timestamp.
5. Prerequisite: spark-1 blocker fix (bd `llm-asw`) before qwen positions are run.

## 6. Verified CLI flags for mode selection (Phase B prerequisites)

- `claude --effort <low|medium|high|xhigh|max>` — verified via `claude --help`; also applies to GLM
  through the `claude-glm` wrapper (z.ai documents low/high/max for glm-5.3).
- Codex: `codex exec -m <model> -c model_reasoning_effort=<value>`; accepted values
  `none|minimal|low|medium|high|xhigh|max`; picker labels map Low->low, Medium->medium, High->high,
  Extra high->xhigh, Max->max. `ultra` is NOT reliably settable via config — some client paths
  silently normalize it (sources: [dev.to](https://dev.to/aicoding-guide/how-to-change-reasoning-effort-in-codex-cli-modelreasoningeffort-values-and-one-off-overrides-2bf4),
  [codexinsider](https://codexinsider.com/config/model-reasoning-effort/)). The config parser does not
  validate the value locally (accepted `banana` without error) — treat measured "ultra" rows as suspect.
- Anthropic fast mode has no verified non-interactive CLI flag (`/fast` is an interactive toggle) —
  excluded from the automated sweep, noted as a manual-only position.
- Measured wall-clock via CLI wrappers includes CLI startup overhead (hooks, MCP for `claude`) —
  comparable within a pool, biased across pools; recorded as-is and flagged.

## 7. Phase B results — small-context sweep (measured 2026-09-22)

Method: 1 call per position, identical short prompt ("reverse a string" + one sentence), wall-clock
seconds including CLI startup overhead; `timeout 300`; raw CSV and answers in the session job dir
(`speed_small.csv`). Single-shot — indicative ranking, not statistically significant. qwen38-27b and
Anthropic fast mode not run (see section 6).

| Pool / model | low | medium | high | xhigh | max | ultra |
|---|---|---|---|---|---|---|
| anthropic/fable | 8.0 | 7.4 | 12.8 | 12.4 | 12.5 | — |
| anthropic/opus | 8.3 | 8.7 | 11.2 | 7.6 | 8.6 | — |
| anthropic/sonnet | 6.3 | 6.9 | 6.2 | 7.2 | 25.6 | — |
| anthropic/haiku | 8.8 (no effort param) | | | | | |
| glm/glm-5.3 | 11.2 | — | 12.9 | — | 17.5 | — |
| glm/glm-5.3-flash | 12.7 | — | 17.6 | — | 14.8 | — |
| glm/glm-4.7 | 19.2 (no effort) | | | | | |
| codex/gpt-6-astra | 13.4 | 9.9 | 12.0 | 21.9 | 30.6 | 22.9 |
| codex/gpt-5.6-sol | 17.7 | 18.3 | 25.6 | 22.9 | 28.0 | 30.8 |
| codex/gpt-5.6-terra | 15.3 | 13.7 | 13.3 | 13.5 | 28.8 | 23.1 |
| codex/gpt-5.6-luna | 7.9 | 19.5 | 13.9 | 18.8 | 29.6 | 27.1 |
| codex/gpt-5.5 | 13.4 | 9.6 | 15.5 | 20.7 | **400 error** | 17.1 (suspect) |

Findings:

1. **gpt-5.5 rejects `max`** — API 400: supported values are none/low/medium/high/xhigh only. Its
   `ultra` row returned 200, confirming silent client-side normalization — treat all `ultra` rows as
   unreliable positions (consistent with section 6).
2. **Fastest at small context:** anthropic/sonnet at low-xhigh (~6-7 s) and anthropic/fable,opus at
   low/medium (~7-9 s); codex/gpt-5.6-luna low (7.9 s) is the only non-Anthropic entry in that band.
3. **haiku is not faster than sonnet here** (8.8 vs 6.2-7.2 s) — CLI startup overhead dominates at
   this task size; haiku's advantage should reappear on longer outputs (verify in the medium tier).
4. **Effort level costs real time on Codex:** max/ultra rows run 22-31 s across all models vs 8-18 s
   at low-high. On Anthropic the effect is milder (fable high+ ~12.5 s vs ~7.5 s at low/medium);
   outlier: sonnet max 25.6 s.
5. **GLM sits in the middle band** (11-19 s), slower than Anthropic low-effort but comparable to
   mid-tier Codex; glm-4.7 (19.2 s) is the slowest GLM channel.
6. Quota spent: 53 short calls total (~16 Anthropic, 7 GLM, 30 Codex) — well within one 5-hour
   window on every subscription, per the no-significant-spend constraint.

### 7.1 Medium tier (~50-65k tokens of context), 9 shortlist positions

Filler: word-salad lines (295KB). **anthropic/sonnet refused the word-salad filler on both calls**
("Sonnet 5 can't help with this", AUP-classifier refusal — the only model to do so) and was re-run
with natural coherent prose of the same byte size; its rows are therefore not byte-identical input.

| Position | seconds | note |
|---|---|---|
| anthropic/opus xhigh | 6.8 | fastest |
| anthropic/sonnet low | 8.0 | natural-text retry |
| anthropic/haiku | 8.7 | |
| codex/gpt-5.6-luna low | 9.9 | |
| anthropic/sonnet high | 11.8 | natural-text retry |
| anthropic/fable medium | 11.8 | |
| codex/gpt-6-astra medium | 12.7 | |
| codex/gpt-5.6-terra high | 13.8 | |
| glm/glm-5.3 low | 15.7 | slowest |

Side datapoint: an accidental oversized run fed sonnet ~300k tokens of natural prose — processed in
12-20 s (low/high), confirming near-flat input-scaling on the Anthropic channel.

### 7.2 Large tier (~200k tokens of context — relabeled), 6 finalists

The "large" natural-prose filler (888KB) measured **~225k tokens total request** per the CLI's own
error report on haiku, i.e. ~4.45 chars/token — denser than the 150k estimate. Tier relabeled ~200k.

| Position | seconds | note |
|---|---|---|
| anthropic/opus xhigh | 9.5 | fastest |
| anthropic/sonnet low | 10.5 | |
| glm/glm-5.3 low | 17.9 | |
| codex/gpt-5.6-luna low | 19.0 | |
| codex/gpt-6-astra medium | 21.8 | |
| anthropic/haiku | **fail** | "Prompt is too long: ~225,166 tokens (limit 200,000)" — haiku's 200K window disqualifies it from large-context steps |

### 7.3 Local qwen38-27b — blocker resolved, measured 2026-09-22

The bd `llm-asw` blocker (LiteLLM 500 on a second `role=system` message) **no longer reproduces**.
Verified two ways before measuring: a direct `curl` to the gateway with an extra `role=system` entry
in `messages[]` returned **HTTP 200** (as did the single-system control), and `claude-spark-qwen38`
completed a normal prompt. The fix landed on the spark-1 side between 2026-09-20 and 2026-09-22; the
shell function was not changed. The stale blocker comment in `~/.bashrc:193-197` is now wrong.

Routing sanity check: asked directly over `curl`, the model answers *"I am Qwen, a large language
model independently developed by Alibaba Group's Tongyi Lab"*, and the response body carries
`"model":"qwen38-27b"`. Through Claude Code the same model answers *"I am Claude Fable 5"* — it is
echoing Claude Code's system prompt, **not** evidence of mis-routing. Do not use self-identification
to verify which endpoint served a request; read the response `model` field or the gateway logs.

| Tier | seconds | outcome |
|---|---|---|
| small (~2k) | 80.5 | ok |
| medium (~65k) | 190.0 | ok |
| large (~225k) | fail | "Prompt is too long" — 122,880-token window |

### 7.4 Cross-tier picture (seconds, small / medium / large)

- anthropic/opus xhigh: 7.6 / 6.8 / 9.5 — near-flat, best overall
- anthropic/sonnet low: 6.3 / 8.0 / 10.5 — near-flat
- anthropic/haiku: 8.8 / 8.7 / fail — fine until the 200K wall
- codex/gpt-5.6-luna low: 7.9 / 9.9 / 19.0 — degrades ~2.4x
- codex/gpt-6-astra medium: 9.9 / 12.7 / 21.8 — degrades ~2.2x
- glm/glm-5.3 low: 11.2 / 15.7 / 17.9 — slow start, modest degradation
- local/qwen38-27b: 80.5 / 190.0 / fail — **10-24x slower than every subscription pool**

The qwen numbers are the single most decision-relevant result of the sweep: the local gateway is free
in tokens but costs 1.5-3 minutes of wall-clock per call, and its 122,880-token window is the smallest
of any channel. It is a batch/background pool, not an in-loop one.

Routing implications (speed axis only; quality axis = Phase C, not yet measured):

1. Anthropic channel is the fastest at every context size and scales almost flat — consistent with
   keeping `top/strong` tiers on Anthropic in the do-feature Routing Matrix.
2. codex/gpt-5.6-luna low is the best non-Anthropic option at small/medium context — a candidate
   second voice for cheap parallel work while quotas allow.
3. glm-5.3 low never wins on speed but is the bulk-work pool by quota economics (separate $18-20
   subscription) — its role stays "offload volume", not "win latency".
4. haiku must not be routed to steps whose context can exceed ~170k tokens (200K limit minus CLI
   overhead); qwen38-27b hits the same wall five times earlier, at ~110k.
5. qwen38-27b belongs to queued background work only. At 80-190 s per call, a 10-step in-loop
   sequence costs 13-32 minutes of pure model latency.

Phase C (quality benchmark) was **cancelled by user decision 2026-09-22** — the rating stands on
passport + speed only. Every routing claim below is therefore a statement about latency, cost and
capacity, never about answer quality.

Still pending: Anthropic fast mode (interactive-only, no non-interactive flag found).

## 8. Proposed changes to skills and instruction files (NOT applied — awaiting approval)

Each item names the exact file and line, the measured fact that motivates it, and the proposed
wording. Nothing here has been applied. Items are ordered by how wrong the current text is.

### P1 — `claude-home/CLAUDE.md:341` (Four Token Pools, item 3) — **factually misleading**

Current: *"Local gateway ... **costs no tokens at all**, only machine time. All in-pipeline LLM work
belongs here."*

Measured: 80.5 s small / 190.0 s medium / fails above ~110k tokens. "All in-pipeline LLM work" reads
as an instruction to put latency-sensitive steps on a channel that is 10-24x slower than every
alternative and has the smallest window of any channel.

Proposed: keep the free-in-tokens claim, replace the scope sentence — *"costs no tokens, but 80-190 s
per call (measured 2026-09-22) and a 122,880-token window. Use it for queued and background work —
corpus annotation, batch scoring, overnight sweeps — never for a step a human or a loop is waiting on.
A 10-step in-loop sequence on this pool costs 13-32 minutes of pure model latency."*

### P2 — `do-feature/SKILL.md:103-108` (Escalation rule) — **silent-failure gap**

Current: escalation triggers only on *"2 consecutive test fails"*.

Measured: `cheap`=haiku returns `Prompt is too long · the request is ~225,166 tokens (limit 200,000)`.
That is not a test failure, so the current rule never escalates — the step dies instead.

Proposed: add rule 5 — *"**Escalate immediately on context overflow.** A worker that returns a
context-limit error (`Prompt is too long`, HTTP 400 on input size) is re-dispatched one tier up at
once, without waiting for the 2-fail counter. Window sizes are not uniform across tiers: haiku 200K,
qwen38-27b 122,880, every other current model 1M."*

### P3 — `claude-home/CLAUDE.md:100-110` (Plan Sizing) — **ambiguous under tiered routing**

Current: a phase must fit *"одно контекстное окно активной модели"*, budget at ~60%.

Problem: under the Routing Matrix the planning step (mid) and the executing step (cheap) run on
different models with a 5x window difference (1M vs 200K). A plan sized against the planner's window
is unexecutable by a cheap-tier worker.

Proposed: add — *"Окно считать по **наименьшему** среди ярусов, которые будут исполнять и
верифицировать фазу, а не по окну модели, которая пишет план. Практический ориентир для оценки
объёма: ~4.45 знака на токен на связном английском тексте (замер 2026-09-22)."*

### P4 — `audit-loop/SKILL.md:140` — **2x slower than necessary**

Current: `codex exec -s read-only --cd "$PWD"` — no `-m`, no effort, so it inherits
`~/.codex/config.toml` (`gpt-5.6-sol`, `model_reasoning_effort = "high"`).

Measured: sol/high = 25.6 s, the slowest Codex position measured; terra/high = 13.3 s and
luna/low = 7.9 s for the same prompt.

Proposed: pin the model explicitly in the skill rather than inheriting a global default that can
change under it — `codex exec -s read-only --cd "$PWD" -m gpt-5.6-terra -c model_reasoning_effort=high`,
with a one-line note that the skill pins its own model so a global config change cannot silently
alter audit behaviour.

### P5 — `claude-home/CLAUDE.md:350` (tier mapping is NOT identity) — **incomplete**

The tier remapping itself is confirmed correct. Missing facts that change how a delegate is written:
glm-5.3 supports only `low`/`high`/`max` (no `medium`, no `xhigh`) and **cannot disable reasoning**;
glm-4.7's window is ~205K, not 1M. Proposed: append these three facts to the existing rule.

### P6 — `claude-home/CLAUDE.md:342` (Codex pool) — **missing the default-is-slowest trap**

Proposed: append — *"Дефолт `~/.codex/config.toml` — `gpt-5.6-sol` + `effort=high`, самая медленная
из замеренных позиций Codex (25.6 с). Для фоновых проверок задавать модель явно: terra/high 13.3 с,
luna/low 7.9 с."*

### P7 — `do-feature/SKILL.md:78` (tier mapping) — **decision needed, not an automatic edit**

Measured: `opus` at xhigh is faster than `fable` at every context size (7.6/6.8/9.5 s vs 12.4/11.8 s)
and costs half as much per token ($5/$25 vs $10/$50); fable additionally requires 30-day data
retention. **Quality was not measured** (Phase C cancelled), and `top`=fable was a deliberate user
decision on 2026-08-28.

Proposed: do **not** silently re-map the tier. Instead add one line under the tier list recording the
measured latency/cost delta, so the next person choosing between them sees the tradeoff. Re-mapping
`top` to `opus`+xhigh is a separate decision that needs a quality signal this sweep does not provide.

### P8 — `docs/adr/ADR-002-model-routing-ab-validation.md` (Consequences) — **stale limitation**

Current: *"The matrix has NOT been revalidated against Claude 5 models."*

Proposed: amend to record that the **latency and capacity axes** were revalidated on 2026-09-22
(pointer to this document), while the **quality axis remains unvalidated** against the Claude 5
lineup — so `python-ai-skills-4f4` stays open for quality only.

### P9 — new facts worth recording wherever tooling gotchas live

1. `gpt-5.5` rejects `effort=max` with HTTP 400 (supported: none/low/medium/high/xhigh).
2. Codex accepts any string for `model_reasoning_effort` locally without validation (`banana` was
   accepted); `ultra` is silently normalized by some client paths — never trust an `ultra` run.
3. `sonnet` refused a word-salad test fixture under the AUP classifier ("Sonnet 5 can't help with
   this"). Generate large test fixtures as coherent prose, not random word lists.
4. **A model's self-identification does not prove which endpoint served it.** qwen38-27b answers
   "I am Claude Fable 5" through Claude Code (echoing the system prompt) and "I am Qwen ... Alibaba"
   over direct curl. Verify routing by the response `model` field, never by asking the model.

### P10 — outside the repo (cannot edit, user action)

`~/.bashrc:193-197` still carries the "ИЗВЕСТНЫЙ БЛОКЕР (bd llm-asw)" comment describing the
LiteLLM 500. That blocker is resolved (section 7.3) — the comment now misleads anyone reading the
function. Editing `~/.bashrc` is outside the allowed write scope (global CLAUDE.md → Security), so
this is a suggestion for the user to apply.

## 9. Open items / not verified

- glm-5.3-flash max output and effort levels; glm-4.7 reasoning modes.
- GPT-6 Astra and GPT-5.5 API pricing (not needed for subscription use, kept for completeness).
- Exact Z.ai tier of the user's account ($18 Lite vs a $20 legacy price) — check the dashboard.
- Actual quota multipliers of glm-5.3 family on the Coding Plan.
- Reasoning-level -> quota-consumption coefficients for Codex (only the qualitative
  "Max and Ultra consume faster" is published in the picker).
