#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=$EM/evomaster-TT-129a7a56.jar
WANT_JAR=129a7a56fce83df8
BASE=$THESIS/infra/em-results/airflow-ttl-20260927
WAITFOR=$THESIS/infra/em-results/transitiontrim-chain-20260927c/progress.log
PROXY=$THESIS/infra/evomaster-ext/selftest/capture_proxy.py
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
JH=$(/usr/libexec/java_home -v 17)
PROG=$BASE/progress.log
CSV=$BASE/runs.csv
mkdir -p $BASE/logs $BASE/tests $BASE/traffic

say () { echo "$(date +%H:%M:%S) $*" >> $PROG }
die () { say "DUNG: $*"; echo "RUN STOPPED $(date)" >> $PROG; exit 1 }

echo "Airflow hai nhanh cache_ttl, start $(date), doi chuoi transition-trim xong" > $PROG
echo "arm,port,cache_ttl,seed,exit,det970,assembled,void,unconfirmed,triples" > $CSV

while true; do
  grep -qE "CHAIN DONE|CHAIN STOPPED" $WAITFOR 2>/dev/null && break
  sleep 60
done
while pgrep -f "evomaster.*\.jar" > /dev/null; do sleep 30; done
say "chuoi truoc: $(grep -E 'CHAIN DONE|CHAIN STOPPED' $WAITFOR)"

JARSHA=$(shasum -a 256 $JAR | cut -c1-16)
[ "$JARSHA" = "$WANT_JAR" ] || die "jar sha $JARSHA, cho $WANT_JAR"

if ! docker ps --format '{{.Names}}' | grep -q '^airflow-ttl0$'; then
  docker rm -f airflow-ttl0 >> $PROG 2>&1
  docker run -d --name airflow-ttl0 -p 8084:8080 \
    -e AIRFLOW__CORE__AUTH_MANAGER=airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager \
    -e AIRFLOW__API_AUTH__JWT_SECRET=thesis-airflow-jwt-secret \
    -e AIRFLOW__CORE__LOAD_EXAMPLES=False \
    -e AIRFLOW__FAB__CACHE_TTL=0 \
    airflow-fab-vuln bash -c "airflow db migrate && airflow fab-db migrate && \
      airflow users create -u admin -p adminpass -f a -l a -r Admin -e a@x.com && \
      airflow users create -u victim -p victimpass -f v -l v -r Op -e v@x.com && airflow api-server" >> $PROG 2>&1
fi
for i in $(seq 1 90); do
  [ "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' -X POST -H 'Content-Type: application/json' \
    -d '{"username":"admin","password":"adminpass"}' http://localhost:8084/auth/token)" = "201" ] && break
  sleep 5
done
say "airflow-ttl0 /auth/token: $(curl -s -o /dev/null --max-time 5 -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{"username":"admin","password":"adminpass"}' http://localhost:8084/auth/token)"

T8082=$(docker exec airflow-vuln airflow config get-value fab cache_ttl 2>/dev/null | tail -1)
T8084=$(docker exec airflow-ttl0 airflow config get-value fab cache_ttl 2>/dev/null | tail -1)
say "cache_ttl: airflow-vuln=$T8082 airflow-ttl0=$T8084"
[ "$T8082" = "30" ] && [ "$T8084" = "0" ] || die "cache_ttl khong dung nhu khai"
say "image: airflow-vuln=$(docker inspect -f '{{.Image}}' airflow-vuln | cut -c1-19) airflow-ttl0=$(docker inspect -f '{{.Image}}' airflow-ttl0 | cut -c1-19)"

run () {
  local arm=$1 port=$2 ttl=$3 pport=$4 seed=$5
  local name=$arm-seed$seed
  zsh $THESIS/infra/airflow-target/reset-3users.sh http://localhost:$port > $BASE/logs/$name-reset.txt 2>&1
  if ! grep -q "victim roles \['Op'\]" $BASE/logs/$name-reset.txt || ! grep -q "viewer roles \['Viewer'\]" $BASE/logs/$name-reset.txt; then
    echo "$arm,$port,$ttl,$seed,RESET,ERR,0,0,0,NA" >> $CSV
    say "$name reset hong"
    return
  fi
  python3 $PROXY $pport localhost $port $BASE/traffic/$name.jsonl &
  local px=$!
  sleep 2
  local OUT=$BASE/tests/$name; rm -rf $OUT
  local log=$BASE/logs/$name.log
  JAVA_HOME=$JH java $DEBUG -jar $JAR --blackBox true \
    --bbSwaggerUrl file://$THESIS/infra/airflow-target/airflow-merged-nodelete.json \
    --bbTargetUrl http://localhost:$pport \
    --configPath $THESIS/infra/em-config/airflow-auth-3users.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 60 --maxTime 600s --seed $seed \
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
  echo "$arm,$port,$ttl,$seed,$e,$d,$ac,$vc,$uc,${tr:-NA}" >> $CSV
  say "$name exit=$e det970=$d assembled=$ac void=$vc unconfirmed=$uc triples=${tr:-NA}"
  zsh $THESIS/infra/airflow-target/reset-3users.sh http://localhost:$port > $BASE/logs/$name-reset-after.txt 2>&1
}

for seed in 1 2 3; do
  run default 8082 30 8186 $seed
  run ttl0 8084 0 8187 $seed
done

docker stop airflow-ttl0 >> $PROG 2>&1
say "sao luu"
cd /Users/minhnguyen/IdeaProjects
TAR=~/thesis-backups/thesis-full-$(date +%Y%m%d-%H%M).tar.gz
tar --exclude 'graduational-thesis/infra/em-venv' -czf $TAR graduational-thesis
shasum -a 256 $TAR > $TAR.sha256
say "sao luu $TAR"
echo "RUN DONE $(date)" >> $PROG
