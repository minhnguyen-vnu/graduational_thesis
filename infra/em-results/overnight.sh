#!/usr/bin/env zsh
# Overnight run after the 2026-08-07 judgment-rule fix.
#
#   STAGE 0  wait for the in-flight regression probes (/tmp/regress.out) and GATE on them.
#            If the fixed targets fire 970, or Tier-1 vulnerable does NOT, the oracle is still
#            wrong -- stop and leave everything for review rather than burn ~10 h on bad data.
#   STAGE 1  Tier-1 re-measurement, 20 seeds x {vuln :8080, fixed :8081}. The pre-fix numbers
#            (16/20, 0/20) are void: they were produced by the old rule.
#   STAGE 2  Tier-2 head-to-head, 20 seeds x 4 arms on the seeded VAmPI fork.
#   STAGE 3  baseline_blindness.py over the retained baseline-arm tests (the "cannot CONSTRUCT"
#            axis), so the head-to-head does not rest on a config-disabled fault code alone.
#
# Everything is appended to overnight.log; each stage also writes its own CSV.
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
BASE=$THESIS/infra/em-results
LOG=$BASE/overnight.log

say () { echo "$(date '+%m-%d %H:%M:%S') $*" >> $LOG }

: > $LOG
say "=== overnight run start ==="

# ---------------------------------------------------------------- STAGE 0: gate
# SKIP_GATE=1 reuses an already-completed /tmp/regress.out instead of waiting again.
say "STAGE 0: waiting for regression probes"
if [ "${SKIP_GATE:-0}" != "1" ]; then
  for i in $(seq 1 120); do
    grep -q DONE /tmp/regress.out 2>/dev/null && break
    sleep 30
  done
fi
if ! grep -q DONE /tmp/regress.out 2>/dev/null; then
  say "ABORT: regression probes did not finish in 60 min"
  exit 1
fi
cat /tmp/regress.out >> $LOG

t1v=$(grep -o 't1vuln: 970=[0-9]*'  /tmp/regress.out | grep -o '[0-9]*$')
t1f=$(grep -o 't1fixed: 970=[0-9]*' /tmp/regress.out | grep -o '[0-9]*$')
v2v=$(grep -o 'v2vuln: 970=[0-9]*'  /tmp/regress.out | grep -o '[0-9]*$')
v2f=$(grep -o 'v2fixed: 970=[0-9]*' /tmp/regress.out | grep -o '[0-9]*$')
t1v=${t1v:-0}; t1f=${t1f:-9}; v2v=${v2v:-0}; v2f=${v2f:-9}
say "gate values: t1vuln=$t1v t1fixed=$t1f v2vuln=$v2v v2fixed=$v2f"

# Hard gate: a FIXED target must never fire. (Single seeds, so we do NOT gate on the vulnerable
# targets firing -- detection is stochastic and a single miss is normal; stage 1/2 measure it.)
if [ "$t1f" != "0" ] || [ "$v2f" != "0" ]; then
  say "ABORT: 970 fired on a FIXED target -- false positive survives the fix. Nothing else run."
  exit 1
fi
say "GATE PASSED (no firing on fixed targets)"

# ---------------------------------------------------------------- STAGE 1: Tier-1
say "STAGE 1: Tier-1 re-measurement (40 runs)"
cd $BASE/tier1-trials
# Remove the previous CSV/summary outright: the stale file has exactly 40 rows, so a row-count
# guard would happily pass on last week's data if a failed run left it in place.
rm -f runs.csv progress.log
zsh ./tier1_trials.sh 20 >> $LOG 2>&1
rc=$?
[ $rc -ne 0 ] && { say "ABORT: tier1_trials.sh exited $rc"; exit 1 }
n1=$(( $(wc -l < $BASE/tier1-trials/runs.csv) - 1 ))
[ "$n1" -lt 40 ] && { say "ABORT: Tier-1 produced $n1/40 rows"; exit 1 }
say "STAGE 1 done ($n1 runs)"
sed -n '/SUMMARY/,$p' $BASE/tier1-trials/progress.log >> $LOG

# ---------------------------------------------------------------- STAGE 2: Tier-2
say "STAGE 2: Tier-2 head-to-head (80 runs)"
cd $BASE/tier2-trials
rm -f runs.csv progress.log
zsh ./tier2_trials.sh 20 >> $LOG 2>&1
rc=$?
[ $rc -ne 0 ] && { say "ABORT: tier2_trials.sh exited $rc"; exit 1 }
n2=$(( $(wc -l < $BASE/tier2-trials/runs.csv) - 1 ))
[ "$n2" -lt 80 ] && { say "ABORT: Tier-2 produced $n2/80 rows"; exit 1 }
say "STAGE 2 done ($n2 runs)"
sed -n '/SUMMARY/,$p' $BASE/tier2-trials/progress.log >> $LOG

# ---------------------------------------------------------------- STAGE 3: blindness
say "STAGE 3: baseline construction-blindness analysis"
python3 $BASE/tier2-trials/baseline_blindness.py $BASE/tier2-trials/tests/base-vuln-* >> $LOG 2>&1
say "=== overnight run complete ==="
