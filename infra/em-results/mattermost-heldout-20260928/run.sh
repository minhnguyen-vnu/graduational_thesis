#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:?}
WANT_JAR=$(cut -c1-16 $JAR.sha256)
BASE=$THESIS/infra/em-results/mattermost-heldout-20260928
T=$THESIS/infra/mattermost-target
PROXY=$THESIS/infra/evomaster-ext/selftest/capture_proxy.py
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
JH=$(/usr/libexec/java_home -v 17)
PROG=$BASE/progress.log
CSV=$BASE/runs.csv
MAXT=${MAXT:-300s}
RATE=${RATE:-300}
SEEDS=(${=SEEDS:-1 2 3 4 5 6 7 8 9 10})
ARMS=(${=ARMS:-auto})
mkdir -p $BASE/logs $BASE/tests $BASE/traffic

say () { echo "$(date +%H:%M:%S) $*" >> $PROG }
die () { say "DUNG: $*"; echo "RUN STOPPED $(date)" >> $PROG; exit 1 }

say "start jar=$(basename $JAR) arms=$ARMS seeds=$SEEDS maxTime=$MAXT"
[ -f $CSV ] || echo "arm,seed,maxtime,exit,det970,assembled,void,unconfirmed,triples" > $CSV
pgrep -f "evomaster.*\.jar" > /dev/null && die "EvoMaster khac dang chay"
JARSHA=$(shasum -a 256 $JAR | cut -c1-16)
[ "$JARSHA" = "$WANT_JAR" ] || die "jar sha $JARSHA, cho $WANT_JAR"

run () {
  local arm=$1 seed=$2
  local name=$arm-seed$seed-$MAXT-$(basename $JAR .jar)
  $T/up.sh mattermost-heldout 8065 > $BASE/logs/$name-up.txt 2>&1
  if ! grep -q "^victim id-roles [a-z0-9]* system_user system_admin$" $BASE/logs/$name-up.txt || [ $(grep -c "^login .* 200$" $BASE/logs/$name-up.txt) != 3 ]; then
    echo "$arm,$seed,$MAXT,UP,ERR,0,0,0,NA" >> $CSV
    say "$name up hong"
    return
  fi
  python3 $PROXY 8165 localhost 8065 $BASE/traffic/$name.jsonl &
  local px=$!
  sleep 2
  local OUT=$BASE/tests/$name; rm -rf $OUT
  local log=$BASE/logs/$name.log
  local extra=()
  JAVA_HOME=$JH java $DEBUG -jar $JAR --blackBox true \
    --bbSwaggerUrl file://$T/mattermost-11-nokill.json \
    --bbTargetUrl http://localhost:8165 \
    --configPath $THESIS/infra/em-config/mattermost-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    $extra \
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
  local tr=$(grep -o "victim '[a-z]*', operator '[a-z]*'[^)]*" $log | sed "s/victim '\([a-z]*\)', operator '\([a-z]*\)'.* \([0-9/-]*\)$/\1<\2:\3/" | paste -sd';' -)
  echo "$arm,$seed,$MAXT,$e,$d,$ac,$vc,$uc,${tr:-NA}" >> $CSV
  say "$name exit=$e det970=$d assembled=$ac void=$vc unconfirmed=$uc triples=${tr:-NA}"
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
    say "DUNG SOM: 3 seed dau cung mau, 0 bo ba hop le"
    docker rm -f mattermost-heldout >> $PROG 2>&1
    echo "RUN STOPPED $(date)" >> $PROG
    exit 0
  fi
done
docker rm -f mattermost-heldout >> $PROG 2>&1
echo "RUN DONE $(date)" >> $PROG
