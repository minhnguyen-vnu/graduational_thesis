# Results — current numbers

Single source for every number quoted in `CLAUDE.md`, progress reports and the thesis. Edit in place.
A number in another doc that disagrees with this file is superseded. Paths are under `infra/em-results/`.
Run incidents (sleep, parallel lanes, re-run seeds) stay in each run folder's `PROTOCOL.md`; they do not go into the
thesis.

## 0. Provenance

- Jar `evomaster-ND-07ebf19f.jar` = HEAD `2c3f281f13` (branch `stateful-authz-oracle`, not pushed) plus
  `infra/evomaster-ext/wip/nodup-tokens-20261113-tree.patch` (the `THESIS` comments and the ND change; the ND change
  alone is `nodup-tokens-20261113.patch`, against the commented tree), not committed: `f:` op features come from query and body
  fields only, `tokens` walks characters instead of a regex, and `stateful-authz-model.csv` is the no-duplication model
  (sha256 `dcc77b59ed0f…`, `infra/analysis/lexicon-rules/m2-nodup-20261112/`). Each harness refuses a jar whose sha16 is
  not `07ebf19f9682497e`.
- The jar has no reset, no declared transition and no D1: `EMConfig.kt` equals v6.1.1, and judgment is the C4 re-login
  probe only.
- The no-duplication model is M2 relearned with path parameters left out of `f:`: same corpus
  (`nop-hoi-dong/nhan-hoc-cuoi.csv`, 209 T of 10,381 write ops), same formula; only the `op` table differs
  (`docs/naive-bayes.md`).
- Runs, 2026-11-13: `nd-wave1-20261113/runs.csv` (reports-api, vampi-seeded, pyLoad; 90 runs) and
  `nd-wave2-20261113/` (artifact-keeper 8 runs), same protocol and harness as M2 apart from jar and labels. Counts:
  `nd-wave1-20261113/nd_counts.py` (the M2 script with the wave-2 path changed), output `nd-counts-cp.out`. Triples are
  counted from `Assembled` log lines; the `assembled` column of the artifact-keeper CSVs counts each triple twice (it
  also matches the "proven by an attempt" line).
- Reseed before every run, `--useExperimentalOracles true`, `-Xmx2g`:

| Target | Seeds | `--maxTime` | `--ratePerMinute` | `--extraPhaseBudgetPercentage` | Other |
|---|---|---|---|---|---|
| reports-api | 1–20 per arm | 150s | 120 | 0.6 | |
| vampi-seeded | 1–20 per arm | 150s | 120 | 0.6 | |
| pyLoad | 1–5 per arm | 10m | 200 | 0.6 | `--endpointExclude "/api/kill,/api/restart"` |
| artifact-keeper | 1–5 vulnerable, 1–3 vendor patch | 1200s | 600 | 0.25 | spec without `DELETE /users/{id}`; traffic proxy :8212 |

- ND against M2, the previous thesis jar (`m2-wave1-20261108/`, `m2-wave2-20261108/`): equal in 970 on 96 of 98 rows
  (§6). M2 is the fallback jar (`infra/evomaster-ext/jars.md`).
- Each run records the triple it performed as `[source/transition/follow-up]` statuses, so construction (a triple
  was performed) and judgment (970 raised) are counted separately.

## 1. Detection and false positives

| Target | Bug | Arm | Runs with a performed triple | 970 raised |
|---|---|---|---|---|
| reports-api | seeded | vulnerable | 19/20 | **19/20** [75.1, 99.9] |
| reports-api | seeded | fixed | 19/20 | 0/20 |
| vampi-seeded | seeded | vulnerable | 6/20 | **6/20** [11.9, 54.3] |
| vampi-seeded | seeded | fixed | 6/20 | 0/20 |
| pyLoad | CVE-2026-41133 | vulnerable | 5/5 | **5/5** [47.8, 100] |
| pyLoad | CVE-2026-41133 | fixed (ours) | 5/5 | 0/5 |
| artifact-keeper | vendor bug #1821 | vulnerable `e56d3aa7e2` | 4/5 | **4/5** [28.4, 99.5] |
| artifact-keeper | vendor bug #1821 | vendor patch `e64cc5c608` | 0/3 | 0/3 |

Intervals are Clopper–Pearson 95% (exact binomial). False-positive rate over the 30 fixed runs with a triple: 0/30,
Clopper–Pearson [0, 11.6]%. One performed triple per run with a triple.

