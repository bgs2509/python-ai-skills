# Planning

> Format and rules for creating plans. Applies both in the documentation pipeline (stage 2) and for standalone planning (research, estimation).

---

## When a Plan Enters the Pipeline

If Claude created a plan file for a backlog task — this is the planning stage of the pipeline. The plan is saved in `docs/plans/` of the target project.

Plans outside the pipeline (research, "do or don't" estimation) are not saved in `docs/plans/`.

---

## Storage

| Rule | Description |
|------|-------------|
| Storage | `docs/plans/` in the target project repository |
| Naming | `PLAN-NNN-{short-name}.md` |
| Numbering | PLAN-001, PLAN-002, ... — sequential |
| Task link | Mandatory field `Task: TASK-NNN` |
| Language | Russian (stage descriptions, questions, answers) |

---

## Plan File Format

> **CRITICAL RULE**: This instruction is MANDATORY for EVERY plan. Violation = rewriting the plan from scratch.

### Structure (STRICTLY in this order)

**1. Context** (3-5 sentences)
- What we are doing, why, what problem we are solving

**2. Table of Contents** (outline)
- Numbered list of all plan stages (names only)

**3. Brief version of the plan**
- For each stage: 6 questions (answer to each — 1-2 sentences in plain language)
- No code and no implementation details (line numbers, function signatures, design patterns)
- MUST mention specific names: services, files, parameters, directories — so it is clear WHAT is being discussed
- Goal: understand WHAT each stage does in 30 seconds of reading

Mandatory questions for each stage:

1. **Problem** — What problem does it solve?
2. **Action** — What does it do?
3. **Result** — What result do we get?
4. **Dependencies** — What does it depend on? (which stages come before this one)
5. **Risks** — What new problems does it create?
6. **Without this** — What breaks if this stage is skipped?

**4. Full version of the plan**
- Detailed description with files, code, technical details
- Each stage starts with a heading `## Stage N: Name`

---

## Prohibitions

- Prohibited: writing a plan without a table of contents and brief version
- Prohibited: mixing the brief and full versions
- Prohibited: starting the full version without the brief version before it
- Prohibited: editing the plan file if the user asked for a verbal explanation — respond with TEXT IN CHAT

---

## User Interaction in Planning Mode

- If the user asks "explain", "tell me", "describe" — respond with TEXT IN CHAT, DO NOT edit the plan file
- Edit the plan file ONLY if the user explicitly asks "change the plan", "add to the plan", "rewrite the plan"
