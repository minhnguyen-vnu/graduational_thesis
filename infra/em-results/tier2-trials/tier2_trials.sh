#!/usr/bin/env zsh
# Tier-2 head-to-head trials on the seeded VAmPI fork (infra/vampi-seeded/).
# Four arms (docs/tier2-seeded-benchmark-plan.md §5):
#   ours-vuln      :5002 VULNERABLE  + --useExperimentalOracles  -> expect 970 (recall)
#   ours-fixed     :5003 FIXED       + --useExperimentalOracles  -> expect NO 970 (FP rate)
#   base-vuln      :5002 VULNERABLE  WITHOUT our oracle          -> expect NO stateful finding (the delta)
#   base-fixed     :5003 FIXED       WITHOUT our oracle          -> control
#
# Usage: ./tier2_trials.sh [N]     (default N=20 seeds per arm)
set -u

# Refuse to run if another instance is alive. On 2026-08-07 `pkill -f overnight.sh` killed the
# parent but left THIS script orphaned; it kept fuzzing :5002/:5003 for 4 hours and then ran
# concurrently with a fresh batch on the same containers, each reseeding via GET /createdb under
# the other. That silently corrupted a whole Tier-2 measurement. A lockfile makes it impossible.
LOCK=/tmp/tier2_trials.lock
if [ -e $LOCK ] && kill -0 $(cat $LOCK) 2>/dev/null; then
  echo "FATAL: tier2_trials.sh already running as PID $(cat $LOCK). Refusing to start." >&2
  exit 1
fi
echo $$ > $LOCK
# Drop the lock on any exit. On a signal, also kill our OWN children (the in-flight java) so none
# outlives us -- but only direct children: `kill 0` would hit the whole process group, i.e. also
# the overnight.sh that invoked us, killing the later stages on a perfectly normal exit.
trap 'rm -f $LOCK' EXIT
trap 'rm -f $LOCK; pkill -P $$ 2>/dev/null; exit 143' INT TERM

THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/core/target/evomaster.jar
CFG=$THESIS/infra/em-config/vampi-seeded-auth.yaml
BASE=$THESIS/infra/em-results/tier2-trials
JH=$(/usr/libexec/java_home -v 17)
N=${1:-20}

mkdir -p $BASE/logs $BASE/reports
CSV=$BASE/runs.csv
PROG=$BASE/progress.log
echo "arm,port,seed,assembled,assembled_count,void_count,statuses,detected_970,security_codes,other_codes,endpoints_covered,elapsed_s,exit" > $CSV
echo "batch start $(date) N=$N per arm (4 arms = $((N*4)) runs)" > $PROG

