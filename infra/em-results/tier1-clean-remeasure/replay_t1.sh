#!/usr/bin/env zsh
set -u
BASE=/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/em-results/tier1-clean-remeasure
VENV=$BASE/.replay-venv
CSV=$BASE/replay.csv
LOGS=$BASE/replay-logs
mkdir -p $LOGS

if [ ! -x $VENV/bin/python ]; then
  python3 -m venv $VENV
  $VENV/bin/pip -q install pytest requests timeout_decorator rfc3986
fi

echo "run,test,replay,fail_step" > $CSV

for d in $BASE/tests/t1-*/; do
  run=$(basename $d)
  t=$($VENV/bin/python - "$d/EvoMaster_faults_Test.py" <<'PY'
import re, sys, os
p = sys.argv[1]
if not os.path.exists(p):
    sys.exit(0)
src = open(p, encoding="utf-8", errors="replace").read()
fns = list(re.finditer(r'\n    def (test_\w+)\(', src))
for i, m in enumerate(fns):
    end = fns[i+1].start() if i+1 < len(fns) else len(src)
    if "# Fault970" in src[m.start():end]:
        print(m.group(1))
PY
)
  [ -z "$t" ] && continue
  case $run in *vuln*) port=8080 ;; *) port=8081 ;; esac
  curl -s -o /dev/null -X POST http://localhost:$port/reset
  log=$LOGS/$run.log
  ( cd $d && $VENV/bin/python -m pytest -q "EvoMaster_faults_Test.py::EvoMaster_faults_Test::$t" > $log 2>&1 )
  if [ $? -eq 0 ]; then
    echo "$run,$t,PASS,\"-\"" >> $CSV
  else
    if grep -q "ERROR collecting\|found no collectors" $log; then
      echo "$run,$t,ERROR,\"collection error - see $log\"" >> $CSV; continue
    fi
    step=$(grep -E "^E +assert|^E +[A-Za-z]+Error" $log | head -1 | sed 's/^E *//; s/,/;/g')
    [ -z "$step" ] && step="see $log"
    echo "$run,$t,FAIL,\"$step\"" >> $CSV
  fi
done

echo "replay done $(date)"
awk -F, 'NR>1{c[$3]++} END{for(k in c) print k, c[k]}' $CSV
