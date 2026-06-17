# Audit checks reference

For each check: what it measures, source of truth, how to act on FAIL.

| ID | Tool | Required | Measures | Action on FAIL |
|----|------|----------|----------|----------------|
| 01 | `ruff check` | yes | Lint errors (E/F/I/N/B/UP/RUF/ASYNC/S/SIM) | `uv run ruff check . --fix` |
| 02 | `ruff format --check` | yes | Formatting drift | `uv run ruff format .` |
| 03 | `mypy src` | yes | Static type errors (strict on `src.shared.*`) | Fix type annotations |
| 04 | `gitleaks` | yes | Committed secrets in git history | Rotate secret + rewrite history |
| 05 | filename allowlist | yes | Tracked secret-pattern files outside allowlist | `git rm --cached` + .gitignore |
| 06 | `pytest tests/unit --cov` | yes | Failing unit tests / coverage drop | Fix tests / add coverage |
| 07 | `pytest tests/integration` | no | Integration tests (DB, HTTP) | Bring up `make test-up` & rerun |
| 08 | `grace lint` | yes | GRACE markup integrity (XML, contracts, anchors) | Fix per `grace lint` output |
| 09 | `grace status` | no | Artefact health snapshot | Informational |
| 10 | `check_ssot.py` | yes | docs/knowledge-graph.xml ↔ src/ drift; xml staleness | `grace-refresh` / `md_to_xml.py` |
| 11 | `check_anchors.py` | yes | START_BLOCK_/END_BLOCK_ paired & unique | Fix anchors in source |
| 12 | `check_contracts.py` | yes | MODULE_CONTRACT presence in src/**/*.py | Add contract block to module |
| 13 | `bd doctor / stale / orphans` | no | Beads sync issues, stale issues, broken deps | `bd dolt push`, close/clean |
| 14 | `radon cc -n C` | no | Cyclomatic complexity ≥ rank C | Refactor function |
| 15 | `radon mi -n B` | no | Maintainability index ≤ B | Split module / reduce complexity |
| 16 | `vulture` | no | Dead code (≥80% confidence) | Delete unused symbols |
| 17 | `interrogate -f 70` | no | Docstring coverage < 70% | Add docstrings to public API |
| 18 | `pip-audit` | no | Known CVEs in pinned deps | Bump dep / pin secure version |
| 19 | `check_pins.py` | yes | Runtime deps pinned with `==` | Replace `>=`/`~=`/`^` with `==` |
| 20 | sentrux MCP | no | Architecture/contract rules + test gaps | Invoke from agent via MCP |
| 21 | `make total-test` | no | Project's own e2e quality gate | Run individually & fix |

## Status semantics

- **PASS** — exit 0
- **FAIL** — exit ≠ 0 AND check is in `REQUIRED_IDS` (see `lib/render.py`)
- **WARN** — exit ≠ 0 but check is optional
- **SKIPPED** — tool/artefact unavailable (not a failure)

## Skill exit code

- `0` — zero required FAILs
- `1` — at least one required FAIL
- `2` — pre-flight refused (life-project / no pyproject.toml)

## Trend detection (step 22)

`/full-audit` после CLI/MCP pipeline (шаги 1–21) запускает aggregator + history append (шаг 22).

### `lib/aggregate_findings.py`

Source-of-truth для per-run finding-level данных. Читает:

1. `.full_audit_tmp/excerpts/01-ruff-check.txt` → `parse_ruff`
2. `.full_audit_tmp/excerpts/03-mypy.txt` → `parse_mypy`
3. `.full_audit_tmp/excerpts/04-gitleaks.txt` → `parse_gitleaks` (если файл JSON)
4. `.full_audit_tmp/sidecars/*.jsonl` → load as-is (self-check scripts emit нормализованные findings через `--json-out=` flag)
5. `docs/reports/<latest>-audit.md` → `parse_ai_section_json` (если есть фенс-block ` ```json ` в AI deep code analysis section)

Каждый record обогащается:
- `message_canonical` — нормализованный текст для diff'инга
- `fingerprint` — strict (file:line_bucket:message)
- `fingerprint_loose` — rename-tolerant (module:message)
- `line_bucket` — `line // 5`

Output: `.full_audit_tmp/findings.jsonl`.

### `lib/history_store.py`

`append_run(history_path, findings_path, commit, run_id)` пишет каждую строку из `findings.jsonl` в `docs/reports/.audit-history.jsonl` с обогащением `{commit, run_id, date}`.

Если findings = 0, пишет sentinel-row (`{"_sentinel": True, "run_id": ..., "commit": ..., "date": ...}`). Sentinel'ы нужны чтобы total_runs накапливалось даже на чистом codebase.

### `lib/check_trends.py`

Read-only детекторы поверх `.audit-history.jsonl`:

| Detector | Условие | Output |
|----------|---------|--------|
| `find_sticky(history, min_consecutive=3)` | fingerprint в последних 3 consecutive runs | List of sticky records |
| `find_oscillating(history, window=5, min_cycles=2)` | fingerprint pattern on/off/on в окне ≥ 2 циклов | List with `cycles`, `pattern` (e.g. `X.X.X`) |
| `find_cross_breaking(history, min_repeats=2)` | (A, B) пара в одном модуле, A исчез + B появился, повторяется ≥ 2 раз | List with `module`, `fingerprints`, `boundaries` |

Sentinel-rows фильтруются из fingerprint-индексов (`_index_by_run`, `_last_seen`, `_first_seen`, `find_cross_breaking`) — они только увеличивают `total_runs` count.

### `lib/render_trends.py`

`render_trends_section(sticky, oscillating, cross_breaking, total_runs) -> str` форматирует секцию `## Trends` markdown. Возвращает пустую строку если `total_runs < 3` (`MIN_RUNS_FOR_TRENDS`).

### Disable

`bash run.sh --no-trends` пропускает шаг 22 целиком. Не рекомендуется для регулярных прогонов — теряется trend signal.

### Per-tool parser coverage (current)

| check_id              | Source                         | Parser                       |
|-----------------------|--------------------------------|------------------------------|
| 01-ruff-check         | `excerpts/01-ruff-check.txt`   | `parse_ruff`                 |
| 03-mypy               | `excerpts/03-mypy.txt`         | `parse_mypy`                 |
| 04-gitleaks           | `excerpts/04-gitleaks.txt`     | `parse_gitleaks`             |
| 05-secret-files       | `sidecars/05-secret-files.jsonl` | direct JSON load           |
| 10-ssot-drift         | `sidecars/10-ssot-drift.jsonl`   | direct JSON load           |
| 11-block-anchors      | `sidecars/11-block-anchors.jsonl` | direct JSON load          |
| 12-contracts          | `sidecars/12-contracts.jsonl`    | direct JSON load           |
| 19-pins               | `sidecars/19-pins.jsonl`         | direct JSON load           |
| ai-*                  | `<latest>-audit.md`              | `parse_ai_section_json`    |

Other checks (pytest, pip-audit, radon, vulture, interrogate, bd doctor, grace-lint, sentrux, make total-test) emit human-readable output that is not yet parsed into findings — they contribute only to check-level `results.jsonl` data. Adding parsers is the extension point: register new entry in `aggregate_findings.PARSERS` dict.
