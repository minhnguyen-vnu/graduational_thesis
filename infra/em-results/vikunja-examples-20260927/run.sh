#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=$EM/evomaster-TT-129a7a56.jar
WANT_JAR=129a7a56fce83df8
BASE=$THESIS/infra/em-results/vikunja-examples-20260927
WAITFOR=$THESIS/infra/em-results/airflow-ttl-20260927/progress.log
SPEC=$THESIS/infra/vikunja-target/vikunja-2.2.2-docs-examples.json
WANT_SPEC=ca71849841104ec8
PROXY=$THESIS/infra/evomaster-ext/selftest/capture_proxy.py
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
DECLARED="POST /api/v1/projects/{projectID}/users/{userID} permission=0 projectID=4 userID=<victim>"
JH=$(/usr/libexec/java_home -v 17)
PROG=$BASE/progress.log
CSV=$BASE/runs.csv
mkdir -p $BASE/logs $BASE/tests $BASE/traffic

say () { echo "$(date +%H:%M:%S) $*" >> $PROG }
die () { say "DUNG: $*"; echo "RUN STOPPED $(date)" >> $PROG; exit 1 }

echo "Vikunja spec co example, start $(date), doi Airflow xong" > $PROG
echo "arm,seed,exit,det970,assembled,void,unconfirmed,hits_project4,sources,triples" > $CSV

while true; do
  grep -qE "RUN DONE|RUN STOPPED" $WAITFOR 2>/dev/null && break
  sleep 60
done
while pgrep -f "evomaster.*\.jar" > /dev/null; do sleep 30; done
say "Airflow: $(grep -E 'RUN DONE|RUN STOPPED' $WAITFOR)"

[ "$(shasum -a 256 $JAR | cut -c1-16)" = "$WANT_JAR" ] || die "jar sha sai"
[ "$(shasum -a 256 $SPEC | cut -c1-16)" = "$WANT_SPEC" ] || die "spec sha sai"

run () {
  local arm=$1 seed=$2
  local name=$arm-seed$seed
  zsh $THESIS/infra/vikunja-target/reset.sh 3457 > $BASE/logs/$name-reset.txt 2>&1
  grep -q "carol writes task 403" $BASE/logs/$name-reset.txt || { echo "$arm,$seed,RESET,ERR,0,0,0,0,NA,NA" >> $CSV; say "$name reset hong"; return; }
  python3 $PROXY 8188 localhost 3457 $BASE/traffic/$name.jsonl &
  local px=$!
  sleep 2
  local OUT=$BASE/tests/$name; rm -rf $OUT
  local log=$BASE/logs/$name.log
  if [ "$arm" = "declared" ]; then
    JAVA_HOME=$JH java $DEBUG -jar $JAR --blackBox true \
      --bbSwaggerUrl file://$SPEC --bbTargetUrl http://localhost:8188 \
      --configPath $THESIS/infra/em-config/vikunja-auth.yaml \
      --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
      --statefulAuthzTwoCredentialJudgment false \
      --statefulAuthzTransition "$DECLARED" \
      --outputFormat PYTHON_UNITTEST --ratePerMinute 60 --maxTime 600s --seed $seed \
      --outputFolder $OUT > $log 2>&1
  else
    JAVA_HOME=$JH java $DEBUG -jar $JAR --blackBox true \
      --bbSwaggerUrl file://$SPEC --bbTargetUrl http://localhost:8188 \
      --configPath $THESIS/infra/em-config/vikunja-auth.yaml \
      --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
      --statefulAuthzTwoCredentialJudgment false \
      --outputFormat PYTHON_UNITTEST --ratePerMinute 60 --maxTime 600s --seed $seed \
      --outputFolder $OUT > $log 2>&1
  fi
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
  local hits=$(grep -c '"path": "/api/v1/projects/4' $BASE/traffic/$name.jsonl)
  local src=$(grep -o "guarded source candidates: [0-9]*" $log | tail -1 | awk '{print $4}')
  local tr=$(grep -o "victim '[a-z]*', operator '[a-z]*'[^)]*" $log | sed "s/victim '\([a-z]*\)', operator '\([a-z]*\)'.* \([0-9/-]*\)$/\1<\2:\3/" | paste -sd';' -)
  echo "$arm,$seed,$e,$d,$ac,$vc,$uc,$hits,${src:-NA},${tr:-NA}" >> $CSV
  say "$name exit=$e det970=$d assembled=$ac void=$vc unconfirmed=$uc hits_project4=$hits sources=${src:-NA} triples=${tr:-NA}"
}

for seed in 1 2; do
  run auto $seed
  run declared $seed
done

docker stop vikunja-em >> $PROG 2>&1
say "sao luu"
cd /Users/minhnguyen/IdeaProjects
TAR=~/thesis-backups/thesis-full-$(date +%Y%m%d-%H%M).tar.gz
tar --exclude 'graduational-thesis/infra/em-venv' -czf $TAR graduational-thesis
shasum -a 256 $TAR > $TAR.sha256
say "sao luu $TAR"
echo "RUN DONE $(date)" >> $PROG
