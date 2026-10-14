#!/usr/bin/env zsh
# Repeated Tier-1 reliability trials for the stateful-authz oracle (fault 970).
# vuln  = :8080 (VULNERABLE)  -> expect 970 to fire (detection rate)
# fixed = :8081 (FIXED)       -> expect 970 to NEVER fire (false-positive rate)
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/core/target/evomaster.jar
CFG=$THESIS/infra/em-config/reports-auth.yaml
BASE=$THESIS/infra/em-results/tier1-trials
JH=$(/usr/libexec/java_home -v 17)
N=${1:-20}

# clean prior pilot clutter; keep a fresh, uniform dataset
rm -rf $BASE/pilot $BASE/pilot.log $BASE/logs $BASE/reports $BASE/_tmp_* 2>/dev/null
mkdir -p $BASE/logs $BASE/reports
CSV=$BASE/runs.csv
PROG=$BASE/progress.log
echo "app,port,seed,assembled,assembled_count,void_count,statuses,detected_970,other_codes,elapsed_s,exit" > $CSV
echo "batch start $(date) N=$N per app" > $PROG

run_one () {
  local app=$1 port=$2 seed=$3
  curl -s -X POST http://localhost:$port/reset >/dev/null
  local OUT=$BASE/_tmp_${app}_${seed}
  rm -rf $OUT
  local log=$BASE/logs/${app}-seed${seed}.log
  local t0=$(date +%s)
  JAVA_HOME=$JH java -jar $JAR \
    --blackBox true \
    --bbSwaggerUrl http://localhost:$port/v3/api-docs --bbTargetUrl http://localhost:$port \
    --configPath $CFG \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $seed \
    --outputFolder $OUT > $log 2>&1
  local rc=$?
  local t1=$(date +%s)
  local elapsed=$((t1-t0))
  local parsed=$(python3 - "$OUT/report.json" <<'PY'
import json,sys
try:
    d=json.load(open(sys.argv[1]))
    codes=[c['code'] for f in d['faults']['foundFaults'] for c in f['faultCategories']]
    det=1 if 970 in codes else 0
    others=sorted(set(codes)-{970})
    print(f"{det}|{'/'.join(map(str,others))}")
except Exception as e:
    print(f"ERR|{e}")
PY
)
  local det=${parsed%%|*}
  local others=${parsed#*|}
  # CONSTRUCTION, counted independently of the verdict: this log line is emitted before
  # judgment runs, so a run with assembled>0 and detected_970=0 is a real true negative
  # (a triple was built and the oracle stayed silent), not merely "nothing was tried".
  local ac=$(grep -c "Assembled a stateful-authorization" $log)
  local assembled=0; [ "$ac" -gt 0 ] && assembled=1
  # the triple's own [source/transition/follow-up] statuses, one group per assembled triple. This is
  # what turns a silent run from an unexplained false negative into a diagnosed one, and what proves
  # a silent run on the FIXED target is a real true negative (2xx/2xx/403) rather than a broken premise.
  local st=$(grep -o "statuses [0-9?/]*" $log | awk '{print $2}' | paste -sd';' -)
  [ -z "$st" ] && st=NA
  # attempts thrown away as VOID (§5.3): the retry that rescued the run, or the proof that no
  # valid (victim, operator) pair was left after the search destroyed the accounts it needed.
  local vc=$(grep -c "Discarded a VOID stateful-authorization" $log)
  cp -f $OUT/report.json $BASE/reports/${app}-seed${seed}.report.json 2>/dev/null
  rm -rf $OUT
  echo "$app,$port,$seed,$assembled,$ac,$vc,$st,$det,$others,$elapsed,$rc" >> $CSV
  echo "$(date +%H:%M:%S) $app seed=$seed assembled=$ac void=$vc statuses=$st det970=$det others=[$others] ${elapsed}s exit=$rc" >> $PROG
}

for seed in $(seq 1 $N); do run_one vuln  8080 $seed; done
for seed in $(seq 1 $N); do run_one fixed 8081 $seed; done

echo "batch done $(date)" >> $PROG
{
  echo ""
  echo "================ SUMMARY ================"
  python3 - $CSV <<'PY'
import csv,sys
rows=list(csv.DictReader(open(sys.argv[1])))
for app in ('vuln','fixed'):
    a=[r for r in rows if r['app']==app]
    n=len(a) or 1
    det=sum(int(r['detected_970']) for r in a)
    asm=sum(int(r['assembled']) for r in a)
    cond=f"{det}/{asm}" if asm else "n/a"
    print(f"{app:5s}: n={len(a)}  assembled={asm} ({asm/n*100:.0f}%)  detected970={det} ({det/n*100:.0f}%)  detected|assembled={cond}")
PY
} >> $PROG
