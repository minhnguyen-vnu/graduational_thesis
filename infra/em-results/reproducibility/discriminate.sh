#!/usr/bin/env zsh
# Which jar is responsible for tier2 ours-fixed-reset seed=3 turning from 200/200/403 into NA?
#
# One variable: the JAR. Same flags, same reseed, same seed, copied verb-for-verb from
# regression_check.sh. Three runs, ordered so the cheapest refutation comes first:
#   1. FROZEN jar  -- if this also yields NA, the recorded expectation is stale (the container has
#                     been up for weeks) and the new build is not implicated at all.
#   2. NEW jar     -- repeat of the failing run, to tell a deterministic change from a flaky one.
#   3. NEW jar     -- second repeat, only run if 2 disagreed with the check.
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
FROZEN=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-frozen-769c16d.jar
NEW=/Users/minhnguyen/IdeaProjects/EvoMaster/core/target/evomaster.jar
OUTD=$(dirname $0)/discriminate
JH=$(/usr/libexec/java_home -v 17)
mkdir -p $OUTD
LOG=$OUTD/result.log
echo "discriminator start $(date)" > $LOG
echo "expectation on record: 200/200/403 with no 970" >> $LOG

one () {
  local tag=$1 jar=$2
  curl -s http://localhost:5003/createdb >/dev/null
  local o=$OUTD/$tag; rm -rf $o
  JAVA_HOME=$JH java -jar $jar --blackBox true \
    --bbSwaggerUrl http://localhost:5003/openapi.json --bbTargetUrl http://localhost:5003 \
    --configPath $THESIS/infra/em-config/vampi-seeded-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzResetEndpoint "GET http://localhost:5003/createdb" \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 3 \
    --outputFolder $o > $OUTD/$tag.log 2>&1
  local st=$(grep -o "statuses [0-9?/]*" $OUTD/$tag.log | awk '{print $2}' | paste -sd';' -)
  [ -z "$st" ] && st=NA
  local d=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$o/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")
  echo "$(date +%H:%M:%S) $tag statuses=$st det970=$d" >> $LOG
  grep -cE "Discarded a VOID" $OUTD/$tag.log | xargs -I{} echo "    void_attempts={}" >> $LOG
  grep -cE "Discarded an UNCONFIRMED" $OUTD/$tag.log | xargs -I{} echo "    probe_rejections={}" >> $LOG
}

one frozen  $FROZEN
one new-1   $NEW
one new-2   $NEW
echo "DISCRIMINATOR DONE $(date)" >> $LOG
