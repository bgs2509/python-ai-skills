#!/usr/bin/env bash
# model-run.sh — run a task on the first usable model of a role.
#
# The caller decides ONE thing: which role the task needs. Everything else
# (which model, which launch flags, how long to wait, what to do on failure,
# what to record) is decided here, deterministically, from the registry.
#
#   model-run.sh --role executor --task task.txt [--out result.md]
#
# Outcomes per attempt, written to the journal one line each:
#   ok               — model answered, exit 0. Run stops, result is in --out.
#   unavailable      — quota exhausted / 5xx / auth / network. Penalised (see registry).
#   context_overflow — task does not fit this model's window. NOT penalised.
#   timeout          — exceeded the model's timeout. NOT penalised by default.
#   error            — anything else (bad flag, crash). NOT penalised.
#
# Exit: 0 when some model answered, 1 when the role was exhausted.
set -uo pipefail

REGISTRY="${MODEL_REGISTRY:-$HOME/.claude/model-registry.json}"
JOURNAL="${MODEL_JOURNAL:-$HOME/.claude/model-journal.jsonl}"
PENALTIES="${MODEL_PENALTIES:-$HOME/.claude/model-penalties.json}"
# The Bash tool exports CLAUDE_CODE_SESSION_ID (verified 2026-09-22); the shorter
# CLAUDE_SESSION_ID does not exist, which is why early journal lines said "unknown".
SESSION="${MODEL_RUN_SESSION:-${CLAUDE_CODE_SESSION_ID:-${CLAUDE_SESSION_ID:-unknown}}}"
# Average chars per token measured on coherent English prose (2026-09-22 sweep).
CHARS_PER_TOKEN="${MODEL_CHARS_PER_TOKEN:-4.45}"

die() { printf 'model-run: %s\n' "$*" >&2; exit 2; }

ROLE=""; TASK=""; OUT=""; DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --role)    ROLE="${2:-}"; shift 2 ;;
    --task)    TASK="${2:-}"; shift 2 ;;
    --out)     OUT="${2:-}";  shift 2 ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

[ -n "$ROLE" ] || die "--role is required"
[ -n "$TASK" ] || die "--task is required"
[ -f "$TASK" ] || die "task file not found: $TASK"
[ -f "$REGISTRY" ] || die "registry not found: $REGISTRY"
command -v jq >/dev/null 2>&1 || die "jq is required"

CANDIDATES=$(jq -r --arg r "$ROLE" '.roles[$r].models[]?' "$REGISTRY") || die "cannot read registry"
[ -n "$CANDIDATES" ] || die "role '$ROLE' has no models in $REGISTRY"

CTX_CHARS=$(wc -c < "$TASK" | tr -d ' ')
CTX_TOKENS=$(awk -v c="$CTX_CHARS" -v r="$CHARS_PER_TOKEN" 'BEGIN{printf "%d", c/r}')
PENALTY_SECONDS=$(jq -r '.policy.penalty_seconds // 3600' "$REGISTRY")
OUTPUTS="${MODEL_OUTPUTS:-$(dirname "$JOURNAL")/model-outputs}"
RETENTION_DAYS=$(jq -r '.policy.output_retention_days // 14' "$REGISTRY")

mkdir -p "$(dirname "$JOURNAL")"
[ -f "$PENALTIES" ] || echo '{}' > "$PENALTIES"

# Kept outputs are machine-local evidence of non-ok attempts (NFR-3). Pruned
# here, on every real run, so the component that creates the state expires
# it — same ownership pattern as the penalty expiry below.
if [ "$DRY" -eq 0 ]; then
  mkdir -p "$OUTPUTS"
  find "$OUTPUTS" -maxdepth 1 -type f -name '*.out' -mmin "+$((RETENTION_DAYS * 1440))" -delete
fi

now() { date +%s; }

# A model is skipped while its penalty is unexpired.
penalty_active() {
  local m="$1" until
  until=$(jq -r --arg m "$m" '.[$m].until // 0' "$PENALTIES" 2>/dev/null) || until=0
  [ "$until" -gt "$(now)" ] 2>/dev/null
}

set_penalty() {
  local m="$1" reason="$2" until tmp
  until=$(( $(now) + PENALTY_SECONDS ))
  tmp=$(mktemp)
  jq --arg m "$m" --argjson u "$until" --arg r "$reason" \
     '.[$m] = {until: $u, reason: $r}' "$PENALTIES" > "$tmp" && mv "$tmp" "$PENALTIES"
}

journal() { # model pool runner seconds outcome exit attempt
  jq -nc --arg ts "$(date -Is)" --arg role "$ROLE" --arg model "$1" --arg pool "$2" \
     --arg runner "$3" --argjson ctx_chars "$CTX_CHARS" --argjson ctx_tokens "$CTX_TOKENS" \
     --argjson seconds "$4" --arg outcome "$5" --argjson exit "$6" --argjson attempt "$7" \
     --arg session "$SESSION" \
     '{ts:$ts,role:$role,model:$model,pool:$pool,runner:$runner,ctx_chars:$ctx_chars,
       ctx_tokens:$ctx_tokens,seconds:$seconds,outcome:$outcome,exit:$exit,
       attempt:$attempt,session:$session}' >> "$JOURNAL"
}

