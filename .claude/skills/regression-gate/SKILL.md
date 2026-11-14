---
name: regression-gate
description: Run and interpret the 12-row EvoMaster regression gate. Use before a new jar is used to re-quote any existing number, and when a gate row mismatches.
---

# Regression gate

- Script: `infra/em-results/regression-check-SR-20261027/regression_check_noreset.sh`, jar set by `JAR=`. Copy it into
  a new folder `infra/em-results/regression-check-<jar>-<yyyymmdd>/` before a run.
- 12 recorded no-reset `(arm, seed)` rows on reports-api and vampi-seeded, re-run with their original flags. Half are
  fixed-target rows. Four vampi-seeded rows (seeds 2–3) expect `NA/0`: they show only that no triple was built and 970
  did not fire.
- Expectations are read by `awk` from `tier{1,2}-trials/runs.csv`, never retyped. The reports-api expectations equal
  the cleaned-app batch (`tier1-clean-remeasure/`).
- Output `observed.csv` (verdict MATCH per row) and `progress.log`; exit 1 on any mismatch. ~1 h.
- The 21-row gate of P2f and earlier (`regression-check/regression_check.sh`) adds 9 reset rows; jars from SR on have
  no reset, so it no longer runs.
- Passed: SR 12/12 on 2026-10-27 (`regression-check-SR-20261027/`), DC 12/12 on 2026-11-03
  (`regression-check-DC-20261103/`). M2 and ND ran no gate: each re-measured every arm of every target instead
  (`docs/results.md` §0).

## Reading it

- A pass shows nothing broke on those 12 rows. It never shows that nothing improved: a construction change can
  rescue runs outside the sample, so re-measure the affected arms before re-quoting.
- One mismatching row is not a regression by itself. The search is bounded by wall-clock `--maxTime`, and the same
  jar, seed and config vary run to run. Repeat the row interleaved against the reference jar
  (`infra/em-results/reproducibility/interleave.sh`) before concluding.
- Never change an expectation to make the gate pass.
