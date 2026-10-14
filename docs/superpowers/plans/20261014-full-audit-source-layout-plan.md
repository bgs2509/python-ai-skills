# Plan: full-audit source layout (bd python-ai-skills-5xi)

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** `/full-audit` derives its source dirs once (src/, else pyproject-declared paths, else top-level packages) so mypy, coverage, radon, vulture and interrogate never go green on a missing `src/`.

**Architecture:** new stdlib-only helper `full-audit/lib/source_dirs.py` (`derive(root) -> list[str]`, `main()` prints one dir per line). `run.sh` calls it once into bash arrays; empty result -> checks 06/14-17 go through the existing `skip()`.

**Tech Stack:** bash, Python 3.12 (`tomllib`, stdlib), pytest.

Discovery: `docs/superpowers/specs/20261014-full-audit-source-layout-discovery.md` (FR-1..5, NFR-1..4, Q1-Q3).
Design (the contract; this plan adds nothing to it): `docs/superpowers/specs/20261014-full-audit-source-layout-design.md` (approach A, OQ-1 src/ first, OQ-2 coverage uses the tests-dropped list).

## Files touched

- Create: `full-audit/lib/source_dirs.py`
- Create: `full-audit/tests/test_source_dirs.py`
- Modify: `full-audit/lib/run.sh` (before line 80; lines 83-92; 111-117; 159-163)
- Modify: `full-audit/SKILL.md` (table rows 3, 6, 14-17, lines 84, 87, 95-98)
- Modify: `full-audit/references/checks.md` (rows 03, 06, lines 9, 15)
- Modify: `CHANGELOG.md` (`## [Unreleased]` -> existing `### Fixed`, line 45)

No GRACE artifacts and no MODULE_CONTRACT headers in `full-audit/lib/*.py` (only `check_contracts.py` mentions them as a check) - none added. Existing style: `from __future__ import annotations`, one-line module docstring, `main()`, tests import lib modules directly (`conftest.py` puts `lib/` on `sys.path`).

## Global Constraints

- NFR-1: `cd full-audit && python3 -m pytest` stays green; baseline 38 passed (2026-10-14).
- NFR-2: a project with `src/` runs the same commands as today (`mypy src --no-error-summary`, `--cov=src`, `radon cc src -n C -a`, ...).
- NFR-3: no new dependency; Python 3.11+ stdlib `tomllib`.
- NFR-4: derived dirs never include `.venv`, `tests`, `docs`, `data`, `_output`, `scripts`.
- Thresholds (`-n C`, `-f 70`, `--min-confidence 80`), required/optional flags and `tests/golden/*` are out of scope; do not touch.
- English only in code, docs, commit. No `git push`, no `--no-verify`.
- Ruff baseline for `ruff check full-audit`: 5 errors; must not grow.

---

### Task 1: RED - tests for the helper and the run.sh wiring

**Files:**
- Create: `full-audit/tests/test_source_dirs.py`

**Interfaces:**
- Produces: tests importing `from source_dirs import derive, main` (Task 2 must provide `derive(root: Path) -> list[str]` and `main() -> int`).

- [ ] **Step 1: Create `full-audit/tests/test_source_dirs.py`**

