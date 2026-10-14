#!/usr/bin/env zsh
set -u
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-AF2-6b5606d4.jar
BASE=$THESIS/infra/em-results/pyload-seeds6-20-af2-20261004
JH=$(/usr/libexec/java_home -v 17)
CSV=$BASE/runs.csv; PROG=$BASE/progress.log
SPEC2B=file://$THESIS/infra/pyload-cve/openapi-merged.json
EXCLUDE="/api/kill,/api/restart"
mkdir -p $BASE/logs $BASE/tests
echo "tier,arm,seed,reset,det970,assembled,void_count,resets,restores_ok,restores_no,statuses,faults" > $CSV
echo "pyLoad seeds 6-20 no-reset start $(date)  jar=$(shasum -a 256 $JAR | cut -c1-16)" > $PROG
echo "protocol: arms vuln:8090 fixed:8091, seed 6-20, reset=0; early-stop if vuln seeds 6,7,8 all assembled=0" >> $PROG
SLEEP0=$(pmset -g log 2>/dev/null | grep -c 'Entering Sleep')

collect () {
  local st=$(grep -o "statuses [0-9?/-]*" $1 | awk '{print $2}' | paste -sd';' -); [ -z "$st" ] && st=NA
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
}

sleepcheck () {
  local n=$(pmset -g log 2>/dev/null | grep -c 'Entering Sleep')
  if [ "$n" -gt "$SLEEP0" ]; then
    echo "$(date +%H:%M:%S) DEVIATION may ngu trong luc batch chay, dung" >> $PROG
    exit 2
  fi
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

echo "=== pyload vuln seeds 6-8 (early-stop probe) $(date) ===" >> $PROG
for s in 6 7 8; do t2b vuln 8090 $s 0; sleepcheck; done
probe=$(awk -F, '$1=="tier2b" && $2=="vuln" && ($3==6||$3==7||$3==8){sum+=$6} END{print sum+0}' $CSV)
if [ "$probe" -eq 0 ]; then
  echo "$(date +%H:%M:%S) DEVIATION vuln seeds 6-8 assembled=0, dung de soat moi truong" >> $PROG
  exit 3
fi
echo "=== pyload vuln seeds 9-20 $(date) ===" >> $PROG
for s in $(seq 9 20); do t2b vuln 8090 $s 0; sleepcheck; done
echo "=== pyload fixed seeds 6-20 $(date) ===" >> $PROG
for s in $(seq 6 20); do t2b fixed 8091 $s 0; sleepcheck; done
echo "PYLOAD SEEDS 6-20 DONE $(date)" >> $PROG
