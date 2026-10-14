---
feature: full-audit-source-layout
bd_id: python-ai-skills-5xi
date: 2026-10-14
status: approved
risk: low
risk_justification: One shell orchestrator (full-audit/lib/run.sh) plus its SKILL.md/references rows; deterministic, reversible, no secrets, no network; a wrong derivation is visible (red audit), not silent, and the src/ branch stays as the fallback.
evidence: strong
evidence_justification: Every src assumption located by grep; exit codes of radon/vulture/interrogate/pytest-cov on a missing dir measured in a scratch project; pyproject keys of 47 sibling projects inventoried (21 with src/, 26 without); tool config behaviour confirmed via Context7 (vulture, coverage.py, pytest-cov, radon) and interrogate 1.7.0 --help + installed source.
open_questions: []
decisions:
  - "Q1 (user, 2026-10-14): no derivable target dir -> the checks are SKIPPED with a reason via run.sh skip(), never PASS."
  - "Q2 (user, 2026-10-14): the Python self-checks (check_anchors/check_contracts/check_ssot) are out of scope here -> bd python-ai-skills-aw0.1."
  - "Q3 (user, 2026-10-14): tests/ is dropped from the derived list for radon, vulture and interrogate; mypy keeps a declared list verbatim."
functional_requirements:
  - id: FR-1
    text: run.sh derives the list of target package dirs once per run from project config, falling back to src/ when that dir exists (issue text, suggested direction).
  - id: FR-2
    text: mypy (03), coverage (06), radon cc (14), radon mi (15), vulture (16), interrogate (17) run against the derived dirs; on a backend/telegram_bot/scheduler/shared layout their excerpts are non-empty (issue ACCEPTANCE).
  - id: FR-3
    text: When nothing can be derived, checks 06/14/15/16/17 are never recorded PASS; measured today radon cc/mi exit 0 with empty output and pytest --cov=src exits 0 with "No data to report" on a missing src/.
  - id: FR-4
    text: The existing mypy branch (run.sh:88-92) and the new derivation share one decision, so mypy and the metric tools cannot disagree about the layout (prior art db54d0a; SSoT principle).
  - id: FR-5
    text: SKILL.md rows 3, 6, 14-17 and references/checks.md rows 03, 06 describe the derived target instead of the literal src (SKILL.md:84-98 is the user-facing contract of the check commands).
non_functional_requirements:
  - id: NFR-1
    text: full-audit test suite stays green (38 passed, 0 failed on 2026-10-14) and tests cover the derivation for src/, config-declared and __init__-detected layouts.
  - id: NFR-2
    text: Projects with src/ run exactly the commands they run today (21 of 47 sibling projects use src/; no scope change for them).
  - id: NFR-3
    text: Derivation needs only tools already required by run.sh (bash, python3 3.11+ with tomllib per rules/python-dev.md); no new dependency.
  - id: NFR-4
    text: Derived dirs never include .venv, tests, docs, data, _output, scripts (Taro pyproject.toml:79-81 records coverage polluted by nested .venv dirs).
constraints:
  - "radon reads [tool.radon] only for cc_min/exclude/ignore - no paths key; radon cc without a path exits 2 'the following arguments are required: paths' (Context7 /rubik/radon; measured)."
  - "interrogate 1.7.0 honours [tool.interrogate] paths only when -c pyproject.toml is passed; without -c it scans cwd including tests/ (measured; cli.py:364-365 falls back to cwd)."
  - "pytest-cov: --cov=X overrides [tool.coverage.run] source; bare --cov uses it, and bare --cov with no config measures tests too (Context7 /pytest-dev/pytest-cov; measured)."
  - "vulture reads [tool.vulture] paths; CLI args take precedence; no path and no config exits 2 'Please pass at least one file or directory' (Context7 /jendrikseipp/vulture; measured)."
  - "Taro pyproject.toml:98-102 notes interrogate hits RecursionError on that codebase - acceptance for check 17 on Taro may show an error excerpt rather than a percentage."
  - "Do not read .env or secret files in sibling projects (global Security rule); only pyproject.toml was read."
risks:
  - Top-level __init__.py probe picks tests/ (Taro has tests/__init__.py) - needs an exclusion list.
  - Multi-service repos with no top-level package (zemdozor_microservices, boilerplate_microservices, fastapi-crud-aidd-generated) still derive nothing - must land in the visible SKIPPED path, not PASS.
  - src/ projects with extra roots (Sinayara-Isuzu migrations/, migrations_mart/, tools/) - derivation must not widen their scope silently.
  - Namespace packages without __init__.py (Taro sets namespace_packages = true for mypy) are invisible to an __init__ probe; config keys stay the primary signal.
  - fingerprint.py:33-38 and check_trends.py:56-61 group findings by the segment after "src"; for non-src layouts grouping degrades (first segment / whole path) - trend pairing gets weaker but not wrong.
