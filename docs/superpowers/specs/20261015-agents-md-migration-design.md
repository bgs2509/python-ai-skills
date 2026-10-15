---
feature: agents-md-migration
bd_id: python-ai-skills-lvt.2
date: 2026-10-15
status: draft
risk: high
risk_justification: 38 repositories get a rename commit of the file every Claude Code and Codex session loads first; four need a hand merge; commit-time hooks in six repos rewrite or lint markdown; the write side runs with per-command sandbox bypass in sibling repos, so a wrong command lands outside the project that owns this task.
approach: manifest-script
open_questions: []
context7_verified: []
context7_note: no external library is used; the script is Python 3 stdlib (`json`, `os`, `pathlib`, `subprocess`), the rest is `git`, `bd`, `pre-commit`, `codex` CLIs whose behaviour was probed in this session.
requirements: docs/superpowers/specs/20261015-agents-md-migration-discovery.md (FR-1..FR-8, NFR-1..NFR-4, groups A-G, resolutions 1-6)
---

# Design: AGENTS.md migration procedure (python-ai-skills-lvt.2)

Requirements, inventory and target layout are in the Discovery spec and are not restated here. This document decides HOW.

## 1. Approaches

### 1.1 hand-commands — per-project commands typed by the orchestrator, no script
Six to nine commands per repo (`git mv`, `ln -s`, merge edits, `git add`, `pre-commit run`, `git commit`, checks), each needing
its own sandbox bypass in a sibling repo: ~250 approvals for 38 dirs. Verification would be `cat`/eyeballing: it fails the brief's
"deterministic post-checks" and NFR-3 (no idempotent re-run). Smallest in code, largest in operator error surface. Rejected.

