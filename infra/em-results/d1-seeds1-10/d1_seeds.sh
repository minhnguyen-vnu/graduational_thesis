#!/usr/bin/env zsh
set -u
# Do gi: tren Tier-1 va Tier-2 ban dinh loi, khong reset, seeds 1-10, hai canh khac nhau dung mot bien:
# --statefulAuthzTwoCredentialJudgment false hoac true. Ghi lai 970, so triple lap duoc, so dong log probe
# va ma trang thai cua probe. pyLoad khong nam trong dot nay.
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/core/target/evomaster.jar
BASE=$THESIS/infra/em-results/d1-seeds1-10
JH=$(/usr/libexec/java_home -v 17)
CSV=$BASE/runs.csv; PROG=$BASE/progress.log
mkdir -p $BASE/logs $BASE/tests
echo "tier,arm,seed,d1,det970,assembled,void_count,probe_lines,probe_403,statuses,faults" > $CSV
echo "d1 seeds 1-10 start $(date)  jar=$(shasum -a 256 $JAR | cut -c1-16)" > $PROG

collect () {
  local log=$1 out=$2 tier=$3 arm=$4 seed=$5 d1=$6
  local st=$(grep -o "statuses [0-9?/-]*" $log | awk '{print $2}' | paste -sd';' -); [ -z "$st" ] && st=NA
  local ac=$(grep -c "Assembled .* statuses" $log)
  local vc=$(grep -c "Discarded a VOID stateful-authorization" $log)
  local pl=$(grep -c "fresh-credential probe:" $log)
  local p4=$(grep "fresh-credential probe:" $log | grep -c "=403")
  local d=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$out/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")
  local fl=$(python3 -c "
import json
try: print('|'.join(str(x) for x in sorted({x['code'] for f in json.load(open('$out/report.json'))['faults']['foundFaults'] for x in f['faultCategories']})))
except Exception: print('ERR')")
  echo "$tier,$arm,$seed,$d1,$d,$ac,$vc,$pl,$p4,$st,$fl" >> $CSV
  echo "$(date +%H:%M:%S) $tier $arm seed=$seed d1=$d1 det970=$d assembled=$ac void=$vc probe=$pl probe403=$p4 statuses=$st" >> $PROG
}

t1 () {
  local seed=$1 d1=$2
  curl -s -o /dev/null -X POST http://localhost:8080/reset
  local OUT=$BASE/tests/t1-d1$d1-seed$seed; rm -rf $OUT
  local log=$BASE/logs/t1-d1$d1-seed$seed.log
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:8080/v3/api-docs --bbTargetUrl http://localhost:8080 \
    --configPath $THESIS/infra/em-config/reports-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment $d1 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $seed \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT tier1 vuln $seed $d1
}

t2 () {
  local seed=$1 d1=$2
  curl -s -o /dev/null http://localhost:5002/createdb
  local OUT=$BASE/tests/t2-d1$d1-seed$seed; rm -rf $OUT
  local log=$BASE/logs/t2-d1$d1-seed$seed.log
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:5002/openapi.json --bbTargetUrl http://localhost:5002 \
    --configPath $THESIS/infra/em-config/vampi-seeded-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment $d1 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $seed \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT tier2 vuln $seed $d1
}

for s in $(seq 1 10); do t1 $s false; done
for s in $(seq 1 10); do t1 $s true;  done
for s in $(seq 1 10); do t2 $s false; done
for s in $(seq 1 10); do t2 $s true;  done
echo "D1 SEEDS 1-10 DONE $(date)" >> $PROG
