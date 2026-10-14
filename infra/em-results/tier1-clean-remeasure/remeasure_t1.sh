#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-R-5bce137f.jar
BASE=$THESIS/infra/em-results/tier1-clean-remeasure
JH=$(/usr/libexec/java_home -v 17)
CSV=$BASE/runs.csv; PROG=$BASE/progress.log
mkdir -p $BASE/logs $BASE/tests
echo "tier,arm,seed,reset,det970,assembled,void_count,resets,restores_ok,restores_no,statuses,faults" > $CSV
echo "tier1 clean-app remeasure start $(date)  jar=$(shasum -a 256 $JAR | cut -c1-16)  image=$(docker image inspect reports-api --format '{{.Created}}')" > $PROG

collect () {
  local st=$(grep -o "statuses [0-9?/-]*" $1 | awk '{print $2}' | paste -sd';' -); [ -z "$st" ] && st=NA
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
  echo "$(date +%H:%M:%S) $3 $4 seed=$5 reset=$6 det970=$d assembled=$ac void=$vc resets=$rs restore_ok=$rok restore_no=$rno statuses=$st" >> $PROG
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

for s in $(seq 1 20); do t1 vuln  8080 $s 0; done
for s in $(seq 1 20); do t1 fixed 8081 $s 0; done
for s in $(seq 1 20); do t1 vuln  8080 $s 1; done
for s in $(seq 1 20); do t1 fixed 8081 $s 1; done
echo "TIER1 CLEAN REMEASURE DONE $(date)" >> $PROG
