#!/usr/bin/env zsh
# Re-measure the RESET-ARM ablation on the operator-restore jar (R-5bce137f).
#
# WHY: restore-remeasure/ moved the four NO-RESET arms onto jar R (Tier-1 16->19, Tier-2 5->7,
# 0 false positives). The four RESET arms are still recorded from jars frozen/B, so quoting the
# ablation table would mix two builds. This runs the reset arms on the same jar so the whole
# 8-arm table has one provenance.
#
# ONE VARIABLE vs tier1-reset-trials/ and tier2-reset-trials/: the jar. Every flag below is copied
# verbatim from tier1_reset_trials.sh / tier2_reset_trials.sh, so rows pair one-to-one with the
# recorded CSVs. No expected outcome is encoded here.
#
# 80 rows, not the 72 outstanding: the 8 reset rows already run in restore-remeasure/ are repeated
# so this directory is self-contained rather than spliced from two batches. The duplicates are a
# free repeatability check, which matters because these runs are bounded by wall-clock --maxTime
# and are documented to vary run to run.
#
# The `resets` column is the integrity check the original ablation harnesses carry: resets=0 with
# attempts>0 would mean the flag was silently ignored.
set -u

LOCK=/tmp/restore_reset_remeasure.lock
if [ -e $LOCK ] && kill -0 $(cat $LOCK) 2>/dev/null; then
  echo "FATAL: already running as PID $(cat $LOCK). Refusing to start." >&2
  exit 1
fi
echo $$ > $LOCK
trap 'rm -f $LOCK' EXIT
trap 'rm -f $LOCK; pkill -P $$ 2>/dev/null; exit 143' INT TERM

THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-R-5bce137f.jar
BASE=$THESIS/infra/em-results/restore-reset-remeasure
JH=$(/usr/libexec/java_home -v 17)
CSV=$BASE/runs.csv; PROG=$BASE/progress.log
mkdir -p $BASE/logs
echo "tier,arm,seed,reset,det970,assembled,void_count,resets,restores_ok,restores_no,statuses,faults" > $CSV
echo "reset-arm re-measure start $(date)  jar=$(shasum -a 256 $JAR | cut -c1-16)" > $PROG

collect () {   # $1=log $2=outdir $3=tier $4=arm $5=seed
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
  echo "$3,$4,$5,1,$d,$ac,$vc,$rs,$rok,$rno,$st,$fl" >> $CSV
  echo "$(date +%H:%M:%S) $3 $4 seed=$5 det970=$d assembled=$ac void=$vc resets=$rs restore_ok=$rok restore_no=$rno statuses=$st" >> $PROG
}

t1 () {  # $1=arm $2=port $3=seed
  curl -s -o /dev/null -X POST http://localhost:$2/reset
  local OUT=$BASE/_t1_$1_$3; rm -rf $OUT
  local log=$BASE/logs/t1-$1-seed$3.log
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:$2/v3/api-docs --bbTargetUrl http://localhost:$2 \
    --configPath $THESIS/infra/em-config/reports-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzResetEndpoint "POST http://localhost:$2/reset" \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $3 \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT tier1 $1 $3; rm -rf $OUT
}

t2 () {  # $1=arm $2=port $3=seed
  local rs=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$2/createdb)
  if [ "$rs" != "200" ]; then sleep 3; rs=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$2/createdb)
    echo "$(date +%H:%M:%S) WARN $1 seed=$3 reseed http=$rs" >> $PROG; fi
  local OUT=$BASE/_t2_$1_$3; rm -rf $OUT
  local log=$BASE/logs/t2-$1-seed$3.log
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:$2/openapi.json --bbTargetUrl http://localhost:$2 \
    --configPath $THESIS/infra/em-config/vampi-seeded-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzResetEndpoint "GET http://localhost:$2/createdb" \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $3 \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT tier2 $1 $3; rm -rf $OUT
}

for s in $(seq 1 20); do t1 vuln-reset  8080 $s; done
for s in $(seq 1 20); do t1 fixed-reset 8081 $s; done
for s in $(seq 1 20); do t2 ours-vuln-reset  5002 $s; done
for s in $(seq 1 20); do t2 ours-fixed-reset 5003 $s; done
echo "RESET-ARM RE-MEASURE DONE $(date)" >> $PROG
