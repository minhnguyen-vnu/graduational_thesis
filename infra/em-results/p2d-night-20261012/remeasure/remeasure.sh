#!/usr/bin/env zsh
set -u
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-P2d-2e0dbd4d.jar
BASE=$THESIS/infra/em-results/p2d-night-20261012/remeasure
JH=$(/usr/libexec/java_home -v 17)
CSV=$BASE/runs.csv; PROG=$BASE/progress.log
SPEC2B=file://$THESIS/infra/pyload-cve/openapi-merged.json
EXCLUDE="/api/kill,/api/restart"
mkdir -p $BASE/logs $BASE/tests
echo "tier,arm,seed,reset,det970,assembled,void_count,resets,restores_ok,restores_no,statuses,faults" > $CSV
echo "P2d full re-measure start $(date)  jar=$(shasum -a 256 $JAR | cut -c1-16)" > $PROG
echo "images reports=$(docker image inspect reports-api --format '{{.Created}}') vampi=$(docker image inspect vampi-seeded --format '{{.Created}}')" >> $PROG
SLEEP0=$(pmset -g log | grep "Entering Sleep" | tail -1)
ERRS=0; ZERO=0

halt () {
  echo "STOPPED $(date +%H:%M:%S) $*" >> $PROG
  exit 1
}

check () {
  local last=$(tail -1 $CSV)
  local d=$(echo $last | cut -d, -f5) ac=$(echo $last | cut -d, -f6)
  [ "$3" = 1 ] && { ERRS=0; ZERO=0; }
  case $2 in *fixed*) [ "$d" = 1 ] && halt "false positive: $1 $2 seed=$3 reset=$4 det970=1";; esac
  if [ "$d" = ERR ]; then ERRS=$((ERRS+1)); [ $ERRS -ge 2 ] && halt "two consecutive broken rows ending $1 $2 seed=$3 reset=$4"; else ERRS=0; fi
  case $2 in *vuln*) if [ $3 -le 3 ]; then [ "$ac" = 0 ] && ZERO=$((ZERO+1)); [ $3 = 3 ] && [ $ZERO -ge 3 ] && halt "first 3 seeds assembled=0: $1 $2 reset=$4"; fi;; esac
  [ "$(pmset -g log | grep 'Entering Sleep' | tail -1)" != "$SLEEP0" ] && halt "machine slept during $1 $2 seed=$3 reset=$4"
  return 0
}

collect () {
  local st=$(grep -v "proven by an attempt with" $1 | grep -o "statuses [0-9?/-]*" | awk '{print $2}' | paste -sd';' -); [ -z "$st" ] && st=NA
  local ac=$(grep -c "Assembled .* statuses" $1)
  local vc=$(grep -c "Discarded a VOID stateful-authorization" $1)
  local rs=$(grep -c "SUT state reset via" $1)
  local rok=$(grep -c "Privilege-restore accepted" $1)
  local rno=$(grep -c "Privilege-restore refused" $1)
  local d=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$2/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")
  local fl=$(python3 -c "
import json
try: print('|'.join(str(x) for x in sorted({x['code'] for f in json.load(open('$2/report.json'))['faults']['foundFaults'] for x in f['faultCategories']})))
except Exception: print('ERR')")
  echo "$3,$4,$5,$6,$d,$ac,$vc,$rs,$rok,$rno,$st,$fl" >> $CSV
  echo "$(date +%H:%M:%S) $3 $4 seed=$5 reset=$6 det970=$d assembled=$ac void=$vc resets=$rs restore_ok=$rok restore_no=$rno statuses=$st faults=$fl" >> $PROG
  check $3 $4 $5 $6
}

t1 () {
  curl -s -o /dev/null -X POST http://localhost:$2/reset
  local OUT=$BASE/tests/t1-$1-seed$3-r$4; rm -rf $OUT
  local log=$BASE/logs/t1-$1-seed$3-r$4.log
  local rf=(); [ "$4" = "1" ] && rf=(--statefulAuthzResetEndpoint "POST http://localhost:$2/reset")
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:$2/v3/api-docs --bbTargetUrl http://localhost:$2 \
    --configPath $THESIS/infra/em-config/reports-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 "${rf[@]}" \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $3 \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT tier1 $1 $3 $4
}

t2 () {
  local rc=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$2/createdb)
  [ "$rc" != "200" ] && sleep 3 && curl -s -o /dev/null http://localhost:$2/createdb
  local OUT=$BASE/tests/t2-$1-seed$3-r$4; rm -rf $OUT
  local log=$BASE/logs/t2-$1-seed$3-r$4.log
  local rf=(); [ "$4" = "1" ] && rf=(--statefulAuthzResetEndpoint "GET http://localhost:$2/createdb")
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:$2/openapi.json --bbTargetUrl http://localhost:$2 \
    --configPath $THESIS/infra/em-config/vampi-seeded-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 "${rf[@]}" \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $3 \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT tier2 $1 $3 $4
}

t2b () {
  curl -s -o /dev/null -X POST http://localhost:$2/thesis/reset
  local OUT=$BASE/tests/t2b-$1-seed$3-r$4; rm -rf $OUT
  local log=$BASE/logs/t2b-$1-seed$3-r$4.log
  local rf=(); [ "$4" = "1" ] && rf=(--statefulAuthzResetEndpoint "POST http://localhost:$2/thesis/reset")
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl $SPEC2B --bbTargetUrl http://localhost:$2 \
    --configPath $THESIS/infra/em-config/pyload-auth.yaml \
    --endpointExclude "$EXCLUDE" \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 "${rf[@]}" \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 200 --maxTime 10m --seed $3 \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT tier2b $1 $3 $4
}

echo "=== TIER1 reports $(date) ===" >> $PROG
for s in $(seq 1 20); do t1 vuln  8080 $s 0; done
FIRED=$(awk -F, '$1=="tier1" && $2=="vuln" && $4=="0" && $5=="1"' $CSV | wc -l | tr -d ' ')
echo "reports vuln no-reset det970 $FIRED/20" >> $PROG
[ $FIRED -le 15 ] && halt "reports vuln no-reset det970 $FIRED/20 <= 15"
for s in $(seq 1 20); do t1 fixed 8081 $s 0; done
for s in $(seq 1 20); do t1 vuln  8080 $s 1; done
for s in $(seq 1 20); do t1 fixed 8081 $s 1; done
echo "=== TIER2 vampi $(date) ===" >> $PROG
for s in $(seq 1 20); do t2 ours-vuln  5002 $s 0; done
for s in $(seq 1 20); do t2 ours-fixed 5003 $s 0; done
for s in $(seq 1 20); do t2 ours-vuln  5002 $s 1; done
for s in $(seq 1 20); do t2 ours-fixed 5003 $s 1; done
echo "=== TIER2B pyload $(date) ===" >> $PROG
for s in $(seq 1 5); do t2b vuln  8090 $s 0; done
for s in $(seq 1 5); do t2b vuln  8090 $s 1; done
for s in $(seq 1 5); do t2b fixed 8091 $s 0; done
for s in $(seq 1 5); do t2b fixed 8091 $s 1; done
echo "P2d FULL RE-MEASURE DONE $(date)" >> $PROG
