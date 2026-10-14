# AF2 full re-measure — §4 numbers on jar AF2 (6b5606d4)

Decision B (2026-10-03): make AF2 the single thesis jar. AF2 broadened MR-A1 triple
construction (RestSecurityBuilder.kt 473+/93−), so CLAUDE.md §4 (jar R) does not carry
over. AF2 passed the 21-row regression gate on 2026-10-02; §4 still needs a full seeds
set because the construction changed (CLAUDE.md §6: "thay đổi lớn … chờ một lượt đầy đủ").

## Jar under test
`/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-AF2-6b5606d4.jar`
sha256 `6b5606d4…`, byte-identical to `core/target/evomaster.jar` and to the gate-validated jar.

## What is measured
The §4 table, re-run on AF2. One variable differs between any two arms (jar is held fixed,
flags copied byte-for-byte from the R harnesses `remeasure_t1.sh`, `restore-remeasure/remeasure.sh`,
`tier2b-restore-trials/tier2b_restore_trials.sh`). No expected outcome is encoded in the harness.

| Tier | Target | Arms (seeds) | Runs |
|---|---|---|---|
| 1 | reports-api :8080/:8081 | vuln·noreset, fixed·noreset, vuln·reset, fixed·reset (1–20) | 80 |
| 2 | vampi-seeded :5002/:5003 | ours-vuln·noreset, ours-fixed·noreset, ours-vuln·reset, ours-fixed·reset (1–20) | 80 |
| 2b | pyLoad :8090/:8091 | vuln·noreset, vuln·reset, fixed·noreset, fixed·reset (1–5) | 20 |

Tier-2b is the INFERRED arm: no `--statefulAuthzTransition`. A recall here is a legitimate
black-box figure on a third-party CVE. No number may ever be quoted from a declared-transition arm.

Flags per tier: reports/vampi `--maxTime 150s --ratePerMinute 120`; pyLoad `--maxTime 10m
--ratePerMinute 200 --endpointExclude "/api/kill,/api/restart"`. All: `--useExperimentalOracles true
--extraPhaseBudgetPercentage 0.6`. Reset arm adds `--statefulAuthzResetEndpoint`.

## Ground truth verified before launch (2026-10-03, over HTTP, AF2-independent)
- reports vuln 201/200/201, fixed 201/200/403.
- vampi  vuln 200/200/200, fixed 200/200/403.
- pyLoad vuln 200/200/200, fixed 200/200/403 (verify_ground_truth.sh).

## Early-stop rule (write before run, CLAUDE.md §2)
Read each row as it lands in progress.log.
- Vuln arms (reports vuln, vampi ours-vuln, pyLoad vuln): if the first 3 seeds of an arm all
  show assembled=0 (0 valid triples), stop the batch, record the stop as a deviation, and find
  the cause in the logs before any further run. 0 valid triples means the builder is not
  constructing on that target, not that the app is clean.
- Fixed arms: any det970=1 on a fixed target is a false positive — stop and investigate.
- Any run whose statuses=NA / faults=ERR (crash, dead target) is a failed row, not a silent 0:
  stop if two in a row on the same arm.

## Machine-sleep rule
Launched under `caffeinate -dims`, lid open. If `pmset -g log` shows any `Entering Sleep`
after the start timestamp while a row is running, every row it touched is void — stop, note it,
re-run the affected arm.

## Runtime
≈ reports 6.7 h + vampi 6.7 h + pyLoad 3.7 h ≈ 17 h wall-clock. runs.csv is appended per run,
so completed rows survive an interruption. Order reports → vampi → pyLoad so the core tiers finish first.

## After the batch
audit970_seeded.py over the emitted tests; integrity (no 970 without an assembled triple; log
counts == runs.csv); replay the 970 tests against a freshly reseeded SUT; snapshot to
~/thesis-backups/; then update docs/results.md and CLAUDE.md §4, naming jar AF2.
