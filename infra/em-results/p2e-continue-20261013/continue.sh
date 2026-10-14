#!/usr/bin/env zsh
set -u
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-P2e-6ae8277b.jar
BASE=$THESIS/infra/em-results/p2e-continue-20261013
P2D=$THESIS/infra/em-results/p2d-night-20261012/remeasure/runs.csv
JH=$(/usr/libexec/java_home -v 17)
CSV=$BASE/runs.csv; PROG=$BASE/progress.log
SPEC2B=file://$THESIS/infra/pyload-cve/openapi-merged.json
EXCLUDE="/api/kill,/api/restart"
SUF=""
mkdir -p $BASE/logs $BASE/tests
HEAD="tier,arm,seed,reset,det970,assembled,void_count,resets,restores_ok,restores_no,statuses,faults"
echo $HEAD > $CSV
echo "$HEAD,step" > $BASE/verify-rerun.csv
echo "P2e continue start $(date)  jar=$(shasum -a 256 $JAR | cut -c1-16)" > $PROG
[ "$(shasum -a 256 $JAR | cut -c1-16)" = 6ae8277bef229574 ] || { echo "STOPPED jar sha mismatch" >> $PROG; exit 1; }
echo "images reports=$(docker image inspect reports-api --format '{{.Created}}') vampi=$(docker image inspect vampi-seeded --format '{{.Created}}')" >> $PROG
SLEEP0=$(pmset -g log | grep "Entering Sleep" | tail -1)
ERRS=0

halt () {
  echo "STOPPED $(date +%H:%M:%S) $*" >> $PROG
  exit 1
}

check () {
  local d=$(tail -1 $CSV | cut -d, -f5)
  case $2 in *fixed*) [ "$d" = 1 ] && halt "false positive: $1 $2 seed=$3 reset=$4 det970=1";; esac
  if [ "$d" = ERR ]; then ERRS=$((ERRS+1)); [ $ERRS -ge 2 ] && halt "two consecutive broken rows ending $1 $2 seed=$3 reset=$4"; else ERRS=0; fi
  [ "$(pmset -g log | grep 'Entering Sleep' | tail -1)" != "$SLEEP0" ] && halt "machine slept during $1 $2 seed=$3 reset=$4"
  return 0
}

collect () {
  local st=$(grep -v "proven by an attempt with" $1 | grep -o "statuses [0-9?/-]*" | awk '{print $2}' | paste -sd';' -); [ -z "$st" ] && st=NA
  local ac=$(grep -c "Assembled .* statuses" $1)
  local vc=$(grep -c "Discarded a VOID stateful-authorization" $1)
  local rs=$(grep -c "SUT state reset via" $1)
  local rok=$(grep -c "Privilege-restore accepted" $1)
  local rno=$(grep -c "Privilege-restore refused" $1)
  local d=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$2/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")
  local fl=$(python3 -c "
import json
try: print('|'.join(str(x) for x in sorted({x['code'] for f in json.load(open('$2/report.json'))['faults']['foundFaults'] for x in f['faultCategories']})))
except Exception: print('ERR')")
  echo "$3,$4,$5,$6,$d,$ac,$vc,$rs,$rok,$rno,$st,$fl" >> $CSV
  echo "$(date +%H:%M:%S) $3 $4 seed=$5 reset=$6$SUF det970=$d assembled=$ac void=$vc resets=$rs restore_ok=$rok restore_no=$rno statuses=$st faults=$fl" >> $PROG
  check $3 $4 $5 $6
}

t1 () {
  curl -s -o /dev/null -X POST http://localhost:$2/reset
  local OUT=$BASE/tests/t1-$1-seed$3-r$4$SUF; rm -rf $OUT
  local log=$BASE/logs/t1-$1-seed$3-r$4$SUF.log
  local rf=(); [ "$4" = "1" ] && rf=(--statefulAuthzResetEndpoint "POST http://localhost:$2/reset")
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:$2/v3/api-docs --bbTargetUrl http://localhost:$2 \
    --configPath $THESIS/infra/em-config/reports-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 "${rf[@]}" \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $3 \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT tier1 $1 $3 $4
}

t2 () {
  local rc=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$2/createdb)
  [ "$rc" != "200" ] && sleep 3 && curl -s -o /dev/null http://localhost:$2/createdb
  local OUT=$BASE/tests/t2-$1-seed$3-r$4$SUF; rm -rf $OUT
  local log=$BASE/logs/t2-$1-seed$3-r$4$SUF.log
  local rf=(); [ "$4" = "1" ] && rf=(--statefulAuthzResetEndpoint "GET http://localhost:$2/createdb")
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:$2/openapi.json --bbTargetUrl http://localhost:$2 \
    --configPath $THESIS/infra/em-config/vampi-seeded-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 "${rf[@]}" \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $3 \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT tier2 $1 $3 $4
}

