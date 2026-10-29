---
name: plan-progress-page
description: >
  Build and keep updated a one-page HTML progress view of a multi-stage project
  plan, published as a private claude.ai Artifact: a vertical bar where each stage's
  height is its share of plan hours, green = done, red = left, a big blue "now"
  arrow, percent and hour ticks with fact/forecast timestamps, a forecast finish,
  and every stage's sub-stages in a scrollable box beside its bar segment; above it a
  burn-up chart (done hours over calendar time, forecast to finish) and a Gantt chart
  (stages on the calendar against their plan-hour length). Works
  for any project (dev or life) and any number of stages. Plan start and actual
  hours come from Claude Code session logs via a bundled script, never from memory.
  TRIGGER when: user asks where they are in a big plan, wants "ход плана", "прогресс
  плана в процентах и часах", "страница прогресса", "сколько сделано и сколько
  осталось", "когда закончим", a progress page/chart/dashboard of a plan, release
  or epic, or asks to refresh such a page after a stage or sub-stage finished.
  SKIP when: watching a running process on an interval (use progress-watch),
  designing the plan itself (grace-plan, writing-plans), or a one-line status answer
  without a page.
argument-hint: "[plan path | epic id] [--update <artifact url>]"
---

# /plan-progress-page — proportional HTML progress page of a plan

> **Utility skill.** Builds or updates one page; does NOT auto-transition to other skills.
> The layout is fixed by `assets/template.html` — a copy of the owner-approved reference
> (Sinayara-Isuzu release 0, Artifact `UvmCnuPtSDU8C4ShuoGXha` v6, bd `python-ai-skills-29g`)
> plus two time views the owner chose on 2026-10-15 from three prototypes: burn-up and Gantt.
> You write only data (`plan.json`); `scripts/render.py` fills the template. Do not edit the
> template's CSS or JS for one project: every rule in it answers a correction by the owner
> (see "Owner corrections" below), and a local tweak silently reverts one of them.

Paths below are relative to this skill's directory (`~/.claude/skills/plan-progress-page/`).
One-off scripts go to `$TMPDIR`, run with `python3 -I`, and are not committed.

## 1. Collect the plan model — every number from a checked source

1. **Stages and plan hours** — the project's main plan document (e.g. its feasibility /
   estimate section). A stage the plan does not count as working hours (an unattended
   machine run) is still included, by the plan's limit or estimate, with a caveat in the
   footer. A stage with no estimate (typically "decision and planning") gets its **actual**
   working hours from the logs (step 3).
2. **Sub-stages** — task headings of the sub-plans (`grep -n '^### Task\|^## Задача'`),
   acceptance-section items. Group tasks (P1–P11) when a stage has more than ~15 and the
   plan already groups them.
3. **Plan start and actual hours** — `scripts/session_hours.py`, never the owner's memory:
   ```bash
   python3 -I scripts/session_hours.py start --project <workdir> \
     --pattern '<plan keywords, e.g. Р-45|выпуск|release>' --since "<YYYY-MM-DD HH:MM>" --top 5
   python3 -I scripts/session_hours.py hours --project <workdir> \
     --from "<YYYY-MM-DD HH:MM>" --to "<YYYY-MM-DD HH:MM>"
   ```
   `start` lists the earliest matching prompts — read them and pick the one that actually
   opens the plan (pasted text can match a keyword by accident). Cross-check with the first
   plan commit (`git log --reverse --grep=<keyword>`) and the epic's `created_at`
   (`bd show <epic> --json`). If the logs disagree with what the owner said ("вчера утром"
   vs a first prompt at 18:26), use the log time and say so in the reply and in the footer.
   `hours` sums gaps ≤ 10 min between consecutive records of all top-level sessions of the
   project and its worktrees. Reference check: Sinayara-Isuzu 2026-10-14 18:26 → 2026-10-15
   15:51 gives 9.62 h (reference page: 9.6 h).
4. **States** — tracker (`bd show`), execution ledger, `git log`, test/gate output.
   A running stage's `done` = share of its sub-stages × hours (3 of 6 sub-stages plus half
   of a measurement → 0.5 h of 1.0 h).
5. **Nothing confidential** on the page (third-party data maps, personal data): stage
   names, numbers, project paths and ids only.

## 2. Forecast future stages

1. Code stages — at the pace of an already finished stage of the same kind:
   factor = actual / plan (reference: 2.0 h instead of 5.3 h → 0.38) × plan hours.
2. Machine runs, waiting and acceptance stages — plan duration, no factor.
3. Owner's working window (reference 10:00–23:00); a stage that does not fit by the end
   of the window continues at the window start next day.
4. Parallel stages (next stage coded during a machine run; a second stream in another
   session) get their own starts; plan finish = max of ends.
5. Write the assumptions (pace, window, owner's "yes" without delay, machine-run limit and
   the alternative estimate with its shift of the finish) into the footer paragraph «Прогноз».

## 3. Write `plan.json`

Keep it next to the page in `$TMPDIR` (e.g. `$TMPDIR/<plan-slug>-progress.json`).
`assets/example-plan.json` is a complete 4-stage example — copy it and replace values.

