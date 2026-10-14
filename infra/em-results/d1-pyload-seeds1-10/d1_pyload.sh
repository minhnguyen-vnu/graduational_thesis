#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/core/target/evomaster.jar
CFG=$THESIS/infra/em-config/pyload-auth.yaml
SPEC=file://$THESIS/infra/pyload-cve/openapi-merged.json
BASE=$THESIS/infra/em-results/d1-pyload-seeds1-10
JH=$(/usr/libexec/java_home -v 17)
EXCLUDE="/api/kill,/api/restart"
CSV=$BASE/runs.csv; PROG=$BASE/progress.log
echo "tier,arm,seed,d1,det970,assembled,void_count,probe_lines,probe_403,statuses,faults" > $CSV
echo "d1 pyload seeds 1-10 start $(date)  jar=$(shasum -a 256 $JAR | cut -c1-16)" > $PROG

run_one () {
  local seed=$1 d1=$2
  curl -s -o /dev/null -X POST http://localhost:8090/thesis/reset
  local OUT=$BASE/tests/t2b-d1$d1-seed$seed; rm -rf $OUT
  local log=$BASE/logs/t2b-d1$d1-seed$seed.log
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl $SPEC --bbTargetUrl http://localhost:8090 \
    --configPath $CFG \
    --endpointExclude "$EXCLUDE" \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment $d1 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 200 --maxTime 10m --seed $seed \
    --outputFolder $OUT > $log 2>&1
  local st=$(grep -o "statuses [0-9?/-]*" $log | awk '{print $2}' | paste -sd';' -); [ -z "$st" ] && st=NA
  local ac=$(grep -c "Assembled .* statuses" $log)
  local vc=$(grep -c "Discarded a VOID stateful-authorization" $log)
  local pl=$(grep -c "fresh-credential probe:" $log)
  local p4=$(grep "fresh-credential probe:" $log | grep -c "=403")
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
  echo "tier2b,vuln,$seed,$d1,$d,$ac,$vc,$pl,$p4,$st,$fl" >> $CSV
  echo "$(date +%H:%M:%S) tier2b vuln seed=$seed d1=$d1 det970=$d assembled=$ac void=$vc probe=$pl probe403=$p4 statuses=$st" >> $PROG
}

for s in 1 2 3 4 5 6 7 8 9 10; do
  run_one $s false
  run_one $s true
done
echo "D1 PYLOAD SEEDS 1-10 DONE $(date)" >> $PROG