### 1.2 bash-loop — one shell script with a `for dir` loop and here-doc checks
Handles group A/E/G well (`git mv`, `ln -s`, `cmp`). The B/D merge (insert a section before a marker, insert a block after another,
a set-difference content check, JSON parsing of `codex debug prompt-input`) is where bash gets fragile (`sed` on multi-line blocks,
no set type, `jq` not guaranteed). Would end up shelling out to `python3 -c` for the hard parts: two languages for one tool. Rejected
on KISS (two mechanisms where one does) and CoC (the repo's helper scripts are Python with `python3 -I`, e.g. `claude-home/scripts/*.py`).

### 1.3 manifest-script (RECOMMENDED) — one Python stdlib script in `$TMPDIR` + a JSON manifest
One file, three commands (`plan`, `apply <dir>`, `check <dir>`), one manifest row per dir (group, flags). `apply` runs every write
and the commit for one repo in one process, so one sandbox-bypass approval per repo instead of six to nine. `check` is read-only and
re-runnable. Idempotent by construction: every step is guarded by the observed state (NFR-3). Throwaway (task level 5: not shipped,
not committed, no tests); its post-checks are the evidence, not its own claims. This is also the smallest change that meets FR-1..FR-8
with deterministic verification: it adds no files to any repo beyond the two the requirement names.

Trade-off accepted: a script that runs `git` via `subprocess` inside the sandbox needs bypass per invocation; the alternative
(standalone unsandboxed `git`) is impossible for sibling repos because `git -C` and `cd ... && git` are sandboxed (global CLAUDE.md, RTK section).

## 2. Recommended approach in detail

### 2.1 Tool shape and location
- `$TMPDIR/agents-md-migrate/migrate.py` (stdlib only, run as `python3 -I migrate.py ...`) and `manifest.json` next to it.
  `$TMPDIR` is `/tmp/claude-1000/...` on this machine and survives a session; if lost, regenerate from this section. Not committed:
  it is level-5 throwaway (deletion test: nothing in any repo depends on it).
- `manifest.json`: `{"<abs dir>": {"group": "A|B|C|D|E|G", "git": true|false, "oversize_ok": bool, "merged_file": "<path>|null"}}`
  — 38 rows from the Discovery table; `oversize_ok` true only for aidd-mvp-generator, ebooks, ML_CAREER_2026 (resolution 4).
- Commands:
  1. `plan [dir...]` — read-only. Prints per dir: current state (`fresh`, `partial`, `done`), the operations it would run, the merged
     file written to `$TMPDIR/agents-md-migrate/out/<name>/AGENTS.md` (B/D/C), its byte size vs 32768, the content check against that
     file, and the lines of the old AGENTS.md dropped by design (B/D). This is the `--dry-run`.
  2. `apply <dir>` — one repo: operations of its group (2.2) → `pre-commit run --files AGENTS.md CLAUDE.md` if `.pre-commit-config.yaml`
     exists (this also honours the gate in free-ai-selector and Prognosis, which have the config but no installed hook) → content check
     again (fixers may have rewritten the file) → `git add -- CLAUDE.md AGENTS.md` (never `-a`, never `-A .`: 2025_Noveo has four other
     dirty paths) → `git commit -m "docs(agents-md): make AGENTS.md the single instruction file"` → `check`. Exit non-zero on the first
     failed step; nothing is bypassed (`--no-verify` is forbidden by the Pre-commit Policy).
  3. `check <dir>` — read-only post-checks of 2.3; prints a one-line verdict per check; exit 1 on any failure.
- State detection (idempotency, NFR-3): `done` = `CLAUDE.md` is a symlink with target `AGENTS.md`, `AGENTS.md` is a regular file,
  `git status --porcelain -- CLAUDE.md AGENTS.md` is empty (2025_Noveo: ` M AGENTS.md` accepted) → `apply` prints `skip` and exits 0.
  `partial` = any mix (e.g. moved but not committed) → `apply` runs only the steps whose precondition still holds (rename only if
  `CLAUDE.md` is a regular file; symlink only if `CLAUDE.md` is absent; commit only if `git diff --cached --quiet` is non-zero).
- Preconditions checked before any write: `.git/index.lock` absent; HEAD is the inventory branch; `git status --porcelain -- CLAUDE.md
  AGENTS.md` empty (2025_Noveo: exactly ` M CLAUDE.md`); `.beads/` presence recorded for the bd check.

### 2.2 Per-group operations
- **A (21 repos)**: `git mv CLAUDE.md AGENTS.md` → `ln -s AGENTS.md CLAUDE.md` → add/commit. Expected `git show --format= --name-status
  -M HEAD`: `R100 CLAUDE.md AGENTS.md` and `A CLAUDE.md`. Content: `git show HEAD:AGENTS.md` byte-equal to `git show HEAD~1:CLAUDE.md`.
  2025_Noveo: the working-tree edit (+2/-2 in "Red/Green flags") follows the rename as an unstaged change of AGENTS.md and is not committed
  (resolution 5); `check` expects ` M AGENTS.md` there and nothing else for the two paths.
- **A, no git (my_funny_images)**: `mv CLAUDE.md AGENTS.md; ln -s AGENTS.md CLAUDE.md`; content check by `cmp` against a copy taken
  before the move (`$TMPDIR/agents-md-migrate/out/my_funny_images/CLAUDE.md.orig`). No commit, no hooks.
- **A, claude_bot.bak**: stays in A (acceptance criteria: every project; Discovery risk 9 says harmless). Committing into a backup
  copy is what the user approved by approving the inventory; no special handling.
- **B (6 pairs) and D (pilot)** — one assembly rule, applied to the text of CLAUDE.md:
  1. Locate `<!-- BEGIN BEADS INTEGRATION` … `<!-- END BEADS INTEGRATION -->` in CLAUDE.md (exactly one occurrence required; it is the
     block kept — hashes `6cd5cc61`/`970c3bf2` are bd's business, nothing in this task rewrites a block; `bd setup claude --check`
     answers `(current)` for the pilot today and will be re-asked after the merge).
  2. If CLAUDE.md has no line `## Non-Interactive Shell Commands` (true in all seven), insert the section of the old AGENTS.md from that
     heading up to the line before its `BEGIN BEADS INTEGRATION` marker (891 B in the pilot: `AGENTS.md:28-51`) immediately before the
     BEGIN marker, with exactly one blank line on each side.
  3. If the old AGENTS.md has a `BEADS CODEX SETUP` block (all but tg-video-downloader) and CLAUDE.md has none, insert it (pilot:
     `AGENTS.md:108-130`, 1250 B) right after the END BEADS INTEGRATION line, separated by one blank line. Adjacent blocks mirror the
     layout `bd setup codex` itself produces (verified in all six pairs), so bd's idempotent re-run stays on the path Q3 verified.
  4. Everything that followed the END marker in CLAUDE.md (pilot: hand-written sections; quickexambot lines 59-94; tg-video-downloader
     70-98) follows the CODEX block unchanged.
  5. Nothing else from the old AGENTS.md is carried: its title, `bd prime` pointer, architecture note, Quick Reference (incl. `bd dolt push`),
     its own INTEGRATION block and — in the pilot — line 3 "Repository rules live in `CLAUDE.md`" are dropped by design (Q2 decision).
     `plan` lists these dropped lines per repo so the user sees exactly what disappears.
  Then: write the merged text to `$TMPDIR/.../out/<name>/AGENTS.md`; in `apply`: `git rm -q --cached AGENTS.md` is NOT used — instead
  `git mv CLAUDE.md AGENTS.md` (so git records the rename of the larger file), overwrite `AGENTS.md` with the merged text, `ln -s
  AGENTS.md CLAUDE.md`, add/commit. Expected name-status: `R0xx CLAUDE.md AGENTS.md` (similarity below 100) and `A CLAUDE.md`.
  bd is not invoked as a mutator anywhere: the blocks are copied verbatim, so `bd init`/`bd setup codex` would change nothing (Q3), and
  not running them keeps the diff reviewable and the repos' `.agents/` untouched.
- **C (ai-generator-asyncmicroservices, Sinayara-Indonesia, VPS-VPN-Home-Server-Guide, ai-steward-wiki)**: the merged file is written by hand
  (orchestrator or a mid-tier subagent) into `out/<name>/AGENTS.md` with the rule "CLAUDE.md text first, then every section of the old
  AGENTS.md whose heading is absent from CLAUDE.md, verbatim"; `plan` runs the content check on it (union of both old files' non-blank lines
  must be a subset, dropped lines listed) and the user sees `git diff --no-index CLAUDE.md out/<name>/AGENTS.md` and the dropped-line list
  before `apply`. ai-steward-wiki differs: `git rm -q AGENTS.md` (the link to `docs/Spec-WIKI/CLAUDE.md`), `git mv CLAUDE.md AGENTS.md`,
  `ln -s AGENTS.md CLAUDE.md`; `docs/Spec-WIKI/CLAUDE.md` untouched (resolution 2); no merge, content byte-equal; still shown to the user.
