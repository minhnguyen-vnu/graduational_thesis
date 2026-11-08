# Results — current numbers

Single source for every number quoted in `CLAUDE.md`, progress reports and the thesis. Edit in place.
A number in another doc that disagrees with this file is superseded. Paths are under `infra/em-results/`.
Run incidents (sleep, parallel lanes, re-run seeds) stay in each run folder's `PROTOCOL.md`; they do not go into the
thesis.

## 0. Provenance

- Jar `evomaster-M2-917c57dd.jar` = HEAD `9c4be5b1dc` (branch `stateful-authz-oracle`, pushed) with
  `stateful-authz-model.csv` replaced by model M2 (sha256 `b2deef150bf8…`,
  `infra/analysis/lexicon-rules/m2-model-20261107/`). The source tree still holds M1. Each harness refuses a jar whose
  sha16 is not `917c57ddafcc3d93`.
- The jar has no reset, no declared transition and no D1: `EMConfig.kt` equals v6.1.1, and judgment is the C4 re-login
  probe only.
- M2 is the Naive Bayes model rebuilt from the relabelled corpus `nop-hoi-dong/nhan-hoc-cuoi.csv` (209 T of 10,381
  write ops), with the formula and code of M1 (`docs/naive-bayes.md`).
- Runs, 2026-11-08: `m2-wave1-20261108/runs.csv` (reports-api, vampi-seeded, pyLoad; 90 runs) and
  `m2-wave2-20261108/` (artifact-keeper 8 runs). Counts: `m2-wave1-20261108/m2_counts.py`, output
  `m2-counts-cp.out` (`m2-counts-final.out` is the same count with Wilson intervals, superseded). Triples are
  counted from `Assembled` log lines; the `assembled` column of the artifact-keeper CSVs counts each triple twice (it
  also matches the "proven by an attempt" line).
- Reseed before every run, `--useExperimentalOracles true`, `-Xmx2g`:

| Target | Seeds | `--maxTime` | `--ratePerMinute` | `--extraPhaseBudgetPercentage` | Other |
|---|---|---|---|---|---|
| reports-api | 1–20 per arm | 150s | 120 | 0.6 | |
| vampi-seeded | 1–20 per arm | 150s | 120 | 0.6 | |
| pyLoad | 1–5 per arm | 10m | 200 | 0.6 | `--endpointExclude "/api/kill,/api/restart"` |
| artifact-keeper | 1–5 vulnerable, 1–3 vendor patch | 1200s | 600 | 0.25 | spec without `DELETE /users/{id}`; traffic proxy :8212 |

- M2 equals P2f, the previous thesis jar, in 970 on all 90 rows of the three benchmark targets, and in triples and
  statuses on 89 (vampi-seeded fixed seed 15: P2f performed one `200/200/403` triple, M2 none). P2f is the fallback
  jar (`infra/evomaster-ext/jars.md`).
- Each run records the triple it performed as `[source/transition/follow-up]` statuses, so construction (a triple
  was performed) and judgment (970 raised) are counted separately.

## 1. Detection and false positives

| Target | Bug | Arm | Runs with a performed triple | 970 raised |
|---|---|---|---|---|
| reports-api | seeded | vulnerable | 19/20 | **19/20** [75.1, 99.9] |
| reports-api | seeded | fixed | 19/20 | 0/20 |
| vampi-seeded | seeded | vulnerable | 7/20 | **7/20** [15.4, 59.2] |
| vampi-seeded | seeded | fixed | 6/20 | 0/20 |
| pyLoad | CVE-2026-41133 | vulnerable | 5/5 | **5/5** [47.8, 100] |
| pyLoad | CVE-2026-41133 | fixed (ours) | 5/5 | 0/5 |
| artifact-keeper | vendor bug #1821 | vulnerable `e56d3aa7e2` | 5/5 | **5/5** [47.8, 100] |
| artifact-keeper | vendor bug #1821 | vendor patch `e64cc5c608` | 0/3 | 0/3 |

Intervals are Clopper–Pearson 95% (exact binomial). False-positive rate over the 30 fixed runs with a triple: 0/30,
Clopper–Pearson [0, 11.6]%. One performed triple per run with a triple.

- Vulnerable vs fixed, Fisher exact one-sided: reports-api p < 0.001, vampi-seeded p = 0.004, pyLoad p = 0.004,
  artifact-keeper p = 0.018.
