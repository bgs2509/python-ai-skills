#!/usr/bin/env bash
# Turn the last run in the housekeeping journal into a short human summary.
#
# Runs right after the cleanup, from the same scheduler entry. The cleanup
# itself uses no model at all; this step is the only place one is involved.
#
# Never fails loudly: a summary is a convenience, and losing it must not make
# a successful cleanup look broken. Every outcome, including failure to
# produce a summary, is recorded in the journal.
#
# Usage: housekeeping-report.sh [path-to-journal]

set -uo pipefail

LOG="${1:-$HOME/.claude/housekeeping.log}"
REPORT="$HOME/.claude/housekeeping-report.md"
CLAUDE_BIN="${HOUSEKEEPING_CLAUDE:-$HOME/.local/bin/claude}"
MODEL="${HOUSEKEEPING_MODEL:-sonnet}"
KEEP_REPORTS=30
TIMEOUT=180

note() {
    printf '%s host=%s %s\n' "$(date --iso-8601=seconds)" "$(uname -n)" "$*" >>"$LOG"
}

if [ ! -r "$LOG" ]; then
    printf 'no journal at %s\n' "$LOG" >&2
    exit 0
fi

if [ ! -x "$CLAUDE_BIN" ]; then
    note 'level=ERROR part=report message="claude binary not found" path='"$CLAUDE_BIN"
    exit 0
fi

# Everything from the last "run=start" onwards is the run that just finished.
last_run=$(awk '/run=start/{buf=""} {buf=buf $0 "\n"} END{printf "%s", buf}' "$LOG")
if [ -z "$last_run" ]; then
    note 'part=report action=skip reason="journal holds no complete run"'
    exit 0
fi

# The glossary matters: without it the summary reads `reclaimable` as "this is
# what got deleted", when it is docker's ceiling for everything unused.
read -r -d '' PROMPT <<'EOF'
Ниже журнал одного запуска скрипта ежедневной уборки. Напиши короткий отчёт
по-русски: что удалено, что пропущено и почему, были ли ошибки.

Не больше 8 строк. Без вступлений, без заголовков, без похвалы и без советов.
Если удалять было нечего — скажи это одной фразой.

Как читать поля:
- mode=dry-run — это проверка, ничего не удалялось; mode=apply — удаление настоящее
- action=keep — объект защищён, причина в поле reason
- action=would-* — только показано, что было бы сделано
- reclaimable — потолок Docker для ВСЕГО неиспользуемого, а НЕ объём удалённого
- disk_gained — сколько места реально освободилось за запуск
- level=ERROR — ошибка, о ней сказать обязательно

Журнал:
EOF

summary=$(printf '%s\n%s\n' "$PROMPT" "$last_run" \
    | timeout "$TIMEOUT" "$CLAUDE_BIN" -p --model "$MODEL" \
        --disallowedTools "Bash,Read,Write,Edit,Glob,Grep,WebFetch,WebSearch,Task" 2>/dev/null)

if [ -z "${summary// /}" ]; then
    note 'level=ERROR part=report message="model produced no summary" model='"$MODEL"
    exit 0
fi

stamp=$(date --iso-8601=seconds)
tmp=$(mktemp) || exit 0
{
    printf '## %s — %s\n\n%s\n\n' "$stamp" "$(uname -n)" "$summary"
    [ -f "$REPORT" ] && cat "$REPORT"
} >"$tmp"

# Keep only the most recent reports so this file does not become the next
# thing that needs cleaning up.
awk -v keep="$KEEP_REPORTS" '/^## /{n++} n<=keep' "$tmp" >"$REPORT" && rm -f "$tmp"
note 'part=report action=written model='"$MODEL"' file='"$REPORT"
