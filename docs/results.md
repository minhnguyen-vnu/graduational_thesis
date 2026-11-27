# Results — current numbers

Single source for every number quoted in `CLAUDE.md`, progress reports and the thesis. Edit in place.
A number in another doc that disagrees with this file is superseded. Paths are under `infra/em-results/`.
Run incidents (sleep, parallel lanes, re-run seeds) stay in each run folder's `PROTOCOL.md`; they do not go into the
thesis.

## 0. Provenance

- Jar `evomaster-TR2-3beccb00.jar` = `9e779c15dd` (branch `stateful-authz-oracle`) plus
  `infra/evomaster-ext/wip/trim-restore-20261121-tree.patch`. The same code without the `THESIS` comments is commit
  `a44d91f478` (HEAD, pushed). That tree is the LF tree plus two changes:
  - C4 change (`wip/c4-source-status-20261121.md`): the re-login probe judges on the source's own status, and every
    call before the source must end in the same status group (2xx, 4xx, ...) as in the triple; otherwise
    INCONCLUSIVE and the triple is discarded as UNCONFIRMED.
  - Code cleanup (`wip/audit-970-54-20261121.md`, `wip/audit-970-e7-20261121.md`): the operator restore sends one
    value per role field (enum: the value the model scores most privileged, bool `true`, number `0`); a transition
    candidate without a victim field is dropped.
  The model is the no-duplication model (sha256 `dcc77b59ed0f…`, `infra/analysis/lexicon-rules/m2-nodup-20261112/`).
  Each harness refuses a jar whose sha16 is not `3beccb0086b6983a`.
- `EMConfig.kt` equals v6.1.1: no reset, no declared transition, no D1. Judgment is the C4 re-login probe only.
- The no-duplication model is M2 relearned with path parameters left out of `f:`: same corpus
  (`nop-hoi-dong/nhan-hoc-cuoi.csv`, 209 T of 10,381 write ops), same formula; only the `op` table differs
  (`docs/naive-bayes.md`).
- Runs: `tr2-final-20261126/`, 100 runs (`runs.csv`: reports-api, vampi-seeded, pyLoad; `runs-ak-*.csv`:
  artifact-keeper), builder debug log on every run (`infra/em-config/logback-builder-debug.xml`). Same harness flags as
  jars CS2 and LF apart from jar, labels and that log config. Source folder of each file: its `PROTOCOL.md`.
  Counts: `tr2_counts.py` (`tr2-counts.out`). Per-seed triples, discards, restores and the paired comparisons:
  `tr2_details.py` (`tr2-details.out`). Triples are counted from `Assembled` log lines.
- Reseed before every run, `--useExperimentalOracles true`, `-Xmx2g`:

| Target | Seeds | `--maxTime` | `--ratePerMinute` | `--extraPhaseBudgetPercentage` | Other |
|---|---|---|---|---|---|
| reports-api | 1–20 per arm | 150s | 120 | 0.6 | |
| vampi-seeded | 1–20 per arm | 150s | 120 | 0.6 | |
| pyLoad | 1–5 per arm | 10m | 200 | 0.6 | `--endpointExclude "/api/kill,/api/restart"` |
| artifact-keeper | 1–5 per arm | 1200s | 600 | 0.25 | spec without `DELETE /users/{id}`; traffic proxy :8212 |

- TR2 against LF, the previous thesis jar: equal in 970 on 90 of 98 rows (§6). LF is the fallback jar
  (`infra/evomaster-ext/jars.md`).
- Each run records the triple it performed as `[source/transition/follow-up]` statuses, so construction (a triple
  was performed) and judgment (970 raised) are counted separately.

## 1. Detection and false positives

| Target | Bug | Arm | Runs with a performed triple | 970 raised |
|---|---|---|---|---|
| reports-api | seeded | vulnerable | 12/20 | **12/20** [36.1, 80.9] |
| reports-api | seeded | fixed | 20/20 | 0/20 |
| vampi-seeded | seeded | vulnerable | 7/20 | **7/20** [15.4, 59.2] |
| vampi-seeded | seeded | fixed | 7/20 | 0/20 |
| pyLoad | CVE-2026-41133 | vulnerable | 5/5 | **5/5** [47.8, 100] |
| pyLoad | CVE-2026-41133 | fixed (ours) | 5/5 | 0/5 |
| artifact-keeper | vendor bug #1821 | vulnerable `e56d3aa7e2` | 5/5 | **5/5** [47.8, 100] |
| artifact-keeper | vendor bug #1821 | vendor patch `e64cc5c608` | 0/5 | 0/5 |

