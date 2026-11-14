#!/usr/bin/env zsh
set -u
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
E=$THESIS/infra/em-results
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-SLM2-b8b5cf1a.jar
WANT=b8b5cf1adb560c87
BASE=$E/slm2-wave1-20261112
JH=$(/usr/libexec/java_home -v 17)
SPEC2B=file://$THESIS/infra/pyload-cve/openapi-merged.json
EXCLUDE="/api/kill,/api/restart"
MAIN=$BASE/progress.log
mkdir -p $BASE/logs $BASE/tests
echo "M2 wave1 start $(date)  jar=$(shasum -a 256 $JAR | cut -c1-16)" > $MAIN
[ "$(shasum -a 256 $JAR | cut -c1-16)" = $WANT ] || { echo "STOPPED jar sha mismatch" >> $MAIN; exit 1; }
echo "images reports=$(docker image inspect reports-api --format '{{.Created}}') vampi=$(docker image inspect vampi-seeded --format '{{.Created}}')" >> $MAIN
SLEEP0=$(pmset -g log | grep "Entering Sleep" | tail -1)

halt () {
  echo "STOPPED $(date +%H:%M:%S) $*" >> $PROG
  exit 1
}

check () {
  local d=$(tail -1 $CSV | cut -d, -f5)
  case $2 in *fixed*) [ "$d" = 1 ] && halt "false positive: $1 $2 seed=$3 det970=1";; esac
  if [ "$d" = ERR ]; then ERRS=$((ERRS+1)); [ $ERRS -ge 2 ] && halt "two consecutive broken rows ending $1 $2 seed=$3"; else ERRS=0; fi
  case $2 in *vuln*)
    local n=$(awk -F, -v t=$1 -v a=$2 '$1==t && $2==a' $CSV | wc -l | tr -d ' ')
    local s=$(awk -F, -v t=$1 -v a=$2 '$1==t && $2==a {x+=$6} END {print x+0}' $CSV)
    [ "$n" = 3 ] && [ "$s" = 0 ] && halt "first 3 rows of $1 $2 assembled 0";;
  esac
  [ "$(pmset -g log | grep 'Entering Sleep' | tail -1)" != "$SLEEP0" ] && halt "machine slept during $1 $2 seed=$3"
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
  echo "$3,$4,$5,0,$d,$ac,$vc,$rs,$rok,$rno,$st,$fl" >> $CSV
  echo "$(date +%H:%M:%S) $3 $4 seed=$5 det970=$d assembled=$ac void=$vc statuses=$st faults=$fl" >> $PROG
  echo "$(date +%H:%M:%S) $3 $4 seed=$5 det970=$d assembled=$ac statuses=$st faults=$fl" >> $MAIN
  check $3 $4 $5
}

t1 () {
  curl -s -o /dev/null -X POST http://localhost:$2/reset
  local OUT=$BASE/tests/t1-$1-seed$3; rm -rf $OUT
  local log=$BASE/logs/t1-$1-seed$3.log
  JAVA_HOME=$JH java -Xmx2g -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:$2/v3/api-docs --bbTargetUrl http://localhost:$2 \
    --configPath $THESIS/infra/em-config/reports-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $3 \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT tier1 $1 $3
}

t2 () {
  local rc=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$2/createdb)
  [ "$rc" != "200" ] && sleep 3 && curl -s -o /dev/null http://localhost:$2/createdb
  local OUT=$BASE/tests/t2-$1-seed$3; rm -rf $OUT
  local log=$BASE/logs/t2-$1-seed$3.log
  JAVA_HOME=$JH java -Xmx2g -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:$2/openapi.json --bbTargetUrl http://localhost:$2 \
    --configPath $THESIS/infra/em-config/vampi-seeded-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $3 \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT tier2 $1 $3
}

t2b () {
  curl -s -o /dev/null -X POST http://localhost:$2/thesis/reset
  local OUT=$BASE/tests/t2b-$1-seed$3; rm -rf $OUT
  local log=$BASE/logs/t2b-$1-seed$3.log
  JAVA_HOME=$JH java -Xmx2g -jar $JAR --blackBox true \
    --bbSwaggerUrl $SPEC2B --bbTargetUrl http://localhost:$2 \
    --configPath $THESIS/infra/em-config/pyload-auth.yaml \
    --endpointExclude "$EXCLUDE" \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 200 --maxTime 10m --seed $3 \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT tier2b $1 $3
}

have () { grep -q "^$1,$2,$3,0," $CSV 2>/dev/null; }

lane () {
  CSV=$BASE/runs-$1.csv
  PROG=$BASE/logs/$1.log
  ERRS=0
  local WD=$BASE/wd/$1
  mkdir -p $WD && cd $WD
  echo "tier,arm,seed,reset,det970,assembled,void_count,resets,restores_ok,restores_no,statuses,faults" > $CSV
  echo "lane $1 start $(date) wd=$WD" > $PROG
  local fn=$2 tier=$3 a=$4 port=$5 n=$6
  for s in $(seq 1 $n); do have $tier $a $s || $fn $a $port $s < /dev/null; done
  echo "lane $1 DONE $(date)" >> $PROG
}

lane t1v  t1  tier1  vuln       8080 20 &
lane t1f  t1  tier1  fixed      8081 20 &
lane t2v  t2  tier2  ours-vuln  5002 20 &
lane t2f  t2  tier2  ours-fixed 5003 20 &
lane t2bv t2b tier2b vuln       8090 5 &
lane t2bf t2b tier2b fixed      8091 5 &
wait

OUT=$BASE/runs.csv
echo "tier,arm,seed,reset,det970,assembled,void_count,resets,restores_ok,restores_no,statuses,faults" > $OUT
for f in t1v t1f t2v t2f t2bv t2bf; do tail -n +2 $BASE/runs-$f.csv 2>/dev/null >> $OUT; done
echo "M2 WAVE1 DONE $(date)  rows=$(tail -n +2 $OUT | wc -l | tr -d ' ')" >> $MAIN
