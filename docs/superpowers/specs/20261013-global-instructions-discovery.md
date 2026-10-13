---
feature: global-instructions
bd_id: python-ai-skills-8of.3
date: 2026-10-13
status: awaiting-approval
risk: high
risk_justification: claude-home/CLAUDE.md is loaded into every session of every project and is ~/.codex/AGENTS.md for Codex; changing it changes agent behaviour everywhere at once.
evidence: strong
evidence_justification: /context breakdown (global CLAUDE.md 16.4k of ~43k tokens of a fresh session); section sizes measured; arXiv 2602.11988 abstract (context files add >20 % cost without raising success); code.claude.com/docs/en/memory ("target under 200 lines", imports do not reduce cost, path-scoped rules).
open_questions:
  - Approve the cut list below, or name sections to keep as they are.
  - Explanation Protocol (2.6k tokens) - move only the worked examples, or leave the section untouched.
functional_requirements:
  - id: FR-1
    text: Global CLAUDE.md keeps every rule that must hold in every session (language, output format, anti-hallucination, explanation rules, security rules, push policy, pre-commit gate, trust-0 verification) and points to where moved rules live.
  - id: FR-2
    text: Dev-workflow rules (GRACE, approval gates, plan sizing, documentation SSoT table, semantic markup, logging convention, modification rules) live in do-feature (or its reference) and in CLAUDE-APPENDIX.md, reachable through one pointer.
  - id: FR-3
    text: Model Routing shrinks to the pool order, "use model-run.sh --role", "registry is the single home", and Trust = 0 %; the rest is already in model-registry.json and the launch hook.
  - id: FR-4
    text: Multi-machine consistency moves to python-ai-skills/CLAUDE.md (needed only when editing this config repo).
non_functional_requirements:
  - id: NFR-1
    text: Global CLAUDE.md at most ~9k tokens (from 16.4k), measured with /context.
  - id: NFR-2
    text: Behaviour check before and after on a fixed task set (claude -p, same prompts) - no regression on the rules that stay; Codex reads the same file.
constraints:
  - Hooks already enforce part of the text (anti-hallucination.sh, explanation-terms.sh, block-no-verify.sh, delegation-pool-nudge.sh); the text for those can shrink to the rule plus a pointer.
---

# Discovery: global instructions (python-ai-skills-8of.3, plan items 2a-2c)

## Measured

`claude -p "/context"` in this repo, 2026-10-13: memory files 24.8k tokens of ~43k before the first
message; the global `CLAUDE.md` alone 16.4k (40.9k chars, 453 lines; official target < 200 lines).
It is re-read on every request of every session: ~50k requests per 35 days.

## Section sizes (tokens ≈ chars × 16.4k / 40.9k)

| Section | ~tokens | Proposal | ~saved |
|---|---|---|---|
| Explanation Protocol | 2,574 | user decision; at least move "Разобранные примеры" to the appendix | 0-400 |
| Model Routing | 2,470 | keep pool order, `model-run.sh --role`, registry as home, Trust = 0 % | 1,900 |
| Security | 1,170 | keep rules; move "Scope of the read-side gate (honest limits)" to appendix | 500 |
| Preferences | 878 | keep; move rationale-style lines | 300 |
| Anti-Hallucination | 837 | keep (hook-backed) | 0 |
| Pre-commit Policy | 754 | keep 3 rules; template-hook mechanics to appendix | 400 |
| Multi-machine consistency | 753 | move to python-ai-skills/CLAUDE.md | 700 |
| GRACE Core Principles | 751 | move (do-feature / appendix) | 700 |
| Documentation SSoT | 722 | move | 700 |
| Plan Sizing | 692 | move | 650 |
| First-Contact Protocol | 684 | keep | 0 |
| Git Push Policy | 606 | keep | 0 |
| USER APPROVAL Gates | 480 | move (do-feature already states them) | 450 |
| Output Formatting | 437 | keep | 0 |
| other dev-only (Workflow Hierarchy, Logging, Rules for Modifications, Semantic Markup, File Structure) | 740 | move, one pointer | 650 |
| rest | ~1,900 | keep | 0 |
| **Total** | **16.4k** | | **≈ 7,000-7,400** |

## Expected effect

- Tokens: ≈ 7k fewer per request → ≈ 350 M cache-read tokens and ≈ 13 M cache-write tokens per 35 days
  (≈ 2-3 % of API-equivalent spend), before the indirect effect arXiv 2602.11988 reports (instructions
  are followed, so each rule adds steps).
- Quality risk: a moved rule is applied only when the pointer leads the agent to it. Mitigation: dev
  rules move into `do-feature`, which every dev change already goes through; A/B check per NFR-2.
- Codex: the same file is `~/.codex/AGENTS.md`; Codex does not run `do-feature` hooks, so dev-only
  rules for Codex sessions would be reachable only through the pointer.
