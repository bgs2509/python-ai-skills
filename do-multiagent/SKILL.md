---
name: do-multiagent
description: >
  Team-lead orchestrator that runs a TEAM of subagents to execute work in parallel,
  each in its own git worktree, via `do-feature --auto-approve` per bead. Accepts EITHER
  free-form work / a draft (which it first decomposes into a bd dependency graph and asks
  you to approve) OR an existing bead queue. Before execution it analyses fork-points and
  uncertainties for every bead via `best-questions` and waits for your decisions. The
  controller owns the merge queue (serialised rebase+merge into master), owns all bd state
  writes, and independently re-verifies every branch before merging. Parallel only across
  beads with disjoint write-scope; beads touching shared files are grouped into one session.
  TRIGGER when: user wants a team of subagents to implement multiple beads / a whole body of
  work in parallel branches, OR explicitly invokes /do-multiagent.
  SKIP when: a single feature (use /do-feature), a sequential draft→chain build with context
  resets (use /do-autopilot), or a non-dev project.
argument-hint: "<free-text work | path-to-draft.md | bd-id ... | --ready> [--max-parallel N] [--resume <epic-slug>]"
role: orchestrator
---

# /do-multiagent — Team-Lead Orchestration of Subagents over a Bead Graph

> You play the **team lead**. Input: any work (free text / draft) OR an existing bead queue.
> Output: all beads implemented by a team of subagents working in parallel git worktrees,
> each branch verified and merged into master by you (the controller), branches deleted, bd closed.
> Cycle: decompose → [APPROVAL] → fork-analysis (best-questions) → waves of worktree subagents
> (each runs `do-feature --auto-approve`) → independent re-verify → serialised merge → reassess → repeat.

## 0. Scope and Boundaries

1. **Dev-projects only** (`project_type: dev`). Refuse in life-projects with a clear message.
2. **Orchestrator role** — MAY invoke `do-feature`, `best-questions`, `best-approach`. Sub-skills
   MUST NOT auto-transition; this skill drives the loop.
3. **Boundary vs siblings (do NOT duplicate):**
   - `do-feature` — ONE feature end-to-end. This skill calls it once per bead/group.
   - `do-autopilot` — a draft → **sequential** chain with `/clear` between chunks, unit = step-NN.
   - `do-multiagent` — any work → **bead dependency graph** → **parallel team** with git-worktree
     isolation and a controller-owned merge queue. Different execution model on purpose.
4. **Decomposition SSoT** — this skill owns its own decomposition logic but obeys the shared
   **Plan Sizing** rule in `~/.claude/CLAUDE.md`. It does NOT share code with `do-autopilot`
   (rule of three — extract a shared engine only once a third, identical consumer appears).
5. **Cross-reference key** — `bd_id` per bead, used in branch names, commit trailers, and notes.

## 1. Inputs

The skill auto-detects the input type:

1. **Free-form work** (prose describing what to build) or a **path to a draft** (`.md`/`.txt`/`.xml`)
   → triggers the **Decompose** stage (Stage 1) + USER APPROVAL.
2. **Existing beads** — one or more `bd-id`s, or `--ready` to pull the current `bd ready` set
   → skips Decompose, goes straight to fork-analysis (Stage 2).

Optional flags:
- `--max-parallel N` — cap on concurrent subagents (default: a small safe number, e.g. 3–4;
  never exceed what the host comfortably runs). Excess beads queue.
- `--resume <epic-slug>` — pick up an interrupted run from persisted state.

## 2. The Three Stages

```
Stage 1  DECOMPOSE      (only if input is work/draft, not beads)
         1.1  Cut the work into bd issues with explicit dependencies (bd dep)
         1.2  Estimate per-bead write-scope (files it will likely touch) — best-effort
         1.3  Build the grouping plan (see §3) and the wave plan (see §4)
         1.4  [USER APPROVAL] — present beads, deps, groups, waves; wait for your approval
Stage 2  FORK-ANALYSIS
         2.1  Upfront pass: for EVERY bead, surface fork-points & uncertainties
         2.2  Run /best-questions over them; record your decisions into bd notes
Stage 3  ORCHESTRATE (wave loop)
         For each wave W (beads/groups whose deps are all closed AND write-scope disjoint):
           3.1  reassess: any NEW fork revealed by closed beads? → targeted /best-questions
           3.2  dispatch one fresh subagent per bead/group, each in its own git worktree
           3.3  subagent runs `do-feature --auto-approve` per its bead(s); implements + commits in-branch
           3.4  subagent reports back (changed files, branch, in-branch verification) — bd-stateless
           3.5  controller INDEPENDENTLY re-verifies the branch (tests + lint + grace lint) — Trust=0%
           3.6  controller MERGE QUEUE: rebase branch on fresh master → re-test → merge → delete branch
           3.7  controller writes bd state (close / notes); persist run-state for --resume
           3.8  next wave
```

