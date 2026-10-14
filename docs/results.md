# Results — current numbers

Single source for every number quoted in `CLAUDE.md`, progress reports and the thesis. Edit in place.
A number in another doc that disagrees with this file is superseded. Paths are under `infra/em-results/`.

## 0. Provenance

- Thesis jar `evomaster-P2e-6ae8277b.jar` (commit `a544c996ac`, branch `stateful-authz-oracle`) for §1, §1a, §4
  and §5, on the merged set `p2e-continue-20261013/merged.csv` (180 runs): 71 runs on P2e, 109 on jar P2d
  (`2e0dbd4d`), column `jar`. **Declared deviation** (user, 2026-10-14): the set mixes two jars. P2e differs from
  P2d only in the enum restore values (`RestSecurityBuilder.kt:1265–1269`). None of the 109 P2d runs reaches that
  code: 106 make no restore call, 3 pyLoad runs restore integer fields. The 11 runs that reach it gave the P2d row
  again on P2e (`p2e-continue-20261013/RESULTS.md`). A single-jar run is prepared, not run (`p2e-full-20261014/`).
- P2e = AF2 + P1 (every transition candidate, 20 triple attempts instead of 8) + P2 (Naive Bayes in place of the
  hand-written lists). Every 970 cell equals AF2 seed for seed (`af2-full-remeasure-20261003/runs.csv`,
  2026-10-03/04), and AF2 equals the earlier jar-`R` batches. The places P2e differs from AF2 are marked below.
  AF2 (`evomaster-AF2-6b5606d4.jar`, commit `8d6cf8431f`), jar `R` (`5bce137f`, commit `007e5e09f9`) and their
  batches (`tier1-clean-remeasure/`, `restore-remeasure/`, `restore-reset-remeasure/`, `tier2b-restore-trials/`)
  are kept as provenance.
- Regression gate: jar P2d passed the 21-row gate as a job, 21/21 MATCH (2026-10-13 01:44,
  `p2d-night-20261012/gate/`). In that run only Tier-2 seed 3 no reset, vuln and fixed, reached the code P2e
  changes (one restore with `EVOMASTER` each); the other 19 rows made no restore call. Both seed-3 rows re-run on
  P2e match the gate's expectation (`p2e-continue-20261013/gate-predict.out`). P2e has not run the gate as a job.
  AF2 passed the gate on 2026-10-02 (`regression-check/`).
- Seeds 1–20 per arm (Tier-2b: 1–5), reseed before each run, `--useExperimentalOracles true`,
  `--extraPhaseBudgetPercentage 0.6`. Tier-1/Tier-2 `--maxTime 150s`; Tier-2b `--maxTime 10m`.
- Each run records the triple it performed as `[source/transition/follow-up]` statuses, so construction
  (a triple was performed) and judgment (970 raised) are counted separately.
- Tier-1 = `reports-api` after the 2026-09-10 cleanup. Pre-cleanup Tier-1 numbers are not quoted.

## 1. Detection and false positives

| Target | Arm | Runs with a performed triple | 970 raised | Source |
|---|---|---|---|---|
| Tier-1 | vuln, no reset | 19/20 | **19/20** [76, 99] | `p2e-continue-20261013/merged.csv` |
| Tier-1 | fixed, no reset | 19/20 | 0/20 | same |
| Tier-1 | vuln, reset | 20/20 | 20/20 [84, 100] | same |
| Tier-1 | fixed, reset | 20/20 | 0/20 | same |
| Tier-2 | vuln, no reset | 7/20 | **7/20** [18, 57] | same |
| Tier-2 | fixed, no reset | 7/20 | 0/20 | same |
| Tier-2 | vuln, reset | 13/20 | 13/20 [43, 82] | same |
| Tier-2 | fixed, reset | 13/20 | 0/20 | same |
| Tier-2b | vuln, no reset | 5/5 (5 triples) | **5/5** [57, 100] | same |
| Tier-2b | fixed, no reset | 5/5 (5 triples) | 0/5 | same |
| Tier-2b | vuln, reset | 5/5 (73 triples) | 5/5 | same |
| Tier-2b | fixed, reset | 5/5 (52 triples) | 0/5 | same |

