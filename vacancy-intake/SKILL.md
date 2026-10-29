---
name: vacancy-intake
description: >
  Analyse one incoming job offer for the ML_CAREER_2026 project: split the pasted recruiter
  message from the vacancy text, compare the vacancy with every vacancy already in the project
  (duplicate alarm, stops on a match), check the stop-list, then write the four-file analysis
  folder with a technical-fit verdict against the owner's legends.
  TRIGGER when: the session is in ML_CAREER_2026 and the user pastes a recruiter message or a
  vacancy text, gives a path to a vacancy .pdf/.docx or a vacancy URL, or says "new vacancy" /
  "новая вакансия" / "новое предложение".
  SKIP when: the work is about legends, résumé or LinkedIn profile text, outgoing search for
  companies, or a vacancy that is already analysed and only needs a pitch (use the extension
  list in reference.md directly).
---

# /vacancy-intake — incoming job offer analysis (ML_CAREER_2026)

> Executes the procedure that used to live in the project `AGENTS.md`, section «Порядок разбора входящего предложения». The project `AGENTS.md` keeps a pointer to this skill and the cross-cutting rules (stop-list, «условия работы — предмет переговоров», reconnaissance rules); read them there, do not copy them here.
> Output documents are in Russian (project language); this file is in English (repository rule).

## Preconditions

1. `docs/owners/` exists in the working directory. If not, stop: this is not ML_CAREER_2026.
2. **Owner of the profile:** default `docs/owners/2026-10-budov/`. The archive owner (`2026-08-gennady-archive`) only when the user says so. Facts of one owner's legends never confirm the other's (`AGENTS.md`, «Несколько владельцев профилей»).

## Procedure

### 1. Split the pasted text

Separate: recruiter message / vacancy text / the owner's own reply / **restatement of the owner's profile**. A letter that lists the owner's own projects and numbers back to them (gateway failover, token cost, retrieval metrics) is the recruiter's flattery, often machine-generated from the profile: mark it «пересказ профиля, не требования вакансии» and never extract requirements from it.

If only the letter exists, get the full text: the vacancy URL, a `.pdf` (`pdftotext -layout`), a `.docx`. Do not log in to LinkedIn and do not construct profile addresses (`docs/shared/linkedin_guide/07_people_search_safety.md`). Text unavailable → say so and ask.

### 2. Duplicate alarm — before anything is written

1. Take keys from the new vacancy: client or company, recruiter name, platform, vacancy URL or ID, 3–5 distinctive requirement phrases.
2. Search **all** owners, not only the current one:
   `grep -r -i -l --include='01_vacancy.md' --include='03_recruiter_contact.md' -e "<key1>" -e "<key2>" docs/owners/*/job_search/inbound_offers`
   and the same keys over `docs/shared/contacts_log.md docs/shared/recruiter_keywords.md` (`grep` exit 1 means no match, not an error; plain `grep` because `rg` exists only as a Claude Code shell function). Read only the files `grep` returned. A hit that only mentions the key in passing (another vacancy naming the same company) is still reported: the user decides.
3. **Any match on client, recruiter, URL or ID, or on at least half of the requirement phrases is an alarm**, including a match in another owner's folder (the same vacancy or the same recruiter reaching two similar profiles — the very case `contacts_log.md` exists for).
4. On an alarm, print this block first and **stop**:
   - `ТРЕВОГА: возможный дубликат`;
   - for each match: the file path, the keys that matched, same owner or other owner;
   - what is identical and what differs (vacancy text, recruiter, client, date).
   Create no folder, add no row to `contacts_log.md`, draft no reply. Continue only after the user says to.
5. No match → write «Совпадений нет (проверено <дата>, <N> файлов)» in `00_report.md`.

### 3. Stop-list and contact log

The stop-list is the only filter that can close a vacancy at once (`AGENTS.md`, «Стоп-лист»). Check the client, the recruiter's employer and `docs/shared/contacts_log.md`. Client not named → write «заказчик не назван, проверить нельзя».

### 4. Folder

`docs/owners/<owner>/job_search/inbound_offers/ГГГГММДД_Компания-Площадка_Роль/`, date = today. Use the names that appear in the text; never invent a client. Files and skeletons — `template.md`:

1. `00_report.md` — summary and the **verdict on technical fit**;
2. `01_vacancy.md` — the vacancy verbatim with sources, then the conditions section «справочно, на вердикт не влияет»;
3. `02_tech_fit.md` — line-by-line check of the vacancy requirements against the owner's legends; **the ground of the verdict**;
4. `03_recruiter_contact.md` — recruiter and the verbatim message;
5. `profile_company.md` — only when the client is known;
6. `04_outreach_draft.md` — only on request: it sells skills and contains no questions about conditions.

Folder already exists for this vacancy (the user confirmed after an alarm) → update the files, do not create a second folder.

### 5. `02_tech_fit.md`

1. Check every requirement and duty against `docs/owners/<owner>/legends/` only. Each confirmation names the file and the section number. Labels: **прямое / частично / пробел / превышение уровня**.
2. A requirement without proof is a gap, never counted as a match.
3. Add the list «заявлять нельзя»: skills the legends exclude or confirm only partly (read the legend's own notes; example: a framework the owner used only through its adapters).
4. Gaps are recorded where found: a new subsection of section 7 of `docs/owners/<owner>/derived/gaps_to_close.md`; a repeated gap is a reference to the earlier subsection.
5. Never edit a legend. A new fact enters a legend only from the owner's own words.

### 6. Verdict

By technical fit only. Format, location, contract type and pay go to the reference section and **never** change the verdict. Forbidden wording: «отброс по формату», «релокация не рассматривается». The reply to the recruiter has no questions about conditions.

### 7. Answer to the user (Russian, in this order)

1. Duplicate check result.
2. Conditions: location, pay, contract type, visa, time zone.
3. Client and recruiting company: size, place, main services.
4. The work itself.
5. Unusual requirements and non-standard terms.
6. Verdict and questions to the owner (before any reply to the recruiter).

What the text does not state is «не названо». Every inference is marked «вывод, не факт из текста».

### 8. Records and commit

1. Row in `docs/shared/contacts_log.md`, the same day.
2. Row in the owner's index `docs/owners/<owner>/job_search/inbound_offers/README.md` when it exists (folder, date, recruiter, role, verdict).
3. Keywords: append the vacancy to `docs/shared/recruiter_keywords.md` by the rule written in that file.
4. Check by command, not by reading: the four files exist; every legend section cited in `02_tech_fit.md` exists (`grep` for the heading).
5. Commit, message `docs(budov-inbound): add <Company> <Role> analysis, contact log row and gaps` (the pattern of the last commits of the project). **No `git push`.** Do not skip pre-commit hooks.

## Extensions — only on request

Pitch (30 seconds and 2 minutes), questions for the recruiter's call, outreach draft, salary range, company research, hidden client hypothesis, technology-to-project hypotheses, test task → `reference.md`.

## Rules

1. Evidence: every statement about the owner cites a legend file and section; about the vacancy — a quote; about a company — a source and the date of the search.
2. A result from a subagent or another model pool is checked with a command before it is reported.
3. Terminology: a role is always named with the entity («рекрутёр Shaik Ahmed, площадка TechTree»); one phenomenon — one designation.
4. Writes stay inside `ML_CAREER_2026/docs/`.
