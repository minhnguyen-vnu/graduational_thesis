---
name: regression-gate
description: Run and interpret the 21-row EvoMaster regression gate. Use before a new jar is used to re-quote any existing number, and when a gate row mismatches.
---

# Regression gate

- Script: `infra/em-results/regression-check/regression_check.sh`. It runs `core/target/evomaster.jar`
  (line 32): do not build while it runs.
- 21 recorded `(arm, seed, reset)` rows, re-run with their original flags and never `--statefulAuthzTransition`.
  12 are fixed-target rows.
- Expectations are read by `awk` from `tier{1,2}-trials/runs.csv` and `tier{1,2}-reset-trials/runs.csv`,
  never retyped. The 10 Tier-1 expectations equal the cleaned-app batch (`tier1-clean-remeasure/`).
- Before a run, move `observed.csv`, `progress.log` and `logs/` into `archive-<yyyymmdd>-<jar>/`.
- Output `observed.csv` (verdict MATCH per row) and `progress.log`; exit 1 on any mismatch. ~2 h.
- 2026-10-02, jar `AF2-6b5606d4` (broadened MR-A1 construction): 21/21 MATCH, 1 h 48
  (`regression-check/archive-20261002-AF2-6b5606d4/`). AF2 then re-measured §4 full seeds 1–20
  (`af2-full-remeasure-20261003/`), reproducing jar R per-seed; AF2 was the thesis jar 2026-10-04 to 10-14.
- 2026-10-13, jar `P2d-2e0dbd4d`: 21/21 MATCH (`p2d-night-20261012/gate/`). P2e (thesis jar from 2026-10-14)
  differs from P2d only where 2 of those rows reached (Tier-2 seed 3 no reset); both re-run on P2e match
  (`p2e-continue-20261013/gate-predict.out`). P2e has not run the gate as a job.

## Reading it

- A pass shows nothing broke on those 21 rows. It never shows that nothing improved: a construction change can
  rescue runs outside the sample, so re-measure the affected arms before re-quoting.
- One mismatching row is not a regression by itself. The search is bounded by wall-clock `--maxTime`, and the same
  jar, seed and config vary run to run. Repeat the row interleaved against the reference jar
  (`infra/em-results/reproducibility/interleave.sh`) before concluding.
- Never change an expectation to make the gate pass.
