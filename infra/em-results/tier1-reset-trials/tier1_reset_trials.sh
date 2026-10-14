#!/usr/bin/env zsh
# Tier-1 RESET ABLATION for the stateful-authz oracle (fault 970).
#
# One variable only: --statefulAuthzResetEndpoint. Everything else (seeds, budget, rate, config)
# is identical to tier1_trials.sh, so this directory pairs row-for-row with tier1-trials/runs.csv.
#
#   vuln-reset   :8080 VULNERABLE + reset  -> recall ceiling once state destruction is removed
#   fixed-reset  :8081 FIXED      + reset  -> the reset must not manufacture false positives
#
# WHY: black-box EvoMaster has no analogue of the white-box driver's resetStateOfSUT(), so the
# search spends minutes demoting and deleting the accounts an MR-A1 triple needs. Comparing against
# tier1-trials/ turns "the search destroys its own preconditions" from a diagnosis read off status
# codes into a measured causal claim.
set -u

LOCK=/tmp/tier1_reset_trials.lock
if [ -e $LOCK ] && kill -0 $(cat $LOCK) 2>/dev/null; then
  echo "FATAL: tier1_reset_trials.sh already running as PID $(cat $LOCK). Refusing to start." >&2
  exit 1
fi
echo $$ > $LOCK
trap 'rm -f $LOCK' EXIT
trap 'rm -f $LOCK; pkill -P $$ 2>/dev/null; exit 143' INT TERM

THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/core/target/evomaster.jar
CFG=$THESIS/infra/em-config/reports-auth.yaml
BASE=$THESIS/infra/em-results/tier1-reset-trials
JH=$(/usr/libexec/java_home -v 17)
N=${1:-20}

mkdir -p $BASE/logs $BASE/reports
CSV=$BASE/runs.csv
PROG=$BASE/progress.log
echo "arm,port,seed,assembled,assembled_count,void_count,resets,statuses,detected_970,other_codes,elapsed_s,exit" > $CSV
echo "batch start $(date) N=$N per arm (2 arms = $((N*2)) runs)" > $PROG

run_one () {
  local arm=$1 port=$2 seed=$3
  curl -s -X POST http://localhost:$port/reset >/dev/null
  local OUT=$BASE/_tmp_${arm}_${seed}
  rm -rf $OUT
  local log=$BASE/logs/${arm}-seed${seed}.log
  local t0=$(date +%s)
  JAVA_HOME=$JH java -jar $JAR \
    --blackBox true \
    --bbSwaggerUrl http://localhost:$port/v3/api-docs --bbTargetUrl http://localhost:$port \
    --configPath $CFG \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzResetEndpoint "POST http://localhost:$port/reset" \
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
  local ac=$(grep -c "Assembled a stateful-authorization" $log)
  local assembled=0; [ "$ac" -gt 0 ] && assembled=1
  local st=$(grep -o "statuses [0-9?/]*" $log | awk '{print $2}' | paste -sd';' -)
  [ -z "$st" ] && st=NA
  local vc=$(grep -c "Discarded a VOID stateful-authorization" $log)
  # Proof the hook actually fired. resets=0 with attempts>0 would mean the flag was ignored;
  # resets=0 with attempts=0 is the OTHER failure mode -- no candidate pair existed in the archive
  # at all, which happens upstream in the search and which a reset before the attempt cannot fix.
  local rs=$(grep -c "SUT state reset via" $log)
  cp -f $OUT/report.json $BASE/reports/${arm}-seed${seed}.report.json 2>/dev/null
  rm -rf $OUT
  echo "$arm,$port,$seed,$assembled,$ac,$vc,$rs,$st,$det,$others,$elapsed,$rc" >> $CSV
  echo "$(date +%H:%M:%S) $arm seed=$seed assembled=$ac void=$vc resets=$rs statuses=$st det970=$det others=[$others] ${elapsed}s exit=$rc" >> $PROG
}

for seed in $(seq 1 $N); do run_one vuln-reset  8080 $seed; done
for seed in $(seq 1 $N); do run_one fixed-reset 8081 $seed; done

echo "batch done $(date)" >> $PROG
{
  echo ""
  echo "================ SUMMARY ================"
  python3 - $CSV <<'PY'
import csv,sys
rows=list(csv.DictReader(open(sys.argv[1])))
for arm in ('vuln-reset','fixed-reset'):
    a=[r for r in rows if r['arm']==arm]
    if not a: continue
    n=len(a)
    det=sum(int(r['detected_970']) for r in a)
    asm=sum(int(r['assembled']) for r in a)
    noatt=sum(1 for r in a if int(r['assembled_count'])==0 and int(r['void_count'])==0)
    cond=f"{det}/{asm}" if asm else "n/a"
    print(f"{arm:12s}: n={n}  assembled={asm} ({asm/n*100:.0f}%)  detected970={det} ({det/n*100:.0f}%)"
          f"  det|asm={cond}  no-attempt-at-all={noatt}")
PY
} >> $PROG
