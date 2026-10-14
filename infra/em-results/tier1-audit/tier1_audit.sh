#!/usr/bin/env zsh
# Tier-1 AUDIT runs (2026-08-16): identical config to tier1_trials.sh / tier1_reset_trials.sh, but KEEPS
# the generated tests so every 970 -- and every true negative -- can be read by hand. Those two batch
# harnesses discard the tests, which is why auditing Tier-1 means re-running rather than re-reading.
#
# Three arms x 3 seeds. Evidence this directory exists to support (CLAUDE.md §6, "Hand-audit status"):
#   - the source and follow-up carry the SAME auth_alice credential, with no re-login between them;
#   - the transition is performed by auth_superadmin and asserts role == "VIEWER", so it took effect;
#   - the fixed-target run contains byte-identical actions and differs ONLY in the follow-up
#     (403 vs 200), with no 970 anywhere -- a clean differential rather than a silent oracle.
#
# Results are NOT part of the measured dataset (tier1-trials/, tier1-reset-trials/); they reproduce it.
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/core/target/evomaster.jar
CFG=$THESIS/infra/em-config/reports-auth.yaml
BASE=$THESIS/infra/em-results/tier1-audit
JH=$(/usr/libexec/java_home -v 17)
mkdir -p $BASE/logs
PROG=$BASE/progress.log
echo "audit batch start $(date)" > $PROG

run_one () {
  local arm=$1 port=$2 seed=$3 reset=$4
  curl -s -X POST http://localhost:$port/reset >/dev/null
  local OUT=$BASE/$arm-seed$seed
  rm -rf $OUT
  local log=$BASE/logs/$arm-seed$seed.log
  local rflag=()
  [ "$reset" = "1" ] && rflag=(--statefulAuthzResetEndpoint "POST http://localhost:$port/reset")
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:$port/v3/api-docs --bbTargetUrl http://localhost:$port \
    --configPath $CFG \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    "${rflag[@]}" \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $seed \
    --outputFolder $OUT > $log 2>&1
  local st=$(grep -o "statuses [0-9?/]*" $log | awk '{print $2}' | paste -sd';' -)
  local d=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")
  echo "$(date +%H:%M:%S) $arm seed=$seed statuses=${st:-NA} det970=$d resets=$(grep -c 'SUT state reset via' $log)" >> $PROG
}

for s in 1 2 3; do run_one vuln-reset  8080 $s 1; done
for s in 1 2 3; do run_one fixed-reset 8081 $s 1; done
for s in 1 2 3; do run_one vuln-noreset 8080 $s 0; done
echo "AUDIT BATCH DONE $(date)" >> $PROG