```python
"""Tests for source_dirs.derive and the run.sh wiring."""
from pathlib import Path

import pytest

from source_dirs import derive, main

RUN_SH = Path(__file__).resolve().parent.parent / "lib" / "run.sh"


def make(root: Path, dirs=(), pyproject: str | None = None, pkgs=()):
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)
    for d in pkgs:
        (root / d).mkdir(parents=True, exist_ok=True)
        (root / d / "__init__.py").write_text("")
    if pyproject is not None:
        (root / "pyproject.toml").write_text(pyproject)
    return root


def test_src_wins_over_config(tmp_path):
    make(tmp_path, ["src", "backend"], '[tool.mypy]\nfiles = ["backend"]\n')
    assert derive(tmp_path) == ["src"]


def test_mypy_files_taro_shape(tmp_path):
    dirs = ["backend", "telegram_bot", "scheduler", "shared"]
    make(tmp_path, dirs, '[tool.mypy]\nfiles = ["backend", "telegram_bot", "scheduler", "shared"]\n')
    assert derive(tmp_path) == dirs


def test_coverage_run_source(tmp_path):
    make(tmp_path, ["app"], '[tool.coverage.run]\nsource = ["app"]\n')
    assert derive(tmp_path) == ["app"]


def test_interrogate_paths(tmp_path):
    make(tmp_path, ["pkg"], '[tool.interrogate]\npaths = ["pkg"]\n')
    assert derive(tmp_path) == ["pkg"]


def test_vulture_paths(tmp_path):
    make(tmp_path, ["pkg"], '[tool.vulture]\npaths = ["pkg"]\n')
    assert derive(tmp_path) == ["pkg"]


def test_missing_declared_dir_is_dropped(tmp_path):
    make(tmp_path, ["a"], '[tool.mypy]\nfiles = ["a", "gone"]\n')
    assert derive(tmp_path) == ["a"]


def test_all_declared_missing_tries_next_key(tmp_path):
    make(
        tmp_path,
        ["app"],
        '[tool.mypy]\nfiles = ["gone"]\n[tool.coverage.run]\nsource = ["app"]\n',
    )
    assert derive(tmp_path) == ["app"]


def test_probe_skips_excluded_dirs(tmp_path):
    make(tmp_path, ["docs", "data"], pkgs=["bot", "tests", ".venv", "scripts"])
    assert derive(tmp_path) == ["bot"]


def test_probe_ignores_dirs_without_init(tmp_path):
    make(tmp_path, ["plain"], pkgs=["bot"])
    assert derive(tmp_path) == ["bot"]


def test_nothing_returns_empty(tmp_path):
    assert derive(tmp_path) == []


def test_unparsable_pyproject_falls_through_to_probe(tmp_path):
    make(tmp_path, pyproject="[tool.mypy\nfiles = ", pkgs=["bot"])
    assert derive(tmp_path) == ["bot"]


def test_main_prints_nothing_when_empty(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main() == 0
    assert capsys.readouterr().out == ""


def test_main_prints_one_dir_per_line(tmp_path, monkeypatch, capsys):
    make(tmp_path, pkgs=["a", "b"])
    monkeypatch.chdir(tmp_path)
    assert main() == 0
    assert capsys.readouterr().out == "a\nb\n"


@pytest.mark.parametrize(
    "literal",
    ["--cov=src", "radon cc src", "radon mi src", "vulture src", "interrogate src"],
)
def test_run_sh_has_no_hardcoded_src(literal):
    assert literal not in RUN_SH.read_text(encoding="utf-8")


def test_run_sh_calls_helper():
    assert "source_dirs.py" in RUN_SH.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run, expect failure**

Run: `cd full-audit && python3 -m pytest tests/test_source_dirs.py`
Expected: collection error `ModuleNotFoundError: No module named 'source_dirs'` (1 error, 0 passed).

---

### Task 2: GREEN - the helper (FR-1, FR-2, NFR-3, NFR-4)

**Files:**
- Create: `full-audit/lib/source_dirs.py`

**Interfaces:**
- Produces: `derive(root: Path) -> list[str]` (paths relative to `root`), `main() -> int` (prints `derive(Path.cwd())`, one per line, exit 0). `run.sh` (Task 3) relies on: CLI `python3 source_dirs.py` run in the project root, empty stdout = nothing derived.

- [ ] **Step 1: Create `full-audit/lib/source_dirs.py`**

```python
#!/usr/bin/env python3
"""Print the project's source dirs (one per line) for the full-audit checks."""
from __future__ import annotations

import tomllib
from pathlib import Path

# Top-level dirs the __init__.py probe never reports as source.
EXCLUDE = frozenset({".venv", "tests", "docs", "data", "_output", "scripts"})
# pyproject keys that declare source paths, tried in order.
KEYS = (
    ("tool", "mypy", "files"),
    ("tool", "coverage", "run", "source"),
    ("tool", "interrogate", "paths"),
    ("tool", "vulture", "paths"),
)


def _declared(cfg: dict, key: tuple[str, ...]) -> list[str]:
    for part in key:
        cfg = cfg.get(part) if isinstance(cfg, dict) else None
    if not isinstance(cfg, list):
        return []
    return [p for p in cfg if isinstance(p, str)]


def derive(root: Path) -> list[str]:
    """Return source dirs relative to root: src/, declared paths, or top-level packages."""
    if (root / "src").is_dir():
        return ["src"]
    try:
        cfg = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        cfg = {}
    for key in KEYS:
        found = [p for p in _declared(cfg, key) if (root / p).exists()]
        if found:
            return found
    return sorted(
        d.name
        for d in root.iterdir()
        if d.is_dir() and d.name not in EXCLUDE and (d / "__init__.py").is_file()
    )


def main() -> int:
    for d in derive(Path.cwd()):
        print(d)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run, expect unit tests green and the 6 static run.sh tests red**