## 3. Decompose & Grouping Rules (Stage 1)

The grouping decision uses **three factors** (all must be respected):

1. **Dependencies** — independent beads MAY run in parallel; strictly dependent beads run in order.
2. **Window budget** — a chain of small dependent beads that together fit one context window
   MAY be assigned to ONE subagent to run sequentially (avoids worktree/spawn overhead).
   Split a group when scope > ~60% effective window (per Plan Sizing in `~/.claude/CLAUDE.md`).
3. **Shared write-scope** — beads predicted to modify the **same files** are grouped into ONE
   session (run sequentially by one agent), NOT split across parallel branches. This prevents
   cross-branch merge conflicts at the source.

A wave may run beads in parallel **only** when their write-scopes are **disjoint** (the
`grace-multiagent-execute` "disjoint write scope" principle, applied at decomposition time).

> **Heuristic, not a guarantee:** exact write-scope is unknown before implementation. Predict it
> best-effort from the bead description and likely files. If an overlap surfaces only during
> execution, fall back to the merge-conflict handling in §6. Log every grouping decision to bd notes.

USER APPROVAL (Stage 1.4) presents:
- the bead list with `bd_id`, title, type, `depends_on`
- the groups (which beads share an agent and why: dependency chain / window / shared files)
- the wave plan (which groups run in parallel, which are serial)
- decisions auto-applied vs decisions that need you (forks deferred to Stage 2)

## 4. Wave & Parallelism Rules (Stage 3)

1. Build waves from the `bd` dependency graph: a bead/group is wave-eligible when all its
   `depends_on` are closed.
2. Within a wave, run in parallel only disjoint-write-scope groups, capped by `--max-parallel`.
3. **Isolation:** each parallel subagent works in its own **git worktree** (dispatch via
   `Agent(isolation:"worktree")`, or an explicit `git worktree add <path> -b <branch>`).
   Branch name: `do-multiagent/<bd_id>` (or `<epic>/<bd_id>`). The worktree is removed after merge.
4. Each subagent is **fresh** (no session reuse across beads). Give it a compact packet:
   its bead(s), the approved fork-decisions relevant to it, its branch/worktree path, exact
   write-scope, and the success criteria (what "done" means + verification commands).
5. The subagent runs the inner `do-feature <bd_id> --auto-approve`. Its three USER APPROVAL gates
   (Discovery/Design/Plan) are auto-approved by `do-feature`'s own risk×evidence matrix; a
   `high`-risk bead still falls back to ask (surfaced up to you), and quality gates are never
   bypassed (`do-feature/SKILL.md` Flags section).

## 5. Approval Model

1. **Stage 1.4 decomposition gate — INTERACTIVE.** You approve the bead breakdown, groups, and
   waves before any execution. This is a mandatory USER APPROVAL gate (not auto-approved).
2. **Stage 2 fork-analysis — INTERACTIVE.** `best-questions` collects your decisions on every
   fork upfront; targeted follow-ups appear per wave on newly-revealed forks (§3.1).
3. **Per-bead `do-feature` gates — AUTO-APPROVED** via `--auto-approve`. High-risk beads fall back
   to ask through `do-feature`'s matrix. Your human control points are (1) and (2), not 3×N prompts.
4. **Quality gates are never auto-approved away** — tests, linters, `grace lint`, pre-commit, and
   the controller's independent re-verify (§7) all remain mandatory.

## 6. Merge Queue & Conflict Handling (controller-owned)

The controller is the **sole owner of master** and merges **one branch at a time**:

1. Take the next merge-ready branch (§7 passed).
2. **Rebase** it onto fresh master.
   - Clean auto-rebase → re-run the bead's quality gate (catch logical conflicts) → merge → delete branch.
   - **Real conflict** (git cannot resolve) → hand the branch + conflict diff to a **fresh subagent**
     in its worktree to resolve by hand → re-verify → return to the queue. NEVER use `-X ours/theirs`
     or any destructive auto-resolve (silent code loss is forbidden — `~/.claude/CLAUDE.md`).
