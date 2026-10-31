#!/bin/bash
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
DIR="$(dirname "$HERE")"
W="$(mktemp -d "${TMPDIR:-/tmp}/relabel-selftest.XXXXXX")"
mkdir -p "$W/state"
cp "$DIR/GUIDE.md" "$W/GUIDE.md"
python3 "$HERE/make_fixture.py" "$W"
export RELABEL_WORK="$W" RELABEL_CLAUDE="$HERE/fake_claude.sh" RELABEL_SCALE=0.01 FAKE_STATE="$W/state" CLAUDE_CODE_SESSION_ID=phai-bi-go

python3 "$DIR/driver.py" > "$W/first.out" 2>&1 &
PID=$!
for i in $(seq 1 400); do
  [ "$(cat "$W/state/counter" 2>/dev/null || echo 0)" -ge 9 ] && break
  sleep 0.05
done
kill -9 "$PID" 2>/dev/null
wait "$PID" 2>/dev/null
AT_KILL="$(cat "$W/state/counter")"
python3 "$DIR/driver.py" > "$W/second.out" 2>&1
RC=$?
python3 "$HERE/check.py" "$W" "$AT_KILL" "$RC"
exit $?
