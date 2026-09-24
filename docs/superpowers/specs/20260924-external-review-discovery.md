---
feature: external-review
bd_id: python-ai-skills-xp4
date: 2026-09-24
status: approved
risk: medium
risk_justification: Three modules (do-feature SKILL.md/reference.md, model-registry.json + model-run.sh codex output, a new reviewer prompt template) and it reverses a documented routing rule (ADR-002); reversible, no data migration.
evidence: strong
evidence_justification: One measured comparison on range ddf0dc6^..d8f81aa (bd comment on python-ai-skills-xp4) plus a second Anthropic review baseline on python-ai-skills-a67; user requirement stated 2026-09-24.
open_questions: []
functional_requirements:
  - id: FR-1
    text: do-feature Step 12 code review is performed by a non-Anthropic model from the registry (GLM or GPT) via model-run.sh, not by an Anthropic Agent subagent.
  - id: FR-2
    text: The reviewer receives an exhaustive prompt from a versioned template in the repo that states inputs (commit range, discovery FR/NFR, design, plan), what to check, how to verify (read-only, repro outside the repo, HYPOTHESIS label) and a strict output format.
  - id: FR-3
    text: The review answer is checked by model-run.sh --expect on the verdict line; an answer without it is check_failed and the next reviewer model is tried.
  - id: FR-4
    text: When every external reviewer fails, an Anthropic model reviews as the last resort, and that fallback is logged as a routing exception.
  - id: FR-5
    text: The orchestrator verifies every finding (code reading or repro) before acting on it — Trust = 0% unchanged.
  - id: FR-6
    text: The reviewer cannot modify the working repository.
  - id: FR-7
    text: The routing change is recorded in an ADR that supersedes the Step 12 part of ADR-002, and SKILL.md (outward fork + matrix row) and reference.md (Step 12) state it consistently.
non_functional_requirements:
  - id: NFR-1
    text: A review delivered by a codex model is its final message only, not the full execution log (the comparison run produced 327 KB of log around a 3 KB report).
  - id: NFR-2
    text: make test stays green; new model-run.sh behaviour is covered by tests on the synthetic registry.
constraints:
  - Registry is the single home for which model serves the reviewer role (CLAUDE.md "choosing WHICH model").
  - "Planning and design steps stay on Anthropic (user requirement: plans by Anthropic, review by GLM/GPT)."
---

# Discovery: external code review in do-feature Step 12 (python-ai-skills-xp4)

User requirement (2026-09-24): plans are written by Anthropic models, the review is done by GLM or GPT, and the reviewer gets an exhaustive prompt explaining what to check and what result to return.

Measured (bd comment on python-ai-skills-xp4): same range, same 36-line prompt. Anthropic review 9 findings (~3 min). gpt-sol-xhigh 8/9 + 2 real defects the Anthropic review missed (verified), 558 s. glm-5.3-high 6/9, 533 s, missed three minors. Neither modified the worktree. codex stdout was a 327 KB log; the report sat at its end.

Current rules that change: `do-feature/SKILL.md:86` (review listed as Anthropic-only judgement), `:91` (Step 12 always inward), `:117` (matrix row: strong tier Agent), `do-feature/reference.md:284-323` (Step 12 dispatch), ADR-002 (evidence for strong-tier review).
