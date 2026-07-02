#!/usr/bin/env bash
# Orchestrator: runs deterministic audit checks, writes JSONL + excerpts.
# Usage: bash run.sh [--quick] [--no-tests]
set -uo pipefail

QUICK=0
NO_TESTS=0
NO_TRENDS=0
for arg in "$@"; do
  case "$arg" in
    --quick) QUICK=1 ;;
    --no-tests) NO_TESTS=1 ;;
    --no-trends) NO_TRENDS=1 ;;
  esac
done

ROOT="$(pwd)"
TMP="${ROOT}/.full_audit_tmp"
EXCERPTS="${TMP}/excerpts"
RESULTS="${TMP}/results.jsonl"
LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

rm -rf "$TMP"
mkdir -p "$EXCERPTS"
: > "$RESULTS"
START_TS=$(date +%s)

# emit <id> <name> <status:PASS|FAIL|WARN|SKIPPED> <exit> <metric>
# excerpt is read from EXCERPTS/<id>.txt
emit() {
  local id="$1" name="$2" status="$3" code="$4" metric="$5"
  python3 -c "
import json,sys
print(json.dumps({'id':sys.argv[1],'name':sys.argv[2],'status':sys.argv[3],'exit':int(sys.argv[4]),'metric':sys.argv[5]}))
" "$id" "$name" "$status" "$code" "$metric" >> "$RESULTS"
}

# run <id> <name> <required:0|1> <command...>
# status: PASS if exit 0, FAIL if required & nonzero, WARN otherwise.
run() {
  local id="$1"; shift
  local name="$1"; shift
  local required="$1"; shift
  local out="${EXCERPTS}/${id}.txt"
  echo "▶ [$id] $name" >&2
  ( "$@" ) >"$out" 2>&1
  local code=$?
  local status
  if [[ $code -eq 0 ]]; then status=PASS
  elif [[ $required -eq 1 ]]; then status=FAIL
  else status=WARN
  fi
  # last 50 lines kept; trim file
  tail -n 50 "$out" > "${out}.tail" && mv "${out}.tail" "$out"
  local metric
  metric=$(wc -l < "$out" | tr -d ' ')
  emit "$id" "$name" "$status" "$code" "${metric} lines"
}

skip() {
  local id="$1" name="$2" reason="$3"
  echo "(reason: $reason)" > "${EXCERPTS}/${id}.txt"
  emit "$id" "$name" "SKIPPED" 0 "$reason"
  echo "⏭ [$id] $name — $reason" >&2
}

have() { command -v "$1" >/dev/null 2>&1; }

# ── 0. context
{
  echo "commit: $(git rev-parse HEAD 2>/dev/null || echo none)"
  echo "branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo none)"
  echo "dirty:"
  git status --porcelain 2>/dev/null | head -50
} > "${EXCERPTS}/00-context.txt"
emit "00-context" "git context" "PASS" 0 "captured"

# ── 1-3. ruff + mypy
run "01-ruff-check"  "ruff check"          1 uv run ruff check . --output-format=concise
run "02-ruff-format" "ruff format --check" 1 uv run ruff format --check .
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

# ── 4. secrets via gitleaks (pre-commit hook OR direct binary)
if have gitleaks; then
  run "04-gitleaks" "gitleaks detect" 1 gitleaks detect --no-banner --redact --source .
elif [[ -f .pre-commit-config.yaml ]] && grep -q gitleaks .pre-commit-config.yaml; then
  run "04-gitleaks" "pre-commit gitleaks" 1 uv run pre-commit run gitleaks --all-files
else
  skip "04-gitleaks" "gitleaks" "binary and pre-commit hook not found"
fi

# ── self-check JSON sidecars (for finding-level aggregation)
SIDECARS_DIR="${TMP}/sidecars"
mkdir -p "$SIDECARS_DIR"

# ── 5. filename policy
run "05-secret-files" "secret-file policy" 1 \
  python3 "${LIB_DIR}/check_secret_files.py" --json-out="${SIDECARS_DIR}/05-secret-files.jsonl"

