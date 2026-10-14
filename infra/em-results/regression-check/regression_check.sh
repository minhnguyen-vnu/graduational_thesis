#!/usr/bin/env zsh
# REGRESSION CHECK for the declared-transition extension (statefulAuthzTransition).
#
# The extension is gated behind a config option that defaults to empty, so by design the default
# code path is untouched and the recorded Tier-1/Tier-2 numbers still stand. This script exists
# because a DESIGN argument is not a MEASUREMENT -- and the extension did not only add code, it
# rewrote the reducedRole branch and changed the signature of the predicate shared with the
# judgment side, either of which could move the default behaviour.
#
# Method: re-run a few recorded (arm, seed) pairs with the NEW jar and DEFAULT flags -- no
# --statefulAuthzTransition anywhere -- and compare the triple statuses and the 970 verdict against
# infra/em-results/tier{1,2}-trials/runs.csv. Every other flag is copied from the original
# harnesses, so a mismatch can only come from the jar.
#
# Tier-1 is the sharpest probe: it was uniform to the run, all 20 vulnerable runs 200/200/200 and
# all 20 fixed 200/200/403. Tier-2 is included precisely because it is NOT uniform -- seed 2 built
# no triple at all -- so this also checks that a barren run stays barren rather than only that a
# detection stays a detection.
#
# The RESET arms (CLAUDE.md 6.1) are covered too, and deliberately weighted towards the FIXED
# targets. That is the gap the "re-run the FP arms" requirement names: broadening what counts as a
# permission-reducing transition is the exact mechanism that produced the earlier VAmPI false
# positive, so the rows that matter most are the ones where the oracle MUST stay silent. The reset
# arms are also the ones that build the most triples on a fixed target -- i.e. the most
# opportunities to raise a false alarm -- which makes them a stronger FP probe than the no-reset
# arms, not a weaker one.
#
# Exit 0 = every checked row reproduced. Exit 1 = at least one mismatch; revert with
# evomaster-frozen-769c16d.jar (see EvoMaster/evomaster-frozen-769c16d.jar.sha256).
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/core/target/evomaster.jar
BASE=$THESIS/infra/em-results/regression-check
JH=$(/usr/libexec/java_home -v 17)
mkdir -p $BASE/logs
OUTCSV=$BASE/observed.csv
PROG=$BASE/progress.log
echo "tier,arm,seed,reset,expected_statuses,observed_statuses,expected_970,observed_970,verdict" > $OUTCSV
echo "regression check start $(date)" > $PROG
echo "jar: $(shasum -a 256 $JAR | cut -c1-16)..." >> $PROG

FAILED=0

# Pull the recorded row out of the original CSV, so expectations are never re-typed by hand.
# The reset harnesses inserted a "resets" column before "statuses", so the two layouts differ by
# exactly one position; that offset is the only thing this function has to know.
#   no-reset: arm,port,seed,assembled,assembled_count,void_count,statuses,detected_970,...
#   reset   : arm,port,seed,assembled,assembled_count,void_count,resets,statuses,detected_970,...
expected_of () {
  local tier=$1 arm=$2 seed=$3 reset=$4
  local csv col_st col_970
  if [ "$reset" = "1" ]; then
    csv=$THESIS/infra/em-results/tier${tier}-reset-trials/runs.csv; col_st=8; col_970=9
  else
    csv=$THESIS/infra/em-results/tier${tier}-trials/runs.csv;        col_st=7; col_970=8
  fi
  awk -F, -v a="$arm" -v s="$seed" -v cs="$col_st" -v cd="$col_970" \
    '$1==a && $3==s {print $cs","$cd; exit}' $csv
}

run_one () {
  local tier=$1 arm=$2 port=$3 seed=$4 reset=${5:-0}

  local exp=$(expected_of $tier $arm $seed $reset)
  if [ -z "$exp" ]; then
    echo "$(date +%H:%M:%S) SKIP tier$tier $arm seed=$seed -- no recorded row" >> $PROG
    return
  fi
  local exp_st=${exp%%,*} exp_970=${exp##*,}

  # Reseed exactly as the original harness did.
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

  # Copied verb-for-verb from the two reset harnesses, so the only difference from the recorded
  # run remains the jar.
  local rflag=()
  if [ "$reset" = "1" ]; then
    if [ "$tier" = "1" ]; then
      rflag=(--statefulAuthzResetEndpoint "POST http://localhost:$port/reset")
    else
      rflag=(--statefulAuthzResetEndpoint "GET http://localhost:$port/createdb")
    fi
  fi

  # NOTE: no --statefulAuthzTransition. That absence is the whole point of this check.
  JAVA_HOME=$JH java -jar $JAR \
    --blackBox true \
    --bbSwaggerUrl $spec --bbTargetUrl http://localhost:$port \
    --configPath $CFG \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    "${rflag[@]}" \
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
  echo "$tier,$arm,$seed,$reset,$exp_st,$obs_st,$exp_970,$obs_970,$verdict" >> $OUTCSV
  echo "$(date +%H:%M:%S) tier$tier $arm seed=$seed reset=$reset expected=$exp_st/$exp_970 observed=$obs_st/$obs_970 $verdict" >> $PROG
  rm -rf $OUT
}

# --- no-reset arms (the headline configuration) -------------------------------------------------
# Tier-1: deterministic, so any drift shows immediately.
for s in 1 2 3; do run_one 1 vuln  8080 $s; done
for s in 1 2 3; do run_one 1 fixed 8081 $s; done
# Tier-2: seed 1 detected, seed 2 built no triple -- both must reproduce.
for s in 1 2 3; do run_one 2 ours-vuln  5002 $s; done
for s in 1 2 3; do run_one 2 ours-fixed 5003 $s; done

# --- reset arms, weighted towards the FIXED targets (the false-positive probe) -------------------
# Tier-1 fixed-reset is the densest FP opportunity in the whole evaluation: all 20 recorded runs
# built a real triple and every one of them was correctly silent.
for s in 1 2 3; do run_one 1 fixed-reset 8081 $s 1; done
run_one 1 vuln-reset 8080 1 1
# Tier-2 reset rows chosen for OUTCOME diversity, not convenience:
#   fixed seed 1  -> triple built, correctly silent          (plain FP probe)
#   fixed seed 3  -> 3 VOID attempts, 4 resets, then silent  (exercises retry + reset loop)
#   fixed seed 2  -> barren, no triple at all                (barren must stay barren)
#   vuln  seed 15 -> 3 VOID attempts and NO detection        (the seed-15 regression of 6.1)
#   vuln  seed 1  -> detection                               (a true positive must survive too)
for s in 1 3 2; do run_one 2 ours-fixed-reset 5003 $s 1; done
run_one 2 ours-vuln-reset 5002 15 1
run_one 2 ours-vuln-reset 5002 1  1

echo "REGRESSION CHECK DONE $(date) failed=$FAILED" >> $PROG
if [ "$FAILED" = "0" ]; then
  echo "ALL ROWS REPRODUCED" >> $PROG
else
  echo "MISMATCHES PRESENT -- do not proceed; revert to evomaster-frozen-769c16d.jar" >> $PROG
fi
exit $FAILED