scope:
  in:
    - full-audit/lib/run.sh lines 88-92, 114, 160-163 (derivation + five checks)
    - full-audit/SKILL.md rows 3, 6, 14-17; full-audit/references/checks.md rows 03, 06
    - tests for the derivation in full-audit/tests/
  out:
    - thresholds (-n C, -f 70, --min-confidence 80) and required/optional flags
    - tests/golden/* fixture paths (data, not behaviour)
    - lib/ai_review_prompt.md src/ wording (agent-side review, separate concern)
  later:
    - check_anchors.py:19, check_contracts.py:11, check_ssot.py:39 - same defect class, no source in the issue text
    - fingerprint.py / check_trends.py module grouping for non-src layouts
    - summarize.py:35 remediation hint mentioning src.shared.*
---

# Discovery: full-audit source layout (python-ai-skills-5xi)

## Intent

The user wants `/full-audit` to be unable to go green by accident on a project whose code is not
under `src/`. The acceptance is behavioural: on a `backend/telegram_bot/scheduler/shared` layout the
five tools produce non-empty results. The real such project is
`/home/bgs/ai-steward/Gena_Beeline_Local/taro_project_2026-04-01` (four top-level packages, each
with `__init__.py`; also `backups/ data/ docs/ _output/ scripts/ tests/`).

## Findings - every `src` assumption in full-audit/ and what happens when src/ is absent

1. `lib/run.sh:88-92` (prior art, commit db54d0a): `if [[ -d src ]]; then run "03-mypy" ... uv run mypy src ... else run "03-mypy" "mypy (pyproject)" 1 uv run mypy --no-error-summary; fi` - mypy reads `[tool.mypy] files`. Correct on Taro (files = backend, telegram_bot, scheduler, shared).
2. `lib/run.sh:114` `pytest tests/unit -q --cov=src` (required): measured - tests run, coverage prints "Failed to generate report: No data to report", exit 0 -> **PASS, false green** for the coverage figure.
3. `lib/run.sh:160-161` `radon cc src -n C -a`, `radon mi src -n B`: measured exit 0, empty output -> **PASS, silent false green**.
4. `lib/run.sh:162` `vulture src --min-confidence 80`: exit 1 "src could not be found" -> WARN (visible, but reads like a dead-code warning).
5. `lib/run.sh:163` `interrogate src -q -f 70`: exit 2 "Path 'src' does not exist" -> WARN (visible).
6. `lib/check_anchors.py:19,50-52`, `lib/check_contracts.py:11,20-22`: `ROOT = Path.cwd() / "src"`, print "src/ absent - skipping", exit 0 -> status PASS; skip text only in the excerpt. Pinned by `tests/test_self_check_backcompat.py:22-23`.
7. `lib/check_ssot.py:39-41`: `if not src_dir.exists(): return` - knowledge-graph vs code comparison silently skipped, no message.
8. `lib/fingerprint.py:33-38`, `lib/check_trends.py:56-61`: module grouping keyed on a `src` path segment; fallback is first segment / whole path.
9. Docs: `SKILL.md:84,87,91,93,95-98,178,185-186,224`; `references/checks.md:9,16,18`; `lib/ai_review_prompt.md:17,47,118`; `lib/summarize.py:35` hint "src.shared.* is strict".

## Findings - what real projects declare

47 sibling projects with pyproject.toml: 21 have `src/`, 26 do not. Keys seen in non-src projects:
`taro_project_2026-04-01` sets `[tool.mypy] files` (line 58), `[tool.coverage.run] source` (82),
`[tool.interrogate] paths` (103), all to the same four dirs; no `[tool.vulture]`, no build-system.
`mini-crm-ai-gen` sets `[tool.coverage.run] source = ["app"]` and `[tool.mypy]` with only `exclude`.
`Prognosis` (app/), `tg_bitrix` (bot/), `uv-fastapi-example` (app/) declare nothing but pytest.
src projects: Sensedar `[tool.hatch.build.targets.wheel] packages = ["src"]`, `[tool.vulture]`,
`[tool.coverage.run]`; Sinayara-Isuzu `[tool.mypy] files = ["src", "tests"]`, hatch packages
`["src/isuzu"]`; claude_bot hatch packages `["src/ai_steward"]`. No project sets `[tool.radon]`,
`[tool.setuptools.packages]`, `[tool.poetry]` or a `[tool.full-audit]` key.

## Context7 and tool-level findings

- vulture (`/jendrikseipp/vulture` README): `[tool.vulture] paths = [...]`, CLI wins over config. Measured: no path + config -> scans config paths.
- coverage.py (`/coveragepy/coveragepy` doc/source.rst, doc/config.rst): `[tool.coverage.run] source` list of dirs or importable names; only importable files counted.
- pytest-cov (`/pytest-dev/pytest-cov` docs/config.rst): "If you use the --cov=something option (with a value) then coverage's source option will also get overridden ... use --cov (without a value)". Measured in the scratch project: bare `--cov` + `source = ["pkg"]` reports only pkg.
- radon (`/rubik/radon` _autodocs/10-configuration.md): config carries cc_min/cc_max/exclude/ignore; paths are positional and required.
- interrogate: not on Context7; `interrogate --help` lists `-c/--config FILE Read configuration from pyproject.toml or setup.cfg`; `config.py:111-119` finds pyproject.toml at the project root; measured 1.7.0: `paths` from config applied only with explicit `-c`.
