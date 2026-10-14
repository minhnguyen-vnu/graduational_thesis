#!/usr/bin/env zsh
set -u
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-P2d-2e0dbd4d.jar
BASE=$THESIS/infra/em-results/p2d-af2fired-probe-20261013
JH=$(/usr/libexec/java_home -v 17)
CSV=$BASE/runs.csv; PROG=$BASE/progress.log
SPEC2B=file://$THESIS/infra/pyload-cve/openapi-merged.json
EXCLUDE="/api/kill,/api/restart"
mkdir -p $BASE/logs $BASE/tests
echo "tier,arm,seed,reset,det970,assembled,void_count,resets,restores_ok,restores_no,statuses,faults" > $CSV
echo "P2d AF2-fired probe start $(date)  jar=$(shasum -a 256 $JAR | cut -c1-16)" > $PROG
echo "images vampi=$(docker image inspect vampi-seeded --format '{{.Created}}')" >> $PROG
SLEEP0=$(pmset -g log | grep "Entering Sleep" | tail -1)
ARM=""; IDX=0; ERRS=0; ZA=0; ZD=0

halt () {
  echo "STOPPED $(date +%H:%M:%S) $*" >> $PROG
  exit 1
}

check () {
  local last=$(tail -1 $CSV)
  local d=$(echo $last | cut -d, -f5) ac=$(echo $last | cut -d, -f6)
  local key="$1 $2 reset=$4"
  [ "$key" != "$ARM" ] && { ARM=$key; IDX=0; ERRS=0; ZA=0; ZD=0; }
  IDX=$((IDX+1))
  if [ "$d" = ERR ]; then ERRS=$((ERRS+1)); [ $ERRS -ge 2 ] && halt "two consecutive broken rows ending $key seed=$3"; else ERRS=0; fi
  if [ $IDX -le 3 ]; then [ "$ac" = 0 ] && ZA=$((ZA+1)); [ "$d" = 0 ] && ZD=$((ZD+1)); fi
  [ $IDX = 3 ] && [ $ZA -ge 3 ] && halt "first 3 rows assembled=0: $key"
  [ $IDX = 3 ] && [ $ZD -ge 3 ] && halt "first 3 rows det970=0: $key"
  [ "$(pmset -g log | grep 'Entering Sleep' | tail -1)" != "$SLEEP0" ] && halt "machine slept during $key seed=$3"
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

echo "=== TIER2 vampi reset $(date) ===" >> $PROG
for s in 1 3 5 7 8 9 10 11 12 16 17 19 20; do t2 ours-vuln 5002 $s 1 < /dev/null; done
echo "=== TIER2B pyload $(date) ===" >> $PROG
for s in 1 2 3; do t2b vuln 8090 $s 0 < /dev/null; done
echo "P2d AF2-FIRED PROBE DONE $(date)" >> $PROG
