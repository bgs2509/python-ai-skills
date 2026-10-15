---
feature: branch-name-check
bd_id: python-ai-skills-31d
date: 2026-10-15
status: approved
risk: high
risk_justification: same as Discovery - one PreToolUse deny hook (exit 2) in the global settings of every project on this machine (83 repositories), matchers Bash and EnterWorktree, running in the main conversation and in subagents; a false positive blocks branch and worktree creation machine-wide until fixed. Upward-only escalation keeps high.
approach: python-file-with-launcher
open_questions: []
context7_verified: []
context7_note: stdlib only (json, re, shlex, subprocess, os, datetime, pathlib); no third-party library, so no Context7 lookup applies. Git option spellings were probed with git 2.43.0 in a throwaway repository in this session (`--create=<name>` and glued `-c<name>` are accepted; `git worktree add --orphan <path>` names the branch after the path).
requirements: docs/superpowers/specs/20261015-branch-name-check-discovery.md (FR-1..FR-10, NFR-1..NFR-6, risks 1-9, forms 1-7, scope)
---

# Design: branch-name-check PreToolUse hook (python-ai-skills-31d)

Requirements, hook-contract quotes, git form list and risks are in the Discovery spec and are not restated. This document decides
the code structure only; the solution shape (one PreToolUse hook, Bash + EnterWorktree, deny exit 2, override `N-BRANCH: off`) is fixed.
Scores: `X% / Y%` as defined in the global CLAUDE.md section "Questions and Numbers" (X of all options plus the own-option line sum to 100 %).

## 1. Approaches

### 1.1 python-file-with-launcher (RECOMMENDED) - 50% / 85%
Two files: `claude-home/hooks/branch-name-check.py` (all logic, one `python3 -I` process, reads the hook JSON from stdin) and a
3-line launcher `claude-home/hooks/branch-name-check.sh` (`exec /usr/bin/env python3 -I "$(dirname "$0")/branch-name-check.py"`), the
pattern of `explanation-terms.sh` -> `explanation-terms.py` (3 + 278 lines). Nothing is shared with `block-no-verify.sh`; the
segment split (`SEPARATORS`, trailing `;`) and the global-option skip are re-typed (about 25 lines) with a comment naming the origin.
Strengthens: KISS (no helper, no `source`), YAGNI (every function traces to FR-1..FR-6), CoC (an existing two-file precedent),
Testability (`python3 -I` means the parser cannot import a planted module; the test may call `bash <launcher>` exactly like
`test_block_no_verify.py`), and the ruff gate - `ruff check claude-home/hooks/` (baseline in bd notes) lints a `.py` file but never
the body of a bash heredoc. Violates: SSoT/DRY for the 25 duplicated parser lines - accepted by the project rule of bd r1f.3
("trigger to extract: a third caller"); real consumers of the shlex-segment logic today: 1 (`block-no-verify.sh`; `project-sync/lib/sync.py`
uses `shlex.quote` only), this hook is the 2nd. Y below 90 % because the parser covers seven git forms (risk 1 and 3 false positives).

