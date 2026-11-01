#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=${JAR:-/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-SR-77465fe5.jar}
BASE=$THESIS/infra/em-results/regression-check-SR-20261027
JH=$(/usr/libexec/java_home -v 17)
mkdir -p $BASE/logs
OUTCSV=$BASE/observed.csv
PROG=$BASE/progress.log
echo "tier,arm,seed,reset,expected_statuses,observed_statuses,expected_970,observed_970,verdict" > $OUTCSV
echo "regression check (no-reset rows) start $(date)" > $PROG
echo "jar: $JAR $(shasum -a 256 $JAR | cut -c1-16)..." >> $PROG
echo "reset rows: N/A, --statefulAuthzResetEndpoint removed from this jar" >> $PROG

FAILED=0
SLEPT=0

expected_of () {
  local tier=$1 arm=$2 seed=$3
  awk -F, -v a="$arm" -v s="$seed" '$1==a && $3==s {print $7","$8; exit}' \
    $THESIS/infra/em-results/tier${tier}-trials/runs.csv
}

slept_since () {
  pmset -g log | awk -v t="$1" '$0 ~ /Entering Sleep/ && ($1" "$2) >= t {found=1} END {exit found ? 0 : 1}'
}

run_one () {
  local tier=$1 arm=$2 port=$3 seed=$4

  local exp=$(expected_of $tier $arm $seed)
  if [ -z "$exp" ]; then
    echo "$(date +%H:%M:%S) SKIP tier$tier $arm seed=$seed -- no recorded row" >> $PROG
    return
  fi
  local exp_st=${exp%%,*} exp_970=${exp##*,}

  if [ "$tier" = "1" ]; then
    curl -s -X POST http://localhost:$port/reset >/dev/null
  else
    curl -s http://localhost:$port/createdb >/dev/null
  fi

  local OUT=$BASE/_tmp_t${tier}_${arm}_${seed}
  rm -rf $OUT
  local log=$BASE/logs/t${tier}-${arm}-seed${seed}.log
  local spec
  if [ "$tier" = "1" ]; then
    spec=http://localhost:$port/v3/api-docs
    CFG=$THESIS/infra/em-config/reports-auth.yaml
  else
    spec=http://localhost:$port/openapi.json
    CFG=$THESIS/infra/em-config/vampi-seeded-auth.yaml
  fi

  local started=$(date "+%Y-%m-%d %H:%M:%S")
  JAVA_HOME=$JH java -jar $JAR \
    --blackBox true \
    --bbSwaggerUrl $spec --bbTargetUrl http://localhost:$port \
    --configPath $CFG \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $seed \
    --outputFolder $OUT > $log 2>&1

  local obs_st=$(grep -v "proven by an attempt with" $log | grep -o "statuses [0-9?/]*" | awk '{print $2}' | paste -sd';' -)
  [ -z "$obs_st" ] && obs_st=NA
  local obs_970=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")

  local verdict=MATCH
  if [ "$obs_st" != "$exp_st" ] || [ "$obs_970" != "$exp_970" ]; then
    verdict=MISMATCH
    FAILED=1
  fi
  if slept_since "$started"; then
    verdict=FAILED-SLEEP
    FAILED=1
    SLEPT=1
  fi
  echo "$tier,$arm,$seed,0,$exp_st,$obs_st,$exp_970,$obs_970,$verdict" >> $OUTCSV
  echo "$(date +%H:%M:%S) tier$tier $arm seed=$seed reset=0 expected=$exp_st/$exp_970 observed=$obs_st/$obs_970 $verdict" >> $PROG
  rm -rf $OUT
}

for s in 1 2 3; do [ $SLEPT = 0 ] && run_one 1 vuln  8080 $s; done
for s in 1 2 3; do [ $SLEPT = 0 ] && run_one 1 fixed 8081 $s; done
for s in 1 2 3; do [ $SLEPT = 0 ] && run_one 2 ours-vuln  5002 $s; done
for s in 1 2 3; do [ $SLEPT = 0 ] && run_one 2 ours-fixed 5003 $s; done

echo "REGRESSION CHECK DONE $(date) failed=$FAILED slept=$SLEPT" >> $PROG
exit $FAILED