- **E (taro_project_2026-04-01)**: `git rm -q AGENTS.md` (link → CLAUDE.md), `git mv CLAUDE.md AGENTS.md`, `ln -s AGENTS.md CLAUDE.md`,
  add/commit. Expected: AGENTS.md `T` (120000→100644), CLAUDE.md `T` (100644→120000); content byte-equal to `HEAD~1:CLAUDE.md`.
  Its commit runs `pytest-unit-fast`, `sentrux-check`, `marker-compliance` (slow; may fail for reasons unrelated to this change): run it
  last in its batch; a failure leaves the repo in `partial` state, which `apply` resumes after the cause is fixed.
- **G (bge-m3-api)**: `ln -s AGENTS.md CLAUDE.md`, `git add CLAUDE.md`, commit. Content check: `AGENTS.md` unchanged (`git diff --quiet HEAD -- AGENTS.md`).

### 2.3 Per-project verification (`check`, all deterministic, no eyeballing)
1. Layout: `os.path.islink(CLAUDE.md)` and `os.readlink(CLAUDE.md) == "AGENTS.md"`; `AGENTS.md` regular and not a link.
2. Content: A/E/G/wiki — `git show HEAD:AGENTS.md` byte-equal to the pre-move content (`HEAD~1:CLAUDE.md`, or the `.orig` copy for
   my_funny_images, or `HEAD~1:AGENTS.md` for bge-m3-api). B/D/C — the set of non-blank `rstrip()`ped lines of the old CLAUDE.md
   (`HEAD~1:CLAUDE.md`) is a subset of the new AGENTS.md; for B/D additionally the lines of the carried Non-Interactive section and
   CODEX block of `HEAD~1:AGENTS.md`; for C the lines of both old files minus the user-approved dropped list. Whitespace-only hook fixes
   (end-of-file-fixer, trailing-whitespace) therefore pass; any dropped text fails.