### 1.2 single bash file with one python heredoc - 30% / 80%
One file `branch-name-check.sh` in the literal shape of `block-no-verify.sh`: `INPUT=$(cat)`, then one `python3 -I - "$INPUT" <<'PY' ... PY`
that parses, looks up the override, writes the journal and prints the deny text (the pattern's three python starts collapse to one for
NFR-1). Same logic, same line count, minus one file. Violates: Testability and the lint gate (150-200 python lines inside a heredoc are
invisible to ruff and to the pre-commit `hook-regression-tests` syntax pass), Explicit > Implicit (the input travels through `argv`
instead of stdin; the heredoc already occupies stdin). Strengthens CoC toward the one pattern the user named ("same style as
`block-no-verify.sh`"); the style the user approved is the deny behaviour (exit 2 + stderr), which 1.1 keeps. Y lower: an error inside a
heredoc is found only at run time.

### 1.3 shared splitting helper with block-no-verify.sh - 5% / 70%
`claude-home/hooks/lib/gitcmd.py` with `segments()` and `find_git_subcommand()`, imported by the new hook and by `block-no-verify.sh`
(whose heredoc would need `sys.path` surgery or a rewrite into a `.py`). Pays SSoT for 25 lines at the price of a new directory, an edit
of a shipped hook outside this feature's scope ("Match scope to request"), and the rule of bd r1f.3: extract on the third consumer; today
there would be two. Rejected on KISS/YAGNI precedence.

### Own option / none - 15%
Top X 50 % exceeds the next line (30 %) by 20 percentage points and top Y is 85 % >= 80 %: on the auto-select threshold, not above it; the
design gate is interactive anyway (risk high).

## 2. Recommended approach in detail

### 2.1 File map
- NEW `claude-home/hooks/branch-name-check.py` - the hook (FR-1..FR-6, NFR-1..NFR-4); header comment states the contract below.
- NEW `claude-home/hooks/branch-name-check.sh` - launcher, `exec /usr/bin/env python3 -I "$(dirname "$0")/branch-name-check.py"`.
- NEW `claude-home/hooks/test_branch_name_check.py` - FR-9, NFR-5.
- CHANGED `claude-home/settings.json.template` - FR-7 (2.6). `make install-symlinks` re-renders the live file.
- CHANGED `claude-home/CLAUDE.md` -> `## Naming` N-BRANCH paragraph - FR-8 (2.5); `claude-home/CLAUDE-APPENDIX.md` - one `**Почему:**`
  paragraph under a new `## Naming` heading (scope IN of the Discovery; file convention: one paragraph per heading).
- CHANGED `Makefile` `test:` - add `claude-home/hooks/test_branch_name_check.py \` after the `test_block_no_verify.py` line.
- CHANGED `CHANGELOG.md` `## [Unreleased]` - FR-10: Added (hook), Changed (N-BRANCH text).

### 2.2 Hook contract
- stdin: the PreToolUse JSON; fields read: `tool_name`, `tool_input.command` (Bash), `tool_input.name` and `tool_input.path`
  (EnterWorktree), `cwd` (override lookup only). Unknown `tool_name`, missing fields, non-JSON stdin -> exit 0, no output (NFR-2).
- exit 0: allow (silent). exit 2: deny, reason on stderr. No other exit code; every exception path is caught at `main()` -> exit 0.
- stderr template (deny); `{names}` = the offending names joined by `, `; `{toplevel}` = 2.4; the last line only when 2.4 found other
  N-BRANCH text:
  ```text
  [branch-name-check] Refusing to create branch '{names}': no `branch` segment.

  Naming rule N-BRANCH (~/.claude/CLAUDE.md -> "Naming"): form <type>/branch-<slug>,
  <type> one of feat, fix, docs, style, refactor, test, chore, perf, build, ci (Commit Convention).
  Worktrees: pass that form as the EnterWorktree name (Claude Code adds `worktree-` and turns `/` into `+`).
  Project override: a line `N-BRANCH: off` under `## Naming overrides` in {toplevel}/AGENTS.md.
  Note: {toplevel}/AGENTS.md mentions N-BRANCH under Naming overrides, but only `N-BRANCH: off` is machine-readable.
  ```
  The segment regex `(^|[-/_+])branch($|[-/_+])`, the form string and the type tuple are module constants with a comment pointing to
  `claude-home/CLAUDE.md` -> Naming and -> Commit Convention; no other rule text is copied (NFR-3).
- journal (FR-4): one line appended to `~/.claude/hook-stats/blocks.jsonl` before exit 2, same keys as `block-no-verify.sh:26-32`:
  `{"ts": <UTC ISO seconds>, "hook": "branch-name-check", "cwd": os.getcwd(), "kind": "bash-git" | "enter-worktree",
  "command": <command or name>[:300]}`; a journal write error is ignored (deny still happens).

### 2.3 Parsing algorithm (Bash route; FR-1, FR-5, risks 1-3)
1. `"git" not in command` -> exit 0 (no shlex, the cheapest path; covers most Bash calls).
2. `shlex.split(command, posix=True)`; `ValueError` -> exit 0.
3. Truncate the token list at the first token that starts with `<<` (heredoc or here-string): everything after it is unchecked
   (fail-open, NFR-2). A quoted string is one token, so a name inside `-m "..."` or `echo '...'` never becomes a `git` token.
4. Split into segments on `&&`, `||`, `;`, `|`, `&` and a trailing `;` glued to a word (copy of `block-no-verify.sh:52-70`).
5. Per segment, drop leading prefix tokens: `NAME=value` assignments (`^[A-Za-z_][A-Za-z0-9_]*=`), `command`, `env`, `nice`, `time`,
   and the pair `rtk proxy`. Then find the first token equal to `git` or ending in `/git`; none -> next segment.
6. Skip git global options exactly as `block-no-verify.sh:75-91` (`-C`, `-c`, `--git-dir`, `--work-tree`, `--namespace`, `--exec-path`
   take a value; any other `-...` is skipped); the next token is `sub`.
7. Extract candidates by `sub` (tokens after `sub`; a bare `--` ends option parsing - later tokens are positional):
   - `checkout` (form 1): `-b`, `-B`, `--orphan` -> next token; `--orphan=<v>`, glued `-b<v>` / `-B<v>` -> the rest. No such flag ->
     not creating (`git checkout <name>`, `--track origin/x`, `-- file`: form 7 / non-creating).
   - `switch` (form 2): `-c`, `-C`, `--create`, `--force-create`, `--orphan` and their `=<v>` / glued forms -> value; otherwise not creating.
   - `branch`: a non-creating flag present (`-d`, `-D`, `--delete`, `-l`, `--list`, `-a`, `--all`, `-r`, `--remotes`, `-v`, `-vv`,
     `--verbose`, `--show-current`, `-u`, `--set-upstream-to[=]`, `--unset-upstream`, `--edit-description`, `--merged`, `--no-merged`,
     `--contains`, `--no-contains`, `--points-at`, `--format[=]`, `--sort[=]`, `--column`, `--color`) -> not creating. Else positionals =
     tokens not starting with `-`; with `-m`, `-M`, `--move`, `-c`, `-C`, `--copy` -> the last positional (form 6, also the one-argument
     rename); no positional -> list, not creating; otherwise the first positional (form 3; `--track`, `-f`, `--recurse-submodules` are
     flags without a value).
   - `worktree` + next token `add` (forms 4, 5, 7): `-b` / `-B` -> next token (form 4). Else `--detach`/`-d` -> not creating. Else
     positionals after skipping `--reason <v>`: 1 positional -> `os.path.basename(path.rstrip("/"))` (form 5, also with `--orphan`);
     2 positionals (`<path> <commit-ish>`) -> not creating (form 7 DWIM / existing branch).
   - any other `sub` -> not creating.
8. A candidate without a `branch` segment (regex of 2.2) is an offending name; an empty candidate (flag at end of line) is skipped.
   No offending name -> exit 0 before any subprocess.

EnterWorktree route (FR-2): `name` present -> candidate `name` (checked raw: the prefix `worktree-` and the `/`->`+` rewrite add
only boundary characters, so the raw name and the generated branch are equivalent under the regex); `path` present and no `name` ->
exit 0; neither -> offending name `<generated>` (the harness slug never contains the segment); kind `enter-worktree`.

### 2.4 Override lookup (FR-6; runs only after an offending name was found)
1. `cwd` from the input (fallback `os.getcwd()`); `subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], timeout=5,
   capture_output=True, text=True)`; exit 0 -> `toplevel` = stdout stripped; any failure or `TimeoutExpired` -> `toplevel = cwd`.
2. Read `<toplevel>/AGENTS.md` (`FileNotFoundError`/`OSError` -> no override). Cut the section: lines after the one equal to
   `## Naming overrides` up to the next line starting with `## ` (the awk idiom of `task-level-inject.sh:24`, in python).