Intervals are Clopper–Pearson 95% (exact binomial). False-positive rate over the 32 fixed runs with a triple: 0/32,
Clopper–Pearson [0, 10.9]%.

- Vulnerable vs fixed, Fisher exact one-sided: reports-api p < 0.001, vampi-seeded p = 0.004, pyLoad p = 0.004,
  artifact-keeper p = 0.004.
- **False positives: 0 in 50 fixed-target runs**, over **50 triples performed on patched code** in 32 runs
  (reports-api 38, vampi-seeded 7, pyLoad 5, artifact-keeper 0).
- Triples per run: reports-api vulnerable 2 in seeds 2 and 11, 1 in the other 10 runs with a triple; reports-api fixed
  2 (seeds 16 and 17: 1); artifact-keeper vulnerable 2; vampi-seeded and pyLoad 1. Performed triples read
  `200/200/200` or `201/200/201` on the vulnerable side and `200/200/403` or `201/200/403` on the fixed side; `201` is
  `POST /reports`.
- **reports-api, two sources.** `PUT /reports/{id}` with victim `alice` or `superadmin` and the other admin as
  operator; `POST /reports` with operator `bob`. `bob` is VIEWER in the seed data (`infra/reports-api/README.md`); an
  operator restore by the victim raises him to ADMIN before his transition is retried. Vulnerable: 12 triples on
  `POST /reports` (one per run with a triple) and 2 on `PUT /reports/{id}` (seeds 2 and 11). Fixed: 19 and 19.
- **C4 discards: 24, all reports-api vulnerable**, all on source `PUT /reports/{id}`, each with codes `200/200/200`
  and the probe reason "a call before the source of the replayed slice changed status group". The 8 vulnerable runs
  without a triple (seeds 1, 3, 4, 7, 13, 14, 16, 19) have only discarded attempts of this kind besides VOID ones.
  C4 runs only when the follow-up is 2xx, so it never runs on a triple on patched code (§2).
- **artifact-keeper candidate skipped.** `PUT /api/v1/admin/sso/oidc/{id}` returned 404 for each victim, and the
  builder drops that (transition, victim) pair (`that victim is skipped`, 2 per run, both arms). No arm without C4
  was run: never write that the vendor patch would otherwise have raised 970.
- **artifact-keeper vulnerable.** Every run performs two triples with transition `PATCH /api/v1/users/{id}` and body
  `{"is_admin": false}`, both `200/200/200`: source `POST /api/v1/admin/analytics/snapshot` (victim `victim`,
  operator `operator`), and source `POST /api/v1/admin/backups` (seed 3: `POST /api/v1/admin/cleanup`) with victim
  `operator` and operator `viewer`, after `operator` raised `viewer` with `is_admin: true`.
- **artifact-keeper vendor patch performs no triple.** In all 5 seeds the demotion succeeds and the old token gets
  401 (`codes 200/200/401`, twice per run, logged `REVOKED`); 401 is INCONCLUSIVE, so the attempt is VOID. The vendor
  fix revokes the token (401) where the oracle reads a denial only from 403. The arm shows no false alarm and counts
  no TN.
