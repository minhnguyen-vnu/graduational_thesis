#!/usr/bin/env zsh
# Tier-2b with the transition INFERRED -- the arm this whole extension exists to make possible.
#
# WHAT THIS MEASURES, AND WHY IT IS THE HEADLINE TIER-2B NUMBER
# ------------------------------------------------------------
# The pre-extension arm (tier2b-trials/) scored 0/5 and was read as "a real app defeats transition
# inference". That reading was wrong on two counts, both corrected in docs/tier2b-pyload-target.md
# 5.3: its spec contained only the 20 /json/* routes, so pyLoad's own named-parameter role endpoint
# was not even visible; and its "no builder log lines" evidence was an artefact of logback's
# <root level="warn"> swallowing every log.debug on that path. Measured properly, inference FINDS
# POST /api/set_user_permission unaided and dies one step later, on three narrow binding blockers
# (enum-only role values, path/body-only parameter binding, PUT/PATCH-only sources).
#
# The declared arm (tier2b-declared-trials/) then showed the REST of the pipeline works on
# third-party code -- but it changed two variables at once (the declaration AND the spec), so it
# could not show that the declaration was NECESSARY. This arm holds the spec and removes only the
# declaration. C1-C5 are the changes meant to make that survivable.
#
# So, unlike the declared arm, a detection rate from HERE is a legitimate black-box recall figure
# on a real, third-party, CVE-carrying bug -- the thing the mentor asked for.
#
# Four arms, vuln/fixed x reset/no-reset, mirroring CLAUDE.md 6.1 so the rows pair one-to-one with
# the declared batch.
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/core/target/evomaster.jar
CFG=$THESIS/infra/em-config/pyload-auth.yaml
SPEC=file://$THESIS/infra/pyload-cve/openapi-merged.json
BASE=$THESIS/infra/em-results/tier2b-inference-trials
JH=$(/usr/libexec/java_home -v 17)
mkdir -p $BASE/logs
CSV=$BASE/runs.csv
PROG=$BASE/progress.log
echo "arm,seed,det970,assembled,void_count,statuses,resets,faults,coverage" > $CSV
echo "tier2b INFERENCE batch start $(date)" > $PROG

# NO --statefulAuthzTransition here. The declared arm supplied
#     POST /api/set_user_permission user=<victim> role=1 permission=0
# and this arm withholds it, so the tool must find that endpoint and aim it on its own. Everything
# else -- spec, auth config, exclusions, budget, rate, seeds, reset endpoint -- is byte-identical to
# the declared harness, which is the point: the two now differ in exactly ONE variable.

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
  # Tests are KEPT: every firing must be auditable by hand, and on a third-party target that audit is
  # the only thing separating a real CVE detection from a lucky status string.
}

for s in 1 2 3 4 5; do run_one vuln-noreset  8090 pyload-vuln  $s 0; done
for s in 1 2 3 4 5; do run_one vuln-reset    8090 pyload-vuln  $s 1; done
for s in 1 2 3 4 5; do run_one fixed-noreset 8091 pyload-fixed $s 0; done
for s in 1 2 3 4 5; do run_one fixed-reset   8091 pyload-fixed $s 1; done
echo "TIER2B INFERENCE BATCH DONE $(date)" >> $PROG
