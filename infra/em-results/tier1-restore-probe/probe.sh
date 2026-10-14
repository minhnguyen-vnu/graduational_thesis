#!/usr/bin/env zsh
# DECISIVE, NARROW: do the four Tier-1 no-reset seeds that did NOT detect (6, 8, 11, 14) behave
# differently on the operator-restore jar? Plus the same four on the FIXED target, so any new triple
# on the vulnerable side has its matched false-positive opportunity.
#
# If all four stay barren, CLAUDE.md 6's 80% reproduces on this build and no re-measurement is owed.
# If any detect, Tier-1 rises and Tier-1 must be re-measured in full.
# No expected outcome is written into this harness; it records what happens.
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-R-5bce137f.jar
CFG=$THESIS/infra/em-config/reports-auth.yaml
BASE=$THESIS/infra/em-results/tier1-restore-probe
JH=$(/usr/libexec/java_home -v 17)
CSV=$BASE/runs.csv; PROG=$BASE/progress.log
echo "app,seed,det970,assembled,void_count,restores_ok,restores_no,statuses,faults" > $CSV
echo "tier1 restore probe start $(date)  jar=$(shasum -a 256 $JAR | cut -c1-16)" > $PROG

one () {
  local app=$1 port=$2 seed=$3
  curl -s -o /dev/null -X POST http://localhost:$port/reset
  local OUT=$BASE/$app-seed$seed; rm -rf $OUT
  local log=$BASE/logs/$app-seed$seed.log
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:$port/v3/api-docs --bbTargetUrl http://localhost:$port \
    --configPath $CFG \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $seed \
    --outputFolder $OUT > $log 2>&1
  local st=$(grep -o "statuses [0-9?/]*" $log | awk '{print $2}' | paste -sd';' -); [ -z "$st" ] && st=NA
  local ac=$(grep -c "Assembled .* statuses" $log)
  local vc=$(grep -c "Discarded a VOID stateful-authorization" $log)
  local rok=$(grep -c "Privilege-restore accepted" $log)
  local rno=$(grep -c "Privilege-restore refused" $log)
  local d=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")
  local fl=$(python3 -c "
import json
try: print('|'.join(str(x) for x in sorted({x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']})))
except Exception: print('ERR')")
  echo "$app,$seed,$d,$ac,$vc,$rok,$rno,$st,$fl" >> $CSV
  echo "$(date +%H:%M:%S) $app seed=$seed det970=$d assembled=$ac void=$vc restore_ok=$rok restore_no=$rno statuses=$st" >> $PROG
}
for s in 6 8 11 14; do one vuln  8080 $s; done
for s in 6 8 11 14; do one fixed 8081 $s; done
echo "TIER1 RESTORE PROBE DONE $(date)" >> $PROG
