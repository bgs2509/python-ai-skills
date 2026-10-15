---
feature: agents-md-migration
bd_id: python-ai-skills-lvt.2
date: 2026-10-15
status: approved
risk: high
risk_justification: 38 repositories change the file every Claude Code and Codex session loads first; the change is a git rename plus a committed symlink per repo, three repos need a hand merge, and two tools (Codex 32 KiB cap, Claude Code default instruction mode) silently drop or truncate content when the layout is wrong.
evidence: strong
evidence_justification: per-directory `git -C` inventory of all 90 dirs (2026-10-15); code.claude.com/docs/en/memory#agents-md fetched (lines quoted below); bd 1.2.2 behaviour from the issue notes (Q3, verified in a temp repo); merged sizes computed with `stat`/`awk`/`wc -c`; `~/.codex/config.toml` has no `project_doc_*` key (grep empty) so the 32 KiB default from the Q4 note applies.
open_questions: []
status_note: approved at gate 3 on 2026-10-15; resolutions below
---

# Discovery: project instruction files move to AGENTS.md (python-ai-skills-lvt.2)

## Intent

Every project under `/home/bgs/ai-steward/Gena_Beeline_Local/` keeps one real `AGENTS.md`, read by Claude Code
(through a `CLAUDE.md -> AGENTS.md` symlink, default instruction mode) and by Codex (which reads `AGENTS.md` only;
`~/.codex/config.toml` sets no `project_doc_fallback_filenames`). The user profile `Gena_Beeline_Local/CLAUDE.md` stays.
Design decisions Q1-Q4 are inputs (bd notes 2026-10-15); this document records the problem space they act on.

Docs evidence (code.claude.com/docs/en/memory, fetched 2026-10-15, line numbers of the fetched text):
- l.356: "An AGENTS.md and a CLAUDE.md or CLAUDE.local.md in your working directory or above it -> Your CLAUDE.md files only".
- l.367-369: "By default, Claude reads AGENTS.md only when you have no CLAUDE.md in your working directory or above it";
  a CLAUDE.md "in your working directory or any directory above it" counts. The profile is such a file.
- l.436: "A CLAUDE.md symlinked to AGENTS.md: nothing, or delete the symlink. Either way Claude reads the content once."
- l.459: Edit and Write "refuse to write through a symlink" and redirect to the target `AGENTS.md`.
- l.460: Windows clones check a committed symlink out as a one-line text file unless `core.symlinks` is on.
- l.390: in `claude-md-and-agents-md` mode an AGENTS.md "your CLAUDE.md imports or symlinks to isn't read twice".
- l.426: `InstructionsLoaded` hooks fire for an AGENTS.md reached through a symlink (none in use here).
Tool versions on this machine: Claude Code 2.1.296, codex-cli 0.160.0, bd 1.2.2. `instructionFiles`/`pluginConfigs`
appear in neither `~/.claude/settings.json` nor `claude-home/settings.json.template` (grep empty) -> default mode.

## Inventory (90 dirs scanned; 40 hold an instruction file; `git -C <dir>` read-only, 2026-10-15)

Columns: branch; `git status --porcelain -- CLAUDE.md AGENTS.md`; C = CLAUDE.md bytes, A = AGENTS.md bytes; pc = `.pre-commit-config.yaml`
present; hk = bootstrap `.git/hooks/pre-commit` present. No repo ignores either file (`git check-ignore` negative everywhere);
no in-scope repo has `no-commit-to-branch` (only Sinayara-Isuzu and Sinayara-Isuzu-web, out of scope); no `CLAUDE.local.md`,
`.claude/CLAUDE.md` or `AGENTS.override.md` exists at any project root; `core.symlinks` is unset (git default) and five repos already
commit a `120000` symlink entry, so symlinks in git are an existing practice here.