# ── 6. tests + coverage
if [[ $NO_TESTS -eq 0 ]]; then
  run "06-pytest-unit" "pytest unit + coverage" 1 \
    uv run pytest tests/unit -q --cov=src --cov-report=json:"${TMP}/cov.json" --cov-report=term
else
  skip "06-pytest-unit" "pytest unit" "--no-tests"
fi

# ── 7. integration tests
if [[ $NO_TESTS -eq 0 && $QUICK -eq 0 ]]; then
  if [[ -d tests/integration ]]; then
    run "07-pytest-int" "pytest integration" 0 uv run pytest tests/integration -q
  else
    skip "07-pytest-int" "pytest integration" "tests/integration absent"
  fi
else
  skip "07-pytest-int" "pytest integration" "quick/no-tests"
fi

# ── 8-9. grace
if have grace; then
  run "08-grace-lint" "grace lint" 1 grace lint --format=text
  run "09-grace-status" "grace status" 0 grace status
else
  skip "08-grace-lint"   "grace lint"   "grace CLI not installed"
  skip "09-grace-status" "grace status" "grace CLI not installed"
fi

# ── 10-12. docs/SSoT/contracts/anchors
run "10-ssot-drift" "docs SSoT drift" 1 \
  python3 "${LIB_DIR}/check_ssot.py" --json-out="${SIDECARS_DIR}/10-ssot-drift.jsonl"

run "11-block-anchors" "block anchors paired" 1 \
  python3 "${LIB_DIR}/check_anchors.py" --json-out="${SIDECARS_DIR}/11-block-anchors.jsonl"

run "12-contracts" "MODULE_CONTRACT presence" 1 \
  python3 "${LIB_DIR}/check_contracts.py" --json-out="${SIDECARS_DIR}/12-contracts.jsonl"

# ── 13. beads
if have bd && [[ -d .beads ]]; then
  run "13-bd-doctor"   "bd doctor"     0 bd doctor
  run "13b-bd-stale"   "bd stale"      0 bd stale
  run "13c-bd-orphans" "bd orphans"    0 bd orphans
else
  skip "13-bd-doctor" "bd doctor" "bd not installed or .beads/ missing"
fi

# ── 14-18. complexity / dead code / docstrings
if have uvx; then
  run "14-radon-cc"   "radon cc (high complexity)" 0 uvx --quiet radon cc src -n C -a
  run "15-radon-mi"   "radon mi (maintainability)" 0 uvx --quiet radon mi src -n B
  run "16-vulture"    "vulture dead code"          0 uvx --quiet vulture src --min-confidence 80
  run "17-interrogate" "interrogate docstring %"   0 uvx --quiet interrogate src -q -f 70
  if [[ $QUICK -eq 0 ]]; then
    # Export deps with colour cleared.
    # Layer 1: NO_COLOR=1 — official convention; uv respects it.
    # Layer 2: sed strips any ANSI escape sequences that leak through (some
    #          uv/wrapper combos still emit colour into pipes).
    # Layer 3 (below): sanity-assert the first non-comment line looks like a pin.
    # Background: ANSI bytes in req.txt make pip-audit error on "Invalid requirement"
    # and the step silently degrades to WARN, hiding real CVEs.
    if NO_COLOR=1 uv export --no-dev --no-emit-project 2>/dev/null \
         | sed -r 's/\x1b\[[0-9;]*m//g' > "${TMP}/req.txt" \
       && [[ -s "${TMP}/req.txt" ]]; then
      first_pkg_line=$(grep -v '^#' "${TMP}/req.txt" | head -1)
      if [[ "$first_pkg_line" =~ ^[a-zA-Z0-9_.-]+== ]]; then
        # --disable-pip: skip `ensurepip` bootstrap inside uvx's ephemeral env (was failing exit 127).
        # No --strict: torch CPU-variants (e.g. 2.x+cpu) live on a separate index and are
        #              correctly reported as "skipped" rather than fatal-erroring the whole audit.
        # Honour a project-owned ignore list: .pip-audit-ignore (one vuln ID per
        # line; '#' comments and blanks allowed). Lets a repo suppress
        # accepted/under-review CVEs without editing this shared script.
        PA_IGNORE=""
        if [[ -f .pip-audit-ignore ]]; then
          while IFS= read -r _vln; do
            _vln="${_vln%%#*}"; _vln="${_vln//[[:space:]]/}"
            [[ -n "$_vln" ]] && PA_IGNORE+=" --ignore-vuln ${_vln}"
          done < .pip-audit-ignore
        fi
        run "18-pip-audit" "pip-audit" 0 bash -c "NO_COLOR=1 uvx --quiet pip-audit -r '${TMP}/req.txt' --disable-pip${PA_IGNORE}"
      else
        # Infra error — surface as FAIL, not WARN. Operator must see red.
        {
          echo "INFRA FAIL: req.txt malformed (likely uv export contamination)."
          echo "First non-comment line: ${first_pkg_line}"
          echo "Hex dump of first 80 bytes:"
          head -c 80 "${TMP}/req.txt" | xxd
        } > "${EXCERPTS}/18-pip-audit.txt"
        emit "18-pip-audit" "pip-audit" "FAIL" 1 "req.txt malformed (export contamination)"
        echo "✗ [18-pip-audit] req.txt malformed — see excerpt" >&2
      fi
    else
      skip "18-pip-audit" "pip-audit" "uv export failed"
    fi
  else
    skip "18-pip-audit" "pip-audit" "--quick"
  fi