3. A line matching `^\s*N-BRANCH:\s*off\s*$` -> exit 0 (no journal). Any other line containing `N-BRANCH` -> the extra Note line of 2.2.

### 2.5 `claude-home/CLAUDE.md` -> `## Naming`, N-BRANCH replacement paragraph (FR-8; the rule text lives only here)
```md
**Rule (N-BRANCH):** Every new git branch name contains `branch` as a separate segment (bounded by the start, the end, `-`, `/`, `_` or `+`), so a branch name is never mistaken for a made-up term. Form: `<type>/branch-<slug>` — `<type>` from Commit Convention above, `<slug>` short kebab-case English, e.g. `feat/branch-gigaam-asr`. Claude Code worktrees: pass that form as the worktree name; Claude Code prefixes it with `worktree-` and replaces `/` with `+` (`worktree-feat+branch-gigaam-asr`). Temporary subagent worktree branches Claude Code generates itself (`worktree-agent-<hex>`) are outside the rule. Enforced by the PreToolUse hook `hooks/branch-name-check.sh` on Bash git commands and `EnterWorktree`; the only machine-readable override is the line `N-BRANCH: off` in a project's `## Naming overrides`. Existing branches are not renamed (bd `python-ai-skills-31d`).
```

### 2.6 `claude-home/settings.json.template` wiring (FR-7)
Fourth entry of the existing `PreToolUse` group with `"matcher": "Bash"` (after `rtk-announce.sh`) and one new group; no `timeout`
field, like the three Bash siblings - the only slow path is bounded by the 5 s git timeout of 2.4:
```json
{ "type": "command", "command": "'{{CLAUDE_HOME}}/hooks/branch-name-check.sh'" }
```
```json
{ "matcher": "EnterWorktree", "hooks": [ { "type": "command", "command": "'{{CLAUDE_HOME}}/hooks/branch-name-check.sh'" } ] }
```
`test_every_hook_path_is_one_shell_word` and the `settings-template-json` pre-commit check cover both entries without a new test.

### 2.7 Test matrix `claude-home/hooks/test_branch_name_check.py` (FR-9, NFR-5)
Harness as `test_block_no_verify.py`: `subprocess.run(["bash", <launcher>], input=json, env={**os.environ, "HOME": fake_home})`, exit code
asserted; Bash cases run with `cwd` = a `tmp_path` git repository created by the test (`git init` + one commit) so the override lookup
is exercised offline; three override fixtures write `AGENTS.md` into that repository. Case -> exit code:
- DENIED (2): `git checkout -b feat/gigaam` (1); `git checkout -B hotfix`; `git checkout --orphan=docs-site`; `git switch -c lazy-fox`;
  `git switch --create=x`; `git switch -cx`; `git branch new-thing`; `git branch -f new-thing main`; `git branch -m old new-thing`;
  `git branch -m renamed`; `git branch --copy a b`; `git worktree add -b feat/x ../wt`; `git worktree add ../lazy-fox`;
  `git worktree add --orphan ../lazy-fox`; `git -C /tmp/r switch -c x`; `git add -A && git checkout -b x`; `cd /tmp; git switch -c x`;
  `VAR=1 git checkout -b x`; `command git checkout -b x`; `/usr/bin/git checkout -b x`; `rtk proxy git switch -c x`;
  `git checkout -b x -- file`; EnterWorktree `{"name": "lazy-fox"}`; EnterWorktree `{}` (no name, no path); override fixture with
  `N-BRANCH: <type>-branch-<slug>` -> 2 and stderr contains `not machine-readable`.
- ALLOWED (0): `git checkout -b feat/branch-x`; `git switch -c fix/branch-y`; `git branch docs/branch-z`; `git branch -m old
  feat/branch-new`; `git worktree add ../feat-branch-x`; `git worktree add -b feat/branch-x ../wt`; `git checkout main`;
  `git checkout -- file`; `git checkout --track origin/lazy-fox`; `git switch lazy-fox`; `git branch -d lazy-fox`; `git branch -D x`;
  `git branch --list`; `git branch`; `git branch -u origin/main`; `git branch --show-current`; `git worktree remove ../wt`;
  `git worktree add --detach ../wt`; `git worktree add ../wt lazy-fox`; `git worktree list`; `git push -u origin HEAD`; `git status`;
  `git commit -m "use git checkout -b x"`; `echo 'git checkout -b x'`; `grep -rn "checkout -b" docs/`; `cat <<EOF\ngit checkout -b x\nEOF`;
  `ls`; `""`; `git checkout -b 'unbalanced`; `git checkout -b` (flag at end); EnterWorktree `{"name": "feat/branch-x"}`;
  EnterWorktree `{"path": "/tmp/wt"}`; `tool_name` `Read` with any input; non-JSON stdin; override fixture `N-BRANCH: off` with
  `git checkout -b lazy-fox` -> 0; `cwd` outside any repository with a compliant name -> 0.