- Vulnerable vs fixed, Fisher exact one-sided: reports-api p < 0.001, vampi-seeded p = 0.010, pyLoad p = 0.004,
  artifact-keeper p = 0.071 (4/5 vs 0/3, not significant at 0.05).
- **False positives: 0 in 48 fixed-target runs**, over **30 triples performed on patched code** (reports-api 19,
  vampi-seeded 6, pyLoad 5, artifact-keeper 0).
- Every performed triple reads `200/200/200` on the vulnerable side and `200/200/403` on the fixed side.
- **C4 discards (artifact-keeper).** In all 8 runs, candidate 2 `POST /api/v1/admin/sso/oidc` gave `200/200/200`; the
  victim's fresh login was not denied, so C4 discarded it. Vulnerable seed 3 also had candidate 4 `POST /api/v1/users`
  discarded the same way. `Discarded an UNCONFIRMED`: 6 on the vulnerable commit (1, 1, 2, 1, 1), 3 on the vendor patch
  (1 per run). 970 fired only on candidate 3 `PATCH /api/v1/users/{id}`. reports-api, vampi-seeded, pyLoad: 0 discards.
  The transition of each discarded attempt is read from the traffic capture (`nd-wave2-20261113/traffic/`: source 2xx,
  one 2xx write by the operator, follow-up 2xx with the source token). No arm without C4 was run: never write that the
  vendor patch would otherwise have raised 970 (`nd-wave2-20261113/logs/ak-*-seed*.log`).
- **artifact-keeper vendor patch performs no triple.** In all 3 seeds the demotion succeeds and the old token gets
  401 (`codes 200/200/401`, once per run); 401 is INCONCLUSIVE, so the attempt is VOID. The vendor fix revokes the
  token (401) where the oracle reads a denial only from 403. The arm shows no false alarm and counts no TN.
- **artifact-keeper vulnerable seed 3 performs no triple.** Its source is `PUT /api/v1/admin/sso/ldap/{id}` with victim
  `operator`; 5 attempts are VOID (transition `400` or `403`) and 2 are C4 discards. The other four seeds use source
  `POST /api/v1/admin/analytics/snapshot`, as every M2 run did.
- vampi-seeded black-box recall is **6/20** on ND, also 6/20 on the jar-`R` audit re-run
  (`audit-batch/runs.csv`) and 7/20 on M2, P2f, P2e and AF2. Both 6/20 runs miss seed 15: on ND every attempt there has
  source 401 (victim `name1`, 6 VOID); on `R` the victim had been deleted during the search.
- Operator restores accepted (refused): reports-api 5 (0) vulnerable, 6 (0) fixed; vampi-seeded 5 (8), 5 (8);
  pyLoad 5 (0), 5 (0); artifact-keeper vulnerable one per run except seed 3 (none), vendor patch 1 (1) per run.
- Baseline arms (Şahin oracles, 970 disabled) are not false-positive opportunities and are not counted.

### 1a. Four cells per target

Same runs, `nd-counts-cp.out`. The vulnerable target gives TP/FN, the fixed target FP/TN. TN counts only fixed
runs with a performed triple (§2).

| Target | TP | FN, triple, no 970 | FN, no triple | FP | TN | Fixed, no triple | Runs vulnerable/fixed |
|---|---|---|---|---|---|---|---|
| reports-api | 19 | 0 | 1 | 0 | 19 | 1 | 20/20 |
| vampi-seeded | 6 | 0 | 14 | 0 | 6 | 14 | 20/20 |
| pyLoad | 5 | 0 | 0 | 0 | 5 | 0 | 5/5 |
| artifact-keeper | 4 | 0 | 1 | 0 | 0 | 3 | 5/3 |
| Total | 34 | 0 | 16 | 0 | 30 | 18 | 50/48 |

Every FN is a run with no performed triple; no performed triple on a vulnerable target missed 970. Per run,
precision is 1.0 on every row; recall is TP over the vulnerable runs.

FN by cause (logs of `nd-wave1-20261113/`, `nd-wave2-20261113/`):

| Cause | Runs | Detail |
|---|---|---|
| Attempts made, every one VOID or discarded by C4 | 10 | reports-api 1 (one attempt recorded no status); vampi-seeded 8 (48 VOID: 37 source 401, 11 transition 401); artifact-keeper 1 (5 VOID, 2 C4) |
| No attempt in the log | 6 | vampi-seeded seeds 2, 4, 6, 13, 14, 18; the default log level gives no reason |

