# P2d night chain, 2026-10-12 → 13

## Jar
`EvoMaster/evomaster-P2d-2e0dbd4d.jar` = P2c (`b2ade764`) + two changes in `RestSecurityBuilder.kt`:
- `:1248–1249` a current-role value the model scores low (`valueScore low > high`) is no longer used to
  exclude reduced values;
- `:1261` an operator snapshot the model scores low is no longer used as the restore value; the enum
  ranking by `high − low` is used instead.

Increment over P2c: `infra/evomaster-ext/wip/p2d-increment-over-p2c-20261012.diff`. Full tree patch:
`wip/p2d-lowkeep-elevate-20261012.patch` (rollback drill byte-identical). Model CSV unchanged, sha256
`9a7a7749…` (untracked file, not in the patch). Self-test: `selftest/p2d-reduce-elevate-20261012.sh`.

Why: P2c missed reports vuln-noreset seeds 10/13/16 where AF2 fires (interleave AF2 9/9, P2c 0/9,
`p2c-interleave-seeds-20261012/`). Debug logs AF2 vs P2c: `p2c-vs-af2-debug-20261012/`.
- A (seeds 10, 13): the current role of superadmin is read as VIEWER from an old response; P2c removes
  VIEWER from the reduced values. AF2 drops low values from the current role first (HEAD line 651).
- B (seeds 16, 13): restore sets operator bob to his observed role VIEWER, equal to the excluded value,
  so no restore. AF2 elevates the operator to a high enum value (ADMIN).

## Declared deviations
1. Unattended run (CLAUDE §6 says no unattended sessions), at the user's request 2026-10-12 22:2x.
2. Built and measured before the user reviewed the diff (user: "làm luôn"). The user reviews the diff
   in the morning; on rejection the chain is stopped and the tree rolled back to P2c.

## Steps and decision rules (written before any step ran)
All runs use the P2c harness flags; only the jar differs. Command lines go to `cmdlines.txt`.

| Step | Runs | Go on when | Otherwise |
|---|---|---|---|
| probe | reports vuln :8080 no-reset, seeds 10/13/16 × 3 | det970 sum ≥ 7 of 9 | stop |
| fp | reports fixed :8081 + vampi fixed :5003, seeds 1–3, no-reset | all 6 det970 = 0 | stop |
| gate | `regression-check/regression_check.sh`, 21 rows, `core/target/evomaster.jar` = P2d | exit 0 | stop; each MISMATCH row (max 3) re-run 3× interleaved AF2/P2d into `gate/interleave.csv`; no remeasure |
| remeasure | 180 runs, `remeasure/remeasure.sh` (copy of `p2c_full_remeasure.sh`, jar + folder changed, stop rules added) | runs to the end | stop on a rule below |

Remeasure stop rules, checked after every row:
- fixed arm row with det970 = 1 (false positive);
- two consecutive rows with det970 = ERR in one arm (broken rows);
- vuln arm: seeds 1, 2, 3 all assembled = 0;
- reports vuln no-reset arm finished with det970 sum ≤ 15 of 20 (below AF2's observed 16–19);
- any new `Entering Sleep` line in `pmset -g log` since the chain started.

After the remeasure: `audit970_seeded.py` on `remeasure/tests/*`; integrity counts. Replay and docs run
with the user.

## Outputs
`STATUS.log` (one line per milestone, STOP lines with the reason), `probe/`, `fp/`, `gate/`, `remeasure/`.
