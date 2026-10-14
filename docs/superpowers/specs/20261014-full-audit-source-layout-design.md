---
feature: full-audit-source-layout
bd_id: python-ai-skills-5xi
date: 2026-10-14
status: approved
risk: low
approach: "A - python3 helper full-audit/lib/source_dirs.py (tomllib) called once by run.sh"
context7_verified:
  - "pytest-cov==7.1.0 (/pytest-dev/pytest-cov docs/config.rst: --cov multi-allowed; --cov=X overrides [tool.coverage.run] source) + measured --cov=backend --cov=shared"
  - "coverage==7.16.2 (pulled by pytest-cov 7.1.0 in the scratch run)"
  - "radon==6.0.1 (radon cc --help / radon mi --help: 'paths ... More than one path is allowed') + measured two dirs"
  - "vulture==2.16 (vulture --help: usage vulture [options] [PATH ...]) + measured two dirs"
  - "interrogate==1.7.0 (interrogate --help: Usage interrogate [OPTIONS] [PATHS]...) + measured two dirs"
  - "python3==3.12.6 stdlib tomllib (import + parse of the scratch pyproject.toml; stdlib since 3.11 per rules/python-dev.md)"
open_questions: []
decisions:
  - "Gate 5 (user, 2026-10-14): approach A approved."
  - "OQ-1 (auto, 85 % > 80 % threshold per user profile): src/ first, then config keys, then the __init__ probe."
  - "OQ-2 (user, 2026-10-14): coverage (06) takes the tests-dropped list shared with 14-17."
---

# Design: full-audit source layout (python-ai-skills-5xi)

Requirements by id: `docs/superpowers/specs/20261014-full-audit-source-layout-discovery.md`.

## Approach summary

One new helper, `full-audit/lib/source_dirs.py`, reads `pyproject.toml` with stdlib `tomllib` and
prints the target dirs one per line. `run.sh` calls it once, stores the result in a bash array, and
all six checks (03, 06, 14-17) consume that array (FR-1, FR-4). Empty array -> 06 and 14-17 go
through the existing `skip()` with one reason string (FR-3, Q1); mypy falls back to today's bare
`mypy` (it cannot go green without targets: exits 2 "Missing target"). Projects with `src/` get
`["src"]` and run byte-identical commands (NFR-2).

## File map

- `full-audit/lib/source_dirs.py` (new, ~40 lines) - `EXCLUDE: frozenset` (NFR-4), `KEYS: tuple`
  (FR-1), `derive(root: Path) -> list[str]` (FR-1, FR-2), `main()` printing one dir per line (FR-1).
- `full-audit/lib/run.sh` - lines 88-92 (mypy, FR-4), 112-117 (coverage, FR-2/FR-3), 159-163
  (radon/vulture/interrogate, FR-2/FR-3, Q3); one new block after line 79 that fills the arrays.
- `full-audit/tests/test_source_dirs.py` (new) - unit tests of `derive()` (NFR-1) plus one static
  check of `run.sh` (FR-4).
- `full-audit/SKILL.md` rows 3, 6, 14-17 (lines 84, 87, 95-98) and
  `full-audit/references/checks.md` rows 03, 06 (lines 9, 15) - wording "derived target dirs" (FR-5).

## Derivation algorithm (`derive`, pure function of `root`)

1. `root/src` is a directory -> `["src"]` (NFR-2; OQ-1 a).
2. Else load `root/pyproject.toml` (missing or unparsable -> `{}`); walk `KEYS` in order
   `tool.mypy.files`, `tool.coverage.run.source`, `tool.interrogate.paths`, `tool.vulture.paths`
   (the four keys real non-src projects set, Discovery "what real projects declare"). The first key
   whose value is a non-empty list of strings is taken; entries whose path does not exist under
   `root` are dropped (radon exits 0 with empty output on a missing path - FR-3); if the filtered
   list is empty the next key is tried. Values are kept verbatim otherwise (files, nested dirs).
3. Else probe: sorted names of top-level dirs with `__init__.py` whose name is not in
   `EXCLUDE = {".venv", "tests", "docs", "data", "_output", "scripts"}` (NFR-4, Discovery risk 1).
4. Else `[]`.

No new config key (`[tool.full-audit]`): no project sets one (Discovery) - YAGNI.