- **False positives: 0 in 48 fixed-target runs**, over **30 triples performed on patched code** (reports-api 19,
  vampi-seeded 6, pyLoad 5, artifact-keeper 0).
- Every performed triple reads `200/200/200` on the vulnerable side and `200/200/403` on the fixed side.
- **artifact-keeper vendor patch performs no triple.** In seeds 1 and 2 the demotion succeeds and the old token gets
  401 (`codes 200/200/401`); 401 is INCONCLUSIVE, so the attempt is VOID. Seed 3 never gets a 2xx demotion (`200/400/200`,
  `200/403/200`). The vendor fix revokes the token (401) where the oracle reads a denial only from 403. The arm shows
  no false alarm and counts no TN.
- vampi-seeded black-box recall is quoted as **30–35%**: 7/20 on M2, P2f, P2e and AF2; the jar-`R` audit re-run gave 6/20
  (`audit-batch/runs.csv`), differing on seed 15, whose victim `name1` had been deleted during the search.
- Operator restores accepted (refused): reports-api 5 (0) vulnerable, 6 (0) fixed; vampi-seeded 5 (8), 5 (8);
  pyLoad 5 (0), 5 (0); artifact-keeper one per run, except vendor-patch seed 3 (none).
- Baseline arms (Şahin oracles, 970 disabled) are not false-positive opportunities and are not counted.

### 1a. Four cells per target

Same runs, `m2-counts-cp.out`. The vulnerable target gives TP/FN, the fixed target FP/TN. TN counts only fixed
runs with a performed triple (§2).

| Target | TP | FN, triple, no 970 | FN, no triple | FP | TN | Fixed, no triple | Runs vulnerable/fixed |
|---|---|---|---|---|---|---|---|
| reports-api | 19 | 0 | 1 | 0 | 19 | 1 | 20/20 |
| vampi-seeded | 7 | 0 | 13 | 0 | 6 | 14 | 20/20 |
| pyLoad | 5 | 0 | 0 | 0 | 5 | 0 | 5/5 |
| artifact-keeper | 5 | 0 | 0 | 0 | 0 | 3 | 5/3 |
| Total | 36 | 0 | 14 | 0 | 30 | 18 | 50/48 |

Every FN is a run with no performed triple; no performed triple on a vulnerable target missed 970. Per run,
precision is 1.0 on every row; recall is TP over the vulnerable runs.

## 2. How to read the numbers

- The 0-FP count is the independent accuracy measurement. Judgment is restricted to the triples our builder
  constructed (commit `bf26b65322` onward), so the 0 false positives are over the 30 builder triples on patched code.
- "Detection given a valid triple" (19/19, 7/7, 5/5, 5/5) is near-definitional: validity keys on the follow-up
  status that judgment also uses. It is never quoted as accuracy. It shows only that the handler, re-deriving
  the triple on its own, never disagreed with the builder.
- A VOID triple is evidence in neither direction. Counting one as a true negative inflates specificity.
- Report all four cells per target. A run without a performed triple is not a TN; the artifact-keeper vendor patch
  is such a case on every seed.

## 3. Hand-audit and replay

Not re-run on M2. Each line names its jar.

| | reports-api | vampi-seeded | pyLoad | artifact-keeper |
|---|---|---|---|---|
| 970 tests passing all four structural checks | 39/39 (AF2, P2f) | 20/20 (AF2, P2f) | not parseable | 5/5 (P2f) |
| Replay of 970 tests from clean state, jar AF2 | 38/39 | 17/20 | 28/38 | not run |
| Source | `af2-full-remeasure-20261003/audit970.out`, `replay.csv`; `p2f-full-20261015/audit970.out` | same | same | `artifactkeeper-machine-20261014/audit970-fixjar-vuln.out` |

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

- Real third-party bug: GHSA-66hx-chf7-3332, CWE-613, CVSS 8.8, `pyload-ng <= 0.5.0b3.dev97`, no upstream fix.
  Setup and the five declared deviations: `docs/tier2b-pyload-target.md` §3.
- Transition inferred, rank 1 of 3 viable ops under M2 (`m2-model-20261107/compare_targets.out`):
  `POST /api/set_user_permission`. Every M2 triple: source `POST /json/status`, victim `pyload`, operator `alice`,
  `200/200/200` on the vulnerable variant, `200/200/403` on the fixed one.