Intervals are Wilson 95%. AF2 and the jar-`R` batches gave the same 970 cells seed for seed (§0). AF2 performed 36
and 35 triples on the Tier-2b reset arms: it stops at 8 attempts per run.

### 1a. Four cells per tier

Same runs, counted per run by `p2e-continue-20261013/four_cells_merged.py` (output `four-cells.md`); AF2 and jar
`R` give the same cells (`infra/analysis/confusion/jar-R-four-cells.md`). The vulnerable target gives TP/FN, the
fixed target FP/TN. TN counts only fixed runs with a performed triple (§2).

| Target | Reset | TP | FN, triple, no 970 | FN, no triple | FP | TN | Fixed, no triple | Runs vuln/fixed |
|---|---|---|---|---|---|---|---|---|
| Tier-1 | no | 19 | 0 | 1 | 0 | 19 | 1 | 20/20 |
| Tier-1 | yes | 20 | 0 | 0 | 0 | 20 | 0 | 20/20 |
| Tier-2 | no | 7 | 0 | 13 | 0 | 7 | 13 | 20/20 |
| Tier-2 | yes | 13 | 0 | 7 | 0 | 13 | 7 | 20/20 |
| Tier-2b | no | 5 | 0 | 0 | 0 | 5 | 0 | 5/5 |
| Tier-2b | yes | 5 | 0 | 0 | 0 | 5 | 0 | 5/5 |

Every FN is a run with no performed triple; no performed triple on a vulnerable target missed 970. Per run,
precision is 1.0 on every row; recall is the TP column over 20 (Tier-2b: 5).

- **False positives: 0 in 90 fixed-target runs** with 970 enabled (40 Tier-1, 40 Tier-2, 10 Tier-2b),
  over **116 triples performed on patched code** (39 Tier-1, 20 Tier-2, 57 Tier-2b; AF2: 99, with 40 on Tier-2b).
- Every performed triple reads `200/200/200` on the vulnerable side and `200/200/403` on the fixed side.
- Vulnerable vs fixed, Fisher one-sided: Tier-2 no reset 7/20 vs 0/20, p = 0.004; Tier-2b 5/5 vs 0/5, p = 0.004.
- **Tier-2 black-box recall is quoted as 30–35%.** P2e and AF2 give 7/20 no reset; the structural audit confirmed
  all 20 vulnerable-side firings (§3). The earlier jar-`R` audit re-run gave 6/20 (`audit-batch/runs.csv`),
  differing on seed 15 only, whose victim `name1` had been deleted during the search (source 401).
- Operator restores, no-reset arms: Tier-1 5 (vuln) and 6 (fixed); Tier-2 5 and 5; Tier-2b 5 and 5.
  Reset arms: 0, except Tier-2b fixed 15, 3 per run (AF2: 0).
- Baseline arms (Şahin oracles, 970 disabled) are not false-positive opportunities and are not counted.

## 2. How to read the numbers

- The 0-FP count is the independent accuracy measurement. P2e, like AF2, is post-0e (`bf26b65322`): judgment is
  restricted to the triples our builder constructed, so the 0 false positives are over the 116 builder triples
  on patched code (§1a). On jar `R`, before 0e, the handler judged every security-phase test including those
  built by EvoMaster's own security builders (which skip C4); that broader 0-FP claim holds only for jar-`R` data.
- "Detection given a valid triple" (19/19, 7/7, 5/5) is near-definitional: validity keys on the follow-up
  status that judgment also uses. It is never quoted as accuracy. It shows only that the handler, re-deriving
  the triple on its own, never disagreed with the builder.
- A VOID triple is evidence in neither direction. Counting one as a true negative inflates specificity.
- Report all four cells per tier: the vulnerable target gives TP/FN, the fixed target FP/TN. A run without a
  performed triple is not a TN. Report precision per fault report and per run.
- **The no-reset figures are the black-box headline.** Reset arms are an ablation. The reset endpoints of
  Tier-1 (`/reset`) and Tier-2b (`/thesis/reset`) are ours; Tier-2's `/createdb` is upstream VAmPI's.
  Fixed arms were reset identically.

## 3. Hand-audit and replay