3. bd markers: count of `<!-- BEGIN BEADS INTEGRATION` == count of `<!-- END BEADS INTEGRATION -->` == 1 where the old files had one;
   `BEADS CODEX SETUP` BEGIN/END == 1 where carried, else 0. Then `bd setup claude --check` with `cwd=dir` (not `bd -C`: verified today
   that `-C` leaves the check on the caller's repo) must print `(current)`; skipped where `.beads/` is absent. `bd setup codex --check`
   is not used: verified today it fails on a missing `.agents/skills/beads/SKILL.md`, which says nothing about the block.
4. Size: `os.path.getsize(AGENTS.md) < 32768` unless `oversize_ok` (NFR-1). Local_LLM_selection expected 31876 B (resolution 3).
5. Git: `git ls-files -s -- CLAUDE.md AGENTS.md` shows `120000 … CLAUDE.md` and `100644 … AGENTS.md`; `git show --format= --name-status -M HEAD`
   touches only these two paths; `git status --porcelain -- CLAUDE.md AGENTS.md` empty (2025_Noveo: ` M AGENTS.md`); HEAD subject is the
   migration message (so `check` also proves the commit landed through the hooks — a hook failure leaves no commit).
6. Codex (NFR-4): `CODEX_HOME=$TMPDIR/codex-home` (contains only a symlink `AGENTS.md -> /home/bgs/.codex/AGENTS.md`; the "could not create
   PATH aliases" warning is harmless, verified today), `cwd=dir`, `codex debug prompt-input` → parse JSON, concatenate every `input_text`,
   assert the first and the last non-blank line of the project's AGENTS.md both occur (the last line proves no 32 KiB cut). Run on the pilot
   and on one dir per group: claude_bot (A), Local_LLM_selection (B, the largest), each C dir, taro_project_2026-04-01 (E), bge-m3-api (G).
7. Claude Code (NFR-4): no deterministic offline probe exists — verified today: `claude --help` offers none, and a `--debug-file` run logs
   plugin hooks but not the instruction files it loaded. Method: the user opens `claude` in the pilot and runs `/memory`; the list must show
   the project file and `~/ai-steward/Gena_Beeline_Local/CLAUDE.md` (profile still loads). Optional non-interactive variant, one Haiku call
   per sample (~30-50k input tokens each, needs network → sandbox bypass): `claude -p "Print verbatim the first heading line of the project
   instruction file you loaded, nothing else" --model haiku --max-turns 1 --permission-prompts none` must print the project's first heading.

### 2.4 Order and batching
1. Pilot python-ai-skills: `plan` → user sees the merged `out/python-ai-skills/AGENTS.md` size and dropped lines → `apply` → `check` →
   Codex check → user runs `/memory` → the pilot is the gate for everything after (bd note: gates 3/5/10 interactive).
2. Batch A (21 repos, one `apply` per repo, each its own bypass approval) + my_funny_images; then `check` over all.
3. Batch G + E (bge-m3-api, then taro_project_2026-04-01 last because of its slow hooks).
4. Batch B: `plan` on all six first (sizes, dropped lines, the `pre-commit run --files` dry run is part of `apply` only); `apply` one by one.
5. Group C: hand-merged files prepared, `plan` output and `git diff --no-index` presented per repo, `apply` only after the user's OK (FR-4).
6. python-ai-skills second commit: generator/doc edits + CHANGELOG (2.5); `claude-home/CLAUDE.md` edit by the user.
7. Final `check` over all 38 dirs → summary (38 lines, one per dir); bd: close lvt.2, add the three oversize A files to lvt.3.

### 2.5 Generator and layout-rule edits in python-ai-skills (resolution 6; every line verified by grep today)
1. `_init/SKILL.md:4` — "Creates CLAUDE.md, CHANGELOG.md," → "Creates AGENTS.md (plus a `CLAUDE.md -> AGENTS.md` symlink), CHANGELOG.md,".
   `:26` — "### 1. CLAUDE.md (in project root)" → "### 1. AGENTS.md (in project root) + `CLAUDE.md` symlink". After the code block
   (after `:42`) add: "Then `ln -s AGENTS.md CLAUDE.md`. Claude Code reads the file through the link (a `CLAUDE.md` above the project —
   the user profile — otherwise hides a bare `AGENTS.md`); Codex reads `AGENTS.md`. Edit `AGENTS.md`, never the link." No reference/templates exist in `_init/`.
2. `grace-init/SKILL.md:3` — "creates docs/ directory, AGENTS.md, and XML templates" → "creates docs/ directory, AGENTS.md with a
   `CLAUDE.md` symlink, and XML templates". `:15` table row target → "`AGENTS.md` (project root) + `CLAUDE.md -> AGENTS.md` symlink".
   After `:46` add bullet: "- Create the symlink `CLAUDE.md -> AGENTS.md` (`ln -s AGENTS.md CLAUDE.md`) when `CLAUDE.md` is absent; when a
   regular `CLAUDE.md` exists, stop and ask the user to merge it into `AGENTS.md` first." `assets/AGENTS.md.template` unchanged (content, not layout).
3. `claude-home/CLAUDE.md:31` — "in its root CLAUDE.md/AGENTS.md:" → "in its root `AGENTS.md` (the single real instruction file;
   `CLAUDE.md` is a symlink to it, `ln -s AGENTS.md CLAUDE.md`):". `:258` and `:270` stay (the profile remains `CLAUDE.md` per Q1; the
   "CLAUDE.md / AGENTS.md" phrasing there is still true). This file is write-protected in this session's sandbox: the user applies the
   one-line edit (or approves it in a session without that deny rule); the commit of 2.4 step 6 waits for it or lands without it, noted.