Run: `cd full-audit && python3 -m pytest tests/test_source_dirs.py`
Expected: `6 failed, 13 passed` - failures are `test_run_sh_has_no_hardcoded_src[...]` (5) and `test_run_sh_calls_helper`.

---

### Task 3: GREEN - wire run.sh (FR-1..FR-4, NFR-2)

**Files:**
- Modify: `full-audit/lib/run.sh` (four edits, apply bottom-up or by exact text; line numbers are the current ones)

**Interfaces:**
- Consumes: `python3 "${LIB_DIR}/source_dirs.py"` (`LIB_DIR` is set at run.sh:23; cwd is the project root, `ROOT="$(pwd)"` at :19, so the helper's `Path.cwd()` is the project root).
- Produces: arrays `SRC_DIRS`, `METRIC_DIRS`, string `NO_SRC_REASON`, used only inside run.sh.

- [ ] **Step 1: Edit A - insert before line 80 (`# ── 1-3. ruff + mypy`)**

Before:
```bash
emit "00-context" "git context" "PASS" 0 "captured"

# ── 1-3. ruff + mypy
```
After:
```bash
emit "00-context" "git context" "PASS" 0 "captured"

# ── source dirs: derived once, used by mypy (03), coverage (06) and checks 14-17
# SRC_DIRS: src/ if present, else paths declared in pyproject.toml, else top-level packages.
# METRIC_DIRS: SRC_DIRS without tests/ (a declared mypy list may include it).
mapfile -t SRC_DIRS < <(python3 "${LIB_DIR}/source_dirs.py")
METRIC_DIRS=()
for d in "${SRC_DIRS[@]}"; do [[ "$d" == tests ]] || METRIC_DIRS+=("$d"); done
NO_SRC_REASON="no target dirs: no src/, no [tool.mypy|coverage.run|interrogate|vulture] paths, no top-level package"

# ── 1-3. ruff + mypy
```

- [ ] **Step 2: Edit B - mypy, lines 83-92**

Before:
```bash
# mypy: honour the project's own source layout. Many repos keep sources in src/,
# but others (e.g. multi-package backends) declare packages via [tool.mypy]
# files=... in pyproject.toml. Hardcoding `mypy src` makes mypy error with
# "Cannot read file 'src'" on those repos. Probe for a src/ dir; if absent, run
# bare `mypy` so it reads the pyproject config instead.
if [[ -d src ]]; then
  run "03-mypy"      "mypy src"            1 uv run mypy src --no-error-summary
else
  run "03-mypy"      "mypy (pyproject)"    1 uv run mypy --no-error-summary
fi
```
After:
```bash
# mypy: run on the derived source dirs; with none, bare `mypy` reads the
# pyproject config itself.
if ((${#SRC_DIRS[@]})); then
  run "03-mypy"      "mypy ${SRC_DIRS[*]}" 1 uv run mypy "${SRC_DIRS[@]}" --no-error-summary
else
  run "03-mypy"      "mypy (pyproject)"    1 uv run mypy --no-error-summary
fi
```
(For a `src/` project the name stays `mypy src` and the command is unchanged.)

- [ ] **Step 3: Edit C - coverage, lines 112-117**

Before:
```bash
if [[ $NO_TESTS -eq 0 ]]; then
  run "06-pytest-unit" "pytest unit + coverage" 1 \
    uv run pytest tests/unit -q --cov=src --cov-report=json:"${TMP}/cov.json" --cov-report=term
else
  skip "06-pytest-unit" "pytest unit" "--no-tests"
fi
```
After:
```bash
if [[ $NO_TESTS -eq 0 ]]; then
  if ((${#METRIC_DIRS[@]})); then
    COV_ARGS=("${METRIC_DIRS[@]/#/--cov=}")
    run "06-pytest-unit" "pytest unit + coverage" 1 \
      uv run pytest tests/unit -q "${COV_ARGS[@]}" --cov-report=json:"${TMP}/cov.json" --cov-report=term
  else
    skip "06-pytest-unit" "pytest unit + coverage" "$NO_SRC_REASON"
  fi
else
  skip "06-pytest-unit" "pytest unit" "--no-tests"
fi
```

- [ ] **Step 4: Edit D - checks 14-17, lines 159-163**

Before:
```bash
if have uvx; then
  run "14-radon-cc"   "radon cc (high complexity)" 0 uvx --quiet radon cc src -n C -a
  run "15-radon-mi"   "radon mi (maintainability)" 0 uvx --quiet radon mi src -n B
  run "16-vulture"    "vulture dead code"          0 uvx --quiet vulture src --min-confidence 80
  run "17-interrogate" "interrogate docstring %"   0 uvx --quiet interrogate src -q -f 70
  if [[ $QUICK -eq 0 ]]; then
```
After:
```bash
if have uvx; then
  if ((${#METRIC_DIRS[@]})); then
    run "14-radon-cc"   "radon cc (high complexity)" 0 uvx --quiet radon cc "${METRIC_DIRS[@]}" -n C -a
    run "15-radon-mi"   "radon mi (maintainability)" 0 uvx --quiet radon mi "${METRIC_DIRS[@]}" -n B
    run "16-vulture"    "vulture dead code"          0 uvx --quiet vulture "${METRIC_DIRS[@]}" --min-confidence 80
    run "17-interrogate" "interrogate docstring %"   0 uvx --quiet interrogate "${METRIC_DIRS[@]}" -q -f 70
  else
    for id in 14-radon-cc 15-radon-mi 16-vulture 17-interrogate; do
      skip "$id" "$id" "$NO_SRC_REASON"
    done
  fi
  if [[ $QUICK -eq 0 ]]; then
```

- [ ] **Step 5: Verify**

Run: `bash -n full-audit/lib/run.sh && cd full-audit && python3 -m pytest tests/test_source_dirs.py`
Expected: no bash output, `19 passed`.

---

### Task 4: Docs and changelog (FR-5)

**Files:**
- Modify: `full-audit/SKILL.md` lines 84, 87, 95-98
- Modify: `full-audit/references/checks.md` lines 9, 15
- Modify: `CHANGELOG.md` line 45 area

- [ ] **Step 1: `full-audit/SKILL.md` - replace these table rows (keep column alignment loose; markdown renders it)**

Row 3 (line 84), replace the command cell:
`` `uv run mypy <dirs> --no-error-summary` - `<dirs>` = target dirs derived by `lib/source_dirs.py`: `src/` if present, else the first non-empty of `[tool.mypy] files`, `[tool.coverage.run] source`, `[tool.interrogate] paths`, `[tool.vulture] paths` (existing dirs only), else top-level packages with `__init__.py` (not `tests`, `docs`, `data`, `_output`, `scripts`, `.venv`); none found - bare `uv run mypy` ``

Row 6 (line 87), command cell:
`` `uv run pytest tests/unit -q --cov=<dir> ... --cov-report=json:.full_audit_tmp/cov.json` - one `--cov` per derived dir without `tests`; no dirs - SKIPPED ``

Rows 14-17 (lines 95-98), replace `src` with `<dirs>` and add the suffix "(`<dirs>` as in row 3 without `tests`; none - SKIPPED)":
- 14: `` `uvx radon cc <dirs> -n C -a` (если доступен `uvx`) ``
- 15: `` `uvx radon mi <dirs> -n B` ``
- 16: `` `uvx vulture <dirs> --min-confidence 80` ``
- 17: `` `uvx interrogate <dirs> -q -f 70` ``
Put the "(`<dirs>` as in row 3 without `tests`; none - SKIPPED)" note once, at the end of row 14's command cell, and "(`<dirs>` - row 14)" in rows 15-17. Do not touch other rows (10, 12 keep `src`: out of scope).

- [ ] **Step 2: `full-audit/references/checks.md`**

Line 9: `| 03 | `mypy src` | yes | ...` -> `| 03 | `mypy <derived dirs>` | yes | Static type errors (strict on `src.shared.*`; dirs: `src/`, else pyproject paths, else top-level packages) | Fix type annotations |`
Line 15: `| 06 | `pytest tests/unit --cov` | ...` -> `| 06 | `pytest tests/unit --cov=<derived dir>` | yes | Failing unit tests / coverage drop (SKIPPED when no dirs can be derived) | Fix tests / add coverage |`

- [ ] **Step 3: `CHANGELOG.md`** - append as the last bullet of the existing `### Fixed` under `## [Unreleased]` (line 45 starts it; do not create a new subsection):

```markdown
- `/full-audit` assumed `src/`: on a layout without it, coverage (06) and radon (14, 15) passed with empty output and vulture/interrogate (16, 17) warned about a missing path (bd `python-ai-skills-5xi`). New `full-audit/lib/source_dirs.py` derives the target dirs once (`src/`, else `[tool.mypy|coverage.run|interrogate|vulture]` paths, else top-level packages); `run.sh` feeds them to mypy, coverage and checks 14-17, and records 06/14-17 as SKIPPED with a reason when nothing is derivable. Projects with `src/` run the same commands as before. `check_anchors.py`, `check_contracts.py`, `check_ssot.py` keep their `src` assumption (bd `python-ai-skills-aw0.1`).
```

- [ ] **Step 4: Check**

Run: `grep -n 'mypy src\|--cov=src\|radon cc src\|vulture src\|interrogate src' full-audit/SKILL.md full-audit/references/checks.md`
Expected: no output.

---

### Task 5: Verification

- [ ] **Step 1:** `cd full-audit && python3 -m pytest` - expect `57 passed` (38 + 19 new).
- [ ] **Step 2:** `bash -n full-audit/lib/run.sh` - expect no output, exit 0.
- [ ] **Step 3:** `ruff check full-audit` - expect `Found 5 errors.` (baseline; none in the two new files).
- [ ] **Step 4:** `make test` - expect exit 0.
- [ ] **Step 5 (smoke, NFR-2 / FR-2):**
  - `cd /home/bgs/ai-steward/Gena_Beeline_Local/taro_project_2026-04-01 && python3 /home/bgs/ai-steward/Gena_Beeline_Local/python-ai-skills/full-audit/lib/source_dirs.py` - expect exactly `backend`, `telegram_bot`, `scheduler`, `shared` (one per line).
  - `cd /home/bgs/ai-steward/Gena_Beeline_Local/Sinayara-Isuzu && python3 /home/bgs/ai-steward/Gena_Beeline_Local/python-ai-skills/full-audit/lib/source_dirs.py` - expect exactly `src`.
  - Read-only: do not run `run.sh` there.
- [ ] **Step 6:** `git status --short` - only the 6 files from "Files touched" (plus pre-existing unrelated changes) are new/modified.

---

### Task 6: Commit

- [ ] **Step 1:** stage only this task's files and commit (pre-commit hooks must pass; no `--no-verify`):

```bash
git add full-audit/lib/source_dirs.py full-audit/tests/test_source_dirs.py full-audit/lib/run.sh full-audit/SKILL.md full-audit/references/checks.md CHANGELOG.md
git commit -m "fix(full-audit): derive source dirs instead of assuming src/"
```

Do not `git push`. Step 12 review is run by the orchestrator.

---

## Self-review (Step 9)

Verification done while writing: helper and tests were run from `$TMPDIR` (outside the repo) against a copy of `run.sh` with the four edits applied - `19 passed`; against the unmodified `run.sh` the same file gave `13 passed, 6 failed` (the static checks only). `bash -n` on the edited copy: ok. The array logic was run in a stub script under `set -u` for Taro (4 dirs, 4 `--cov=` args), Sinayara-Isuzu (`src`, `--cov=src`) and an empty dir (bare mypy, 06 skipped). Not run: the real `run.sh` end to end (needs uv/uvx), the doc edits, `make test`, the repo `ruff check` baseline with the new files.

1. FR-1 -> Task 2 (`derive`, `main`) + Task 3 Edit A (once per run). FR-2 -> Task 3 Edits B-D; tests: Taro shape, config keys. FR-3 -> Task 3 Edits C-D (`skip` on empty); empty-result test. FR-4 -> one `SRC_DIRS` feeds Edit B and `METRIC_DIRS`; static test. FR-5 -> Task 4.
2. NFR-1 -> Task 5 steps 1, 4. NFR-2 -> `src` test + Task 5 step 5 + identical `mypy src` name/command. NFR-3 -> stdlib imports only. NFR-4 -> `EXCLUDE` + probe test. Q1 -> skip path; Q2 -> only noted in CHANGELOG; Q3 -> `METRIC_DIRS`; OQ-1 -> first line of `derive`; OQ-2 -> coverage uses `METRIC_DIRS`.
3. Placeholders: none; test code, helper code and run.sh edits are complete. Docs rows are given as exact target text/instructions, not full table lines (alignment left to the editor).
4. Reverse traceability: every symbol in `source_dirs.py` (`EXCLUDE` NFR-4, `KEYS` FR-1, `_declared` FR-1/FR-3 filtering, `derive`, `main`) and every run.sh addition traces to an FR/NFR above.
5. Excess-code check on GREEN: no config key `[tool.full-audit]`, no CLI args, no logging; `_declared` type guards are boundary checks on external TOML. Deleting the `isinstance(p, str)` filter would break no listed test but guards malformed user pyproject at a system boundary - kept. Deviation from design text: design says "after the `--no-tests` branch" for 06; the plan nests the emptiness check inside `NO_TESTS -eq 0` (same behaviour, smaller diff).