| Dir | Group | Branch | Dirty C/A | C | A | pc | hk | Note |
|---|---|---|---|---|---|---|---|---|
| python-ai-skills | D pilot | main | clean | 16416 | 6165 | y | y | AGENTS.md:3 pointer "rules live in CLAUDE.md" |
| free-ai-selector | B template | master | clean | 13540 | 5926 | y | n | markdownlint, eof/ws fixers in pre-commit |
| Local_LLM_selection | B template | master | clean | 29735 | 5926 | y | y | merged 30985-32872 B, see open question |
| quickexambot | B template | master | clean | 4923 | 5910 | y | y | |
| server-monitor | B template | master | clean | 4800 | 5910 | y | y | |
| spark-public-bot | B template | master | clean | 9850 | 5910 | y | y | eof/ws fixers |
| tg-video-downloader | B template | master | clean | 4778 | 4659 | y | y | AGENTS.md has no BEADS CODEX SETUP block |
| ai-generator-asyncmicroservices | C manual | master | clean | 14362 | 10156 | n | n | no bd markers in either file |
| Sinayara-Indonesia | C manual | master | clean | 5492 | 8264 | n | y | 7 nested instruction files below root |
| VPS-VPN-Home-Server-Guide | C manual | master | clean | 1205 | 5854 | n | y | AGENTS.md is the grace-init GRACE protocol |
| taro_project_2026-04-01 | E invert | master | clean | 11874 | link->CLAUDE.md | y | y | pytest-unit-fast, sentrux-check hooks |
| ai-steward-wiki | E? | master | clean | 7161 | link->docs/Spec-WIKI/CLAUDE.md (14861) | y | y | NOT a plain inversion, see open question |
| bge-m3-api | G AGENTS only | master | clean | - | 2899 | n | n | not loaded by Claude Code today (docs l.367) |
| Sensedar | F done | master | clean | link | 11317 | y | y | hand-managed bd block, untouched |
| checkmyskillsbot | F done | master | clean | link | 3896 | y | n | |
| doc4microservices | F done | master | clean | link | 9738 | n | y | |
| 2025_Noveo | A | master | ` M CLAUDE.md` | 4821 | - | n | n | uncommitted +2/-2 in CLAUDE.md |
| 2026-03-11-magnit-clusterization-ai-classification | A | master | clean | 6775 | - | n | n | |
| aidd-mvp-generator | A | master | clean | 38102 | - | n | n | > 32 KiB |
| Bio-Chem-Career-2026 | A | master | clean | 10992 | - | n | y | |
| boilerplate_microservices | A | master | clean | 12162 | - | n | n | |
| claude_bot | A | master | clean | 5594 | - | n | n | |
| claude_bot.bak | A | master | clean | 5679 | - | n | n | backup copy of claude_bot, still a repo |
| docker-deploy-playbook | A | master | clean | 2363 | - | n | y | |
| ebooks | A | master | clean | 38234 | - | n | y | > 32 KiB |
| fastapi-crud-aidd-generated | A | master | clean | 6683 | - | n | n | |
| ML_CAREER_2026 | A | master | clean | 39512 | - | n | y | > 32 KiB |
| ML_Sobes_2026 | A | master | clean | 14930 | - | n | y | |
| mvp_tg_monitor | A | master | clean | 18526 | - | n | n | |
| nginx-proxy-vps | A | master | clean | 17304 | - | n | n | |
| Preduniversary-High-Schools-Moscow-2026 | A | master | clean | 24137 | - | n | y | |
| Prognosis | A | master | clean | 8249 | - | y | n | detect-secrets, eof/ws fixers |
| Sensedar-Spark | A | master | clean | 8085 | - | n | y | |
| study-check-bot | A | master | clean | 8744 | - | n | n | |
| taro_project | A | master | clean | 17039 | - | n | n | |
| telegram-e2e-runner | A | master | clean | 8444 | - | y | y | pytest-collect hook |
| try_microservices | A | master | clean | 14290 | - | n | n | |
| my_funny_images | A, no git | - | - | 284 | - | n | n | not a repo: plain `mv` + `ln -s`, no commit |
| Sinayara-Isuzu | OUT (lvt.3) | master | clean | 220324 | 6387 | y | y | no-commit-to-branch hook |
| Sinayara-Isuzu-web | OUT (lvt.3) | master | clean | 68053 | 7122 | y | y | no-commit-to-branch hook |

