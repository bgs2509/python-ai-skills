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

## 7. Open items / not verified

- glm-5.3-flash max output and effort levels; glm-4.7 reasoning modes.
- GPT-6 Astra and GPT-5.5 API pricing (not needed for subscription use, kept for completeness).
- Exact Z.ai tier of the user's account ($18 Lite vs a $20 legacy price) — check the dashboard.
- Actual quota multipliers of glm-5.3 family on the Coding Plan.
- Reasoning-level -> quota-consumption coefficients for Codex (only the qualitative
  "Max and Ultra consume faster" is published in the picker).
