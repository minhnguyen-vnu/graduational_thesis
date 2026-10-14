#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=${JAR:?}
WANT_JAR=$(cut -c1-16 $JAR.sha256)
BASE=$THESIS/infra/em-results/aicc-heldout-20260929
T=$THESIS/infra/aicc-target
PROXY=$THESIS/infra/evomaster-ext/selftest/capture_proxy.py
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
JH=$(/usr/libexec/java_home -v 17)
PROG=$BASE/progress.log
CSV=$BASE/runs.csv
MAXT=${MAXT:-300s}
RATE=${RATE:-600}
NEED_TESTS=352
SEEDS=(${=SEEDS:-1 2 3 4 5 6 7 8 9 10})
ARMS=(${=ARMS:-auto})
mkdir -p $BASE/logs $BASE/tests $BASE/traffic

say () { echo "$(date +%H:%M:%S) $*" >> $PROG }
die () { say "DUNG: $*"; docker rm -f aicc-heldout aicc-heldout-db >> $PROG 2>&1; echo "RUN STOPPED $(date)" >> $PROG; exit 1 }

say "start jar=$(basename $JAR) arms=$ARMS seeds=$SEEDS maxTime=$MAXT rate=$RATE"
[ -f $CSV ] || echo "arm,seed,maxtime,exit,det970,assembled,void,unconfirmed,evaluated_tests,victim_logins,triples" > $CSV
pgrep -f "evomaster.*\.jar" > /dev/null && die "EvoMaster khac dang chay"
JARSHA=$(shasum -a 256 $JAR | cut -c1-16)
[ "$JARSHA" = "$WANT_JAR" ] || die "jar sha $JARSHA, cho $WANT_JAR"

run () {
  local arm=$1 seed=$2
  local name=$arm-seed$seed-$MAXT-$(basename $JAR .jar)
  local T0=$(date +%s)
  $T/up.sh aicc-heldout 8097 > $BASE/logs/$name-up.txt 2>&1
  if ! grep -q "^user victim [0-9a-f-]* ADMIN ACTIVE$" $BASE/logs/$name-up.txt || [ $(grep -c "^login .* 200$" $BASE/logs/$name-up.txt) != 3 ]; then
    echo "$arm,$seed,$MAXT,UP,ERR,0,0,0,NA,NA,NA" >> $CSV
    say "$name up hong"
    return
  fi
  python3 $PROXY 8197 localhost 8097 $BASE/traffic/$name.jsonl &
  local px=$!
  sleep 2
  local OUT=$BASE/tests/$name; rm -rf $OUT
  local log=$BASE/logs/$name.log
  JAVA_HOME=$JH java $DEBUG -jar $JAR --blackBox true \
    --bbSwaggerUrl file://$T/aicc-47116cf6-nokill.json \
    --bbTargetUrl http://localhost:8197 \
    --configPath $THESIS/infra/em-config/aicc-auth.yaml \
    --header0 "X-AICC-Csrf: 1" \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute $RATE --maxTime $MAXT --seed $seed \
    --outputFolder $OUT > $log 2>&1
  local e=$?
  kill $px
  local d=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")
  local ac=$(grep -c "Assembled .* statuses" $log)
  local vc=$(grep -c "Discarded a VOID stateful-authorization" $log)
  local uc=$(grep -c "Discarded an UNCONFIRMED stateful-authorization" $log)
  local ev=$(grep -a "Evaluated tests" $log | tail -1 | awk '{print $NF}')
  local vl=$(grep -cE '"username\\": ?\\"victim\\"' $BASE/traffic/$name.jsonl)
  local tr=$(grep -o "victim '[a-z]*', operator '[a-z]*'[^)]*" $log | sed "s/victim '\([a-z]*\)', operator '\([a-z]*\)'.* \([0-9/-]*\)$/\1<\2:\3/" | paste -sd';' -)
  local sl=$(pmset -g log | awk -v a="$(date -r $T0 '+%Y-%m-%d %H:%M:%S')" '($1" "$2)>=a' | grep -c "Entering Sleep")
  echo "$arm,$seed,$MAXT,$e,$d,$ac,$vc,$uc,${ev:-NA},$vl,${tr:-NA}" >> $CSV
  say "$name exit=$e det970=$d assembled=$ac void=$vc unconfirmed=$uc evaluated_tests=${ev:-NA} victim_logins=$vl sleep_events=$sl triples=${tr:-NA}"
  [ "$sl" = "0" ] || die "may ngu trong luot $name"
  if [ "$seed" = "${SEEDS[1]}" ]; then
    [ "$vl" -gt 0 ] || die "DUNG SOM luat 1: seed $seed khong co dang nhap victim"
    [ "${ev:-0}" -ge $NEED_TESTS ] || die "DUNG SOM luat 1: seed $seed evaluated_tests ${ev:-NA} < $NEED_TESTS"
  fi
}

stuck () {
  python3 - $CSV <<'PY'
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
rows = rows[:3]
if len(rows) < 3:
    print(0); sys.exit()
pat = lambda r: tuple(sorted(set(t.split(":")[-1] for t in r["triples"].split(";"))))
print(1 if all(r["assembled"] == "0" for r in rows) and len({pat(r) for r in rows}) == 1 else 0)
PY
}

for seed in $SEEDS; do
  for arm in $ARMS; do
    run $arm $seed
  done
  if [ "$(stuck)" = 1 ]; then
    say "DUNG SOM luat 2: 3 seed dau cung mau, 0 bo ba hop le"
    docker rm -f aicc-heldout aicc-heldout-db >> $PROG 2>&1
    echo "RUN STOPPED $(date)" >> $PROG
    exit 0
  fi
done
docker rm -f aicc-heldout aicc-heldout-db >> $PROG 2>&1
echo "RUN DONE $(date)" >> $PROG