## Data flow in run.sh

```bash
mapfile -t SRC_DIRS < <(python3 "${LIB_DIR}/source_dirs.py")      # once per run (FR-1)
METRIC_DIRS=(); for d in "${SRC_DIRS[@]}"; do [[ "$d" == tests ]] || METRIC_DIRS+=("$d"); done  # Q3
NO_SRC_REASON="no target dirs: no src/, no [tool.mypy|coverage.run|interrogate|vulture] paths, no top-level package"
```

- 03: `((${#SRC_DIRS[@]}))` -> `run "03-mypy" "mypy ${SRC_DIRS[*]}" 1 uv run mypy "${SRC_DIRS[@]}" --no-error-summary`;
  else today's bare branch unchanged (FR-4; for `src` the name and command equal today's).
- 06: after the `--no-tests` branch, `((${#METRIC_DIRS[@]}==0))` -> `skip "06-pytest-unit" ... "$NO_SRC_REASON"`;
  else `COV_ARGS=("${METRIC_DIRS[@]/#/--cov=}")` and `pytest tests/unit -q "${COV_ARGS[@]}" --cov-report=...`
  (`--cov` is multi-allowed and overrides `[tool.coverage.run] source`, verified; OQ-2 a).
- 14-17: inside `have uvx`, empty `METRIC_DIRS` -> four `skip` calls with `$NO_SRC_REASON`
  (same loop shape as the existing "uvx not available" branch); else `radon cc "${METRIC_DIRS[@]}" -n C -a`,
  `radon mi "${METRIC_DIRS[@]}" -n B`, `vulture "${METRIC_DIRS[@]}" --min-confidence 80`,
  `interrogate "${METRIC_DIRS[@]}" -q -f 70` (multiple positional paths verified for all three).
- Helper failure -> empty `mapfile` -> the SKIPPED path, never PASS (FR-3). `set -u` with empty
  arrays is safe on bash 5.2.21 (installed); arrays are only expanded behind the non-empty guard.
- 18 (pip-audit) keeps its position inside the `have uvx` block; untouched.

## Test plan sketch (NFR-1)

`tests/test_source_dirs.py`, `derive(tmp_path)` with fixtures built on disk:

1. `src/` present and a pyproject declaring more -> `["src"]` (NFR-2, OQ-1).
2. `[tool.mypy] files = ["backend", "shared"]` with dirs present -> that list (Taro shape).
3. `[tool.coverage.run] source = ["app"]`, no mypy files -> `["app"]` (mini-crm shape).
4. `[tool.interrogate] paths`, `[tool.vulture] paths` - each taken when earlier keys are absent.
5. Declared list with a missing dir -> missing entry dropped; all missing -> next key / probe.
6. No pyproject, top-level `bot/__init__.py` + `tests/__init__.py` + `docs/` -> `["bot"]` (NFR-4).
7. Nothing -> `[]`; `main()` prints nothing and exits 0.
8. Static run.sh check: `run.sh` contains `source_dirs.py` and no literal `--cov=src`,
   `radon cc src`, `radon mi src`, `vulture src`, `interrogate src` (FR-2, FR-4).

Suite baseline: 38 passed on 2026-10-14 (re-run before the change). An end-to-end `run.sh` run is
not added: it needs `uv`, `uvx` and a venv per fixture (minutes, network) - out of proportion.

## Rejected approaches

- **B - pure bash in run.sh** (grep/sed over pyproject.toml, ~35 lines): hand-rolled TOML parsing
  (multi-line arrays, quotes, comments) where stdlib `tomllib` exists - SOTA violation; testable only
  by running `run.sh` end to end - fails NFR-1 cheaply.
- **C - inline `python3 -c` heredoc inside run.sh** (no new file, ~20 lines): same derivation code
  but unreachable by a unit test without executing `run.sh`; `emit()` uses the inline form for a
  3-line snippet, not for a decision that NFR-1 requires tests for.
- **Bare `--cov` when `[tool.coverage.run] source` is set**: a second decision path for one tool,
  contradicts FR-4 (one list for all tools); the multi-`--cov` form is verified and uniform.
- **`[tool.full-audit] source` key**: no project sets it (Discovery), YAGNI; can be added later as a
  fifth entry in `KEYS` if a multi-service repo asks for it.
