#!/usr/bin/env zsh
set -u
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
E=$THESIS/infra/em-results
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster-upstream/evomaster-upstream-master-d898c1ce.jar
BASE=$E/upstream-master-t1-20261018
JH=$(/usr/libexec/java_home -v 17)
CSV=$BASE/runs.csv; PROG=$BASE/progress.log
PX_PORT=8280
mkdir -p $BASE/logs $BASE/tests $BASE/traffic
[ -f $CSV ] || echo "tier,arm,seed,exit,faults,fault_count,requests,proxy_errors,login_alice,login_superadmin,login_bob,demotions,stale_2xx,stale_403,stale_other,full_triples_2xx" > $CSV
echo "upstream master T1 start $(date)  jar=$(shasum -a 256 $JAR | cut -c1-16)" >> $PROG
[ "$(shasum -a 256 $JAR | cut -c1-16)" = d898c1ceedc82459 ] || { echo "STOPPED jar sha mismatch" >> $PROG; exit 1; }
echo "image reports=$(docker image inspect reports-api --format '{{.Created}}')" >> $PROG
SLEEP0=$(pmset -g log | grep "Entering Sleep" | tail -1)
ERRS=0

halt () {
  echo "STOPPED $(date +%H:%M:%S) $*" >> $PROG
  exit 1
}

check () {
  local row=$(tail -1 $CSV)
  local fl=$(echo $row | cut -d, -f5)
  if [ "$fl" = ERR ]; then ERRS=$((ERRS+1)); [ $ERRS -ge 2 ] && halt "two consecutive broken rows ending seed=$1"; else ERRS=0; fi
  [ "$(echo $row | cut -d, -f8)" != 0 ] && halt "proxy forwarding error seed=$1"
  for c in 9 10 11; do [ "$(echo $row | cut -d, -f$c)" = 0 ] && halt "an account never logged in, seed=$1 column=$c"; done
  [ "$(pmset -g log | grep 'Entering Sleep' | tail -1)" != "$SLEEP0" ] && halt "machine slept during seed=$1"
  return 0
}

collect () {
  local fl=$(python3 -c "
import json
try: print('|'.join(str(x) for x in sorted({x['code'] for f in json.load(open('$2/report.json'))['faults']['foundFaults'] for x in f['faultCategories']})))
except Exception: print('ERR')")
  local fc=$(python3 -c "
import json
try: print(len(json.load(open('$2/report.json'))['faults']['foundFaults']))
except Exception: print('ERR')")
  local tr=$(python3 -c "
import sys
sys.path.insert(0, '$BASE')
from audit_traffic import audit
try:
    a = audit('$3')
    print(','.join(str(x) for x in [a['requests'], a['proxy_errors'], a['logins']['alice'], a['logins']['superadmin'], a['logins']['bob'], a['demotions'], a['stale_2xx'], a['stale_403'], a['stale_other'], a['full_triples_2xx']]))
except Exception: print('ERR,ERR,ERR,ERR,ERR,ERR,ERR,ERR,ERR,ERR')")
  echo "tier1,upstream-master-vuln,$1,$4,$fl,$fc,$tr" >> $CSV
  echo "$(date +%H:%M:%S) seed=$1 exit=$4 faults=$fl count=$fc traffic=$tr" >> $PROG
  check $1
}

t1 () {
  curl -s -o /dev/null -X POST http://localhost:8080/reset
  local OUT=$BASE/tests/t1-upstream-seed$1; rm -rf $OUT
  local log=$BASE/logs/t1-upstream-seed$1.log
  local cap=$BASE/traffic/t1-upstream-seed$1.jsonl; rm -f $cap
  python3 $BASE/capture_proxy.py $PX_PORT localhost 8080 $cap &
  local px=$!
  for i in $(seq 1 20); do nc -z localhost $PX_PORT 2>/dev/null && break; sleep 0.3; done
  nc -z localhost $PX_PORT 2>/dev/null || { kill $px 2>/dev/null; halt "proxy did not start, seed=$1"; }
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:8080/v3/api-docs --bbTargetUrl http://localhost:$PX_PORT \
    --configPath $THESIS/infra/em-config/reports-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $1 \
    --outputFolder $OUT > $log 2>&1
  local rc=$?
  kill $px 2>/dev/null; wait $px 2>/dev/null
  collect $1 $OUT $cap $rc
}

have () {
  grep -q "^tier1,upstream-master-vuln,$1," $CSV
}

for s in $(seq 1 20); do have $s || t1 $s < /dev/null; done
curl -s -o /dev/null -X POST http://localhost:8080/reset

python3 $BASE/audit_traffic.py $BASE/traffic/t1-upstream-seed*.jsonl > $BASE/audit-traffic.out 2>&1
echo "audit-traffic exit $?" >> $PROG
echo "UPSTREAM T1 DONE $(date)" >> $PROG
