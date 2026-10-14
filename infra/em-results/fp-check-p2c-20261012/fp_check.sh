#!/usr/bin/env zsh
set -u
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=${JAR:-/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-P2c-b2ade764.jar}
BASE=$THESIS/infra/em-results/fp-check-p2c-20261012
JH=$(/usr/libexec/java_home -v 17)
CSV=$BASE/runs.csv; PROG=$BASE/progress.log
mkdir -p $BASE/logs $BASE/tests
echo "tier,target,seed,det970,assembled,void,restore_ok,restore_no,statuses" > $CSV
{
  echo "FP guard for the restore-swap fix (RestSecurityBuilder.kt:858) — jar $(shasum -a 256 $JAR | cut -c1-16)"
  echo "FIXED/patched targets only; the swapped restore now succeeds (restorer=admin), so a triple may ASSEMBLE,"
  echo "but a patched app must deny the follow-up -> det970 MUST be 0. Any det970=1 here is a false positive."
  echo "flags = remeasure fixed-noreset; no --statefulAuthzResetEndpoint. restore_ok>0 shows the restore path ran."
} > $PROG
FAIL=0

run() {
  local tier=$1 tgt=$2 port=$3 seed=$4 resetpath=$5 spec=$6 cfg=$7
  curl -s -o /dev/null -X POST http://localhost:$port$resetpath 2>/dev/null || curl -s -o /dev/null http://localhost:$port$resetpath
  local OUT=$BASE/tests/$tgt-seed$seed; rm -rf $OUT
  local log=$BASE/logs/$tgt-seed$seed.log
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:$port$spec --bbTargetUrl http://localhost:$port \
    --configPath $cfg \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $seed \
    --outputFolder $OUT > $log 2>&1
  local d=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")
  local ac=$(grep -c "Assembled .* statuses" $log)
  local vc=$(grep -c "Discarded a VOID stateful-authorization" $log)
  local rok=$(grep -c "Privilege-restore accepted" $log)
  local rno=$(grep -c "Privilege-restore refused" $log)
  local st=$(grep -v "proven by an attempt with" $log | grep -o "statuses [0-9?/-]*" | awk '{print $2}' | paste -sd';' -); [ -z "$st" ] && st=NA
  echo "$tier,$tgt,$seed,$d,$ac,$vc,$rok,$rno,$st" >> $CSV
  local v=PASS; [ "$d" != 0 ] && { v="FAIL-FP"; FAIL=1; }
  echo "$(date +%H:%M:%S) $v tier$tier $tgt seed=$seed det970=$d assembled=$ac void=$vc restore_ok=$rok restore_no=$rno statuses=$st" >> $PROG
  rm -rf $OUT
}

for s in 1 2 3; do run 1 reports-fixed 8081 $s /reset /v3/api-docs $THESIS/infra/em-config/reports-auth.yaml; done
for s in 1 2 3; do run 2 vampi-fixed 5003 $s /createdb /openapi.json $THESIS/infra/em-config/vampi-seeded-auth.yaml; done
echo "FP CHECK DONE $(date) fail=$FAIL" >> $PROG
[ "$FAIL" = 0 ] && echo "NO FALSE POSITIVES — restore-swap safe on patched targets" >> $PROG || echo "FALSE POSITIVE PRESENT — investigate before remeasure" >> $PROG
exit $FAIL
