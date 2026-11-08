# EvoMaster extension — stateful authorization oracle (fault 970)

Code: `/Users/minhnguyen/IdeaProjects/EvoMaster`, branch `stateful-authz-oracle` on tag `v6.1.1`
(commit `46b99c57f273648389d61614ce660a12e8aa06f3`). The contribution is `git diff v6.1.1..HEAD`.
Results: `docs/results.md`. Build, jars, rollback: skill `evomaster-build`. Running: skill `em-batch`.

## 1. What changed

`git diff --stat v6.1.1..HEAD`: 15 commits, 4 files, +1798, 0 deletions, no comments. HEAD `9c4be5b1dc` (pushed).
The thesis jar M2 is HEAD with model M2 in place of the model file below; the tree holds M1. Commit history, the jar
each commit built, and its self-test: `jars.md`.

| File | + | Holds |
|---|---|---|
| `ExperimentalFaultCategory.kt` | 5 | `SECURITY_STATEFUL_AUTHORIZATION(970)` |
| `RestSecurityOracle.kt` | 68 | judgment: `handleStatefulAuthorization()` |
| `RestSecurityBuilder.kt` | 1464 | construction: `addForStatefulAccessControl()`, `buildStatefulAuthzTriple()`, `executeStatefulAuthzTriple()`, Naive Bayes scoring, operator restore, C4 probe |
| `stateful-authz-model.csv` | 261 | Naive Bayes weights, tables `op`, `role`, `victim`, `low`, `high`, `lowstr`, `highstr` (M1 in the tree; M2 in jar M2, `lexicon-rules/m2-model-20261107/`) |

`statefulTripleUnderEvaluation` is true only while `executeStatefulAuthzTriple` evaluates its own triple, and the
handler returns unless it is true (commit `bf26b65322`).

The `.patch` files directly in this folder predate a history rewrite and do not apply to the current tree.
Function notes, in Vietnamese: `docs/evomaster-study/03-ham-stateful-authz.md`.

## 2. Where it plugs in

The MIO search core is untouched.

- **Lifecycle.** `Main.kt` `phaseSecurity()` runs after the search (`if(!config.security) return`) and calls
  `RestSecurityBuilder.applySecurityPhase()`. The phase is time-boxed to `extraPhaseBudgetPercentage × maxTime`.
- **Construction.** `applySecurityPhase()` takes solved tests from the archive, builds `SampleType.SECURITY`
  individuals, runs them and adds them back. `addForStatefulAccessControl()` is wired right after
  `expandWithForbidden()`, so it inherits the 403 evidence and the phase budget.
- **Judgment.** `RestSecurityOracle.analyzeSecurityProperties()` dispatches one `handleXxx()` per oracle.
  `handleStatefulAuthorization()` is modeled on `handleForbiddenOperation` (F206). The security oracle runs only on
  `sampleType == SECURITY` (`AbstractRestFitness.kt:1306`); search-phase tests are never judged.
- **Shared predicate.** `looksLikePermissionReducingTransition` is used by both construction and judgment.
- **Token replay is native.** Auth is a login recipe keyed by user name (`HttpWsAuthenticationInfo.kt`).
  `AuthUtils.getTokens()` logs each user in once per test, before the action loop, and every action reuses that
  token. So `[alice write, superadmin demotes alice, alice write]` sends alice's pre-demotion token twice.
  Cross-test token reuse is a performance cache in `AuthUtils.kt`: reseed before a run.

## 3. How a triple is built

1. **Transition**: a write op with Naive Bayes posterior > 0.5 (`transitionScore > 0`), e.g.
   `PUT /users/{username}/role`, ranked by score with ties in spec order; every such op is tried. The role
   field is the non-path field with the highest role score above zero. Reduced values follow the field kind:
   enum values ranked by `valueScore(low) − valueScore(high)`, bool flipped, array `[]`, numbers `1, 0, 2`,
   strings from the model's `lowstr` table. A value equal to the victim's current role is skipped, unless the
   model scores that role low.
2. **Source**: a guarded write some user was denied (403) and the victim was allowed (2xx). PUT/PATCH first;
   POST only when PUT/PATCH give no candidate.
3. **Individual**: `[create?, source(victim), transition(operator → victim reduced), follow-up(victim, same token)]`.
4. **Run and check performed**: VOID unless source 2xx, transition 2xx, follow-up conclusive. Retry over
   victim × operator × value, up to `MAX_STATEFUL_TRIPLE_ATTEMPTS`.
5. **Operator restore**: when every operator is refused while the victim's source succeeded, the victim's
   credential calls the transition upward on the operator (restorer = victim, target = operator), then the triple
   is retried; at most `MAX_PRIVILEGE_RESTORES = 3`. The upward value is the operator's observed role unless the
   model scores it low; otherwise the enum values the model scores `high > low`, bool `true`,
   numbers `0, 1, 2`, strings from `highstr`. Repairs a lost authorization, never a deleted account.
6. **C4 re-login probe** (`reLoginProbeConfirmsPrivilegeRemoved`): only on a would-be fault; the victim logs in
   again and replays its slice. The fault is kept when the slice's last recorded status is 403 and the same slice
   sent without credentials does not also end in 403; otherwise it is UNCONFIRMED.

Log lines: `Assembled … statuses A/B/C`, `Discarded a VOID … codes A/B/C`, `Discarded an UNCONFIRMED …`, and
`… proven by an attempt with statuses A/B/C` once per transition op (count triples from `Assembled` only). The
builder's diagnostics are `debug`; EvoMaster ships `<root level="warn">`.

## 4. Fault codes in reports

- F100–F104: HTTP faults (F100 = 500, F101 = response does not match schema, F103 = delete not working).
- F200–F210: security faults, the Şahin oracles, from `DefinedFaultCategory` (`com.webfuzzing:commons:0.6.0`):

| | | | | |
|---|---|---|---|---|
| 200 SQL_INJECTION | 201 XSS | 202 SSRF | 203 MASS_ASSIGNMENT | 204 SECURITY_EXISTENCE_LEAKAGE |
| 205 NOT_RECOGNIZED_AUTHENTICATED | 206 WRONG_AUTHORIZATION | 207 IGNORE_ANONYMOUS | 208 ANONYMOUS_MODIFICATIONS | 209 LEAKED_STACK_TRACES |
| 210 HIDDEN_ACCESSIBLE_ENDPOINT | | | | |

- 970: ours, experimental, needs `--useExperimentalOracles true`.
- Each test carries an H-code (HTTP status) and an F-code (fault type).