```json
{
  "title": "Ход <имя плана>",
  "updated": "ДД.ММ.ГГГГ ЧЧ:ММ по <город>",
  "start": "ДД.ММ ЧЧ:ММ",
  "finish": "ДД.ММ ЧЧ:ММ",
  "ann_label": "разметка",
  "ann_summary": "отрезок самой разметки",
  "work_window": [10, 23],
  "meta": [["Проект", "<имя — назначение (project_type: dev)>"], ["Рабочий каталог", "<code>…</code>"],
           ["Репозиторий", "адрес, ветка, коммит"], ["План", "решение/эпик, путь главного плана"],
           ["Цель", "одной строкой, с числами"], ["Машины", "где что исполняется"],
           ["Владелец", "имя; часовой пояс …"]],
  "foot": ["<b>Как читать.</b> …", "<b>Время</b> — …", "<b>Начало плана</b> — …",
           "<b>Часы этапов.</b> …", "<b>Прогноз.</b> …"],
  "stages": [
    {"name": "…", "hours": 9.6, "done": 9.6, "state": "done", "start": "14.10 18:26",
     "end": "15.10 15:51", "fact": true, "ann": false, "detail": "…",
     "subs": [["d", "…"], ["r", "…"], ["w", "…"]]}
  ]
}
```

Field rules (`render.py` enforces each one and refuses to write the page otherwise):

1. `state` — `done` | `run` | `wait`, in that order down the list; exactly one `run`
   (none only when every stage is done) — the arrow must land inside it.
2. `done` — `done` stage: = `hours`; `wait`: 0; `run`: between.
3. `fact` — true only for `done` stages with both times from logs/commands; the `run`
   stage is shown as "начало факт, конец прогноз" automatically.
4. `ann` — optional "key segment" flag on contiguous stages; they get the mark
   «· <ann_label>» and a summary item with their percent range, captioned by `ann_summary`
   (optional; default «отрезок «<ann_label>»»). Drop `ann_label`, `ann_summary` and every
   `ann` when the plan has no such segment.
5. `meta` values and `foot` paragraphs are inserted as HTML (use `<code>`, `<b>`); every
   other string is escaped.
6. Every number with a unit; every percent is of the whole plan (= total hours).
   The footer «Как читать» states the scale rule, not a number: the page picks one scale for the whole bar.
7. `updated` starts with «ДД.ММ.ГГГГ ЧЧ:ММ»: the page takes the year of every other
   timestamp from it, and its time is the «сейчас» line on both time views.
8. `work_window` — the owner's working hours `[start, end]` (default `[10, 23]`); the hours
   outside it are shaded on both time views. Every stage's `end` is not earlier than its `start`.
9. One scale for the whole bar: at least 40 px per hour (34 px on a phone), raised until every
   row fits its left tick and its header (name, status, time), at most 200 px per hour (150 px on
   a phone). Heights stay proportional to hours. A stage shorter than about 0.2 h still gets a
   cramped row (the text inside scrolls), so merge such stages into a neighbour and list them
   as sub-stages; sub-stages and the detail line scroll inside a short row or open in the stage dialog.

## 4. Render, check, publish

```bash
python3 -I scripts/render.py "$TMPDIR/<slug>-progress.json" "$TMPDIR/<slug>-progress.html"
```

Before the first publish, open the page once in a browser at 400 px width and in both
themes (template guarantees it; a broken `meta`/`foot` HTML can still break it).

**First publish** — Artifact tool with `file_path` = the HTML, `icon: "chart"`, a one-sentence
`description`. Tell the owner the link is private: only they can open it until they share it.

**Every update** (after each finished stage or sub-stage) — edit only `updated`, the stage
fields (`done`, `state`, `end`, `fact`, `detail`, `subs`) and `finish` in the JSON, re-render
to the **same** HTML path, publish the same `file_path` again without `icon`, with a short
`label` (what changed). Sizes and colors are never touched.

After publishing, one line to the owner: link, what changed, «сделано X% / осталось Y%»,
forecast finish.

## Owner corrections baked into the template (do not undo)

1. v1 → v2: one bar with % and hour ticks per stage; green done, red left.
2. v2: timestamps (fact from logs, forecast for the rest) and a forecast finish; plan start
   from session logs, not from memory.
3. v3 → v4: each stage description is exactly the height of its bar segment — no leader lines.
4. v4 → v5: a big blue arrow left of the bar instead of a dashed line; every stage shows its
   sub-stages; overflow scrolls inside the box with a thin status-colored scrollbar.
5. v6: header with project, workdir, repository/branch/commit, plan, goal, machines, owner.
6. 2026-10-15: between the summary and the bar, two time views (owner picked "both" of three
   prototypes): **burn-up** — x = calendar time, y = plan hours; green line = done hours
   (0 at `start`, +hours at each done stage's `end`, the running stage's `done` at `updated`),
   red dashed line = forecast (+remaining hours at each other stage's `end`), black line =
   plan scope, blue line = now; **Gantt** — one row per stage from `start` to `end` (green fact,
   blue running with its done share, red hatched forecast) and a grey line under it of the
   stage's plan hours from its start (shorter bar = faster than plan). Both are computed from
   the stage fields; no extra data. Stage-end markers closer than 16 px merge into one «1,2».
7. 2026-10-15: a click on a burn-up marker, on a stage name in the Gantt, or on a stage name
   in the bar opens a dialog with that stage's full description (a merged marker «1,2» shows
   both stages); Esc, × or a click outside closes it. The bar got the heading «Столбец этапов:
   доли часов плана» — the owner called it a sidebar, but a sidebar is a side navigation
   panel; the block is a vertical stacked bar chart with a label beside each segment.
8. 2026-10-29: the scale of the bar is no longer a fixed 40 px per hour. One measured scale for
   the whole bar (see rule 9 above) keeps the bar proportional and keeps every row's header
   readable in plans with stages shorter than 1 h. A broken axis and a nonlinear scale were
   dropped (they break proportion); a separate text column with connector lines was offered
   and not chosen.