run_one () {
  local arm=$1 port=$2 seed=$3 ours=$4
  # reseed: VAmPI's equivalent of reports-api's POST /reset. Retry once -- a 500 here would
  # silently invalidate the run (upstream UNIQUE-collision bug; patched, but stay defensive).
  local rs=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$port/createdb)
  if [ "$rs" != "200" ]; then
    sleep 2
    rs=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$port/createdb)
    echo "$(date +%H:%M:%S) WARN $arm seed=$seed reseed http=$rs" >> $PROG
  fi

  local OUT=$BASE/_tmp_${arm}_${seed}
  rm -rf $OUT
  local log=$BASE/logs/${arm}-seed${seed}.log
  local t0=$(date +%s)

  # The ONLY difference between the two tools is the experimental-oracle flag; every other
  # knob is held constant so the head-to-head is a fair comparison.
  local oracleflag=()
  [ "$ours" = "1" ] && oracleflag=(--useExperimentalOracles true)

  JAVA_HOME=$JH java -jar $JAR \
    --blackBox true \
    --bbSwaggerUrl http://localhost:$port/openapi.json --bbTargetUrl http://localhost:$port \
    --configPath $CFG \
    "${oracleflag[@]}" --extraPhaseBudgetPercentage 0.6 \
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
    # F200-F210 = the Sahin security oracles (CLAUDE.md 7.6); 970 = ours. Kept apart so the
    # head-to-head table can say what each tool found, not just whether ours fired.
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

  # endpoint coverage, for the sanity check that both arms exercise comparable surface
  local cov=$(grep -oE "out of [0-9]+ \([0-9]+%\)" $log | tail -1 | grep -oE "[0-9]+%" | tr -d '%')
  [ -z "$cov" ] && cov=NA

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

  cp -f $OUT/report.json $BASE/reports/${arm}-seed${seed}.report.json 2>/dev/null
  # Keep the generated tests for the BASELINE arms: baseline_blindness.py needs the actual test
  # sources to measure whether the baseline ever assembles a triple. Without them the head-to-head
  # rests only on a fault code we disabled by config, which is circular. For the ours-* arms only
  # the runs that fired are kept, so each 970 can be audited by hand.
  case $arm in
    base-*) mkdir -p $BASE/tests/${arm}-seed${seed}
            cp -f $OUT/EvoMaster_*_Test.py $BASE/tests/${arm}-seed${seed}/ 2>/dev/null ;;
    ours-*) # keep the tests for any run that fired, so every 970 can be hand-audited as a real
            # triple rather than trusted -- this is exactly how the 2026-08-07 false positive was
            # caught. Also keep them when a triple was assembled but no fault was raised: those are
            # the conditional true negatives, and they need auditing just as much as the positives.
            if [ "$det" = "1" ] || [ "$assembled" = "1" ]; then
              mkdir -p $BASE/tests/${arm}-seed${seed}
              # all test files, not just EvoMaster_faults_Test.py: when a triple was assembled but
              # raised no fault, there is no faults file and the triple lives in the others.
              cp -f $OUT/EvoMaster_*_Test.py $BASE/tests/${arm}-seed${seed}/ 2>/dev/null
            fi ;;
  esac
  rm -rf $OUT

  echo "$arm,$port,$seed,$assembled,$ac,$vc,$st,$det,$sec,$othr,$cov,$elapsed,$rc" >> $CSV
  echo "$(date +%H:%M:%S) $arm seed=$seed assembled=$ac void=$vc statuses=$st det970=$det sec=[$sec] cov=${cov}% ${elapsed}s exit=$rc" >> $PROG
}

for seed in $(seq 1 $N); do run_one ours-vuln  5002 $seed 1; done
for seed in $(seq 1 $N); do run_one ours-fixed 5003 $seed 1; done
for seed in $(seq 1 $N); do run_one base-vuln  5002 $seed 0; done
for seed in $(seq 1 $N); do run_one base-fixed 5003 $seed 0; done

echo "batch done $(date)" >> $PROG
{
  echo ""
  echo "================ SUMMARY ================"
  python3 - $CSV <<'PY'
import csv,sys
from collections import Counter
rows=list(csv.DictReader(open(sys.argv[1])))
print(f"{'arm':11s} {'n':>3s} {'assembled':>12s} {'detected970':>12s} {'det|asm':>8s}  security codes seen")
for arm in ('ours-vuln','ours-fixed','base-vuln','base-fixed'):
    a=[r for r in rows if r['arm']==arm]
    if not a: continue
    n=len(a)
    det=sum(int(r['detected_970']) for r in a)
    asm=sum(int(r['assembled']) for r in a)
    sec=Counter(c for r in a for c in r['security_codes'].split('/') if c)
    secs=', '.join(f"{k}x{v}" for k,v in sorted(sec.items())) or '-'
    cond=f"{det}/{asm}" if asm else "n/a"
    print(f"{arm:11s} {n:3d} {asm:5d} ({asm/n*100:3.0f}%) {det:5d} ({det/n*100:3.0f}%) {cond:>8s}  {secs}")
print()
print("HEAD-TO-HEAD: detection of the seeded stateful bug on the VULNERABLE target")
for arm,label in (('ours-vuln','ours (970)'),('base-vuln','Sahin baseline')):
    a=[r for r in rows if r['arm']==arm]
    if not a: continue
    det=sum(int(r['detected_970']) for r in a)
    print(f"  {label:16s}: {det}/{len(a)}")
PY
} >> $PROG