- vampi-seeded black-box recall is **7/20** on TR2, CS2 and LF; 6/20 on ND and on the jar-`R` audit re-run
  (`audit-batch/runs.csv`); 7/20 on M2, P2f, P2e and AF2. The vampi-seeded row that moves is seed 15: the search
  budget is wall clock, so two runs of one jar can diverge before the security phase. A TR2 run of seed 15 without a
  triple: `tr2-wave1-20261121/CORRECTION-vampi-seed15.md` (the mechanism in that folder's `tr2-analysis.out` is wrong).
- Operator restores accepted (refused): reports-api 21 (0) vulnerable, 23 (0) fixed; vampi-seeded 5 (9), 5 (9);
  pyLoad 5 (0), 5 (0); artifact-keeper 1 (0) per run on both commits.
- Baseline arms (Şahin oracles, 970 disabled) are not false-positive opportunities and are not counted.

### 1a. Four cells per target

Same runs, `tr2-counts.out`. The vulnerable target gives TP/FN, the fixed target FP/TN. TN counts only fixed
runs with a performed triple (§2). Every follow-up of a triple on patched code got 403, so counting only 403
follow-ups gives the same TN.

| Target | TP | FN, triple, no 970 | FN, no triple | FP | TN | Fixed, no triple | Runs vulnerable/fixed |
|---|---|---|---|---|---|---|---|
| reports-api | 12 | 0 | 8 | 0 | 20 | 0 | 20/20 |
| vampi-seeded | 7 | 0 | 13 | 0 | 7 | 13 | 20/20 |
| pyLoad | 5 | 0 | 0 | 0 | 5 | 0 | 5/5 |
| artifact-keeper | 5 | 0 | 0 | 0 | 0 | 5 | 5/5 |
| Total | 29 | 0 | 21 | 0 | 32 | 18 | 50/50 |

Every FN is a run with no performed triple; no performed triple on a vulnerable target missed 970. Per run,
precision is 1.0 on every row; recall is TP over the vulnerable runs.

FN by cause (`tr2-details.out`, `vampi-missed-void.out`):

| Target | Cause | Runs | Detail |
|---|---|---|---|
| reports-api | Every non-VOID attempt discarded by C4 | 8 | seeds 1, 3, 4, 7, 13, 14, 16, 19; 15 discards |
| vampi-seeded | Attempts made, every one VOID | 7 | seeds 3, 7, 8, 9, 12, 16, 19; 20 VOID: 9 source 401, 11 transition 401 |
| vampi-seeded | No attempt | 6 | seeds 2, 4, 6, 13, 14, 18; only guarded source `PUT /books/v1/{book_title}/secret`, `victims []` |

`victims []` is a debug line of the builder: no test kept after the search calls that source with a logged-in account
and gets 2xx (`victimSlicesOn`, `RestSecurityBuilder.kt:760` at HEAD). EvoMaster's default log level prints no reason.

## 2. How to read the numbers

- The 0-FP count is the independent accuracy measurement. Judgment is restricted to the triples our builder
  constructed (commit `9021b67cf5` onward), so the 0 false positives are over the 50 builder triples on patched code.
- "Detection given a valid triple" (runs 12/12, 7/7, 5/5, 5/5) is near-definitional: validity keys on the follow-up
  status that judgment also uses. It is never quoted as accuracy. It shows only that the handler, re-deriving
  the triple on its own, never disagreed with the builder.
- C4 runs only when the follow-up is 2xx. On patched code every follow-up was 403, so C4 never ran there and the
  0 FP do not depend on it. A stricter C4 can only lower detection: on reports-api it cost 8 runs (§6).
- A VOID triple is evidence in neither direction. Counting one as a true negative inflates specificity.
- Report all four cells per target. A run without a performed triple is not a TN; the artifact-keeper vendor patch
  is such a case on every seed.

## 3. Hand-audit and replay

Replay not re-run on TR2. Each line names its jar.

| | reports-api | vampi-seeded | pyLoad | artifact-keeper |
|---|---|---|---|---|
| 970 tests passing all four structural checks, jar TR2 | 14/14 | 7/7 | not parseable | 10/10 |
| Same check, earlier jars | 38/38 (LF); 19/19 (ND); 39/39 (AF2, P2f) | 7/7 (LF); 6/6 (ND); 20/20 (AF2, P2f) | not parseable | 10/10 (LF); 4/4 (ND); 5/5 (P2f) |
| Replay of 970 tests from clean state, jar AF2 | 38/39 | 17/20 | 28/38 | not run |
| Source | TR2: `tr2-final-20261126/audit970.out`; LF: `lf-wave1-20261118/audit970.out`; ND: `nd-wave1-20261113/audit970.out`; earlier: `af2-full-remeasure-20261003/audit970.out`, `replay.csv`; `p2f-full-20261015/audit970.out` | same | same | TR2: `tr2-final-20261126/audit970.out`; LF: `lf-wave2-20261118/audit970.out`; ND: `nd-wave2-20261113/audit970.out`; earlier: `artifactkeeper-machine-20261014/audit970-fixjar-vuln.out` |

The AF2 and P2f sets include the reset arms of those jars.

- `audit970_seeded.py` reads the emitted tests, never the log: same credential in source and follow-up,
  no re-login between them, transition by a different credential, 2xx/2xx/2xx. It flipped the right check on five
  deliberately broken copies; redo that validation whenever the parser changes.
- **pyLoad is not auditable by this parser.** It authenticates with a session cookie, so the
  `headers["Authorization"]` regex reads no credential. pyLoad is validated over HTTP by `verify_ground_truth.sh`
  (`200/200/200` vulnerable, `200/200/403` fixed) and by replay.
- Replay misses fail on a dropped search-time state change or a brittle generated assertion, never on the
  authorization claim:
  - reports-api seed 16: the minimized test omits the restore that gave victim `bob` write access, so the follow-up
    is 403.
  - vampi-seeded seeds 5 and 11: fail at the transition (`res_1` 403), the operator promotion the minimizer dropped.
    Seed 15: reseed returns victim `name1` to `user`, so its source becomes 403.
  - pyLoad (10): all fail on a generated body assertion (e.g. `res_0.json()["pause"] == True`), never on a status
    code; the `200/200/200` triple holds.
- **Quote "replayable 55/59"** (reports-api 38/39 + vampi-seeded 17/20, jar AF2), never "reproducible".

## 4. pyLoad — CVE-2026-41133

- Real third-party bug: GHSA-66hx-chf7-3332, CWE-613, CVSS 8.8, `pyload-ng <= 0.5.0b3.dev97`.
- Upstream fix from dev98 (commit `e95804fb`, 2026-04-13): clears a user's sessions on `/json/update_users`, password
  change and deletion. Read from the PyPI wheels: in dev98–dev101 the core-API `set_user_permission`, reached by
  `POST /api/set_user_permission` (the transition the tool uses), does not clear sessions; `develop` adds
  `_invalidate_user_sessions`. The tool has not been run on dev98 or later.
  Setup and the five declared deviations: `docs/tier2b-pyload-target.md` §3.
- Transition inferred, rank 1 of 3 viable ops under the no-duplication model
  (`m2-nodup-20261112/compare_targets_nodup.out`): `POST /api/set_user_permission`. Every TR2 triple: source
  `POST /json/status`, victim `pyload`, operator `alice`, `200/200/200` on the vulnerable variant, `200/200/403` on
  the fixed one.
- Each run performs its triple after one operator restore (`pyload` raises `alice` with values `0,0`),
  identically on both variants.
- **VOID attempts:** 20, 10 per variant, each `200/401/200` on `/json/status`: the transition answered 401
  (INCONCLUSIVE), so the triple is VOID and raises nothing.
- **Transition values.** Each 970 test sends `user=pyload&permission=1&role=1` (seeds 1–5,
  `tr2-final-20261126/tests/t2b-vuln-seed*/`): the first value of the hand-written order `1, 0, 2` for both numeric
  fields. pyLoad treats role `0` as admin and any other value as not, so the demotion lands; C4 confirmed it.
- Restore ceiling: at least one privileged credential must survive. With every admin demoted, a fresh login
  cannot promote anyone (401).

## 5. artifact-keeper — vendor bug #1821

- Public app (`artifact-keeper/artifact-keeper`, Rust, 1,097 stars on 2026-10-01). On the vulnerable commit
  `e56d3aa7e2`, `is_admin` is written into the JWT at login and read from the claim without a database check
  (`middleware/auth.rs:153`), so a demoted admin keeps admin rights until the token expires (30 min). The vendor
  fix `e64cc5c608` adds `privileges_changed_at` to the credential-change watermark: tokens minted before a demotion
  are rejected with 401. Both commits checked by hand over HTTP (`artifactkeeper-20261001/`). Setup:
  `docs/artifact-keeper-target.md`.
- Ours: the compose override and `protoc` in the dev image (build only), and the spec minus `DELETE /users/{id}`, so
  the fuzzer cannot delete the test accounts. Bug, fix, app code and the rest of the spec are the vendor's.
- Transition inferred: `PATCH /api/v1/users/{id}` with `{"is_admin": false}`, rank 3 of 4 viable ops under the
  no-duplication model offline (`m2-nodup-20261112/compare_targets_nodup.out`; rank 4 of 5 under M2); the offline count
  does not check for a victim field. Jar TR2 also drops `POST /api/v1/admin/sso/oidc` (no victim field), so the builder
  tries 3 candidates and `PATCH` is candidate 2 of 3 in all 10 runs (`transition chosen` in
  `tr2-final-20261126/logs/ak-*.log`). Triples of jar TR2: §1.
- No string of the app is in the builder, the oracle or the model (jar TR2), and its spec is excluded from
  the training corpus (`infra/analysis/corpus/sample_specs_field.py:8–9`).
- Development target: three general builder fixes were found by running it. Vulnerable-commit detection by jar:
  ER 0/1, AF 1/4 (boolean admin flag recognized), AF2 5/5 (nullable `is_admin` sent present), P2e 0/2 (`null` sent
  again), P2f 5/5 (value set on the leaf gene), M2 5/5, ND 4/5, LF 5/5, CS2 3/3 (seeds 1–3 only), TR2 5/5
  (`artifactkeeper-machine-20261001/`, `artifactkeeper-machine-20261014/`, `m2-wave2-20261108/`, `nd-wave2-20261113/`,
  `lf-wave2-20261118/`, `cs2-wave2-20261121/`, `tr2-final-20261126/`). Its numbers make no claim about recall on unseen apps.

## 6. Changing the model or the builder

Rows are paired by target, arm and seed; 970 raised or not is compared on each pair (`tr2-details.out`).

- CS2 to TR2 (code cleanup): 93 rows paired, 0 differ. McNemar exact, 0 vs 0 discordant: p = 1.0. The CS2 artifact-keeper runs stopped after vulnerable seeds 1–3, so seeds 4–5 and
  the vendor-patch arm have no CS2 pair (`cs2-wave2-20261121/PROTOCOL.md`).
- LF to CS2 (C4 change): 93 rows paired, 8 lost, none gained: reports-api vulnerable seeds 1, 3, 4, 7, 13, 14, 16, 19,
  each a run whose attempts C4 discarded. McNemar exact, 8 vs 0: p = 0.008. 0 false positives on both jars.
- LF to TR2: 90 of 98 rows equal; the 8 reports-api rows lost, none gained. McNemar exact, 8 vs 0: p = 0.008.
- ND to LF (logic fix, same model): 95 of 98 rows equal in 970. Three rows gained, none lost: reports-api vulnerable
  seed 17, vampi-seeded vulnerable seed 15, artifact-keeper vulnerable seed 3, each a run with no performed triple on
  ND. McNemar exact, 3 vs 0 discordant: p = 0.25. 0 false positives on both jars. Paths: §0.
- M2 to ND: 96 of 98 rows equal in 970. Two rows lost, none gained: vampi-seeded vulnerable seed 15 and
  artifact-keeper vulnerable seed 3, both runs with no performed triple on ND. McNemar exact, 2 vs 0 discordant:
  p = 0.5. 0 false positives on both jars. The M2 rows are equal on all 98 rows to the shorten-logic jar SLM2
  (`slm2-wave1-20261112/`, `slm2-wave2-20261112/`), against which ND was run.
- Lexicon (AF2) to M1 (P2e, P2f): every 970 cell of the three benchmark targets equal seed for seed
  (`p2f-full-20261015/RESULTS.md`). M1 to M2: equal on all 90 benchmark rows; artifact-keeper 5/5 on AF2, P2f and M2.
- Hand-written words to the lexicon (jar `L`): 0 of 30 paired rows changed (`lexicon-chain-20260921/`).

## 7. Limitations

- **The search destroys the triple's preconditions** in two ways. Demotion: the source returns 403, and black-box
  aborts a test at its first failing create call. Deletion: VAmPI's generated tests call
  `DELETE /users/v1/{username}` 75× on `name1`, 17× `name2`, 10× `admin`, 6× `superadmin`. The operator restore
  reverses a demotion, never a deletion. Both cost recall, never precision.
- **Transition inference** ranks write ops by Naive Bayes over path, field and verb tokens. The no-duplication model on
  the relabelled test half (237 specs, 8,674 write ops, 153 T): 101 of 153 T ops score above zero (66.0%,
  Clopper–Pearson 57.9–73.5%); 523 of 624 positive-scored ops are labelled N, so a positive score selects a candidate
  and proves nothing. Before the review of 44 disputed test ops: 100/149 (67.1%). M2 on the same half: 117/153, 763 of
  880 (`infra/analysis/lexicon-rules/m2-nodup-20261112/ket-qua.txt`, `truoc-soat-lai.txt`). M1, vendor-wise
  cross-validation: the true op ranks first in 16–18 and within the first 4 in 21–25 of 47 test specs; those specs
  were looked at many times, so the figures are exploratory (`infra/evomaster-ext/wip/p2-design-20261012.md` §1).
  vampi-seeded's `/role` path was named by us.
- **Reduced-role value** follows the field type: an enum value the model scores low, a flipped bool, `1, 0, 2` for
  numbers (hand-written), or the model's `lowstr` strings (`infra/evomaster-ext/README.md` §3 step 1).
- **C4 on reports-api.** Jar TR2: the probe replays the victim's slice with a fresh login and judges on the source's
  own status; every call before the source must end in the same status group as in the triple, otherwise the result
  is INCONCLUSIVE and the triple is discarded. All 24 discards are on source `PUT /reports/{id}` for that reason
  (§1). The log does not name the call that changed group. On jar TR2 the 14 confirmed triples got their probe 403
  on the source itself.
- **C4 on jar LF**, the fallback jar: the probe took the last status of a call the victim sent (earlier jars: the
  last status of the slice). Of the 38 reports-api 970 tests of jar LF, 19 have source `POST /reports`; of the 19 with
  source `PUT /reports/{id}`, 17 have the victim create a report (`POST /reports`) before the source
  (`lf-wave1-20261118/tests/t1-vuln-seed*/`; jar AF2: 34 of 39). Black-box stops at a non-2xx create, so on jar LF the
  probe's 403 came from `POST /reports`, read from code. Do not write "C4 re-attempts the guard" for jar LF.
- **C4 checks status groups only.** A call before the source that ends in the same group as in the triple but
  leaves different state is not detected (`infra/evomaster-ext/wip/c4-source-status-20261121.md`).
- **Operator restore values are fixed by field type.** The restore sends one value per role field: the enum value
  the model scores most privileged, `true` for a bool, `0` for a number (hand-written). An app where a higher number
  means more privilege cannot have an operator raised. A string field, or an enum with no value the model scores as
  privileged, gets no value; with no value for any role field there is no restore (`restore unavailable`).
- **401 differs by target.** pyLoad `/api/*` answers a non-admin session with 401, `/json/*` with 403; VAmPI's 401
  means no valid token; the artifact-keeper vendor patch answers a revoked token with 401. 401 stays INCONCLUSIVE, and
  the denial code is not configurable.
- **The guard is load-bearing.** Without it, 970 fired on VAmPI tests with no transition
  (`GET /me`, then `GET /_debug` by another user, then `GET /me`). Cost of the guard: zero true positives.
- **Security-phase budget** was hit in 424 of 428 runs mined on 2026-09-13 (90 s seeded, 360 s pyLoad); the
  builder's last line precedes the budget end in every run where timestamps bound it (script not kept).
- **Scope.** One bug class (A1). Both seeded targets plant a stale role claim in a JWT; artifact-keeper has the same
  mechanism in vendor code; pyLoad caches the role in a session.

## 8. Baseline (Şahin et al., arXiv:2604.00702) on A1

- **Cannot judge it.** F204–F208 compare users at one instant; none models "permission removed, so now denied".
- **Cannot construct it.** vampi-seeded: 0/20 baseline-vulnerable runs contain write, downgrade, re-write with the same
  auth variable (`tier2-trials/baseline_blindness.py`). F209 on 17/20 runs shows the baseline was configured.
  reports-api (pre-cleanup app): 5 tests touch `PUT /users/{u}/role`, 32 mutate `/reports`, 0 do both.
- EvoMaster logs each user in once per test, so the baseline always holds a token current at that test.
- Upstream v6.2.0, seed 1, 180 s, vulnerable reports-api and vampi-seeded: 17 and 23 faults (109, 202, 305; 100, 109,
  200, 201), none from a demotion followed by a pre-demotion token (`upstream-dynamic-check-20261004/RESULTS.md`).
- Upstream master `ab983ba338`, seeds 1–20, vulnerable reports-api: 0/20 report an A1-class fault; 4 stale-token
  calls return 200 in traffic, none after a 2xx source with the same token, none flagged, none kept in the emitted
  tests (`upstream-master-t1-20261018/RESULTS.md`).

## 9. Wording for the write-up

| Do not write | Write |
|---|---|
| reproducible failing test | replayable from clean state in 55/59 (jar AF2) |
| vampi-seeded shows transition inference generalizes | vampi-seeded's transition name is ours |
| a benchmark the community lacks | two seeded apps, one CVE and one vendor-fixed bug |
| vampi-seeded recall 35% | 7/20 (jar TR2) |
| the logic fix raised detection | 3 rows gained, 0 lost, McNemar p = 0.25 (jars ND, LF) |
| the code cleanup changed no result | 0 of 93 paired rows differ, McNemar p = 1.0 (jars CS2, TR2) |
| the C4 change removed false positives on reports-api | 24 attempts discarded on the vulnerable target, 8 runs lost, McNemar p = 0.008 (jars LF, CS2) |
| the vendor patch gave 5 true negatives | the vendor patch gave no false alarm in 5 runs and no performed triple |
| pyLoad and artifact-keeper used while the builder was developed | omit |
| "người gán", "tác giả", who reviewed the labels | impersonal: "được soát tay", "viết riêng cho khóa luận" |
