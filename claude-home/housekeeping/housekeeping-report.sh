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

# Отправка в Telegram переиспользует получателя server-monitor, а не заводит
# своего: TG_BOT_TOKEN и TG_USER_ID читаются из его .env, того же файла, что
# использует works/server-monitor/src/srvmon/telegram.py на этой же машине.
# Вызывать сам python-модуль отсюда не стали: это добавило бы скрипту
# зависимость от раскладки чужого репозитория ради пяти строк, которые
# на bash с curl пишутся на месте.
SRVMON_ENV="${HOUSEKEEPING_TELEGRAM_ENV:-$HOME/works/server-monitor/.env}"

note() {
    printf '%s host=%s %s\n' "$(date --iso-8601=seconds)" "$(uname -n)" "$*" >>"$LOG"
}

# Отказ здесь никогда не меняет код возврата скрипта — вызывающий получает
# успешный отчёт-файл даже если сообщение в Telegram не дошло. Токен читается
# из окружения и нигде не печатается: ни curl, ни его вывод в журнал не идут.
send_telegram() {
    local text="$1"
    if [ -r "$SRVMON_ENV" ]; then
        set -a
        # shellcheck disable=SC1090
        . "$SRVMON_ENV"
        set +a
    fi
    if [ -z "${TG_BOT_TOKEN:-}" ] || [ -z "${TG_USER_ID:-}" ]; then
        note 'level=ERROR part=report message="TG_BOT_TOKEN or TG_USER_ID not set"' \
            "env=$SRVMON_ENV"
        return 0
    fi
    if ! curl -fsS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
            --data-urlencode "chat_id=${TG_USER_ID}" \
            --data-urlencode "text=${text}" \
            -o /dev/null 2>/dev/null; then
        note 'level=ERROR part=report message="telegram send failed"'
        return 0
    fi
    note 'part=report action=sent-telegram'
    return 0
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

send_telegram "$summary"
exit 0