Counts: A 22 (21 repos + 1 non-git), B 6, C 3, D 1, E 2 (one not a plain inversion), F 3, G 1, OUT 2 = 40.
Other dirty trees in scope touch only `.beads/interactions.jsonl`, `.aidd` or unrelated docs (free-ai-selector, Local_LLM_selection,
quickexambot, server-monitor, spark-public-bot, nginx-proxy-vps, Sensedar-Spark, taro_project) - no conflict with a rename commit.
50 dirs have no instruction file (several are repos without a HEAD commit: ai_ranez_langchain_rag, try_*, new_folder_2026_09_28); 7 dirs are not repos.

## bd block facts (template pairs and pilot)

- The six B-group `AGENTS.md` are identical outside the bd blocks: 1910 B (1909 in tg-video-downloader) = title + "bd prime" pointer +
  Quick Reference + "Non-Interactive Shell Commands"; the Q2 figure of 1898 B is this text. python-ai-skills has 2149 B (the extra is line 3).
- Both files of every pair carry a `BEADS INTEGRATION` block; hashes differ in five pairs (CLAUDE.md `6cd5cc61`, AGENTS.md `970c3bf2`
  in free-ai-selector and Local_LLM_selection; quickexambot, server-monitor, spark-public-bot, tg-video-downloader: `6cd5cc61` in both).
  python-ai-skills: both `970c3bf2`, byte-identical (`cmp` on the extracted blocks, 2766 B each). The merged file must hold exactly one.