t2b () {
  curl -s -o /dev/null -X POST http://localhost:$2/thesis/reset
  local OUT=$BASE/tests/t2b-$1-seed$3-r$4$SUF; rm -rf $OUT
  local log=$BASE/logs/t2b-$1-seed$3-r$4$SUF.log
  local rf=(); [ "$4" = "1" ] && rf=(--statefulAuthzResetEndpoint "POST http://localhost:$2/thesis/reset")
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl $SPEC2B --bbTargetUrl http://localhost:$2 \
    --configPath $THESIS/infra/em-config/pyload-auth.yaml \
    --endpointExclude "$EXCLUDE" \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 "${rf[@]}" \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 200 --maxTime 10m --seed $3 \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT tier2b $1 $3 $4
}

same_as_p2d () {
  local mine=$(tail -1 $CSV | cut -d, -f5,6,7,8,9,10,11)
  local theirs=$(awk -F, -v t=$1 -v a=$2 -v s=$3 -v r=$4 '$1==t && $2==a && $3==s && $4==r {print $5","$6","$7","$8","$9","$10","$11}' $P2D)
  [ "$mine" = "$theirs" ]
}

echo "=== STEP1 vampi rows affected by C $(date) ===" >> $PROG
for s in 3 5 7 9 11; do t2 ours-vuln  5002 $s 0 < /dev/null; done
for s in 3 5 7 9 11; do t2 ours-fixed 5003 $s 0 < /dev/null; done

echo "=== STEP2 vampi rows not yet run $(date) ===" >> $PROG
for s in $(seq 15 20); do t2 ours-fixed 5003 $s 0 < /dev/null; done
for s in 2 4 6 13 14 15 18; do t2 ours-vuln 5002 $s 1 < /dev/null; done
for s in $(seq 1 20); do t2 ours-fixed 5003 $s 1 < /dev/null; done

echo "=== STEP3 reports rows that called restore with ADMIN only on P2d $(date) ===" >> $PROG
REDO=()
for s in 4 8 9 10 16; do t1 vuln 8080 $s 0 < /dev/null; same_as_p2d tier1 vuln $s 0 || REDO+=("vuln 8080 $s"); done
for s in 4 8 9 10 16 20; do t1 fixed 8081 $s 0 < /dev/null; same_as_p2d tier1 fixed $s 0 || REDO+=("fixed 8081 $s"); done
echo "step3 rows differing from P2d: ${#REDO[@]} ${REDO[*]}" >> $PROG

echo "=== STEP4 pyLoad rows not yet run $(date) ===" >> $PROG
for s in 4 5; do t2b vuln 8090 $s 0 < /dev/null; done
for s in $(seq 1 5); do t2b fixed 8091 $s 0 < /dev/null; done
for s in $(seq 1 5); do t2b vuln  8090 $s 1 < /dev/null; done
for s in $(seq 1 5); do t2b fixed 8091 $s 1 < /dev/null; done

if [ ${#REDO[@]} -gt 0 ]; then
  echo "=== STEP5 re-run step3 rows that differed from P2d, once $(date) ===" >> $PROG
  MAIN=$CSV; CSV=$BASE/verify-rerun-tmp.csv; SUF="-rep2"
  for x in "${REDO[@]}"; do
    set -- ${=x}
    echo $HEAD > $CSV
    t1 $1 $2 $3 0 < /dev/null
    echo "$(tail -1 $CSV),step5" >> $BASE/verify-rerun.csv
  done
  rm -f $CSV; CSV=$MAIN; SUF=""
fi

python3 $BASE/merge.py > $BASE/merge.out 2>&1
echo "merge exit $?: $(head -1 $BASE/merge.out | cut -c1-80)" >> $PROG
python3 $THESIS/infra/em-results/audit970_seeded.py $BASE/tests/t1-* $BASE/tests/t2-* > $BASE/audit970.out 2>&1
echo "audit970 exit $?: $(tail -1 $BASE/audit970.out)" >> $PROG
echo "P2e CONTINUE DONE $(date)" >> $PROG
