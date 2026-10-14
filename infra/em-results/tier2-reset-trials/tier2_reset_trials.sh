#!/usr/bin/env zsh
# Tier-2 RESET ABLATION on the seeded VAmPI fork (infra/vampi-seeded/).
#
# One variable only: --statefulAuthzResetEndpoint. Everything else is identical to tier2_trials.sh,
# so this pairs row-for-row with the ours-* arms of tier2-trials/runs.csv.
#
#   ours-vuln-reset   :5002 VULNERABLE + reset -> recall ceiling once state destruction is removed
#   ours-fixed-reset  :5003 FIXED      + reset -> the reset must not manufacture false positives
#
# The baseline arms are NOT repeated: the baseline has no 970 oracle at all, so the ablation is
# ours-vs-ours by construction. See tier2-trials/ for the head-to-head.
set -u

LOCK=/tmp/tier2_reset_trials.lock
if [ -e $LOCK ] && kill -0 $(cat $LOCK) 2>/dev/null; then
  echo "FATAL: tier2_reset_trials.sh already running as PID $(cat $LOCK). Refusing to start." >&2
  exit 1
fi
echo $$ > $LOCK
trap 'rm -f $LOCK' EXIT
trap 'rm -f $LOCK; pkill -P $$ 2>/dev/null; exit 143' INT TERM

THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/core/target/evomaster.jar
CFG=$THESIS/infra/em-config/vampi-seeded-auth.yaml
BASE=$THESIS/infra/em-results/tier2-reset-trials
JH=$(/usr/libexec/java_home -v 17)
N=${1:-20}

mkdir -p $BASE/logs $BASE/reports
CSV=$BASE/runs.csv
PROG=$BASE/progress.log
echo "arm,port,seed,assembled,assembled_count,void_count,resets,statuses,detected_970,security_codes,other_codes,endpoints_covered,elapsed_s,exit" > $CSV
echo "batch start $(date) N=$N per arm (2 arms = $((N*2)) runs)" > $PROG

run_one () {
  local arm=$1 port=$2 seed=$3
  local rs0=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$port/createdb)
  if [ "$rs0" != "200" ]; then
    sleep 2
    rs0=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$port/createdb)
    echo "$(date +%H:%M:%S) WARN $arm seed=$seed reseed http=$rs0" >> $PROG
  fi

  local OUT=$BASE/_tmp_${arm}_${seed}
  rm -rf $OUT
  local log=$BASE/logs/${arm}-seed${seed}.log
  local t0=$(date +%s)

  JAVA_HOME=$JH java -jar $JAR \
    --blackBox true \
    --bbSwaggerUrl http://localhost:$port/openapi.json --bbTargetUrl http://localhost:$port \
    --configPath $CFG \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzResetEndpoint "GET http://localhost:$port/createdb" \
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
    det = 1 if 970 in codes else 0
    sec  = sorted({c for c in set(codes) if 200 <= c <= 210})
    othr = sorted(set(codes) - set(sec) - {970})
    print(f"{det}|{'/'.join(map(str,sec))}|{'/'.join(map(str,othr))}")
except Exception as e:
    print(f"ERR|{e}|")
PY
)
  local det=${parsed%%|*}
  local rest=${parsed#*|}
  local sec=${rest%%|*}
  local othr=${rest#*|}

  local cov=$(grep -oE "out of [0-9]+ \([0-9]+%\)" $log | tail -1 | grep -oE "[0-9]+%" | tr -d '%')
  [ -z "$cov" ] && cov=NA

  local ac=$(grep -c "Assembled a stateful-authorization" $log)
  local assembled=0; [ "$ac" -gt 0 ] && assembled=1
  local st=$(grep -o "statuses [0-9?/]*" $log | awk '{print $2}' | paste -sd';' -)
  [ -z "$st" ] && st=NA
  local vc=$(grep -c "Discarded a VOID stateful-authorization" $log)
  # Proof the hook actually fired. resets=0 with attempts=0 is the OTHER failure mode -- no candidate
  # pair existed in the archive at all, which happens upstream in the search and which a reset placed
  # before the attempt cannot fix. Keeping the two apart is the point of this ablation.
  local rs=$(grep -c "SUT state reset via" $log)

  cp -f $OUT/report.json $BASE/reports/${arm}-seed${seed}.report.json 2>/dev/null
  if [ "$det" = "1" ] || [ "$assembled" = "1" ]; then
    mkdir -p $BASE/tests/${arm}-seed${seed}
    cp -f $OUT/EvoMaster_*_Test.py $BASE/tests/${arm}-seed${seed}/ 2>/dev/null
  fi
  rm -rf $OUT

  echo "$arm,$port,$seed,$assembled,$ac,$vc,$rs,$st,$det,$sec,$othr,$cov,$elapsed,$rc" >> $CSV
  echo "$(date +%H:%M:%S) $arm seed=$seed assembled=$ac void=$vc resets=$rs statuses=$st det970=$det sec=[$sec] cov=${cov}% ${elapsed}s exit=$rc" >> $PROG
}

for seed in $(seq 1 $N); do run_one ours-vuln-reset  5002 $seed; done
for seed in $(seq 1 $N); do run_one ours-fixed-reset 5003 $seed; done

echo "batch done $(date)" >> $PROG
{
  echo ""
  echo "================ SUMMARY ================"
  python3 - $CSV <<'PY'
import csv,sys
from collections import Counter
rows=list(csv.DictReader(open(sys.argv[1])))
for arm in ('ours-vuln-reset','ours-fixed-reset'):
    a=[r for r in rows if r['arm']==arm]
    if not a: continue
    n=len(a)
    det=sum(int(r['detected_970']) for r in a)
    asm=sum(int(r['assembled']) for r in a)
    noatt=sum(1 for r in a if int(r['assembled_count'])==0 and int(r['void_count'])==0)
    sec=Counter(c for r in a for c in r['security_codes'].split('/') if c)
    secs=', '.join(f"{k}x{v}" for k,v in sorted(sec.items())) or '-'
    cond=f"{det}/{asm}" if asm else "n/a"
    print(f"{arm:17s}: n={n}  assembled={asm} ({asm/n*100:.0f}%)  detected970={det} ({det/n*100:.0f}%)"
          f"  det|asm={cond}  no-attempt-at-all={noatt}  sec[{secs}]")
PY
} >> $PROG
