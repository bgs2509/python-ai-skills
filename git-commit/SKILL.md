---
name: git-commit
description: >
  Analyze all uncommitted files, interactively classify them (commit/ignore/skip),
  group into logical commits, and commit with detailed conventional commit messages.
  TRIGGER when: user calls /git-commit, user has many uncommitted files and wants
  to organize commits, user says "commit my changes" or "sort my changes".
  SKIP when: user wants to triage/clean up branches (use /git-branch), or push/sync
  across machines (use /project-sync, /beads-sync).
argument-hint: "[--all to skip interactive classification]"
---

# /git-commit — Interactive Smart Commit

> Analyze uncommitted files, classify, group into logical commits, commit with detailed messages.

## Phase 1: Collect Data

Run these commands in parallel:

1. `git status --porcelain` — all untracked, modified, staged files
2. `git diff --stat` — scale of changes (staged + unstaged)
3. `git log --oneline -10` — recent commit style for this project
4. Check if `.gitignore` exists in the project root

Parse `git status --porcelain` output:
- `??` = untracked
- `M ` = staged modified
- ` M` = unstaged modified
- `A ` = staged new
- `D ` = deleted
- `MM` = staged + unstaged modifications

If there are NO uncommitted changes — say "Nothing to commit" and stop.

## Phase 2: Classify Files

For each file, read its diff (`git diff <file>` for modified, or file contents for untracked) to understand what it contains.

### Auto-classification (do NOT ask user about these):
- `.env`, `*.pem`, `*.key`, `credentials*`, `*.secret` → **ignore** (security)
- `__pycache__/`, `*.pyc`, `.DS_Store`, `node_modules/`, `.venv/`, `*.egg-info/` → **ignore** (generated)

### Interactive classification:
Present ALL remaining files to the user using AskUserQuestion (multiSelect).

Format the question as a list showing each file with:
- File path
- Status (new/modified/deleted)
- Brief description of changes (1 line, from diff analysis)

Ask 2 questions:
1. "Which files to COMMIT?" (multiSelect) — list all non-auto-ignored files, pre-recommend based on analysis
2. "Which files to add to .gitignore?" (multiSelect) — list remaining files not selected for commit

Files not selected in either question → **skip** (left as-is).

If argument `--all` was passed — skip interactive classification, commit all non-ignored files.

## Phase 3: Group Into Logical Commits

Take the files marked for commit and group them into logical commits:

### Grouping rules (in priority order):
1. **Test + implementation** — if a test file and its implementation were both changed, group together
2. **Same feature/module** — files in the same directory or clearly related functionality
3. **Same type of change** — all config changes together, all doc changes together
4. **Single-file changes** — if a file doesn't fit any group, it gets its own commit

### Determine commit type for each group:
- `fix:` — bug fix (error handling, validation, edge case)
- `feat:` — new feature or capability
- `chore:` — maintenance (deps, config, build)
- `docs:` — documentation only
- `refactor:` — code restructure without behavior change
- `test:` — test-only changes
- `style:` — formatting, whitespace, linting

## Phase 4: Dry-Run Plan

Present the full plan to the user in this format:

```
## Commit Plan

### Commit 1: fix(auth): resolve token validation edge case
Files:
  - src/auth/validator.py (modified, +12 -3)
  - tests/test_auth.py (modified, +25 -0)
Message:
  fix(auth): resolve token validation edge case

  - Add null check for expired tokens in validate_session()
  - Handle edge case where refresh token is present but expired
  - Previously caused 500 error for users with stale sessions

### Commit 2: chore(deps): update FastAPI to 0.104
Files:
  - requirements.txt (modified, +1 -1)
Message:
  chore(deps): update FastAPI to 0.104

  - Bump FastAPI from 0.103 to 0.104
  - Includes fix for OpenAPI schema generation with Pydantic v2

---

### .gitignore additions:
  + __pycache__/
  + .env

### Skipped (no action):
  - scratch/notes.txt
```

Ask user: "Execute this plan? (yes / edit / cancel)"
- **yes** → proceed to Phase 5
- **edit** → ask what to change, rebuild plan
- **cancel** → abort

## Phase 5: Execute

### Step 1: Update .gitignore (if any additions)
- Read current `.gitignore` (or create if doesn't exist)
- Append new entries (avoid duplicates)
- Do NOT commit .gitignore changes separately — include in the most relevant commit, or as a separate `chore: update .gitignore` commit

### Step 2: Commit each group
For each commit in the plan:

```bash
git add <file1> <file2> ...
git commit -m "$(cat <<'EOF'
type(scope): short description

- Detail line 1
- Detail line 2
- Why this change was needed
EOF
)"
```

### Step 3: Summary
After all commits, show:
```
Done! Created N commits:
  abc1234 fix(auth): resolve token validation edge case
  def5678 chore(deps): update FastAPI to 0.104

Remaining uncommitted: M files
```

## Rules

1. **NEVER `git push`** — only local commits
2. **NEVER commit secrets** — .env, *.pem, *.key → always suggest .gitignore
3. **Conventional commits** — type(scope): description, English only
4. **Detailed body** — each commit message MUST have a body explaining WHY, not just WHAT
5. **HEREDOC for messages** — always use HEREDOC syntax for multi-line commit messages
6. **Dry-run first** — ALWAYS show the plan before executing
7. **.gitignore = project-level** — add to repo's `.gitignore`, not global
8. **Preserve staging** — if files were already staged (`git add`), respect that grouping unless user overrides
9. **Atomic commits** — each commit should be independently meaningful (not break the build)
10. **No empty commits** — skip groups where all files ended up in ignore/skip

## Related skills

- `/git-branch` — triage ALL branches (active/worktree, merged→deletable, abandoned+age, junk) and delete safely. Natural pairing: `/git-commit` for changes, then `/git-branch` to clean up stale branches.
- `/beads-sync` — sync bd issue state to the remote (git-commit never touches Dolt/beads).
- `/project-sync`, `/projects-sync` — push/pull the repo across machines (git-commit never pushes).