# Classify an attempt from its exit code and captured output. Text patterns
# refine a non-zero exit; they never override a zero one (exit 0 -> ok).
classify() {
  local code="$1" out_file="$2"
  [ "$code" -eq 124 ] && { echo timeout; return; }
  if [ "$code" -ne 0 ]; then
    if grep -qiE 'prompt is too long|context (length|window) exceeded|too many tokens|maximum context' "$out_file" 2>/dev/null; then
      echo context_overflow; return
    fi
    if grep -qiE 'rate.?limit|quota|usage limit|429|50[0-9] (server|error)|overloaded|authentication|unauthorized|invalid api key|connection (refused|reset)|could not connect' "$out_file" 2>/dev/null; then
      echo unavailable; return
    fi
    echo error; return
  fi
  echo ok
}

attempt=0
for MODEL in $CANDIDATES; do
  attempt=$((attempt + 1))
  spec=$(jq -c --arg m "$MODEL" '.models[$m] // empty' "$REGISTRY")
  [ -n "$spec" ] || { printf 'model-run: %s missing from .models, skipped\n' "$MODEL" >&2; continue; }

  pool=$(jq -r '.pool // "unknown"' <<<"$spec")
  runner=$(jq -r '.runner // ""' <<<"$spec")
  model_arg=$(jq -r '.model_arg // ""' <<<"$spec")
  effort=$(jq -r '.effort // empty' <<<"$spec")
  window=$(jq -r '.context_tokens // 0' <<<"$spec")
  timeout_s=$(jq -r '.timeout_seconds // 300' <<<"$spec")
  cmd_template=$(jq -r '.cmd_template // empty' <<<"$spec")
  penalize_timeout=$(jq -r '.penalize_on_timeout // false' <<<"$spec")

  if penalty_active "$MODEL"; then
    printf 'model-run: %s penalised, skipped\n' "$MODEL" >&2
    continue
  fi

  # Pre-flight window check: cheaper than discovering the overflow by running.
  if [ "$window" -gt 0 ] && [ "$CTX_TOKENS" -gt "$window" ]; then
    journal "$MODEL" "$pool" "$runner" 0 context_overflow 0 "$attempt"
    printf 'model-run: %s window %s < task %s tokens, skipped\n' "$MODEL" "$window" "$CTX_TOKENS" >&2
    continue
  fi

  # Build the command. cmd_template wins when present (used by tests and for
  # any runner the cases below do not cover).
  if [ -n "$cmd_template" ]; then
    CMD="$cmd_template"
  else
    case "$runner" in
      claude)
        CMD="claude -p --model $model_arg"
        [ -n "$effort" ] && CMD="$CMD --effort $effort" ;;
      claude-glm|claude-spark-qwen38)
        inner="$runner -p --model $model_arg"
        [ -n "$effort" ] && inner="$inner --effort $effort"
        CMD="bash -ic '$inner'" ;;
      codex)
        CMD="codex exec -s read-only --skip-git-repo-check -m $model_arg"
        [ -n "$effort" ] && CMD="$CMD -c model_reasoning_effort=$effort"
        CMD="$CMD -" ;;
      *) printf 'model-run: unknown runner %s for %s, skipped\n' "$runner" "$MODEL" >&2; continue ;;
    esac
  fi

  if [ "$DRY" -eq 1 ]; then
    printf '%s\t%s\ttimeout=%s\t%s\n' "$MODEL" "$pool" "$timeout_s" "$CMD"
    continue
  fi

  tmp_out=$(mktemp)
  t0=$(date +%s.%N)
  timeout "$timeout_s" bash -c "$CMD" < "$TASK" > "$tmp_out" 2>&1
  code=$?
  t1=$(date +%s.%N)
  secs=$(awk -v a="$t0" -v b="$t1" 'BEGIN{printf "%.2f", b-a}')

  outcome=$(classify "$code" "$tmp_out")
  journal "$MODEL" "$pool" "$runner" "$secs" "$outcome" "$code" "$attempt"

  case "$outcome" in
    ok)
      if [ -n "$OUT" ]; then mv "$tmp_out" "$OUT"; else cat "$tmp_out"; rm -f "$tmp_out"; fi
      printf 'model-run: %s answered in %ss\n' "$MODEL" "$secs" >&2
      exit 0 ;;
    unavailable)
      set_penalty "$MODEL" unavailable
      printf 'model-run: %s unavailable, penalised %ss\n' "$MODEL" "$PENALTY_SECONDS" >&2 ;;
    timeout)
      [ "$penalize_timeout" = "true" ] && set_penalty "$MODEL" timeout
      printf 'model-run: %s timed out after %ss\n' "$MODEL" "$timeout_s" >&2 ;;
    context_overflow)
      printf 'model-run: %s reported context overflow\n' "$MODEL" >&2 ;;
    *)
      printf 'model-run: %s failed (exit %s)\n' "$MODEL" "$code" >&2 ;;
  esac
  rm -f "$tmp_out"
done

[ "$DRY" -eq 1 ] && exit 0
printf 'model-run: role %s exhausted, no model answered\n' "$ROLE" >&2
exit 1