4. `git-finish/SKILL.md:93` — "- `CLAUDE.md` — skill catalog rows, grouped lists and **counters**." → "- `AGENTS.md` — skill catalog rows,
   grouped lists and **counters** (`CLAUDE.md` is a symlink to it; Edit refuses the link)."
5. Pilot's own merged AGENTS.md, hand-written note (`CLAUDE.md:195-199`): "outside the managed `BEADS INTEGRATION` block above: `bd setup
   claude` rewrites everything between its markers" → "outside the managed `BEADS INTEGRATION` and `BEADS CODEX SETUP` blocks above:
   `bd init` and `bd setup codex` rewrite everything between their markers (`bd setup claude` skips the `CLAUDE.md` symlink)". The content
   check treats this as the one edited line (expected, listed in `plan`).
6. `CHANGELOG.md` `## [Unreleased]` → `### Changed`: "Project instruction files: every project under `Gena_Beeline_Local` keeps one real
   `AGENTS.md` with `CLAUDE.md` as a symlink to it (bd `python-ai-skills-lvt.2`; Claude Code ≥ 2.1.277 reads `AGENTS.md`, Codex reads only
   it). Pilot here: `CLAUDE.md` content + the `Non-Interactive Shell Commands` section and the `BEADS CODEX SETUP` block from the old
   `AGENTS.md`, line-3 pointer dropped. Generators and rules now produce/describe that layout: `_init`, `grace-init` (symlink step),
   `claude-home/CLAUDE.md` Project Classification, `git-finish` doc list. Sinayara-Isuzu, Sinayara-Isuzu-web and three > 32 KiB files → lvt.3."
7. Not changed, by decision: `README.md:94` (global files), `docs/2026-03-15-skills-file-convention-architecture.md:300` (history),
   `claude-home/hooks/explanation-terms.py:134` (reads both names; harmless duplicate), `claude-home/hooks/test_principles_ssot.py`
   (`rglob("*.md")` will now visit `AGENTS.md` and the link with identical content — passes because `CLAUDE.md` passes today),
   `.pre-commit-config.yaml:38` (pattern names neither file). Hash drift of the bd block in five pairs: left to bd (Q3).

### 2.6 Rollback and resume
- Before any push (none is planned): `git reset --hard HEAD~1` in the repo restores both paths exactly — the commit touches only them and
  their tree was clean. 2025_Noveo first: `git diff -- AGENTS.md > $TMPDIR/noveo.patch`, reset, `sed 's#AGENTS.md#CLAUDE.md#g' … | git apply`.
  bge-m3-api: the reset removes the added link only. my_funny_images: `rm CLAUDE.md; mv AGENTS.md CLAUDE.md`.
