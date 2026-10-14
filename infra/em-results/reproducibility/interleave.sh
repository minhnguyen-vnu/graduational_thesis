#!/usr/bin/env zsh
# Is tier2 ours-fixed-reset seed=3 a LOGIC regression of the new jar, or a TIMING sensitivity that
# happens to be exposed by it?
#
# The debug-logging run is what raised the question: the NEW jar, slowed down by debug output,
# produced the recorded 200/200/403 -- while the same jar at full speed produced NA twice. Debug
# logging cannot change logic, so if that is real the deciding variable is wall-clock: the search is
# bounded by --maxTime 150s of REAL time, so how much of it fits changes the archive, which changes
# the victim ordering, which changes whether attempt #1 lands on the pair that works.
#
# Design: INTERLEAVED pairs, so machine load and any drift over the next half hour hit both jars
# equally. A blocked design (all frozen, then all new) would confound jar with time-of-night.
#   frozen, new, frozen, new, frozen, new
#
# Reading it:
#   frozen 3/3 correct AND new 0/3   -> a real logic regression; the timing story is wrong
#   both mixed                       -> timing sensitivity, jar not implicated
#   frozen 3/3 AND new mixed         -> the new jar shifts the odds; needs a wider look before use
set -u
T=/Users/minhnguyen/IdeaProjects/graduational-thesis
FROZEN=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-frozen-769c16d.jar
NEW=/Users/minhnguyen/IdeaProjects/EvoMaster/core/target/evomaster.jar
OUTD=$(dirname $0)/interleave
JH=$(/usr/libexec/java_home -v 17)
mkdir -p $OUTD
LOG=$OUTD/result.log
echo "interleaved frozen-vs-new start $(date)" > $LOG
echo "recorded expectation: 200/200/403, no 970" >> $LOG

one () {
  local tag=$1 jar=$2
  curl -s http://localhost:5003/createdb >/dev/null
  local o=$OUTD/$tag; rm -rf $o
  local t0=$(date +%s)
  JAVA_HOME=$JH java -jar $jar --blackBox true \
    --bbSwaggerUrl http://localhost:5003/openapi.json --bbTargetUrl http://localhost:5003 \
    --configPath $T/infra/em-config/vampi-seeded-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzResetEndpoint "GET http://localhost:5003/createdb" \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 3 \
    --outputFolder $o > $OUTD/$tag.log 2>&1
  local el=$(( $(date +%s) - t0 ))
  local st=$(grep -o "statuses [0-9?/]*" $OUTD/$tag.log | awk '{print $2}' | paste -sd';' -)
  [ -z "$st" ] && st=NA
  # how much search actually fit: the archive size EvoMaster reports, and the endpoint coverage
  local cov=$(grep -o "endpoints out of [0-9]* ([0-9]*%)" $OUTD/$tag.log | tail -1 | grep -o "[0-9]*%")
  local va=$(grep -c "Discarded a VOID" $OUTD/$tag.log)
  echo "$(date +%H:%M:%S) $tag statuses=$st void=$va cov=${cov:-NA} elapsed=${el}s" >> $LOG
  rm -rf $o
}

for i in 1 2 3; do
  one frozen-$i $FROZEN
  one new-$i    $NEW
done
echo "INTERLEAVE DONE $(date)" >> $LOG
