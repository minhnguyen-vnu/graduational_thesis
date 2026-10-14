# P2c full re-measure — §4 numbers on jar P2c (b2ade764)

P2c = P2b (`93db089f`) + one line `RestSecurityBuilder.kt:858` (restore call: `restorer=victimAuth,
target=operator`, matching AF2). P2b replaced the hand-written lists with Naive Bayes (B1/B3),
values by structure (B2), identity-key response reading (B4), anonymous control (D1+C4), gate =
posterior > 0.5. The restore line in P2b had restorer/target swapped, which cost detections where
the victim can only be demoted after elevating the operator (reports seed 4/8: AF2 6/6 fired, P2b
0/6 — `p2b-confirm-20261012/`). The swap is fixed in P2c.

Triple construction changed vs AF2 (large change, CLAUDE §6: "thay đổi lớn … chờ một lượt đầy đủ"),
so §4 (jar AF2) does not carry over: a full seeds-1–20 run is needed. Pre-checks before this batch:
gate trimmed, FP 6/6 clean, self-test 970 PASS — `regression-check/NOTE-20261012-P2c.md`.

## Jar under test
`/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-P2c-b2ade764.jar`
sha256 `b2ade764…`, byte-identical to `core/target/evomaster.jar` at build time.

## What is measured
Table §4, re-run on P2c. Two arms differ in one variable (jar fixed, flags copied byte-for-byte
from `p2b_full_remeasure.sh`). The harness encodes no expected outcome.

| Tier | Target | Arms (seeds) | Runs |
|---|---|---|---|
| 1 | reports-api :8080/:8081 | vuln·noreset, fixed·noreset, vuln·reset, fixed·reset (1–20) | 80 |
| 2 | vampi-seeded :5002/:5003 | ours-vuln·noreset, ours-fixed·noreset, ours-vuln·reset, ours-fixed·reset (1–20) | 80 |
| 2b | pyLoad :8090/:8091 | vuln·noreset, vuln·reset, fixed·noreset, fixed·reset (1–5) | 20 |

Flags per tier: reports/vampi `--maxTime 150s --ratePerMinute 120`; pyLoad `--maxTime 10m
--ratePerMinute 200 --endpointExclude "/api/kill,/api/restart"`. All arms: `--useExperimentalOracles
true --extraPhaseBudgetPercentage 0.6`. Reset arms add `--statefulAuthzResetEndpoint`.

## Harness fix vs the AF2 harness
`collect` strips the `proven by an attempt with` log line before grepping `statuses` (P1/P2 added
it, duplicating the `Assembled` value). `assembled` and `det970` (from `report.json`) are unaffected.

## Early-stop rule (written before the run, CLAUDE §2)
Read each row as it lands.
- vuln arm (reports vuln, vampi ours-vuln, pyLoad vuln): first 3 seeds of an arm all assembled=0
  (0 triples) → stop, declare deviation, find the cause in the log before continuing.
- fixed arm: any det970=1 on a fixed target is a false positive → stop, investigate.
- Any row statuses=NA / faults=ERR (crash, target down) is a broken row, not a silent 0 → stop if
  two consecutive rows in one arm.

## Machine-sleep rule
Run under `caffeinate -dims`, lid open. `pmset -g log` showing any `Entering Sleep` after the start
mark while a row runs voids every row it touched — stop, record, re-run that arm.

## Runtime
≈ reports 6.7h + vampi 6.7h + pyLoad 3.7h ≈ 17h wall. runs.csv appends per run, so finished rows
survive interruption. Order reports → vampi → pyLoad so the two main tiers finish first.

## After the batch
`audit970_seeded.py` on emitted tests; integrity (no 970 without a triple; log counts == runs.csv);
replay 970 tests on a freshly reseeded SUT; snapshot to `~/thesis-backups/`; then update
`docs/results.md` and CLAUDE §4/§5, naming jar P2c.