## 2. How to read the numbers

- The 0-FP count is the independent accuracy measurement. Judgment is restricted to the triples our builder
  constructed (commit `bf26b65322` onward), so the 0 false positives are over the 30 builder triples on patched code.
- "Detection given a valid triple" (19/19, 6/6, 5/5, 4/4) is near-definitional: validity keys on the follow-up
  status that judgment also uses. It is never quoted as accuracy. It shows only that the handler, re-deriving
  the triple on its own, never disagreed with the builder.
- A VOID triple is evidence in neither direction. Counting one as a true negative inflates specificity.
- Report all four cells per target. A run without a performed triple is not a TN; the artifact-keeper vendor patch
  is such a case on every seed.

## 3. Hand-audit and replay

Replay not re-run on ND. Each line names its jar.

| | reports-api | vampi-seeded | pyLoad | artifact-keeper |
|---|---|---|---|---|
| 970 tests passing all four structural checks, jar ND | 19/19 | 6/6 | not parseable | 4/4 |
| Same check, earlier jars | 39/39 (AF2, P2f) | 20/20 (AF2, P2f) | not parseable | 5/5 (P2f) |
| Replay of 970 tests from clean state, jar AF2 | 38/39 | 17/20 | 28/38 | not run |
| Source | ND: `nd-wave1-20261113/audit970.out`; earlier: `af2-full-remeasure-20261003/audit970.out`, `replay.csv`; `p2f-full-20261015/audit970.out` | same | same | ND: `nd-wave2-20261113/audit970.out`; earlier: `artifactkeeper-machine-20261014/audit970-fixjar-vuln.out` |

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
- Transition inferred, rank 1 of 3 viable ops under ND (`m2-nodup-20261112/compare_targets_nodup.out`):
  `POST /api/set_user_permission`. Every ND triple: source `POST /json/status`, victim `pyload`, operator `alice`,
  `200/200/200` on the vulnerable variant, `200/200/403` on the fixed one.
- Each run performs its triple after one operator restore (`pyload` raises `alice`), identically on both variants.
- **VOID attempts:** 20, 10 per variant, each `200/401/200` on `/json/status`: the transition answered 401
  (INCONCLUSIVE), so the triple is VOID and raises nothing.
- **Transition values.** Each 970 test sends `user=pyload&permission=1` with a `role` value left by the search
  (`role=894`, `865`, `837`, `204`, `34`, seeds 1–5), never `0`. pyLoad treats role `0` as admin and any other value
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
- Transition inferred: `PATCH /api/v1/users/{id}` with `{"is_admin": false}`, rank 3 of 4 viable ops under ND
  (`m2-nodup-20261112/compare_targets_nodup.out`; rank 4 of 5 under M2); the builder reaches it by trying every viable
  op. Every ND triple (seeds 1, 2, 4, 5): source `POST /api/v1/admin/analytics/snapshot`, victim `victim`, operator
  `operator`, `200/200/200`. Seed 3: §1.
- No string of the app is in the builder, the oracle or the model (jar ND), and its spec is excluded from
  the training corpus (`infra/analysis/corpus/sample_specs_field.py:8–9`).
- Development target: three general builder fixes were found by running it. Vulnerable-commit detection by jar:
  ER 0/1, AF 1/4 (boolean admin flag recognized), AF2 5/5 (nullable `is_admin` sent present), P2e 0/2 (`null` sent
  again), P2f 5/5 (value set on the leaf gene), M2 5/5, ND 4/5 (`artifactkeeper-machine-20261001/`,
  `artifactkeeper-machine-20261014/`, `m2-wave2-20261108/`, `nd-wave2-20261113/`). Its numbers make no claim about recall on unseen apps.

## 6. Changing the model

- M2 to ND: 96 of 98 rows equal in 970. Two rows lost, none gained: vampi-seeded vulnerable seed 15 and
  artifact-keeper vulnerable seed 3, both runs with no performed triple on ND (§1). McNemar exact, 2 vs 0 discordant:
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
| vampi-seeded recall 35% (jar M2) | 6/20 (jar ND) |
| the vendor patch gave 3 true negatives | the vendor patch gave no false alarm in 3 runs and no performed triple |
| pyLoad and artifact-keeper used while the builder was developed | omit |
| "người gán", "tác giả", who reviewed the labels | impersonal: "được soát tay", "viết riêng cho khóa luận" |
