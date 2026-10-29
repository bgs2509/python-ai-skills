# Extensions of /vacancy-intake — run only when the user asks

Every extension uses facts that the owner's legends confirm. A fact absent from the legends is a question to the owner, never a claim.

## 1. Pitch

1. Language: English. Two lengths: 30 seconds (about 75 words at 150 words per minute — the speed assumed in the project's voice texts, not measured) and 2 minutes.
2. Short sentences that are easy to say aloud.
3. Keywords: as many exact words from the vacancy as the legends confirm.
4. Metrics: **business** metrics (cost, availability, quality of answers), not engineering metrics. Numbers only from the owner's legends.
5. Training or fine-tuning of models: before writing, ask where and when it happened; the legend section that holds the answer is the only source.

## 2. Questions for the recruiter's call

Questions the recruiter will ask the owner, built from the gaps in `02_tech_fit.md`, with a short legend-based answer for each. Questions about conditions are kept for after interest is confirmed.

## 3. Outreach draft (`04_outreach_draft.md`)

Sells technical skills. No questions about format, location, contract type or pay (`AGENTS.md`, «Условия работы — предмет переговоров»). Before sending, `contacts_log.md` is checked again.

## 4. Salary range

Give a range with the reason for the minimum and the maximum: market, region of the employer, contract type (B2B or employment), seniority. Mark it as an estimate; name the sources and the search date. Both ends are also written in euro per month at 40 hours a week and 4 weeks a month (160 hours), by the rules of `SKILL.md`, «Conversions inside the vacancy description».

## 5. Company research

Patents, scientific results, technologies, conference talks, key people, products. Each item: a source and the date of the search. Quotes verbatim with the article they came from. Without logging in to LinkedIn. Web research may go through `~/.claude/scripts/model-run.sh --role researcher`; the result is checked by a command before it is reported (global `CLAUDE.md`, Model Routing).

## 6. Hidden client hypothesis

When the client is not named: list the clues (offices, stack, wording, recruiter's other posts) and a candidate. Mark it «гипотеза, не опознание»; a hypothesis is never used in the stop-list check, the answer or the report as a fact.

## 7. Technology-to-project hypotheses

When the owner confirms a technology but not the project: list the legend projects where it most plausibly fits, with the reasoning. Mark it as a hypothesis; the result goes into the legend only after the owner's confirmation.

## 8. Test task

First state the assumption about what the client does, what services it has and what problems it may have; then a task that matches the vacancy and shows the owner's confirmed experience. Mark every assumption.
