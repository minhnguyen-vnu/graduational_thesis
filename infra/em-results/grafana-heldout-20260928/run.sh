#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=$EM/evomaster-TT-129a7a56.jar
WANT_JAR=129a7a56fce83df8
BASE=$THESIS/infra/em-results/grafana-heldout-20260928
T=$THESIS/infra/grafana-target
PROXY=$THESIS/infra/evomaster-ext/selftest/capture_proxy.py
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
JH=$(/usr/libexec/java_home -v 17)
PROG=$BASE/progress.log
CSV=$BASE/runs.csv
DECLARED="PATCH /api/org/users/{user_id} role=Viewer user_id=2"
MAXT=${MAXT:-600s}
SEEDS=(${=SEEDS:-1 2 3 4 5 6 7 8 9 10})
ARMS=(${=ARMS:-auto declared})
mkdir -p $BASE/logs $BASE/tests $BASE/traffic

say () { echo "$(date +%H:%M:%S) $*" >> $PROG }
die () { say "DUNG: $*"; echo "RUN STOPPED $(date)" >> $PROG; exit 1 }

say "start arms=$ARMS seeds=$SEEDS maxTime=$MAXT"
[ -f $CSV ] || echo "arm,seed,maxtime,exit,det970,assembled,void,unconfirmed,triples" > $CSV
pgrep -f "evomaster.*\.jar" > /dev/null && die "EvoMaster khac dang chay"
JARSHA=$(shasum -a 256 $JAR | cut -c1-16)
[ "$JARSHA" = "$WANT_JAR" ] || die "jar sha $JARSHA, cho $WANT_JAR"

run () {
  local arm=$1 seed=$2
  local name=$arm-seed$seed-$MAXT
  $T/up.sh grafana-heldout 3001 > $BASE/logs/$name-up.txt 2>&1
  if ! grep -q "victim id 2 role Admin" $BASE/logs/$name-up.txt || [ $(grep -c "^login .* 200$" $BASE/logs/$name-up.txt) != 3 ]; then
    echo "$arm,$seed,$MAXT,UP,ERR,0,0,0,NA" >> $CSV
    say "$name up hong"
    return
  fi
  python3 $PROXY 3101 localhost 3001 $BASE/traffic/$name.jsonl &
  local px=$!
  sleep 2
  local OUT=$BASE/tests/$name; rm -rf $OUT
  local log=$BASE/logs/$name.log
  local extra=()
  [ $arm = declared ] && extra=(--statefulAuthzTransition "$DECLARED")
  JAVA_HOME=$JH java $DEBUG -jar $JAR --blackBox true \
    --bbSwaggerUrl file://$T/grafana-12.1.1-nokill.json \
    --bbTargetUrl http://localhost:3101 \
    --configPath $THESIS/infra/em-config/grafana-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    $extra \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 60 --maxTime $MAXT --seed $seed \
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
  local tr=$(grep -o "victim '[a-z]*', operator '[a-z]*'[^)]*" $log | sed "s/victim '\([a-z]*\)', operator '\([a-z]*\)'.* \([0-9/-]*\)$/\1<\2:\3/" | paste -sd';' -)
  echo "$arm,$seed,$MAXT,$e,$d,$ac,$vc,$uc,${tr:-NA}" >> $CSV
  say "$name exit=$e det970=$d assembled=$ac void=$vc unconfirmed=$uc triples=${tr:-NA}"
}

for seed in $SEEDS; do
  for arm in $ARMS; do
    run $arm $seed
  done
done
docker rm -f grafana-heldout >> $PROG 2>&1
echo "RUN DONE $(date)" >> $PROG