- After a push (only on explicit request): `git revert --no-edit HEAD` — the revert of a rename plus symlink is a plain commit.
- Resume after partial failure: re-run `apply <dir>`; the state detection of 2.1 skips done repos and finishes partial ones. A hook failure
  leaves the repo `partial` with the merged file in place: fix the cause (never `--no-verify`), re-run `apply`.
- Group-level: `check` over all dirs prints `done/partial/fresh` per dir, so a second session can resume from the manifest alone.

### 2.7 Risks specific to the procedure
1. Concurrent sessions (4 claude/codex processes live): a session in a sibling repo running `git commit -a` could sweep our staged rename.
   Mitigation: `.git/index.lock` precondition, the two-path `git status` before and after, batches run when the user confirms no session is
   committing there; running sessions keep the old text in context, an `Edit` of `CLAUDE.md` there is refused and redirected (docs l.459) — no corruption path.
2. Markdown-rewriting or -linting hooks: end-of-file-fixer/trailing-whitespace (free-ai-selector, spark-public-bot, Prognosis) only change
   whitespace — the content check is whitespace-tolerant and runs after `pre-commit run`; markdownlint (free-ai-selector, config
   `.markdownlint.json`, no `--fix`) may fail on CLAUDE.md text that was never linted — fix the finding in `out/<name>/AGENTS.md`, re-plan;
   `vocab-check --staged` (Local_LLM_selection) sees a new file as all-changed lines and may object — the `apply` step surfaces it before the commit.
3. Symlink + Edit: after the move every `Edit`/`Write` of `CLAUDE.md` in any session is refused (docs l.459); 2.5 items 1-5 point the
   repo's own skills at `AGENTS.md`; pre-commit hooks receive `CLAUDE.md` as a filename and act on the link's target (same bytes, same result).
4. Windows clones would see a one-line text file (docs l.460); no non-Linux clone is known (Discovery risk 5); five repos already commit links.
5. `codex debug prompt-input` only proves what Codex loads; the three oversize A files stay truncated in Codex exactly as today (lvt.3).
6. The `claude -p` probe spends Anthropic quota (cost discipline): default to the user's `/memory` check; the probe is optional.
7. `bd -C` not retargeting `setup --check` and `bd setup codex --check` not checking the block (both verified today) would have given false
   verdicts; the script uses `cwd` and marker counts instead.

## 3. Merged-file assembly spec for the pilot (current files, 2026-10-15)

Sources: `CLAUDE.md` 240 lines / 16416 B (markers at 139 and 193, two blank lines 137-138, `**Version**: 3.7` at 136); `AGENTS.md`
130 lines / 6165 B (Non-Interactive 28-51, INTEGRATION 52-106 — identical bytes to CLAUDE.md 139-193, 2766 B each — CODEX 108-130).

| # | Segment | Source lines | Bytes | Note |
|---|---------|--------------|-------|------|
| 1 | Project body through `**Version**: 3.7` + one blank | `CLAUDE.md:1-137` | 10860 | unchanged |
| 2 | Non-Interactive Shell Commands section + trailing blank | `AGENTS.md:28-51` | 891 | carried (resolution 3) |
| 3 | BEADS INTEGRATION block | `CLAUDE.md:139-193` | 2766 | kept from CLAUDE.md (hash `970c3bf2`, same as AGENTS.md) |
| 4 | blank line | — | 1 | separator |
| 5 | BEADS CODEX SETUP block | `AGENTS.md:108-130` | 1250 | carried |
| 6 | blank line | — | 1 | separator |
| 7 | Hand-written note + sections | `CLAUDE.md:195-240` | 2788 | note at 195-199 reworded per 2.5 item 5 |

Expected size ≈ 18.6 KB (exact value printed by `plan`; well under 32768). Dropped by design from the old AGENTS.md: lines 1-27 (title, the
line-3 pointer, bd prime text, architecture note, Quick Reference incl. `bd dolt push`) and 52-106 (duplicate INTEGRATION block). `check`
expectations for the pilot: markers 1/1/1/1, `bd setup claude --check` → `(current)`, name-status `R0xx CLAUDE.md AGENTS.md` + `A CLAUDE.md`,
`git ls-files -s` modes 120000/100644, pre-commit hooks of this repo (gitleaks-staged, principles-ssot on `*.md`, …) pass on the commit.