This section is jar AF2 (`af2-full-remeasure-20261003/`). On the merged P2e set the structural audit gives the same
counts: Tier-1 39/39, Tier-2 20/20, 37 + 20 silent triples (`p2e-continue-20261013/audit970-merged.out`). Replay
has not been re-run on P2e.

| | Tier-1 | Tier-2 | Tier-2b |
|---|---|---|---|
| 970 tests passing all four structural checks | 39/39 | 20/20 | see note |
| Silent triples verified in generated tests (fixed) | 37 | 20 | 0 |
| Replay of 970 tests from clean state | 38/39 | 17/20 | 28/38 |
| Source | `af2-full-remeasure-20261003/audit970.out`, `replay.csv` | same | same |

- `audit970_seeded.py` reads the emitted tests, never the log: same credential in source and follow-up,
  no re-login between them, transition by a different credential, 2xx/2xx/2xx. On AF2 it passes all 39 Tier-1
  and all 20 Tier-2 firings. It flipped the right check on five deliberately broken copies; redo that
  validation whenever the parser changes.
- **Tier-2b is not auditable by this parser.** pyLoad authenticates with a session cookie, not a Bearer
  header, so the `headers["Authorization"]` regex reads no credential and marks all 38 vulnerable-side 970
  tests FAIL on the same-credential check (`"cred": "None / op None"`); their recorded statuses are all
  `200/200/200` with no re-login. pyLoad is validated instead over HTTP by `verify_ground_truth.sh`
  (`200/200/200` vulnerable, `200/200/403` fixed) and by replay.
- **57 silent triples, all on fixed arms, none on a vulnerable arm** — the oracle never stayed silent where it
  should have fired.
- Replay misses fail on a dropped search-time state change or a brittle generated assertion, never on the
  authorization claim:
  - Tier-1 seed 16: the minimized test omits the restore that gave victim `bob` write access, so the follow-up
    is 403.
  - Tier-2 seeds 5 and 11: fail at the transition (`res_1` 403) — the operator promotion the minimizer dropped.
    Seed 15: reseed returns victim `name1` to `user`, so its source becomes 403 (the triple ran against
    non-reset search state).
  - Tier-2b (10): all fail on a generated body assertion (e.g. `res_0.json()["pause"] == True`), never on a
    status code; the `200/200/200` triple holds.
- **Quote "replayable 55/59"** (Tier-1 38/39 + Tier-2 17/20), never "reproducible".

## 4. Reset ablation

Same seeds, no reset vs reset, vulnerable side.

| | Gained | Lost | Exact McNemar p, two-sided |
|---|---|---|---|
| Tier-2 recorded | 3, 7, 8, 9, 12, 16, 19 | 15 | **0.070** (one-sided 0.035) |
| Tier-2 audit re-run | 3, 7, 8, 9, 12, 16, 19 | none | 0.016 |
| Tier-1 | 17 | none | 1.0 |

- P2e and AF2 reproduce this discordance exactly: reset gains seeds {3, 7, 8, 9, 12, 16, 19}, loses {15}
  (`p2e-continue-20261013/merged.csv`, `af2-full-remeasure-20261003/runs.csv`), so the recorded McNemar p = 0.070
  carries over unchanged.
- **Not significant at 0.05 on the recorded batch. The diagnosis is not called causal.**
- Power of the exact test at 40% discordant seeds with 7/8 gains: 20 seeds 45%, 40 seeds 86%, 60 seeds 97%
  (with 3/4 gains: 17%, 44%, 63%).
- Tier-2 non-detections split in two:

| Mechanism | Seeds | Rescued by reset |
|---|---|---|
| Attempts ran and came back VOID | 3, 7, 8, 9, 12, 16, 19 | 7/7 |
| No candidate pair in the archive | 2, 4, 6, 13, 14, 18 | 0/6 |

- Seed 15 detects without reset and not with it. Its successes test holds `PUT /users/v1/name1/role` asserting
  `data.role == "admin"`: the search promoted the victim. The reset returns `name1` to user and the source becomes 403.
  Candidates are selected from state observed during the search; the triple runs against reset state.

## 5. Tier-2b — pyLoad CVE-2026-41133

