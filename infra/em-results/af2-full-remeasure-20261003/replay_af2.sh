#!/usr/bin/env bash
set -u
C=/usr/bin/curl
BASE=/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/em-results/af2-full-remeasure-20261003
VENV=/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/em-results/tier1-clean-remeasure/.replay-venv
CSV=$BASE/replay.csv
LOGS=$BASE/replay-logs
mkdir -p $LOGS
echo "run,test,replay,fail_step" > $CSV

extract () {
  "$VENV/bin/python" - "$1" <<'PY'
import re, sys
src = open(sys.argv[1], encoding="utf-8", errors="replace").read()
fns = list(re.finditer(r'\n    def (test_\w+)\(', src))
for i, m in enumerate(fns):
    end = fns[i + 1].start() if i + 1 < len(fns) else len(src)
    if "Fault970" in src[m.start():end]:
        print(m.group(1))
PY
}

for d in $BASE/tests/*/; do
  run=$(basename "$d")
  suite="$d/EvoMaster_faults_Test.py"
  [ -f "$suite" ] || continue
  tests=$(extract "$suite")
  [ -z "$tests" ] && continue
  case $run in
    t1-vuln-*)       reseed=(-X POST http://localhost:8080/reset) ;;
    t1-fixed-*)      reseed=(-X POST http://localhost:8081/reset) ;;
    t2-ours-vuln-*)  reseed=(http://localhost:5002/createdb) ;;
    t2-ours-fixed-*) reseed=(http://localhost:5003/createdb) ;;
    t2b-vuln-*)      reseed=(-X POST http://localhost:8090/thesis/reset) ;;
    t2b-fixed-*)     reseed=(-X POST http://localhost:8091/thesis/reset) ;;
    *) continue ;;
  esac
  while IFS= read -r t; do
    [ -z "$t" ] && continue
    "$C" -s -o /dev/null "${reseed[@]}"
    log="$LOGS/$run-$t.log"
    ( cd "$d" && "$VENV/bin/python" -m pytest -q "EvoMaster_faults_Test.py::EvoMaster_faults_Test::$t" > "$log" 2>&1 )
    rc=$?
    if [ $rc -eq 0 ]; then
      echo "$run,$t,PASS,\"-\"" >> $CSV
    elif grep -q "ERROR collecting\|found no collectors" "$log"; then
      echo "$run,$t,ERROR,\"collection error\"" >> $CSV
    else
      step=$(grep -E "^E +assert|^E +[A-Za-z]+Error" "$log" | head -1 | sed 's/^E *//; s/,/;/g')
      [ -z "$step" ] && step="see log"
      echo "$run,$t,FAIL,\"$step\"" >> $CSV
    fi
  done <<< "$tests"
done
echo "REPLAY DONE $(date)" >> $BASE/replay.progress
awk -F, 'NR>1{c[$3]++} END{for(k in c) print k, c[k]}' $CSV >> $BASE/replay.progress
