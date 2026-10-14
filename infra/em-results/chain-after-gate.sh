#!/usr/bin/env zsh
# Runs the Tier-2b INFERENCE batch after the option-B gate, but ONLY on a full pass.
#
# Launch conditions, both required and both read out of the logs rather than assumed:
#     verify-B/result.log        contains GATE1=PASS
#     regression-check/progress.log ends with failed=0
# Anything else writes a STOP marker and launches nothing. A ~6-hour measurement taken with a build
# that has not cleared the gate produces numbers that have to be thrown away, which is the exact
# mistake this chain exists to avoid.
#
# On failure this does NOT restore the frozen jar. Restoring is a documented step, but it is a step
# taken AFTER a diagnosis, not instead of one -- and the frozen jar is still on disk either way.
set -u
B=/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/em-results
L=$B/chain-after-gate.log
echo "chain waiting for gate-B $(date)" > $L
while pgrep -f "gate-B.sh" >/dev/null 2>&1; do sleep 60; done
echo "gate-B finished $(date)" >> $L

G1=$(grep -c "GATE1=PASS" $B/reproducibility/verify-B/result.log 2>/dev/null)
G2=$(grep -c "failed=0" $B/regression-check/progress.log 2>/dev/null)
echo "GATE1=PASS lines: $G1   regression failed=0 lines: $G2" >> $L
grep -E "frozen correct|newB   correct|GATE1=" $B/reproducibility/verify-B/result.log >> $L 2>/dev/null
tail -3 $B/regression-check/progress.log >> $L 2>/dev/null

if [ "$G1" -ge 1 ] && [ "$G2" -ge 1 ]; then
  echo "=== BOTH PHASES PASSED -- launching tier2b inference batch $(date) ===" >> $L
  $B/tier2b-inference-trials/tier2b_inference_trials.sh >> $L 2>&1
  echo "=== TIER2B CHAIN DONE $(date) ===" >> $L
else
  echo "=== STOP: gate not fully passed. Tier-2b deliberately NOT launched. $(date) ===" >> $L
fi