- Real third-party bug: GHSA-66hx-chf7-3332, CWE-613, CVSS 8.8, `pyload-ng <= 0.5.0b3.dev97`, no upstream fix.
  Setup and the six declared deviations: `docs/tier2b-pyload-target.md` §3.
- Transition inferred (no `--statefulAuthzTransition`): `POST /api/set_user_permission`, victim `pyload`,
  operator `alice`.
- No reset: every triple is performed after an operator restore (`pyload` raises `alice`, writing `0` to both
  `permission` and `role`, as AF2 did through `setAllRoleFieldsTo`; AF2's log prints one value, P2e's one per field),
  identically on both variants.
- **VOID attempts.** No reset: 20, 10 vulnerable and 10 patched, each `200/401/200` on `/json/status`, as on AF2:
  the transition (`POST /api/set_user_permission`) answered 401 (INCONCLUSIVE), so the triple is VOID and raises
  nothing. Reset arms: 63 on P2e, none on AF2, which stops at 8 attempts: 38 `200/500/200` on `/json/status`
  (20 vulnerable, 18 patched) and 25 `200/401/200` on `/json/update_users` (patched). A VOID triple is evidence in
  neither direction (§2). (jar `R` instead reported C4 discarding 8 `POST /json/add_package` attempts at
  `200/200/200`.)
- **Transition values.** The 78 vulnerable-side 970 tests (AF2: 38) send `user=pyload&permission=1` with a
  `role` value left by the search, never `0` (`p2e-continue-20261013/pyload-970-tests.out`). The binder writes the
  reduced value to `permission`, the first matching field; pyLoad treats role `0` as admin and any other value as
  not, so the demotion lands. The tool did not infer the role value; C4 confirmed the privilege was gone. The
  follow-up endpoints span 15 `POST /json/*` routes (most often `/json/status`), broader than jar `R`'s single
  `add_package`. Each requires a permission the transition removes: `ADMIN`, `ACCOUNTS`, `MODIFY`, `LIST`,
  `STATUS` or `SETTINGS` (`p2e-continue-20261013/RESULTS.md`, Soát tay).
- **AF2 performed 41 vulnerable-side triples but emitted 38 970 tests.** In seeds 3–5 with reset it assembled
  `POST /json/edit_package` at `200/200/200` and raised nothing. With D1 off, the oracle skips a source the builder's
  predicate calls a transition (`RestSecurityOracle.kt:583`); on AF2 that predicate is the lexicon, whose word `name`
  (0.08) matches the field `pack_name`. P2e's model scores the op −4.58, below the gate, so its 78 triples give 78
  tests (`p2e-continue-20261013/af2-41-vs-38.md`).
- Restore ceiling: at least one privileged credential must survive. With every admin demoted, a fresh login
  cannot promote anyone (401).

## 5b. Jar L — the derived lexicon replaces the hardcoded words

Jar `evomaster-L-5b3d5442.jar` (sha256 `5b3d5442…`) = commit `634850be3a` + the uncommitted denial-code
patch (`wip/d1-denial-codes-20260917.patch`) + the ranking patch (`wip/lexicon-rank-20260921.patch`) +
`core/src/main/resources/stateful-authz-lexicon.csv` (53 `path` words, 45 `param` words,
`infra/analysis/lexicon-rules/lexicon-20260921-audited/`). It replaces the 8 hardcoded path words (the path part of our 56 hand-written words,
`lexicon-rules/lexicon-20260920/RESULTS.md`) and
makes the builder rank every candidate endpoint by score instead of taking `firstOrNull`.

Chain: `lexicon-chain-20260921/`, 2026-09-21 22:20 to 2026-09-22 07:10, one job at a time.

| Stage | Result | Source |
|---|---|---|
| Self-test `selftest/lexicon-rank.sh` | 14/14 pass | `logs/selftest.log` |
| Regression gate, 21 rows | 21/21 MATCH | `logs/gate-observed.csv` |
| Tier-1 vuln, seeds 1–10 | 970 raised 10/10 | `runs.csv` |
| Tier-2 vuln, seeds 1–10 | 3/10 (seeds 1, 5, 10) | same |
| Tier-2b pyLoad vuln, seeds 1–10 | 10/10 | same |
| Tier-1 + Tier-2 fixed, 20 runs | 0 false positives | same |