3. **Bounded retry:** after 2–3 failed resolution attempts on the same branch → HALT that branch,
   invoke `/best-questions` with the conflict summary, persist state, and continue other waves if safe.
4. Merge commits use Conventional Commits + the bead's `bd_id` trailer.

## 7. "Ready-to-Merge" Gate (Trust = 0%)

A branch is merge-ready only when BOTH hold:

1. The inner `do-feature` reached **Finish** with **Step 12 Review** passed and its tests green.
2. The **controller independently re-runs** an objective gate **in the branch/worktree, before merge**:
   project tests + lint, plus `grace lint` if `docs/development-plan.xml` exists. The set is detected
   from the target repo at start; absent tools are skipped with a logged note.

The subagent's textual "done" is **never** sufficient — the controller runs the checks itself and
reads real exit codes (`~/.claude/CLAUDE.md` "Trust = 0%" rule; mirrors `do-autopilot` per-chunk verify).
A red branch never reaches master.

## 8. Bead State Ownership

1. **The controller is the only writer of `bd`** (claim / close / update / notes). This removes
   concurrent writes to the local Dolt DB entirely.
2. **Subagents are bd-stateless:** they implement code in their worktree and report back.
   Read-only `bd show` is allowed; any `bd` mutation by a subagent is forbidden.
3. Status drift resolves per the SSoT table in `~/.claude/CLAUDE.md` (Beads wins on status).

> Note (unverified): whether git worktrees share one `.beads/` Dolt DB or get a per-worktree copy
> was not confirmed. The single-writer design above is safe regardless — do not rely on a shared DB.

## 9. Failure Handling

1. **Inner `do-feature` blocks despite `--auto-approve`** (high-risk fallback, gate error) → surface
   the bead up to you; leave it `in_progress`; continue other independent waves if safe.
2. **Branch fails the ready-to-merge gate (§7)** → return it to the responsible subagent (or a fresh
   one) with the failing output; do NOT merge; do NOT advance that bead.
3. **Merge conflict unresolved after retries (§6.3)** → HALT branch + `/best-questions`.
4. **Reassess reveals a structural fork (§3.1)** → `/best-questions`, then continue.
5. **User aborts** → finish in-flight safe merges, leave other WIP branches/worktrees intact,
   persist run-state (current waves, epic_slug, target_repo, per-bead status) for `--resume`.

## 10. Outputs

1. All beads implemented, each via its own branch, merged into master by the controller; branches deleted.
2. Beads closed by the controller; `bd dolt push` allowed per session-close protocol.
3. Code merged on the local branch only — **never** `git push` automatically (`~/.claude/CLAUDE.md`).
4. Persisted run-state for `--resume`.
5. A short final report: beads done, waves run, merge order, conflicts handled, follow-ups filed.

## 11. Rules

1. **Always** get your approval of the decomposition (Stage 1.4) before any execution.
2. **Always** run `best-questions` over forks upfront (Stage 2) + reassess per wave.
3. **Parallel only across disjoint write-scope**; group shared-file beads into one session.
4. **Controller owns the merge queue and master** — serialised rebase+merge, one branch at a time.
5. **Controller is the sole `bd` writer**; subagents are bd-stateless.
6. **Trust = 0%** — independently re-verify every branch before merge; never trust a subagent's "done".
7. **Never** bypass quality gates, never destructive auto-resolve, never `git push` automatically.
8. **English** for code/commits/file names/bd content; **Russian** for user-facing prose.

## 12. Out of Scope (defer / reject)

1. Cross-repo orchestration — operates within a single project root.
2. Automatic deployment / release — stop at "merged on local branch".
3. Replacing `do-feature` — this skill is a caller, not a substitute.
4. Sequential draft→chain builds — that is `do-autopilot`.

## 13. Cross-References

- `~/.claude/CLAUDE.md` — Plan Sizing, USER APPROVAL Gates, Trust=0%, Git Push Policy, SSoT table.
- `~/.claude/skills/do-feature/SKILL.md` — the inner per-bead orchestrator (`--auto-approve`).
- `~/.claude/skills/do-autopilot/SKILL.md` — sibling: sequential draft→chain (boundary, §0.3).
- `~/.claude/skills/grace-multiagent-execute/SKILL.md` — controller/worker ownership + disjoint-scope model.
- `~/.claude/skills/best-questions/SKILL.md` — fork-analysis (Stage 2 + per-wave reassess).
