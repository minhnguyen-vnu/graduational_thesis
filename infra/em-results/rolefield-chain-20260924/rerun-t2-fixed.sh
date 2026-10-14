#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=$EM/core/target/evomaster.jar
BASE=$THESIS/infra/em-results/rolefield-chain-20260924
WANT_JAR=7f9d977e4849080a
JH=$(/usr/libexec/java_home -v 17)
PROG=$BASE/progress.log
CSV=$BASE/runs-t2fixed-rerun.csv

say () { echo "$(date +%H:%M:%S) $*" >> $PROG }

until grep -qE 'CHAIN (DONE|STOPPED)' $PROG; do sleep 30; done
grep -q 'CHAIN STOPPED' $PROG && { say "chay lai t2 fixed: chuoi da dung, khong chay"; exit 1; }

say "chay lai Tier-2 ban da va seeds 1-10: container vampi-seeded-fixed bi OOM luc 03:53, 10 dong ERR o runs.csv giu nguyen"
JARSHA=$(shasum -a 256 $JAR | cut -c1-16)
[ "$JARSHA" = "$WANT_JAR" ] || { say "chay lai t2 fixed: jar sha $JARSHA, cho $WANT_JAR"; exit 1; }
c=$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:5003/openapi.json)
[ "$c" = "200" ] || { say "chay lai t2 fixed: cong 5003 tra $c"; exit 1; }

echo "tier,arm,seed,d1,det970,assembled,void_count,probe_lines,probe_403,statuses,faults" > $CSV
for seed in $(seq 1 10); do
  curl -s -o /dev/null http://localhost:5003/createdb
  OUT=$BASE/tests/t2-fixed-rerun-seed$seed; rm -rf $OUT
  log=$BASE/logs/t2-fixed-rerun-seed$seed.log
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:5003/openapi.json --bbTargetUrl http://localhost:5003 \
    --configPath $THESIS/infra/em-config/vampi-seeded-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $seed \
    --outputFolder $OUT > $log 2>&1
  st=$(grep -o "statuses [0-9?/-]*" $log | awk '{print $2}' | paste -sd';' -); [ -z "$st" ] && st=NA
  ac=$(grep -c "Assembled .* statuses" $log)
  vc=$(grep -c "Discarded a VOID stateful-authorization" $log)
  pl=$(grep -c "fresh-credential probe:" $log)
  p4=$(grep "fresh-credential probe:" $log | grep -c "=403")
  d=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")
  fl=$(python3 -c "
import json
try: print('|'.join(str(x) for x in sorted({x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']})))
except Exception: print('ERR')")
  echo "tier2,fixed,$seed,false,$d,$ac,$vc,$pl,$p4,$st,$fl" >> $CSV
  say "tier2 fixed rerun seed=$seed det970=$d assembled=$ac void=$vc statuses=$st"
done
say "chay lai t2 fixed xong"
echo "RERUN DONE $(date)" >> $PROG
