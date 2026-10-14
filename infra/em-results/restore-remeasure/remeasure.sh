#!/usr/bin/env zsh
# Re-measure the NO-RESET headline arms on the operator-restore jar, plus a reset-arm sample.
#
# Why: the Tier-1 probe showed 3 of the 4 previously-barren no-reset seeds now detect, so CLAUDE.md 6's
# 80% does not reproduce on this build. The 21-row gate passed only because its Tier-1 rows were all
# already-successful seeds.
#
# Arms: Tier-1 vuln/fixed and Tier-2 ours-vuln/ours-fixed, seeds 1-20, NO reset flag -- the headline.
# Then 8 reset rows, to check the mechanism really is inert where a reset exists rather than assumed to be.
# Flags are copied from the original harnesses so the only variable is the jar.
# No expected outcome is encoded here.
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-R-5bce137f.jar
BASE=$THESIS/infra/em-results/restore-remeasure
JH=$(/usr/libexec/java_home -v 17)
CSV=$BASE/runs.csv; PROG=$BASE/progress.log
echo "tier,arm,seed,reset,det970,assembled,void_count,restores_ok,restores_no,statuses,faults" > $CSV
echo "restore re-measure start $(date)  jar=$(shasum -a 256 $JAR | cut -c1-16)" > $PROG

collect () {   # $1=log $2=outdir $3=tier $4=arm $5=seed $6=reset
  local st=$(grep -o "statuses [0-9?/-]*" $1 | awk '{print $2}' | paste -sd';' -); [ -z "$st" ] && st=NA
  local ac=$(grep -c "Assembled .* statuses" $1)
  local vc=$(grep -c "Discarded a VOID stateful-authorization" $1)
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
  echo "$3,$4,$5,$6,$d,$ac,$vc,$rok,$rno,$st,$fl" >> $CSV
  echo "$(date +%H:%M:%S) $3 $4 seed=$5 reset=$6 det970=$d assembled=$ac void=$vc restore_ok=$rok restore_no=$rno statuses=$st" >> $PROG
}

t1 () {  # $1=arm $2=port $3=seed $4=reset
  curl -s -o /dev/null -X POST http://localhost:$2/reset
  local OUT=$BASE/_t1_$1_$3_$4; rm -rf $OUT
  local log=$BASE/logs/t1-$1-seed$3-r$4.log
  local rf=(); [ "$4" = "1" ] && rf=(--statefulAuthzResetEndpoint "POST http://localhost:$2/reset")
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:$2/v3/api-docs --bbTargetUrl http://localhost:$2 \
    --configPath $THESIS/infra/em-config/reports-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 "${rf[@]}" \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $3 \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT tier1 $1 $3 $4; rm -rf $OUT
}

t2 () {  # $1=arm $2=port $3=seed $4=reset
  local rs=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$2/createdb)
  [ "$rs" != "200" ] && sleep 3 && curl -s -o /dev/null http://localhost:$2/createdb
  local OUT=$BASE/_t2_$1_$3_$4; rm -rf $OUT
  local log=$BASE/logs/t2-$1-seed$3-r$4.log
  local rf=(); [ "$4" = "1" ] && rf=(--statefulAuthzResetEndpoint "GET http://localhost:$2/createdb")
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:$2/openapi.json --bbTargetUrl http://localhost:$2 \
    --configPath $THESIS/infra/em-config/vampi-seeded-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 "${rf[@]}" \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $3 \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT tier2 $1 $3 $4; rm -rf $OUT
}

for s in $(seq 1 20); do t1 vuln  8080 $s 0; done
for s in $(seq 1 20); do t1 fixed 8081 $s 0; done
for s in $(seq 1 20); do t2 ours-vuln  5002 $s 0; done
for s in $(seq 1 20); do t2 ours-fixed 5003 $s 0; done
# reset-arm sample: is the mechanism really inert where a reset exists?
for s in 1 6; do t1 vuln 8080 $s 1; t1 fixed 8081 $s 1; done
for s in 1 15; do t2 ours-vuln 5002 $s 1; done
for s in 2 3;  do t2 ours-fixed 5003 $s 1; done
echo "RESTORE RE-MEASURE DONE $(date)" >> $PROG
