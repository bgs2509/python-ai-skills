---
feature: subagent-models
bd_id: python-ai-skills-8of.4
date: 2026-10-13
status: approved
risk: medium
risk_justification: Three files of behaviour (settings.json.template env, model-registry.json, delegation-pool-nudge.sh) plus do-feature SKILL.md text; additive, reversible, no breaking API, no security surface.
evidence: strong
evidence_justification: Measured in this session - 126 subagent launches classified (plan §3d), Haiku 5.5 vs Sonnet 5.5 A/B 4/4 (plan §1.8), env-var experiment (general-purpose obeys CLAUDE_CODE_SUBAGENT_MODEL, Explore inherits the session model), alias haiku resolves to claude-haiku-5-5, Haiku 5.5 window 1M verified on platform.claude.com models overview; user decisions on Fable and review recorded in the plan.
open_questions: []
functional_requirements:
  - id: FR-1
    text: settings.json.template sets env CLAUDE_CODE_SUBAGENT_MODEL to sonnet (without the _FORCE variant), so subagents launched without a model run on Sonnet instead of the session model.
  - id: FR-2
    text: model-registry.json holds the single mapping from work type to a tier or role for Agent-tool launches (agent_work_types) - discovery/architecture/plan audits to top, read-only exploration and mechanical edits to cheap, writing code and docs to mid, code review to role reviewer, web research to role researcher.
  - id: FR-3
    text: delegation-pool-nudge.sh adds a model hint when an Agent launch carries no model - it renders the work-type mapping from the registry (tier resolved to the model alias), and for subagent_type Explore states that it inherits the session model; silent for fork launches and when a model is given.
  - id: FR-4
    text: The existing bulk-work nudge keeps its behaviour; both hints can appear in one additionalContext.
  - id: FR-5
    text: Registry entry haiku reflects Haiku 5.5 - 1M context, long-prompt price tier above 100k tokens, A/B evidence; do-feature window warning no longer claims a 200K cheap tier.
non_functional_requirements:
  - id: NFR-1
    text: Hook stays advisory - exit 0 always, malformed input or missing/broken registry degrades to the previous behaviour, never blocks a launch.
  - id: NFR-2
    text: No model names are restated in the hook - they come from the registry at run time (CLAUDE.md "choosing WHICH model").
  - id: NFR-3
    text: make test green; registry stays valid JSON consumed by model-run.sh unchanged.
constraints:
  - A custom read-only guard hook (plan 3c) is not built - Explore already lacks Edit/Write; decision recorded in the plan.
---

# Discovery: subagent model routing (python-ai-skills-8of.4)

Step 3 of `docs/research/skills-revision-plan-2026-10.md` (3a, 3b, 3c; 3d done in the plan).

Facts measured in this session:

1. 91 of 126 subagent launches from main sessions happened outside any skill, so a rule inside
   skills cannot reach them; a PreToolUse hook on the launch can (it fires: its text appears 213
   times in 27 transcripts; matcher `Task` is an alias of the `Agent` tool in Claude Code 2.1.296).
2. `CLAUDE_CODE_SUBAGENT_MODEL=haiku` moved a `general-purpose` subagent to `claude-haiku-5-5`,
   while an `Explore` subagent in the same run stayed on the session model (`claude-sonnet-5-5`).
3. `do-feature` already routes by tier through the registry `tiers` block: top = fable-medium,
   mid = sonnet-low, cheap = haiku; Step 12 review already goes to the `reviewer` role. The
   user's mapping (Fable for discovery/architecture, GPT `gpt-5.6-sol` xhigh for review, Haiku
   for reading, Sonnet for code) is therefore already true inside `do-feature`.
4. The alias `haiku` now resolves to `claude-haiku-5-5` (1M context, 128K output), but the
   registry entry and `do-feature/SKILL.md:95,126` still describe a 200K window.
