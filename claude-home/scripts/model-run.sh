#!/usr/bin/env bash
# model-run.sh — run a task on the first usable model of a role.
#
# The caller decides ONE thing: which role the task needs. Everything else
# (which model, which launch flags, how long to wait, what to do on failure,
# what to record) is decided here, deterministically, from the registry.
#
#   model-run.sh --role executor --task task.txt [--out result.md] [--expect REGEX]
#
# --expect REGEX — extended regex (grep -E) the answer must contain; a miss
#   or an empty answer becomes check_failed instead of ok. Rejected at
#   startup (exit 2) if the regex is invalid or matches the task file itself.
#
# Outcomes per attempt, written to the journal one line each:
#   ok               — model answered, exit 0, non-empty, --expect matched.
#   unavailable      — quota exhausted / 5xx / auth / network.
#   context_overflow — task does not fit this model's window.
#   timeout          — exceeded the effective timeout (role or model).
#   check_failed     — exit 0 but empty or missed --expect.
#   error            — anything else (bad flag, crash).
#   interrupted      — model-run.sh got SIGINT/SIGTERM mid-attempt; the model
#                      command is stopped and the run exits 130 / 143.
#
# Answer file: each attempt gets MODEL_RUN_ANSWER_FILE in its environment. A
# command that writes its final answer there (the codex runner does, via -o)
# has that file taken as the answer — for the empty/--expect checks and for
# --out — instead of its full stdout log. Otherwise stdout is the answer.
#
# Timeout: the model's timeout_seconds, unless the role declares its own
# roles.<role>.timeout_seconds, which then applies to every model of that role.
#
# Penalties: an outcome listed in the registry's policy.penalize_on (default
# ["unavailable"]) penalises the whole model for policy.penalty_seconds; a
# timeout also does when the model sets penalize_on_timeout.
#
# Non-ok attempts that ran keep their output under $MODEL_OUTPUTS (default:
# next to the journal); the journal line's out_path/out_bytes point to it.
#
# Exit: 0 when some model answered, 1 when the role was exhausted, 2 on a
# usage or local error (bad flag, bad registry value, unusable outputs dir,
# unwritable --out).
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
# A flag that takes a value must have one; without this check `shift 2` fails
# on the last argument and the parse loop never ends. Another flag in the value
# position (`--out --dry-run`) is a missing value too, not a path.
is_flag() { case "$1" in --role|--task|--out|--expect|--dry-run|-h|--help) return 0 ;; esac; return 1; }
need_value() { [ "$1" -ge 2 ] && ! is_flag "$3" || die "$2 needs a value"; }

ROLE=""; TASK=""; OUT=""; EXPECT=""; EXPECT_SET=0; DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --role)    need_value $# "$1" "${2-}"; ROLE="$2"; shift 2 ;;
    --task)    need_value $# "$1" "${2-}"; TASK="$2"; shift 2 ;;
    --out)     need_value $# "$1" "${2-}"; OUT="$2";  shift 2 ;;
    --expect)  need_value $# "$1" "${2-}"; EXPECT="$2"; EXPECT_SET=1; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

[ -n "$ROLE" ] || die "--role is required"
[ -n "$TASK" ] || die "--task is required"
[ -f "$TASK" ] || die "task file not found: $TASK"
[ -f "$REGISTRY" ] || die "registry not found: $REGISTRY"
command -v jq >/dev/null 2>&1 || die "jq is required"

[ "$EXPECT_SET" -eq 1 ] && [ -z "$EXPECT" ] \
  && die "--expect needs a non-empty regex; an empty one would silently disable the check"
if [ -n "$EXPECT" ]; then
  grep -qE -- "$EXPECT" </dev/null
  [ $? -eq 2 ] && die "--expect is not a valid extended regex: $EXPECT"
  grep -qE -- "$EXPECT" "$TASK" && die "--expect matches the task text; it would pass on an echoed prompt"
fi

# A role marked "dispatch": false (orchestrator) is a reference list for humans.
[ "$(jq -r --arg r "$ROLE" '.roles[$r].dispatch' "$REGISTRY")" = "false" ] \
  && die "role '$ROLE' is reference-only (dispatch: false) and cannot be run"
CANDIDATES=$(jq -r --arg r "$ROLE" '.roles[$r].models[]?' "$REGISTRY") || die "cannot read registry"
[ -n "$CANDIDATES" ] || die "role '$ROLE' has no models in $REGISTRY"