- Each run performs its triple after one operator restore (`pyload` raises `alice`), identically on both variants.
- **VOID attempts:** 20, 10 per variant, each `200/401/200` on `/json/status`: the transition answered 401
  (INCONCLUSIVE), so the triple is VOID and raises nothing.
- **Transition values.** Each 970 test sends `user=pyload&permission=1` with a `role` value left by the search
  (`role=373`, `282`, `883`, `488`, `946`, seeds 1–5), never `0`. pyLoad treats role `0` as admin and any other value
  as not, so the demotion lands. The tool did not infer the role value; C4 confirmed the privilege was gone.
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
- Transition inferred: `PATCH /api/v1/users/{id}` with `{"is_admin": false}`, rank 4 of 5 viable ops under M2
  (`compare_targets.out`); the builder reaches it by trying every viable op. Every M2 triple: source
  `POST /api/v1/admin/analytics/snapshot`, victim `victim`, operator `operator`, `200/200/200`.
- No string of the app is in the builder, the oracle or the model (HEAD `9c4be5b1dc`), and its spec is excluded from
  the training corpus (`infra/analysis/corpus/sample_specs_field.py:8–9`).
- Development target: three general builder fixes were found by running it. Vulnerable-commit detection by jar:
  ER 0/1, AF 1/4 (boolean admin flag recognized), AF2 5/5 (nullable `is_admin` sent present), P2e 0/2 (`null` sent
  again), P2f 5/5 (value set on the leaf gene), M2 5/5 (`artifactkeeper-machine-20261001/`,
  `artifactkeeper-machine-20261014/`, `m2-wave2-20261108/`). Its numbers make no claim about recall on unseen apps.

## 6. Changing the model lost no detection

- Lexicon (AF2) to M1 (P2e, P2f): every 970 cell of the three benchmark targets equal seed for seed
  (`p2f-full-20261015/RESULTS.md`). M1 to M2: §0. artifact-keeper 5/5 on AF2, P2f and M2.
- Hand-written words to the lexicon (jar `L`): 0 of 30 paired rows changed (`lexicon-chain-20260921/`).

## 7. Limitations

- **The search destroys the triple's preconditions** in two ways. Demotion: the source returns 403, and black-box
  aborts a test at its first failing create call. Deletion: VAmPI's generated tests call
  `DELETE /users/v1/{username}` 75× on `name1`, 17× `name2`, 10× `admin`, 6× `superadmin`. The operator restore
  reverses a demotion, never a deletion. Both cost recall, never precision.
- **Transition inference** ranks write ops by Naive Bayes over path, field and verb tokens. M2 on the relabelled test
  half (237 specs, 8,674 write ops, 153 T): 117 of 153 T ops score above zero (76.5%, Clopper–Pearson 68.9–82.9%);
  763 of 880 positive-scored ops are labelled N, so a positive score selects a candidate and proves nothing
  (`infra/analysis/lexicon-rules/relabel-20261101/PROTOCOL.md`, `cham-thi/ket-qua-sau-soat-lai.txt`). M1, vendor-wise
  cross-validation: the true op ranks first in 16–18 and within the first 4 in 21–25 of 47 test specs; those specs
  were looked at many times, so the figures are exploratory (`infra/evomaster-ext/wip/p2-design-20261012.md` §1).
  vampi-seeded's `/role` path was named by us.
- **Reduced-role value** follows the field type: an enum value the model scores low, a flipped bool, `1, 0, 2` for
  numbers (hand-written), or the model's `lowstr` strings (`infra/evomaster-ext/README.md` §3 step 1).
- **C4 on reports-api.** The probe replays the victim's slice and takes the last executed status. 34 of 39 reports-api
  970 tests (jar AF2) create a report (`POST /reports`) before the guarded write, and black-box stops at a non-2xx
  create, so the probe's 403 comes from `POST /reports`, read from code. Do not write "C4 re-attempts the guard" for
  reports-api.
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
| vampi-seeded recall 35% | 30–35% |
| the vendor patch gave 3 true negatives | the vendor patch gave no false alarm in 3 runs and no performed triple |
| a single labeller, as a limitation; who the labeller is | "người gán" |
