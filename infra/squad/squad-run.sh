#!/bin/zsh
set -u

export PATH="/Users/minhnguyen/.local/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

SLOT="${1:-none}"
CLAUDE_BIN="${CLAUDE_BIN:-/Users/minhnguyen/.local/bin/claude}"
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EVOMASTER=/Users/minhnguyen/IdeaProjects/EvoMaster
SQUAD="$THESIS/infra/squad"
LEDGER="$SQUAD/reports/runs.csv"
DAY=$(date +%F)
START=$(date +%FT%H:%M:%S)
DEADLINE_MIN="${SQUAD_DEADLINE_MIN:-450}"
MAX_TURNS="${SQUAD_MAX_TURNS:-40}"
SOURCES="${SQUAD_SETTING_SOURCES:-project,local}"

mkdir -p "$SQUAD/logs" "$SQUAD/reports" "$SQUAD/tasks"
[ -f "$LEDGER" ] || echo "start,end,slot,task,exit,reason,cost_usd,turns,session" > "$LEDGER"

row() {
  echo "$START,$(date +%FT%H:%M:%S),$SLOT,$1,$2,$3,,," >> "$LEDGER"
}

if [ -f "$SQUAD/PAUSE" ]; then
  row none 0 paused
  exit 0
fi

if [ -n "${SQUAD_TASK:-}" ]; then
  TASKS=("$SQUAD_TASK")
else
  TASKS=("$SQUAD/tasks/$DAY-$SLOT"-*.md(N))
  if [ ${#TASKS[@]} -eq 0 ]; then
    TASKS=("$SQUAD/tasks/$DAY-$SLOT.md")
  fi
  if [ ! -f "${TASKS[1]}" ]; then
    TASKS=("$SQUAD/tasks/$SLOT-standing.md")
  fi
fi

if [ ! -f "${TASKS[1]}" ]; then
  row none 3 "no task file"
  exit 3
fi

cd "$THESIS" || { row none 4 "thesis dir missing"; exit 4; }
[ -x "$CLAUDE_BIN" ] || CLAUDE_BIN=$(command -v claude 2>/dev/null)
[ -n "$CLAUDE_BIN" ] && [ -x "$CLAUDE_BIN" ] || { row none 5 "claude cli not found"; exit 5; }

LAST=0

for TASK in "${TASKS[@]}"; do
  NAME="${TASK##*/}"
  START=$(date +%FT%H:%M:%S)

  if [ ! -f "$TASK" ]; then
    row "$NAME" 3 "no task file"
    continue
  fi

  if grep -q ",$NAME,0,ok," "$LEDGER" 2>/dev/null; then
    row "$NAME" 0 "already run"
    continue
  fi

  LOG="$SQUAD/logs/$DAY-${NAME%.md}.log"
  MODEL=$(head -5 "$TASK" | grep -m1 '^model:' | awk '{print $2}')
  [ -n "$MODEL" ] || MODEL="${SQUAD_MODEL:-opus}"
  echo "$START,,$SLOT,$NAME,,started $MODEL,,," >> "$LEDGER"

  caffeinate -i -t $((DEADLINE_MIN * 60)) &
  CAF=$!

  "$CLAUDE_BIN" -p "$(cat "$TASK")" \
    --add-dir "$EVOMASTER" \
    --permission-mode acceptEdits \
    --max-turns "$MAX_TURNS" \
    --model "$MODEL" \
    --setting-sources "$SOURCES" \
    --output-format json > "$LOG" 2>&1 &
  JOB=$!

  ( sleep $((DEADLINE_MIN * 60)); kill -TERM "$JOB" 2>/dev/null ) &
  WATCH=$!

  wait "$JOB"
  LAST=$?
  kill "$WATCH" 2>/dev/null
  kill "$CAF" 2>/dev/null

  FRAG=$(python3 "$SQUAD/ledger.py" "$LOG")
  echo "$START,$(date +%FT%H:%M:%S),$SLOT,$NAME,$LAST,$FRAG" >> "$LEDGER"

  if grep -qi "session limit\|usage limit\|rate limit" "$LOG" 2>/dev/null; then
    START=$(date +%FT%H:%M:%S)
    row "$NAME" "$LAST" "chain stopped on limit"
    exit "$LAST"
  fi
done

exit $LAST