- Journal: one DENIED case asserts a record with `hook == "branch-name-check"` and `kind == "bash-git"` in `<fake_home>/.claude/hook-stats/blocks.jsonl`;
  one EnterWorktree case asserts `kind == "enter-worktree"`; one ALLOWED case asserts the file does not exist.

### 2.8 NFR-1 measurement (<= 0.10 s per call)
`for i in $(seq 10); do /usr/bin/time -f %e bash claude-home/hooks/branch-name-check.sh < <input>; done` for three inputs: `git status`
(step 1 exit), `git checkout -b feat/branch-x` (full parse, exit 0 before any subprocess), and `git checkout -b lazy-fox` with `cwd` in a
temp repository (parse + `git rev-parse` + `AGENTS.md` read + journal + exit 2). Acceptance: the maximum of the 30 runs <= 0.10 s;
the numbers go into bd notes with the smoke run. Baseline measured this session: `python3 -I` with `json`, `re`, `shlex`, `subprocess`
imported = 0.02 s (5 of 5 runs), through a bash launcher 0.03 s (3 of 3 runs); `block-no-verify.sh` 0.03-0.07 s over 15 runs (Discovery).

### 2.9 Verification in Execution
1. `make test` (baseline 485 of 485 per bd r1f.3 close reason) -> 485 + new tests; `ruff check claude-home/hooks/` stays at the 1
   pre-existing error.
2. `python3 -c 'import json; json.load(open("claude-home/settings.json.template"))'`, `make install-symlinks`, then
   `jq '.hooks.PreToolUse[] | select(.matcher=="Bash" or .matcher=="EnterWorktree") | .hooks | length' ~/.claude/settings.json` -> 4 and 1.
3. Smoke run in a temp repository (scope IN): `git checkout -b lazy-fox` through the Bash tool is denied with the 2.2 text; `git checkout
   -b feat/branch-smoke` passes; `EnterWorktree(name="lazy-fox")` is denied; recorded in bd notes with the NFR-1 numbers.
