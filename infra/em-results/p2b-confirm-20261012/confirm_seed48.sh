#!/usr/bin/env zsh
set -u
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
AF2=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-AF2-6b5606d4.jar
P2B=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-P2b-93db089f.jar
BASE=$THESIS/infra/em-results/p2b-confirm-20261012
JH=$(/usr/libexec/java_home -v 17)
CSV=$BASE/runs.csv; PROG=$BASE/progress.log
mkdir -p $BASE/logs $BASE/tests
echo "jar,seed,rep,det970,assembled,void,statuses" > $CSV
{
  echo "confirm reports-vuln-noreset seed 4,8  AF2 vs P2b  start $(date)"
  echo "af2=$(shasum -a 256 $AF2 | cut -c1-16)  p2b=$(shasum -a 256 $P2B | cut -c1-16)"
  echo "arm = reports vuln :8080, reset once before each run, NO --statefulAuthzResetEndpoint"
  echo "flags copied byte-for-byte from p2b_full_remeasure.sh t1 vuln reset=0; only jar+seed vary"
  echo "READ: AF2 fires most AND P2b misses most on 4,8 -> real regression; both mixed -> noise, jar not implicated"
} > $PROG

one () {
  local lbl=$1 jar=$2 s=$3 rep=$4
  curl -s -o /dev/null -X POST http://localhost:8080/reset
  local OUT=$BASE/tests/$lbl-seed$s-r$rep; rm -rf $OUT
  local log=$BASE/logs/$lbl-seed$s-r$rep.log
  JAVA_HOME=$JH java -jar $jar --blackBox true \
    --bbSwaggerUrl http://localhost:8080/v3/api-docs --bbTargetUrl http://localhost:8080 \
    --configPath $THESIS/infra/em-config/reports-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $s \
    --outputFolder $OUT > $log 2>&1
  local st=$(grep -v "proven by an attempt with" $log | grep -o "statuses [0-9?/-]*" | awk '{print $2}' | paste -sd';' -); [ -z "$st" ] && st=NA
  local ac=$(grep -c "Assembled .* statuses" $log)
  local vc=$(grep -c "Discarded a VOID stateful-authorization" $log)
  local d=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")
  echo "$lbl,$s,$rep,$d,$ac,$vc,$st" >> $CSV
  echo "$(date +%H:%M:%S) $lbl seed=$s rep=$rep det970=$d assembled=$ac void=$vc statuses=$st" >> $PROG
  rm -rf $OUT
}

for s in 4 8; do
  for rep in 1 2 3; do
    one af2 $AF2 $s $rep
    one p2b $P2B $s $rep
  done
done
echo "CONFIRM DONE $(date)" >> $PROG