All 50 runs carry `--statefulAuthzTwoCredentialJudgment false`, so they pair against the recorded D1
rows with `d1=false`.

**No detection is lost.** Paired per seed against the D1 batches (`d1-seeds1-10/runs.csv`,
`d1-pyload-seeds1-10/runs.csv`, `d1=false`): 30 rows in common, **0 mismatches** — same seed, same
`[source/transition/follow-up]` statuses, same verdict. The 20 fixed-arm runs are new; the D1 batches
ran vulnerable targets only.

**What this does not establish.** Ten seeds per arm, not twenty, so §1 never used jar `L`. The lexicon's precision and recall on held-out specs are static measurements
(`lexicon-20260921-audited/RESULTS.md`), not run measurements. `MAX_TRANSITION_CANDIDATES = 8` has no
runtime effect yet: `harvestReducedRoleCandidates` harvests enum values from every action definition in
the API, so the rank-1 candidate almost always yields role values and the loop never advances. The
self-test check `harvest-is-global` records that behaviour rather than asserting the intended one.

## 5c. Held-out public apps — machine campaign (2026-10-14)

External evidence beyond the self-seeded targets (advisor ask, CLAUDE.md §6). Four public apps from the MR-A1
candidate survey (`infra/analysis/mra1-candidates-20261007/FINDINGS.md`), each with MR-A1 confirmed by hand before
any run (`infra/<app>-target/handcheck.sh`). Jar P2e, `--statefulAuthzTwoCredentialJudgment false`, no reset,
`--maxTime 600s --ratePerMinute 600`, auto arm = black-box recall. All Tier B (no vendor contract). No patched
variant exists for any, so there is no 0-FP arm; each 970 is hand-audited. Folders `infra/em-results/<app>-heldout-20261014/`.

| App | Stack | Auto | Outcome | Mechanism |
|---|---|---|---|---|
| raouf (`raouf-b-dev/ecommerce-store-api`) | NestJS, OpenAPI 3.0 | 0 triples | **FN**; declared = **TP** | role field `roleCode` is a free string with no enum → reducing value taken from the model's `lowstr` (`read,member,guest`), none a real role (`CUSTOMER`) → "could not target victim" |
| fastschema | Go, OpenAPI 3.1 | — | **blocked (parser)** | 6 circular `$ref` (User↔Role, Role↔Permission, User↔File) → swagger-parser `ResolverFully` StackOverflow before search |
| alvaro (`alvaromrveiga/ecommerce-backend`) | NestJS+Prisma 3.14 | — | **blocked (environment)** | fuzzing triggers a Prisma arm64 query-engine panic (`parser.rs:250`, non-recoverable); login 500×988 vs 200×20 |
| magic (`polterguy/magic`) | C#/.NET | 0 triples | **FN**; runs clean | transition `DELETE users_roles` chosen correctly (score 4.08, query-string role+user); source `PUT roles` is a crud-update returning 404 for a non-existent name → never observed 2xx → 0 guarded source candidates |

- **raouf** auto: `assembled=0, det970=0` (`runs-auto.csv`); builder chose the transition `PUT /v1/users/{id}/role` but
  the reduced values were `[read, member, guest]`. Declared (`--statefulAuthzTransition "PUT /v1/users/{id}/role
  roleCode=CUSTOMER id=2"`): `assembled=2, det970=1`, triple source `PATCH /v1/categories/{id}` 200/204/200. Hand-audit
  on a clean reseed: `PATCH /categories/{id}` is ADMIN 200 / CUSTOMER 403, `POST /categories` CUSTOMER 403 → the write is
  genuinely admin-only, so the 970 is a true positive, not a guardless read. Fires under D1 too (fresh CUSTOMER token denied).
- **magic** auto: `assembled=0, det970=0, evaluated=3535`, all three accounts logged in (v217/o212/l211), `guarded source
  candidates: 0`. Runs only after four declared deviations (synthesized OpenAPI 3.0 from magic's own `/endpoints/list`
  because its `/endpoints/openapi` serves 0 paths; `/auth/` excluded from the fuzz surface because fuzzing the login
  endpoint locks the accounts out; login throttle raised from 10/min; GET query-string login config). Bug hand-confirmed;
  declared arm not run (only the transition can be forced, and the wall is source identification).
