# EvoMaster extension — stateful authorization oracle (fault 970)

Code: `/Users/minhnguyen/IdeaProjects/EvoMaster`, branch `stateful-authz-oracle` on tag `v6.1.1`
(commit `46b99c57f273648389d61614ce660a12e8aa06f3`). The contribution is `git diff v6.1.1..HEAD`.
Results: `docs/results.md`. Build, jars, rollback: skill `evomaster-build`. Running: skill `em-batch`.

## 1. What changed

`git diff --stat v6.1.1..HEAD`: 12 commits, 6 files, +1825, 0 deletions, no comments. HEAD `a544c996ac` builds
jar P2e and is not pushed. `8d6cf8431f`, one commit earlier, builds jar AF2, which quoted the numbers 2026-10-04 to 10-14; P2e quotes them now
(`docs/results.md` §0).

| File | + | Holds |
|---|---|---|
| `ExperimentalFaultCategory.kt` | 5 | `SECURITY_STATEFUL_AUTHORIZATION(970)` |
| `EMConfig.kt` | 35 | `statefulAuthzResetEndpoint`, `statefulAuthzTransition` (blank by default), `statefulAuthzTwoCredentialJudgment` (false by default) |
| `RestSecurityOracle.kt` | 76 | judgment: `handleStatefulAuthorization()` |
| `RestSecurityBuilder.kt` | 1349 | construction: `addForStatefulAccessControl()`, `buildStatefulAuthzTriple()`, `executeStatefulAuthzTriple()`, `resetSutState()`, Naive Bayes scoring, operator restore |
| `stateful-authz-model.csv` | 261 | Naive Bayes weights, tables `op`, `role`, `victim`, `low`, `high`, `lowstr`, `highstr` (`lexicon-rules/p2-model-20261012/derive_model.py`) |
| `stateful-authz-lexicon.csv` | 99 | 53 `path` + 45 `param` words (`lexicon-rules/lexicon-20260921-audited/`); unread since `a544c996ac` |

`statefulTripleUnderEvaluation` is true only while `executeStatefulAuthzTriple` evaluates its own triple, and the
handler returns unless it is true (commit `bf26b65322`).

The `.patch` files directly in this folder predate the 2026-09-01 history rewrite and do not apply to the
current tree.

### P2 stack, commit `a544c996ac` on top of `8d6cf8431f`

`RestSecurityBuilder.kt` and `core/src/main/resources/stateful-authz-model.csv`.
`git diff 8d6cf8431f a544c996ac -- core/src/main/kotlin` equals `wip/p2e-restore-high-20261013.patch` byte for byte.
The steps below were built as patches before the commit. Jar per step: `jars.md`.

| Step | Patch | Does | Self-test |
|---|---|---|---|
| P1 | `candidate-iteration-20261011` | tries every usable transition op instead of stopping at the first; 20 attempts in total, 5 per unproven op | `candidate-iteration.sh` |
| P2 | `p2-nb-20261012` (includes P1) | Naive Bayes replaces the hand-written lists: op score (A), role field (B1), victim field (B3); values by field kind (B2); response reading by identity key (B4); anonymous control in D1 and C4; gate posterior > 0.5 | `p2-stateful-authz.sh` |
| P2c | `p2-nb-restoreswap-20261012` | restore call `:858`: restorer = victim, target = operator, as in AF2 | `restore-swap-20261012.sh` |
| P2d | `p2d-increment-over-p2c-20261012.diff` | A `:1248–1249`: a current-role value the model scores low does not exclude reduced values. B `:1261`: an operator snapshot the model scores low is not the restore value; enum values ranked by `high − low` are used | `p2d-reduce-elevate-20261012.sh` |
| P2e | `p2e-increment-over-p2d-20261013.diff` | C `:1265–1269`: enum restore values are only those the model scores `high > low`; the whole ranking when none is | `p2e-restore-high-20261013.sh` |

P2c, P2d and P2e restore three AF2 behaviours that P2 lost when it removed the hand-written lists: AF2 dropped low
values from the current role (`isLowPrivRole`, `8d6cf8431f` line 651) and elevated the operator to a high enum value only
(`harvestElevatedRoleCandidates`). Without A and B, P2c missed reports seeds 10/13/16 where AF2 fires
(`em-results/p2c-interleave-seeds-20261012/`, `em-results/p2c-vs-af2-debug-20261012/`). Without C, P2d spent one of
three restore attempts on `EVOMASTER`, the invalid-data value EvoMaster appends to string enums, and missed vampi
seed 11 (`em-results/p2d-night-20261012/STOPPED.md`).

## 2. Where it plugs in

The MIO search core is untouched.

- **Lifecycle.** `Main.kt` `phaseSecurity()` runs after the search (`if(!config.security) return`) and calls
  `RestSecurityBuilder.applySecurityPhase()`. The phase is time-boxed to `extraPhaseBudgetPercentage × maxTime`.
- **Construction.** `applySecurityPhase()` takes solved tests from the archive, builds `SampleType.SECURITY`
  individuals, runs them and adds them back. `addForStatefulAccessControl()` is wired right after
  `expandWithForbidden()`, so it inherits the 403 evidence and the phase budget. `resetSutState()` runs just before
  the fitness call in `executeStatefulAuthzTriple()`.
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
   `PUT /users/{username}/role`, ranked by score with ties in spec order; every such op is tried (P1). The role
   field is the non-path field with the highest role score above zero. Reduced values follow the field kind:
   enum values ranked by `valueScore(low) − valueScore(high)`, bool flipped, array `[]`, numbers `1, 0, 2`,
   strings from the model's `lowstr` table. A value equal to the victim's current role is skipped, unless the
   model scores that role low (P2d A). On `8d6cf8431f` (AF2) the score is the highest lexicon word, at most 8 candidates
   are tried, and reduced values come from hand-written lists.
2. **Source**: a guarded write some user was denied (403) and the victim was allowed (2xx). PUT/PATCH first;
   POST only when PUT/PATCH give no candidate.
3. **Individual**: `[create?, source(victim), transition(operator → victim reduced), follow-up(victim, same token)]`.
4. **Run and check performed**: VOID unless source 2xx, transition 2xx, follow-up conclusive. Retry over
   victim × operator × value, up to `MAX_STATEFUL_TRIPLE_ATTEMPTS`.
5. **Operator restore**: when every operator is refused while the victim's source succeeded, the victim's
   credential calls the transition upward on the operator (restorer = victim, target = operator), then the triple
   is retried; at most `MAX_PRIVILEGE_RESTORES = 3`. The upward value is the operator's observed role unless the
   model scores it low (P2d B); otherwise the enum values the model scores `high > low` (P2e C), bool `true`,
   numbers `0, 1, 2`, strings from `highstr`. Repairs a lost authorization, never a deleted account.
6. **C4 re-login probe**: only on a would-be fault; the victim logs in again and replays its slice. Fresh
   credential denied: keep the fault. Fresh credential allowed: VOID.

Log lines: `Assembled … statuses A/B/C`, `Discarded a VOID … codes A/B/C`,
`Discarded an UNCONFIRMED …`, `SUT state reset via … -> 200`. The builder's diagnostics are `debug`; EvoMaster
ships `<root level="warn">`.

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
