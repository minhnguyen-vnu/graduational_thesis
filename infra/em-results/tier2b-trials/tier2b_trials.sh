#!/usr/bin/env zsh
# Tier-2b (pyLoad CVE-2026-41133) -- PRE-EXTENSION baseline.
#
# Run with the FROZEN RestSecurityBuilder, i.e. the exact build that produced the Tier-1 and
# Tier-2 numbers, BEFORE any change is made to handle pyLoad's transition idiom. This ordering
# is the point of the arm: it records what the tool does on a real third-party bug it was never
# tuned against. Re-running it after the extension would destroy that meaning.
#
# Expectation, from reading RestSecurityBuilder: 0 detections, and no builder log lines at all,
# because findPermissionReducingTransition() matches none of the 23 operations
# (TRANSITION_PATH_SIGNALS = role/permission/member/subscription/plan/owner/grant/access, while
# pyLoad's transition is POST /json/update_users) and harvestReducedRoleValue() then returns null.
#
# Budget differs from Tier-1/Tier-2 (6m, not 150s) because pyLoad is slower per request; the
# SECURITY phase timed out at 150s. Held identical across both arms here, so the arms still pair.
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/core/target/evomaster.jar
CFG=$THESIS/infra/em-config/pyload-auth.yaml
SPEC=file://$THESIS/infra/pyload-cve/openapi-json-routes.json
BASE=$THESIS/infra/em-results/tier2b-trials
JH=$(/usr/libexec/java_home -v 17)
mkdir -p $BASE/logs
CSV=$BASE/runs.csv
PROG=$BASE/progress.log
echo "arm,seed,det970,transition_found,builder_lines,faults" > $CSV
echo "tier2b pre-extension batch start $(date)" > $PROG

run_one () {
  local arm=$1 port=$2 container=$3 seed=$4
  docker exec $container python /seed_users.py /data/data/pyload.db >/dev/null 2>&1
  local OUT=$BASE/$arm-seed$seed
  rm -rf $OUT
  local log=$BASE/logs/$arm-seed$seed.log
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl $SPEC --bbTargetUrl http://localhost:$port \
    --configPath $CFG \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 200 --maxTime 6m --seed $seed \
    --outputFolder $OUT > $log 2>&1

  # Any line our builder emits: assembled triples, discarded VOID ones, or the debug lines
  # explaining why a victim/role could not be bound. Zero lines means it never got started.
  local bl=$(grep -ci "stateful-authorization\|Assembled .* statuses\|Discarded a VOID" $log)
  local tf=$(grep -ci "Stateful-authorization: could not" $log)
  local d=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")
  local fl=$(python3 -c "
import json
try:
    print('|'.join(str(x) for x in sorted({x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']})))
except Exception: print('ERR')")
  echo "$arm,$seed,$d,$tf,$bl,$fl" >> $CSV
  echo "$(date +%H:%M:%S) $arm seed=$seed det970=$d builder_lines=$bl faults=$fl" >> $PROG
  # Generated tests are kept: with detection expected to be 0, the tests are the evidence for WHY.
}

for s in 1 2 3 4 5; do run_one vuln  8090 pyload-vuln  $s; done
for s in 1 2 3 4 5; do run_one fixed 8091 pyload-fixed $s; done
echo "TIER2B PRE-EXTENSION BATCH DONE $(date)" >> $PROG
