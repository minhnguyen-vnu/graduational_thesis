#!/usr/bin/env zsh
set -u
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=$EM/evomaster-P2d-2e0dbd4d.jar
AF2=$EM/evomaster-AF2-6b5606d4.jar
BASE=$THESIS/infra/em-results/p2d-night-20261012
GATE=$THESIS/infra/em-results/regression-check
JH=$(/usr/libexec/java_home -v 17)
ST=$BASE/STATUS.log
CMDS=$BASE/cmdlines.txt
mkdir -p $BASE/probe/logs $BASE/fp/logs $BASE/gate/logs $BASE/tmp
SLEEP0=$(pmset -g log | grep "Entering Sleep" | tail -1)

say () { echo "$(date '+%m-%d %H:%M:%S') $*" >> $ST; }
stop () { say "STOP $*"; say "NIGHT CHAIN END stopped"; exit 1; }
slept () { [ "$(pmset -g log | grep 'Entering Sleep' | tail -1)" != "$SLEEP0" ]; }

det () {
  python3 - "$1" <<'PY'
import json, sys
try:
    c = [x['code'] for f in json.load(open(sys.argv[1] + '/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception:
    print('ERR')
PY
}

statuses () {
  local s=$(grep -v "proven by an attempt with" $1 | grep -o "statuses [0-9?/]*" | awk '{print $2}' | paste -sd';' -)
  echo ${s:-NA}
}

emrun () {
  local jar=$1 tier=$2 port=$3 seed=$4 reset=$5 out=$6 log=$7
  local spec cfg rf=()
  if [ "$tier" = 1 ]; then
    curl -s -o /dev/null -X POST http://localhost:$port/reset
    spec=http://localhost:$port/v3/api-docs; cfg=$THESIS/infra/em-config/reports-auth.yaml
    [ "$reset" = 1 ] && rf=(--statefulAuthzResetEndpoint "POST http://localhost:$port/reset")
  else
    local rc=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$port/createdb)
    [ "$rc" != "200" ] && sleep 3 && curl -s -o /dev/null http://localhost:$port/createdb
    spec=http://localhost:$port/openapi.json; cfg=$THESIS/infra/em-config/vampi-seeded-auth.yaml
    [ "$reset" = 1 ] && rf=(--statefulAuthzResetEndpoint "GET http://localhost:$port/createdb")
  fi
  local args=(-jar $jar --blackBox true
    --bbSwaggerUrl $spec --bbTargetUrl http://localhost:$port
    --configPath $cfg
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 "${rf[@]}"
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $seed
    --outputFolder $out)
  echo "$(basename $log): java ${args[*]}" >> $CMDS
  rm -rf $out
  JAVA_HOME=$JH java "${args[@]}" < /dev/null > $log 2>&1
}

[ "$(shasum -a 256 $JAR | cut -c1-16)" = 2e0dbd4dd04e593f ] || stop "jar sha mismatch"
cmp -s $JAR $EM/core/target/evomaster.jar || stop "core/target/evomaster.jar is not P2d; the gate reads it"
say "NIGHT CHAIN START jar=$(shasum -a 256 $JAR | cut -c1-16) power=$(pmset -g batt | head -1 | grep -o "'.*'")"

say "probe start: reports vuln :8080 no-reset seeds 10/13/16 x3"
echo "seed,rep,det970,assembled,void,restore_ok,restore_no,statuses" > $BASE/probe/runs.csv
for s in 10 13 16; do
  for rep in 1 2 3; do
    log=$BASE/probe/logs/seed$s-r$rep.log; out=$BASE/tmp/probe-seed$s-r$rep
    emrun $JAR 1 8080 $s 0 $out $log
    d=$(det $out)
    echo "$s,$rep,$d,$(grep -c 'Assembled .* statuses' $log),$(grep -c 'Discarded a VOID stateful-authorization' $log),$(grep -c 'Privilege-restore accepted' $log),$(grep -c 'Privilege-restore refused' $log),$(statuses $log)" >> $BASE/probe/runs.csv
    say "probe seed=$s rep=$rep det970=$d"
    rm -rf $out
    slept && stop "machine slept during probe"
  done
done
P=$(awk -F, 'NR>1 && $3=="1"' $BASE/probe/runs.csv | wc -l | tr -d ' ')
say "probe done: det970 $P/9"
[ $P -ge 7 ] || stop "probe det970 $P/9 < 7"

say "fp start: reports fixed :8081 + vampi fixed :5003 seeds 1-3 no-reset"
echo "tier,port,seed,det970,assembled,void,restore_ok,restore_no,statuses" > $BASE/fp/runs.csv
for t in 1 2; do
  port=8081; [ $t = 2 ] && port=5003
  for s in 1 2 3; do
    log=$BASE/fp/logs/t$t-seed$s.log; out=$BASE/tmp/fp-t$t-seed$s
    emrun $JAR $t $port $s 0 $out $log
    d=$(det $out)
    echo "$t,$port,$s,$d,$(grep -c 'Assembled .* statuses' $log),$(grep -c 'Discarded a VOID stateful-authorization' $log),$(grep -c 'Privilege-restore accepted' $log),$(grep -c 'Privilege-restore refused' $log),$(statuses $log)" >> $BASE/fp/runs.csv
    say "fp tier$t seed=$s det970=$d"
    rm -rf $out
    [ "$d" = 0 ] || stop "fp tier$t seed=$s det970=$d"
    slept && stop "machine slept during fp"
  done
done
say "fp done: 6/6 det970=0"

say "gate start"
[ -z "$(ls $GATE/logs)" ] || stop "regression-check/logs not empty; archive it first"
zsh $GATE/regression_check.sh > $BASE/gate/gate-run.out 2>&1
G=$?
cp $GATE/observed.csv $GATE/progress.log $BASE/gate/
cp $GATE/logs/*.log $BASE/gate/logs/
say "gate done: exit $G, $(grep -c ',MATCH$' $GATE/observed.csv) MATCH, $(grep -c ',MISMATCH$' $GATE/observed.csv) MISMATCH"
slept && stop "machine slept during gate"
if [ $G != 0 ]; then
  echo "tier,arm,seed,reset,jar,rep,observed_statuses,observed_970" > $BASE/gate/interleave.csv
  grep "MISMATCH$" $GATE/observed.csv | head -3 | while IFS=, read tier arm seed reset rest; do
    port=8080
    case "$tier:$arm" in 1:*fixed*) port=8081;; 2:*vuln*) port=5002;; 2:*fixed*) port=5003;; esac
    for rep in 1 2 3; do
      for lbl in af2 p2d; do
        jar=$JAR; [ $lbl = af2 ] && jar=$AF2
        log=$BASE/gate/logs/interleave-t$tier-$arm-seed$seed-$lbl-r$rep.log; out=$BASE/tmp/il
        emrun $jar $tier $port $seed $reset $out $log
        echo "$tier,$arm,$seed,$reset,$lbl,$rep,$(statuses $log),$(det $out)" >> $BASE/gate/interleave.csv
        rm -rf $out
      done
    done
    say "gate interleave done for tier$tier $arm seed=$seed reset=$reset"
  done
  stop "gate exit $G; mismatching rows re-run interleaved in gate/interleave.csv; remeasure not started"
fi

say "remeasure start (reports -> vampi -> pyLoad, 180 runs)"
zsh $BASE/remeasure/remeasure.sh
R=$?
say "remeasure exit $R: $(tail -1 $BASE/remeasure/progress.log)"
[ $R = 0 ] || stop "remeasure stopped: $(grep STOPPED $BASE/remeasure/progress.log | tail -1)"

python3 $THESIS/infra/em-results/audit970_seeded.py $BASE/remeasure/tests/t1-* $BASE/remeasure/tests/t2-* > $BASE/remeasure/audit970.out 2>&1
say "audit970 (reports+vampi) exit $? -> remeasure/audit970.out: $(tail -1 $BASE/remeasure/audit970.out)"
ROWS=$(($(wc -l < $BASE/remeasure/runs.csv) - 1))
NOTRIPLE=$(awk -F, 'NR>1 && $5=="1" && $6=="0"' $BASE/remeasure/runs.csv | wc -l | tr -d ' ')
say "integrity: rows=$ROWS (expect 180), det970=1 with assembled=0: $NOTRIPLE"
say "NIGHT CHAIN END done"
