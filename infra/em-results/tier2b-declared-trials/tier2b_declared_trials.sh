#!/usr/bin/env zsh
# Tier-2b with the transition DECLARED rather than inferred (--statefulAuthzTransition), and with
# the state-reset ablation, mirroring the Tier-1/Tier-2 design of CLAUDE.md §6.1.
#
# WHAT THIS ARM DOES AND DOES NOT MEASURE
# ---------------------------------------
# It does NOT measure black-box recall. Declaring the transition tells the tool WHICH action reduces
# a permission and HOW to aim it at a victim -- exactly the step that the frozen build failed at on
# this target (infra/em-results/tier2b-trials/, 0/10). Quoting a detection rate from here as if it
# were comparable to Tier-1/Tier-2 would be dishonest.
#
# What it DOES measure is the question the pre-extension arm left open: once the transition is
# supplied, does the REST of the pipeline work on third-party code? Victim selection, guard
# discovery, credential replay, VOID-and-retry and the judgment rule all still run unchanged.
#
# Four arms, so the two blockers found in the smoke run are separated:
#   vuln/fixed x reset/no-reset
# The no-reset arms are expected to be dominated by state destruction -- in the smoke run every
# attempt came back 200/401/200 because the search had demoted 40 of 41 accounts, leaving no
# operator able to perform the transition. The reset arms remove exactly that variable.
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/core/target/evomaster.jar
CFG=$THESIS/infra/em-config/pyload-auth.yaml
SPEC=file://$THESIS/infra/pyload-cve/openapi-merged.json
BASE=$THESIS/infra/em-results/tier2b-declared-trials
JH=$(/usr/libexec/java_home -v 17)
mkdir -p $BASE/logs
CSV=$BASE/runs.csv
PROG=$BASE/progress.log
echo "arm,seed,det970,assembled,void_count,statuses,resets,faults,coverage" > $CSV
echo "tier2b declared batch start $(date)" > $PROG

# The transition is pyLoad's own /api/set_user_permission -- the endpoint the CVE advisory names.
# It has NAMED query parameters (user, permission, role), which is why it can be declared at all;
# the /json/update_users idiom carries the victim in a body KEY and cannot be expressed this way.
TRANSITION="POST /api/set_user_permission user=<victim> role=1 permission=0"

# kill and restart terminate the process (they set _do_exit / _do_restart), and pyLoad's self-restart
# leaves the webserver dead. Stock EvoMaster option, documented for exactly this.
EXCLUDE="/api/kill,/api/restart"

run_one () {
  local arm=$1 port=$2 container=$3 seed=$4 reset=$5
  # Always start from a clean account state, whatever the arm: the reset FLAG is the variable under
  # test (reset before each triple attempt), not the starting condition.
  curl -s -o /dev/null -X POST http://localhost:$port/thesis/reset

  local OUT=$BASE/$arm-seed$seed
  rm -rf $OUT
  local log=$BASE/logs/$arm-seed$seed.log
  local rflag=()
  [ "$reset" = "1" ] && rflag=(--statefulAuthzResetEndpoint "POST http://localhost:$port/thesis/reset")

  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl $SPEC --bbTargetUrl http://localhost:$port \
    --configPath $CFG \
    --endpointExclude "$EXCLUDE" \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTransition "$TRANSITION" \
    "${rflag[@]}" \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 200 --maxTime 10m --seed $seed \
    --outputFolder $OUT > $log 2>&1

  local st=$(grep -o "statuses [0-9?/]*" $log | awk '{print $2}' | paste -sd';' -)
  [ -z "$st" ] && st=NA
  local ac=$(grep -c "Assembled .* statuses" $log)
  local vc=$(grep -c "Discarded a VOID stateful-authorization" $log)
  local rs=$(grep -c "SUT state reset via" $log)
  local cov=$(grep -o "endpoints out of [0-9]* ([0-9]*%)" $log | tail -1 | grep -o "[0-9]*%")
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

  echo "$arm,$seed,$d,$ac,$vc,$st,$rs,$fl,${cov:-NA}" >> $CSV
  echo "$(date +%H:%M:%S) $arm seed=$seed det970=$d assembled=$ac void=$vc statuses=$st resets=$rs cov=${cov:-NA}" >> $PROG
  # Tests are KEPT: with a declared transition every firing must be auditable by hand.
}

for s in 1 2 3 4 5; do run_one vuln-noreset  8090 pyload-vuln  $s 0; done
for s in 1 2 3 4 5; do run_one vuln-reset    8090 pyload-vuln  $s 1; done
for s in 1 2 3 4 5; do run_one fixed-noreset 8091 pyload-fixed $s 0; done
for s in 1 2 3 4 5; do run_one fixed-reset   8091 pyload-fixed $s 1; done
echo "TIER2B DECLARED BATCH DONE $(date)" >> $PROG
