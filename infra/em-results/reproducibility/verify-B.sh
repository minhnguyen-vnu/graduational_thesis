#!/usr/bin/env zsh
# Does option B fix the C5 defect on the row that exposed it?
#
# Row: tier2 ours-fixed-reset seed=3, recorded 200/200/403 with no 970.
# Established rates on this row (docs/diagnosis-c5-victim-abandon.md):
#     frozen 769c16d  12/12       C1-C5 pre-B  3/15       Fisher one-sided p = 2.6e-5
#
# Design: 8 INTERLEAVED pairs, frozen then B, so machine load and drift over the next ~90 minutes
# hit both builds equally. Frozen is re-run rather than compared against last night's 12/12 because
# the machine is not in the same state it was at 02:00, and a blocked design would confound build
# with time-of-day.
#
# DECISION RULE, fixed before the first run and not to be renegotiated afterwards:
#     new >= frozen - 1   ->  B removed the deficit; go on to the 21-row regression check
#     otherwise           ->  B did not fix it; STOP, restore the frozen jar, do not run phase 2
# Frozen's own count is reported alongside so a drop in BOTH is visible as changed conditions
# rather than being read as a verdict on the build.
set -u
T=/Users/minhnguyen/IdeaProjects/graduational-thesis
FROZEN=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-frozen-769c16d.jar
NEW=/Users/minhnguyen/IdeaProjects/EvoMaster/core/target/evomaster.jar
OUTD=$(dirname $0)/verify-B
JH=$(/usr/libexec/java_home -v 17)
rm -rf $OUTD; mkdir -p $OUTD
LOG=$OUTD/result.log
{
  echo "verify-B start $(date)"
  echo "row: tier2 ours-fixed-reset seed=3   recorded: 200/200/403, no 970"
  echo "frozen jar: $(shasum -a 256 $FROZEN | cut -c1-16)"
  echo "new jar   : $(shasum -a 256 $NEW | cut -c1-16)"
} > $LOG

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
  local f970=$(grep -c "SECURITY_STATEFUL_AUTHORIZATION" $OUTD/$tag.log)
  local rs=$(grep -c "SUT state reset via" $OUTD/$tag.log)
  local va=$(grep -c "Discarded a VOID" $OUTD/$tag.log)
  echo "$(date +%H:%M:%S) $tag statuses=$st f970=$f970 resets=$rs void=$va elapsed=${el}s" >> $LOG
  rm -rf $o
}

for i in 1 2 3 4 5 6 7 8; do
  one frozen-$i $FROZEN
  one newB-$i   $NEW
done

FZ=$(grep -c "^.* frozen-.* statuses=200/200/403 " $LOG)
NB=$(grep -c "^.* newB-.* statuses=200/200/403 " $LOG)
{
  echo "VERIFY-B DONE $(date)"
  echo "frozen correct: $FZ/8"
  echo "newB   correct: $NB/8"
} >> $LOG
if [ "$NB" -ge $(( FZ - 1 )) ]; then
  echo "GATE1=PASS" >> $LOG; exit 0
else
  echo "GATE1=FAIL" >> $LOG; exit 1
fi
