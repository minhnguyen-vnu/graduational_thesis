#!/usr/bin/env zsh
set -u
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
E=$THESIS/infra/em-results
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-P2e-6ae8277b.jar
BASE=$E/p2e-full-20261014
JH=$(/usr/libexec/java_home -v 17)
CSV=$BASE/runs.csv; PROG=$BASE/progress.log; GATE=$BASE/gate.csv
SPEC2B=file://$THESIS/infra/pyload-cve/openapi-merged.json
EXCLUDE="/api/kill,/api/restart"
mkdir -p $BASE/logs $BASE/tests
echo "tier,arm,seed,reset,det970,assembled,void_count,resets,restores_ok,restores_no,statuses,faults" > $CSV
echo "tier,arm,seed,reset,expected_statuses,observed_statuses,expected_970,observed_970,verdict" > $GATE
echo "P2e full start $(date)  jar=$(shasum -a 256 $JAR | cut -c1-16)" > $PROG
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
  case $2 in *vuln*)
    local n=$(awk -F, -v t=$1 -v a=$2 -v r=$4 '$1==t && $2==a && $4==r' $CSV | wc -l | tr -d ' ')
    local s=$(awk -F, -v t=$1 -v a=$2 -v r=$4 '$1==t && $2==a && $4==r {x+=$6} END {print x+0}' $CSV)
    [ "$n" = 3 ] && [ "$s" = 0 ] && halt "first 3 rows of $1 $2 reset=$4 assembled 0";;
  esac
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
  echo "$(date +%H:%M:%S) $3 $4 seed=$5 reset=$6 det970=$d assembled=$ac void=$vc resets=$rs restore_ok=$rok restore_no=$rno statuses=$st faults=$fl" >> $PROG
  check $3 $4 $5 $6
}

t1 () {
  curl -s -o /dev/null -X POST http://localhost:$2/reset
  local OUT=$BASE/tests/t1-$1-seed$3-r$4; rm -rf $OUT
  local log=$BASE/logs/t1-$1-seed$3-r$4.log
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
  local OUT=$BASE/tests/t2-$1-seed$3-r$4; rm -rf $OUT
  local log=$BASE/logs/t2-$1-seed$3-r$4.log
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
  local OUT=$BASE/tests/t2b-$1-seed$3-r$4; rm -rf $OUT
  local log=$BASE/logs/t2b-$1-seed$3-r$4.log
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

expected_of () {
  local tier=$1 arm=$2 seed=$3 reset=$4 csv cs cd
  if [ "$reset" = "1" ]; then csv=$E/tier${tier}-reset-trials/runs.csv; cs=8; cd=9; else csv=$E/tier${tier}-trials/runs.csv; cs=7; cd=8; fi
  awk -F, -v a="$arm" -v s="$seed" -v cs="$cs" -v cd="$cd" '$1==a && $3==s {print $cs","$cd; exit}' $csv
}

gate () {
  local tier=$1 garm=$2 arm=$3 port=$4 seed=$5 reset=$6
  local exp=$(expected_of $tier $garm $seed $reset)
  [ -z "$exp" ] && halt "gate row tier$tier $garm seed=$seed has no recorded expectation"
  local exp_st=${exp%%,*} exp_970=${exp##*,}
  t$tier $arm $port $seed $reset < /dev/null
  local log=$BASE/logs/t$tier-$arm-seed$seed-r$reset.log
  local obs_st=$(grep -v "proven by an attempt with" $log | grep -o "statuses [0-9?/]*" | awk '{print $2}' | paste -sd';' -); [ -z "$obs_st" ] && obs_st=NA
  local obs_970=$(tail -1 $CSV | cut -d, -f5)
  local v=MATCH; [ "$obs_st" != "$exp_st" -o "$obs_970" != "$exp_970" ] && v=MISMATCH
  echo "$tier,$garm,$seed,$reset,$exp_st,$obs_st,$exp_970,$obs_970,$v" >> $GATE
  echo "$(date +%H:%M:%S) gate tier$tier $garm seed=$seed reset=$reset expected=$exp_st/$exp_970 observed=$obs_st/$obs_970 $v" >> $PROG
  [ $v = MISMATCH ] && halt "gate mismatch tier$tier $garm seed=$seed reset=$reset"
  return 0
}

have () {
  grep -q "^$1,$2,$3,$4," $CSV
}

arm () {
  local fn=$1 tier=$2 a=$3 port=$4 n=$5 reset=$6
  for s in $(seq 1 $n); do have $tier $a $s $reset || $fn $a $port $s $reset < /dev/null; done
}

echo "=== PHASE1 gate rows $(date) ===" >> $PROG
for s in 1 2 3; do gate 1 vuln vuln 8080 $s 0; done
for s in 1 2 3; do gate 1 fixed fixed 8081 $s 0; done
for s in 1 2 3; do gate 2 ours-vuln ours-vuln 5002 $s 0; done
for s in 1 2 3; do gate 2 ours-fixed ours-fixed 5003 $s 0; done
for s in 1 2 3; do gate 1 fixed-reset fixed 8081 $s 1; done
gate 1 vuln-reset vuln 8080 1 1
for s in 1 3 2; do gate 2 ours-fixed-reset ours-fixed 5003 $s 1; done
gate 2 ours-vuln-reset ours-vuln 5002 15 1
gate 2 ours-vuln-reset ours-vuln 5002 1 1
echo "gate $(grep -c ',MATCH$' $GATE)/21 MATCH $(date)" >> $PROG

echo "=== PHASE2 tier1 reports $(date) ===" >> $PROG
arm t1 tier1 vuln  8080 20 0
arm t1 tier1 fixed 8081 20 0
arm t1 tier1 vuln  8080 20 1
arm t1 tier1 fixed 8081 20 1
echo "=== PHASE2 tier2 vampi $(date) ===" >> $PROG
arm t2 tier2 ours-vuln  5002 20 0
arm t2 tier2 ours-fixed 5003 20 0
arm t2 tier2 ours-vuln  5002 20 1
arm t2 tier2 ours-fixed 5003 20 1
echo "=== PHASE2 tier2b pyload $(date) ===" >> $PROG
arm t2b tier2b vuln  8090 5 0
arm t2b tier2b vuln  8090 5 1
arm t2b tier2b fixed 8091 5 0
arm t2b tier2b fixed 8091 5 1

python3 $BASE/compare.py > $BASE/compare.out 2>&1
echo "compare exit $?: $(head -1 $BASE/compare.out | cut -c1-80)" >> $PROG
python3 $E/audit970_seeded.py $BASE/tests/t1-* $BASE/tests/t2-* > $BASE/audit970.out 2>&1
echo "audit970 exit $?: $(tail -1 $BASE/audit970.out)" >> $PROG
echo "P2E FULL DONE $(date)" >> $PROG