else
  for id in 14-radon-cc 15-radon-mi 16-vulture 17-interrogate 18-pip-audit; do
    skip "$id" "$id" "uvx not available"
  done
fi

# ── 19. dependency pins
run "19-pins" "runtime deps pinned (==)" 1 \
  python3 "${LIB_DIR}/check_pins.py" --json-out="${SIDECARS_DIR}/19-pins.jsonl"

# ── 20. sentrux (best-effort; only via MCP from agent — здесь no-op)
skip "20-sentrux" "sentrux MCP" "invoked separately via MCP if available"

# ── 21. total-test (project-level e2e gate)
if [[ $QUICK -eq 0 && $NO_TESTS -eq 0 ]] && grep -qE '^total-test:' Makefile 2>/dev/null; then
  run "21-total-test" "make total-test" 0 make total-test
else
  skip "21-total-test" "make total-test" "quick/no-tests/absent"
fi

# ── 22. aggregate findings + append to history (best-effort, opt-out via --no-trends)
if [[ $NO_TRENDS -eq 0 ]]; then
  echo "▶ [22-aggregate] finding-level aggregation" >&2
  AI_REPORT_ARG=""
  if compgen -G "docs/reports/*-audit.md" > /dev/null; then
    LATEST_AI_REPORT=$(ls -1t docs/reports/*-audit.md | head -1)
    AI_REPORT_ARG="--ai-report ${LATEST_AI_REPORT}"
  fi
  SIDECAR_ARGS=""
  for f in "${SIDECARS_DIR}"/*.jsonl; do
    [ -e "$f" ] && SIDECAR_ARGS+=" --self-check-sidecar $f"
  done

  python3 "${LIB_DIR}/aggregate_findings.py" \
    --excerpts "${EXCERPTS}" \
    --out      "${TMP}/findings.jsonl" \
    $AI_REPORT_ARG \
    $SIDECAR_ARGS \
    || echo "(aggregate failed — trend section will be empty)" >&2

  python3 "${LIB_DIR}/history_store.py" append \
    --history docs/reports/.audit-history.jsonl \
    --findings "${TMP}/findings.jsonl" \
    || echo "(history append failed — non-fatal)" >&2
fi

END_TS=$(date +%s)
DURATION=$((END_TS - START_TS))
echo ""
echo "✓ pipeline done in ${DURATION}s. Results: $RESULTS"

# Brief summary with critical/middle/minor classification + remediation hints.
python3 "${LIB_DIR}/summarize.py" "$RESULTS" "$DURATION"
SUMMARY_EXIT=$?
exit $SUMMARY_EXIT