- **fastschema, alvaro**: blockers sit above the oracle (EvoMaster never searched / auth died), partly artifacts of the
  arm64 test host. Both bugs are real by hand. Record as "could not machine-run", not as oracle outcomes.
- Two distinct FN mechanisms on real public apps (enum-less role field; crud-update source returning 404) are the
  field-identification weakness this chapter documents. Do not write a recall figure over this set: n is tiny, two of
  four did not run, and the auto FNs are deterministic, not sampled.

## 6. Limitations

- **The search destroys the triple's preconditions** in two ways. Demotion: the source returns 403, and black-box
  aborts a test at its first failing create call. Deletion: VAmPI's generated tests call
  `DELETE /users/v1/{username}` 75× on `name1`, 17× `name2`, 10× `admin`, 6× `superadmin`. The restore reverses
  a demotion, never a deletion. Both cost recall, never precision.
- **Transition inference** ranks write ops by a Naive Bayes model over path, field and verb tokens
  (`stateful-authz-model.csv`, `lexicon-rules/p2-model-20261012/derive_model.py`), trained on the round-4 labels
  (10,381 write ops, 230 APIs). Vendor-wise cross-validation, 5 folds × 4 repeats: the true op ranks first in 16–18
  and within the first 4 in 21–25 of 47 test specs (`infra/evomaster-ext/wip/p2-design-20261012.md` §1). Those 47
  specs were looked at many times while choosing the model, so the figures are exploratory, with no confirmatory
  p-value; no difference from the max-lexicon rule has p < 0.05. Tier-2's `/role` path was named by us.
- **Reduced-role value** follows the field type: an enum value the model scores low, a flipped bool, `1, 0, 2` for
  numbers (hand-written), or the model's `lowstr` strings (`infra/evomaster-ext/README.md` §3 step 1). Before the
  Tier-1 cleanup, the only accepted value `VIEWER` came from the phantom `caller` enum.
- **C4 on Tier-1.** The probe replays the victim's slice and takes the last executed status. 34 of 39 Tier-1 970
  tests create a report (`POST /reports`) before the guarded write, and black-box stops at a non-2xx create, so
  on Tier-1 the probe's 403 comes from `POST /reports`, read from code (the probe status is not logged). Tier-2 and
  pyLoad slices contain no create. Do not write "C4 re-attempts the guard" for Tier-1.
- **401 differs by target.** pyLoad `/api/*` answers a non-admin session with 401; `/json/*` answers 403; VAmPI's
  401 means no valid token. 401 stays INCONCLUSIVE.
- **The guard is load-bearing.** Without it, 970 fired on VAmPI tests with no transition
  (`GET /me`, then `GET /_debug` by another user, then `GET /me`). Cost of the guard: zero true positives.
- **Security-phase budget** was hit in 424 of 428 runs (90 s seeded, 360 s pyLoad); our builder's last line
  precedes the budget end in every run where timestamps bound it (2026-09-13 log mining, script not kept).
- **Scope.** One bug class (A1). Both seeded targets plant the same mechanism, a stale role claim in a JWT;
  pyLoad caches the role in a session.

## 7. Baseline (Şahin et al., arXiv:2604.00702) on A1

- **Cannot judge it.** F204–F208 compare users at one instant; none models "permission removed, so now denied".
- **Cannot construct it.** Tier-2: 0/20 baseline-vulnerable runs contain write, downgrade, re-write with the same
  auth variable (`tier2-trials/baseline_blindness.py`). F209 on 17/20 runs shows the baseline was configured.
  Tier-1 (pre-cleanup app): 5 tests touch `PUT /users/{u}/role`, 32 mutate `/reports`, 0 do both.
- EvoMaster logs each user in once per test, so the baseline always holds a token current at that test.

## 8. Wording for the write-up

| Do not write | Write |
|---|---|
| the diagnosis is causal | a paired difference with its McNemar p |
| reproducible failing test | replayable from clean state in 55/59 |
| Tier-2 shows transition inference generalizes | Tier-2's transition name is ours |
| a benchmark the community lacks | two seeded apps and one CVE |
| Tier-2 recall 35% | 30–35% |