- `BEADS CODEX SETUP` block is 1250 B where present (not in tg-video-downloader). `bd setup codex --print` is 2122 B (its template, not the file text).
- python-ai-skills merged AGENTS.md = CLAUDE.md lines 1-245 (bd block 139-193, hand-written sections 195-245 that "MUST stay outside the
  managed block") + the Non-Interactive text from AGENTS.md 28-50 + CODEX SETUP from AGENTS.md 108-130; line 3 pointer dropped.
  In the pairs the CODEX block directly follows the INTEGRATION block; in the pilot the hand-written sections will sit between them -
  whether `bd setup codex --check` accepts that order is unverified (hypothesis: it checks markers only; verify in the pilot).
- Nothing in python-ai-skills needs the two files to be distinct: `scripts/test_install_claude_symlinks.py` has no `CLAUDE.md`/`AGENTS.md`
  reference (grep over `scripts/*.py` empty); `.pre-commit-config.yaml:38` `files:` pattern matches only the template, installer and its test;
  hook tests use `tmp_path / "CLAUDE.md"` fixtures (`claude-home/hooks/test_task_level_inject.py:23,73,87`) and `claude-home/CLAUDE.md`
  (`test_principles_ssot.py:54`) - global files, unaffected.

## Reference map in python-ai-skills (grep -rn `CLAUDE\.md|AGENTS\.md`, 174 lines, 70 files; history under docs/ and CHANGELOG omitted)

(a) Keep working because `CLAUDE.md` remains as a symlink:
- `do-autopilot/SKILL.md:28,57` - `project_type` lookup and "walk up until first CLAUDE.md".
- `customer-tz/SKILL.md:20,114`, `full-audit/SKILL.md:16,119`, `agents/do-feature-clean.md:19`, `best-research/SKILL.md:33,95,100`,
  `do-feature/reference.md:359`, `do-feature/reviewer-prompt.md:27`, `full-audit/lib/ai_review_prompt.md:71`.
- `claude-home/hooks/explanation-terms.py:134` reads both `cwd/CLAUDE.md` and `cwd/AGENTS.md` - same bytes twice after the move, harmless.
- `git-finish/SKILL.md:93` - "CLAUDE.md - skill catalog rows ... counters" names the pilot's own file; after the move the edit target is AGENTS.md
  (Edit refuses the symlink, docs l.459), so the wording should name AGENTS.md.

(b) Generators that keep producing the old layout (drift for new projects):
- `_init/SKILL.md:4,26` - "Creates CLAUDE.md"; writes a real `CLAUDE.md` at project root.
- `grace-init/SKILL.md:44-46` - writes `AGENTS.md` from `assets/AGENTS.md.template`, creates no `CLAUDE.md` symlink -> under the profile
  CLAUDE.md the file is not loaded by Claude Code (docs l.367).
- `bd setup claude` - writes the block into `CLAUDE.md`; with the symlink it skips (Q3, verified). `bd init` / `bd setup codex` write into AGENTS.md.
- Claude Code `/init` writes `CLAUDE.md`; behaviour against a symlink not verified (docs l.470 only says `CLAUDE_CODE_NEW_INIT=1` reads AGENTS.md).

(c) Documents that state the layout rule:
- `claude-home/CLAUDE.md:31` "Every project MUST declare its type in its root CLAUDE.md/AGENTS.md"; `:258` "{User}/CLAUDE.md or {User}/AGENTS.md";
  `:270` "instruction files (CLAUDE.md / AGENTS.md)"; `:5` discovery paths of the global file.
- `CLAUDE.md:104-120` (pilot) "Multi-machine consistency": global `~/.claude/AGENTS.md` links to `CLAUDE.md` - the inverse direction, global scope,
  installed by `scripts/install-claude-symlinks.sh:77-78`; out of scope here but the two conventions now point opposite ways.
- `AGENTS.md:3` (pilot) pointer to drop; `README.md:94` (global files only, no change).
- `docs/2026-03-15-skills-file-convention-architecture.md` - not read; candidate for a layout statement.

## Functional requirements

- FR-1 Every in-scope dir ends with one regular `AGENTS.md` and `CLAUDE.md` as a relative symlink `AGENTS.md` (bd notes Q1; docs l.454 `ln -s AGENTS.md CLAUDE.md`).
- FR-2 Group A: `git mv CLAUDE.md AGENTS.md` + symlink, content byte-identical (Q2); my_funny_images without git.
- FR-3 Group B and pilot: merged AGENTS.md = CLAUDE.md content + one BEADS INTEGRATION block + BEADS CODEX SETUP block where the old AGENTS.md had one
  + the Non-Interactive text if absent (Q2; sizes above); exactly one `BEGIN` marker per block type.
- FR-4 Group C and ai-steward-wiki: hand merge with user review (Q2; open question for ai-steward-wiki).
- FR-5 Group E (taro_project_2026-04-01): invert the link direction, content unchanged.
- FR-6 bge-m3-api: symlink added (open question; docs l.367).
- FR-7 Per-project check: `bd setup claude --check`, project pre-commit, content preserved (Q2 notes).
- FR-8 Generators and layout statements in python-ai-skills updated (open question on scope): `_init`, `grace-init`, `claude-home/CLAUDE.md:31`, `git-finish/SKILL.md:93`.

## Non-functional requirements

- NFR-1 Codex loads the whole file: merged AGENTS.md < 32768 B for every migrated repo except the three A-group files already above it (Q4 note; `codex debug prompt-input` verified truncation).
- NFR-2 One commit per repo, conventional message, hooks run (global Pre-commit Policy); no push without an explicit request (Git Push Policy).
- NFR-3 Idempotent script: re-running on a migrated dir changes nothing (Q2 "one-off script"; Q3 shows bd itself is idempotent).
- NFR-4 Acceptance: a Claude Code session and a Codex session (`codex debug prompt-input`) in a sample repo load the file; the profile still loads (bd acceptance criteria).

## Constraints

1. Sandbox: Bash writes only inside python-ai-skills and `$TMPDIR`; each write in a sibling dir needs sandbox bypass with approval. The global rule allows
   edits of `~/ai-steward/**/*.md` outside `$PWD`; `git mv`, `ln -s` and commits also write `.git/` and the symlink entry - outside the letter of that rule, so
   the per-command approval is the gate.
2. `git` runs unsandboxed only as a standalone call (`git -C <dir>` and chains are sandboxed - RTK section of the global file); the script will run sandboxed and
   need bypass per dir.
3. Pre-commit in B/E repos modifies markdown (free-ai-selector markdownlint, eof/ws fixers in free-ai-selector, spark-public-bot, ai-steward-wiki, Prognosis;
   `vocab-check` in Local_LLM_selection is unread) - a fixer may rewrite the merged AGENTS.md on commit, so the content check must run after `pre-commit run`.
   taro_project_2026-04-01 runs `pytest-unit-fast` and `sentrux-check` on every commit (slow, may fail for unrelated reasons).
4. 4 claude/codex processes are live on this machine; CLAUDE.md is read at session start, so running sessions keep the old text in context and any Edit of
   `CLAUDE.md` in them is refused and redirected (docs l.459) - no corruption path, but a confused session is possible.
5. Codex limit defaults: `~/.codex/config.toml` has no `project_doc_max_bytes` / `project_doc_fallback_filenames`; the config reference (learn.chatgpt.com, fetched)
   states no default value - the 32 KiB figure rests on the Q4 measurement.

## Risks and mitigations

1. Codex truncation (Local_LLM_selection 32872 B with full template; A-group 38-40 KB files) -> choose the 891 B Non-Interactive text only; list the three large files in lvt.3; `wc -c` gate in the script.
2. bge-m3-api silently unread by Claude Code today -> include in the symlink group (open question).
3. ai-steward-wiki mis-handled as "invert" would make a life-zone constitution the dev project's root file -> manual group.
4. Dirty 2025_Noveo CLAUDE.md -> commit or stash before the rename.
5. Non-Linux clones: no evidence any machine is non-Linux (the repo docs name only Linux hosts: `spark-1`, `vpn-2`); unknown, stated as such. Five repos already commit symlinks without reported trouble; docs l.460 names the Windows failure mode.
6. Tools writing through the link: Edit/Write refuse (docs); `bd setup claude` skips (Q3); `/init` and pre-commit fixers unverified -> pilot first, `git ls-files -s` must show `120000` for CLAUDE.md after every commit.
7. bd hash drift in five pairs (CLAUDE.md `6cd5cc61` vs AGENTS.md `970c3bf2`) -> after merge run `bd setup claude --check` and `bd setup codex`; bd rewrites its own block idempotently (Q3).
8. Duplicate text: in default mode Claude reads `CLAUDE.md` (the link) and not `AGENTS.md` separately (docs l.356); `explanation-terms.py` reads both names - duplicate corpus text only.
9. `claude_bot.bak` is a repo copy; migrating it is harmless but commits into a backup - confirm it stays in group A.

## Scope

- IN: 37 dirs of groups A-E plus bge-m3-api (open question), the one-off script, pilot python-ai-skills first, per-repo commits, generator/rule text in python-ai-skills (open question).
- OUT: Sinayara-Isuzu, Sinayara-Isuzu-web (lvt.3); global `~/.claude/CLAUDE.md` / `~/.claude/AGENTS.md` direction; Sensedar's hand-managed bd block; `instructionFiles` setting; any push.
- LATER: nested instruction files (29 at depth >= 3, e.g. Sinayara-Indonesia 7, ai-steward-wiki 3 - Codex reads nested `AGENTS.md` only); shrinking the three > 32 KiB A-group files; repos without an instruction file (50) get one only through the updated generators.

## Best-practice check (one search)

Community sources agree on one real file plus a link or an `@AGENTS.md` import for the other tool; the import is preferred where Windows clones exist, the symlink where
contents must be identical bytes (dev.to "Keep AGENTS.md and CLAUDE.md in sync", agentlink on pkg.go.dev, techsy.io "claude md best practices"). Official Claude Code docs
(l.441-460) list both and name the symlink's two constraints (Edit refusal, Windows). Nothing found argues against the symlink on Linux-only machines.

## Resolved open questions (gate 3, user-approved 2026-10-15)

1. `bge-m3-api` (AGENTS.md only) gets the `CLAUDE.md -> AGENTS.md` symlink in the mechanical group.
2. `ai-steward-wiki` moves to the manual-merge group; default: root `CLAUDE.md` becomes `AGENTS.md`, `docs/Spec-WIKI/CLAUDE.md` stays a subdirectory file; result shown to the user.
3. bd template text: only the "Non-Interactive Shell Commands" section (891 B) is carried into the merged file, uniformly for all six pairs and the pilot (`Local_LLM_selection` -> 31876 B).
4. `aidd-mvp-generator`, `ebooks`, `ML_CAREER_2026` (> 32 KiB) migrate as is and are added to python-ai-skills-lvt.3.
5. `2025_Noveo`: `git mv` keeps the uncommitted CLAUDE.md edit as an unstaged modification of AGENTS.md; it is not committed (verified in a temp repo).
6. Generators and layout docs are fixed in lvt.2: `_init`, `grace-init`, `claude-home/CLAUDE.md:31`, `git-finish/SKILL.md:93`.