CTX_CHARS=$(wc -c < "$TASK" | tr -d ' ')
CTX_TOKENS=$(awk -v c="$CTX_CHARS" -v r="$CHARS_PER_TOKEN" 'BEGIN{printf "%d", c/r}')
PENALTY_SECONDS=$(jq -r '.policy.penalty_seconds // 3600' "$REGISTRY")
PENALIZE_ON=$(jq -c '.policy.penalize_on // ["unavailable"]' "$REGISTRY")
# Must be a JSON positive integer when present: false, "", "900" or 1.5 are
# rejected instead of silently falling back to the model timeout.
ROLE_TIMEOUT=$(jq -r --arg r "$ROLE" '.roles[$r] | if has("timeout_seconds")
  then (.timeout_seconds | if type == "number" and . == floor and . > 0 then tostring
        else "INVALID:\(tojson)" end)
  else empty end' "$REGISTRY")
[ -z "$ROLE_TIMEOUT" ] || [[ "$ROLE_TIMEOUT" =~ ^[1-9][0-9]*$ ]] \
  || die "roles.$ROLE.timeout_seconds must be a positive integer, got: ${ROLE_TIMEOUT#INVALID:}"
OUTPUTS="${MODEL_OUTPUTS:-$(dirname "$JOURNAL")/model-outputs}"
RETENTION_DAYS=$(jq -r '.policy.output_retention_days // 14' "$REGISTRY")
[[ "$RETENTION_DAYS" =~ ^[1-9][0-9]*$ ]] \
  || die "policy.output_retention_days must be a positive integer, got: '$RETENTION_DAYS'"

# Kept outputs are machine-local evidence of non-ok attempts (NFR-3). Pruned
# here, on every real run, so the component that creates the state expires
# it — same ownership pattern as the penalty expiry below.
if [ "$DRY" -eq 0 ]; then
  # State is created only by a real run; a dry run reads it if present.
  mkdir -p "$(dirname "$JOURNAL")"
  [ -f "$PENALTIES" ] || echo '{}' > "$PENALTIES"
  # A local fault here must stop the run: otherwise every model would be
  # journalled as a failed attempt although none of them ran.
  mkdir -p "$OUTPUTS" 2>/dev/null && [ -d "$OUTPUTS" ] && [ -w "$OUTPUTS" ] \
    || die "outputs dir not usable: $OUTPUTS"
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

penalised_outcome() { jq -e --arg o "$1" 'index($o) != null' <<<"$PENALIZE_ON" >/dev/null; }

# Each line opens with n — a five-digit sequence number, the last line's n plus
# one, wrapping 99999 -> 00001. Read-increment-append runs under flock so that
# parallel runs never share a number.
journal() { # model pool runner seconds outcome exit attempt out_path out_bytes
  local last n
  exec {lock}>>"$JOURNAL"
  flock "$lock"
  last=$(tail -n 1 "$JOURNAL" | jq -r '.n // empty' 2>/dev/null)
  n=1
  [[ "$last" =~ ^[0-9]{5}$ ]] && n=$(( 10#$last % 99999 + 1 ))
  jq -nc --arg n "$(printf '%05d' "$n")" --arg ts "$(date -Is)" --arg role "$ROLE" --arg model "$1" --arg pool "$2" \
     --arg runner "$3" --argjson ctx_chars "$CTX_CHARS" --argjson ctx_tokens "$CTX_TOKENS" \
     --argjson seconds "$4" --arg outcome "$5" --argjson exit "$6" --argjson attempt "$7" \
     --arg session "$SESSION" --arg out_path "${8:-}" --arg out_bytes "${9:-}" \
     '{n:$n,ts:$ts,role:$role,model:$model,pool:$pool,runner:$runner,ctx_chars:$ctx_chars,
       ctx_tokens:$ctx_tokens,seconds:$seconds,outcome:$outcome,exit:$exit,
       attempt:$attempt,session:$session,
       out_path:(if $out_path == "" then null else $out_path end),
       out_bytes:(if $out_bytes == "" then null else ($out_bytes | tonumber) end)}' >&"$lock"
  exec {lock}>&-
}

# Classify an attempt from its exit code and captured output. Text patterns
# refine a non-zero exit; they never override a zero one (exit 0 -> ok).
classify() {
  local code="$1" out_file="$2" answer="$2"
  [ -s "${3:-}" ] && answer="$3"
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
  grep -q '[^[:space:]]' "$answer" || { echo check_failed; return; }
  if [ -n "$EXPECT" ] && ! grep -qE -- "$EXPECT" "$answer"; then echo check_failed; return; fi
  echo ok
}

# Stop the running model command (timeout forwards TERM to its process group),
# journal the attempt with its kept output, and exit 128+signal.
on_signal() {
  local exit_code="$1" secs bytes
  kill -TERM "$child" 2>/dev/null
  wait "$child" 2>/dev/null
  rm -f "$answer_file"
  secs=$(awk -v a="$t0" -v b="$(date +%s.%N)" 'BEGIN{printf "%.2f", b-a}')
  bytes=$(wc -c < "$tmp_out" | tr -d ' ')
  journal "$MODEL" "$pool" "$runner" "$secs" interrupted "$exit_code" "$attempt" "$tmp_out" "$bytes"
  printf 'model-run: %s interrupted (output kept: %s)\n' "$MODEL" "$tmp_out" >&2
  exit "$exit_code"
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
  [ -n "$ROLE_TIMEOUT" ] && timeout_s="$ROLE_TIMEOUT"
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
        CMD="$CMD -o \"\$MODEL_RUN_ANSWER_FILE\" -" ;;
      *) printf 'model-run: unknown runner %s for %s, skipped\n' "$runner" "$MODEL" >&2; continue ;;
    esac
  fi

  if [ "$DRY" -eq 1 ]; then
    printf '%s\t%s\ttimeout=%s\t%s\n' "$MODEL" "$pool" "$timeout_s" "$CMD"
    continue
  fi

  tmp_out=$(mktemp --suffix=.out "$OUTPUTS/$(date +%Y%m%dT%H%M%S)-${MODEL//[^A-Za-z0-9._-]/_}-XXXXXX") \
    || die "cannot create an output file in $OUTPUTS"
  answer_file="${tmp_out%.out}-answer.out"
  # Pre-created private: a writer that truncates an existing file keeps its
  # mode, so the answer stays 0600 like the capture file whatever the umask.
  (umask 077; : > "$answer_file")
  t0=$(date +%s.%N)
  # Background + wait: bash runs a trap only after a FOREGROUND child exits,
  # which would delay an interrupt by up to the model timeout.
  MODEL_RUN_ANSWER_FILE="$answer_file" timeout "$timeout_s" bash -c "$CMD" < "$TASK" > "$tmp_out" 2>&1 &
  child=$!
  trap 'on_signal 130' INT
  trap 'on_signal 143' TERM
  wait "$child"
  code=$?
  trap - INT TERM
  t1=$(date +%s.%N)
  secs=$(awk -v a="$t0" -v b="$t1" 'BEGIN{printf "%.2f", b-a}')

  outcome=$(classify "$code" "$tmp_out" "$answer_file")
  deliver="$tmp_out"
  [ "$outcome" = ok ] && [ -s "$answer_file" ] && deliver="$answer_file"

  out_path=""
  out_bytes=""
  if [ "$outcome" != "ok" ]; then
    out_path="$tmp_out"
    out_bytes=$(wc -c < "$tmp_out" | tr -d ' ')
  fi

  journal "$MODEL" "$pool" "$runner" "$secs" "$outcome" "$code" "$attempt" "$out_path" "$out_bytes"

  [ "$outcome" = ok ] || rm -f "$answer_file"
  penalty_note=""
  if penalised_outcome "$outcome" || { [ "$outcome" = timeout ] && [ "$penalize_timeout" = "true" ]; }; then
    set_penalty "$MODEL" "$outcome"
    penalty_note=", penalised ${PENALTY_SECONDS}s"
  fi

  case "$outcome" in
    ok)
      if [ -n "$OUT" ]; then
        mv -- "$deliver" "$OUT" || {
          printf 'model-run: cannot write --out %s; answer kept at %s\n' "$OUT" "$deliver" >&2
          # Keep only the file that holds the answer (it is named above).
          if [ "$deliver" = "$tmp_out" ]; then rm -f "$answer_file"; else rm -f "$tmp_out"; fi
          exit 2
        }
      else
        cat "$deliver"; rm -f "$deliver"
      fi
      [ "$deliver" = "$tmp_out" ] || rm -f "$tmp_out"
      rm -f "$answer_file"
      printf 'model-run: %s answered in %ss\n' "$MODEL" "$secs" >&2
      exit 0 ;;
    unavailable)
      printf 'model-run: %s unavailable%s (output kept: %s)\n' "$MODEL" "$penalty_note" "$tmp_out" >&2 ;;
    timeout)
      printf 'model-run: %s timed out after %ss%s (output kept: %s)\n' "$MODEL" "$timeout_s" "$penalty_note" "$tmp_out" >&2 ;;
    context_overflow)
      printf 'model-run: %s reported context overflow%s (output kept: %s)\n' "$MODEL" "$penalty_note" "$tmp_out" >&2 ;;
    check_failed)
      printf 'model-run: %s answer failed the check%s (output kept: %s)\n' "$MODEL" "$penalty_note" "$tmp_out" >&2 ;;
    *)
      printf 'model-run: %s failed (exit %s%s, output kept: %s)\n' "$MODEL" "$code" "$penalty_note" "$tmp_out" >&2 ;;
  esac
done

[ "$DRY" -eq 1 ] && exit 0
printf 'model-run: role %s exhausted, no model answered\n' "$ROLE" >&2
exit 1
