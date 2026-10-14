# Related work and novelty gap

Last full novelty check: **2026-08-24, gap open**. Upstream code check: **2026-10-02, no stateful
authorization oracle** (§2a). Re-check both before submission.
Rule for every entry: a quote enters a deliverable only after a first-party, word-for-word check.

## 1. The gap, argued structurally

No published work, academic or commercial, detects access that persists **after a permission-reducing
transition within one user's session** in a REST-API fuzzer, using a metamorphic temporal oracle.
The argument rests on the structure of existing oracles (single instant, cross-user), never on authors
naming the gap.

- Prior work checks whether the wrong person holds a key now. This thesis checks whether a key still opens
  the door after it was revoked.
- Baseline: differential, across users, one instant. Ours: metamorphic, across time, one user, through a transition.
- Complementary axes: our oracle does not find BOLA/BFLA.

## 2. Baseline

- **Şahin, Zhang & Arcuri (2026)**, *Enhancing REST API Fuzzing with Access Policy Violation Checks and
  Injection Attacks*, arXiv:2604.00702. Verified first-party. 9 security oracles in EvoMaster, added as a
  post-processing phase after fuzzing; authorization checks are single-request, cross-user.
  - Future work, verbatim (Conclusion): *"Future work will aim at designing new automated oracles to identify
    other kinds of security faults in REST APIs…"*. It does not name stateful authorization.
  - §5.4 calls endpoints that modify users' login information *"currently a major issue for fuzzers in
    black-box testing"*. The passage does not mention roles (PDF text re-read 2026-09-13).
  - Fault codes differ by source: the paper writes F900/F901 for Ignore Anonymous / Anonymous Modifications;
    `DefinedFaultCategory` in commons 0.6.0 (jar AF2, `v6.1.1`) numbers them 207/208; commons 0.9.0 (upstream
    master) numbers them 307/308. Name the source and its version when quoting a code.
- **Arcuri, Şahin & Zhang**, *Fuzzing for Detecting Access Policy Violations in REST APIs*, ISSRE 2025,
  doi:10.1109/ISSRE66568.2025.00025. Verified first-party (authors' BUAA repository). Peer-reviewed predecessor;
  same architecture; BOLA/BFLA. Cite ISSRE for the peer-reviewed claim, arXiv for the 9-oracle detail.
- EvoMaster: <https://github.com/WebFuzzing/EvoMaster>; tool report doi:10.1007/s10515-024-00478-1.

## 2a. Upstream EvoMaster code, checked 2026-10-02

Upstream has no oracle for access that persists after a permission reduction.

Revisions read: `WebFuzzing/EvoMaster` master `d8658d97` (2026-10-02, 1213 commits after `v6.1.1`), release
`v6.2.0` `efad6f2b` (2026-09-15), `WebFuzzing/Commons` master `18ea8fea` (2026-10-02). EvoMaster master pins
`wfc.version` 0.9.0 (`pom.xml:248`).

| Checked | Result |
|---|---|
| `git diff v6.1.1 master` on `RestSecurityOracle.kt`, `RestSecurityBuilder.kt` | 58 changed lines, all renames of fault constants, `NoAuth` checks and `DynamicPathUtils` |
| Function list of both files on master | no function builds a transition or reuses an earlier credential |
| `DefinedFaultCategory.java`, Commons master | security codes 300–312, none about a reduced permission |
| `ExperimentalFaultCategory.kt`, master | AsyncAPI 950–951, HTTP 960–961, RPC 970–974, Web 980, GraphQL 990 |
| grep `stateful`, `stale`, `revok`, `demot`, `downgrad`, `privilege`, `role change` in `core/src/main` | 4 files hit, none under `rest/oracle`, `rest/service` or `security` |
| 130 branches, filtered by name | 3 hits: `oracle-applicability` (oracle statistics), `security-v1-additionalTest` (2024, merged), `oauth` (2023, `pom.xml` only) |
| 22 open pull requests, by title | none on security or authorization |
| Issue and PR search: `stateful authorization`, `revoked OR revocation OR demote OR downgrade`, `role change OR permission change` | 0 results each |
| `release_notes.md`, version 6.2.0 | the new oracles are 25 HTTP-semantics oracles |

Nearest upstream oracles (descriptions paraphrased from `DefinedFaultCategory.java`):

| Code | Name | Compares | Missing axis |
|---|---|---|---|
| 113 | `HTTP_NONWORKING_DELETE` | a resource before and after its own successful DELETE | resource existence; no permission involved |
| 306 | `SECURITY_INCONSISTENT_WRITE_AUTHORIZATION` (0.6.0: `WRONG_AUTHORIZATION`, 206) | verbs on one resource for one user: PUT/PATCH 403, DELETE 2xx | one instant; no transition |
| 311 | `SECURITY_DECLARED_AUTH_NOT_ENFORCED` | a call with valid credentials against the same call with none or invalid ones | one instant; added to Commons after `v0.9.0`, not yet in EvoMaster master |

Code numbers moved after `v6.1.1`:
- Upstream assigns 970 to `RPC_INTERNAL_ERROR` since commit `0de70f95c` (2026-09-14, in `v6.2.0`); on `v6.1.1`
  that fault is 940. Our `SECURITY_STATEFUL_AUTHORIZATION(970)` needs a new number on any rebase past `v6.1.1`.
- Security codes moved from 200–210 to 300–310; the HTTP-semantics codes moved from 9xx experimental to 113–120
  in Commons.

Limits of this check:
- Branch contents were read for the 3 name hits only; the other 127 branches were screened by name and date.
- The issue and PR search used the unauthenticated GitHub search API, which matches titles and bodies.
- Upstream papers were not re-read; see §4 for arXiv:2608.16239.

## 3. Nearest neighbours

| Work | What it does | Missing axis |
|---|---|---|
| **BACScan** — Liu et al., CCS 2025, doi:10.1145/3719027.3744825 | access-control scanner, 20 apps, 89 vulns, 35 CVEs | web apps; cross-user; no transition. Must cite |
| **BACFuzz** — Dharmaadi et al., arXiv:2507.15984 (under review) | grey-box BAC fuzzer for PHP, SQL-level oracle | cross-user; no transition; no stale-token replay |
| **GraphQLer** — arXiv:2504.13358v2 | context-aware GraphQL security testing, builds `CREATE → DELETE → READ` chains | GraphQL; cross-user; two static credentials. Must cite |
| **ARMeta** — arXiv:2605.28321 (May 2026) | multi-agent LLM metamorphic testing for REST | functional MRs only; its RBAC case study defines zero authorization MRs |
| **AuthREST** — arXiv:2509.10320 | broken authentication | authentication, not authorization |
| **peerigon/access-control-testing** | OpenAPI access-control tests | self-described *"stateless, immediate authorization model"* |
| **BacAlarm** — arXiv:2512.19997 | runtime ML anomaly detector | IDS-style, not a testing oracle |
| **WuppieFuzz** — arXiv:2512.15554 (HTML) | coverage-guided stateful REST fuzzer | no authorization oracle |
| **RESTler** — microsoft/restler-fuzzer | stateful REST fuzzing with checkers | see §4 |
| Commercial: StackHawk, Invicti, Equixly, BOLABuster | BOLA/BFLA/privilege matrices | differential, one instant |
| Mao, Bianculli, Briand et al., SMRL (2020–2022) | metamorphic security testing, web | methodological ancestor; not REST fuzzing, not temporal authz |

Verbatim quotes kept for the write-up:
- GraphQLer §1: *"EvoMaster [9]—the only published GraphQL fuzzer we reproduce for comparison—applies
  evolutionary search over payloads but does not synthesize cross-user or post-delete chains."*
- GraphQLer §1: *"Black-box scanners (ZAP [35], BurpSuite [38]) vary parameters of individual operations and
  flag HTTP-level anomalies; they never compose multi-step sequences."*
- GraphQLer §6: *"Broken Function Level Authorization (BFLA) can be framed as a two-step chain; race-condition
  vulnerabilities require concurrent chains."*
- WuppieFuzz: *"There is no reset of the SUT in between input sequences, so it is possible that found bugs result
  from a state that was generated by earlier inputs."*

EvoMaster 2026 publications (5 papers: ML failed-call prediction, microservices uncertainty, MongoDB, tool
competition, SSRF) contain no stateful authorization oracle. arXiv:2607.04325 (OAI Overlay) has no security oracle.

## 4. Open items

- **RESTler — not yet written into related work.** The mentor originally pointed at RESTler. Its checker list has
  `UseAfterFreeChecker` (a deleted resource is still accessible: temporal, REST) and `NameSpaceRuleChecker`
  (an unauthorized user accesses resources: cross-user). No checker tests access after a permission reduction.
  Source `docs/user-guide/Checkers.md` read through a web-fetch summary: **not verbatim-verified**; the checker
  paper is not opened.
- **Spec2SeqFuzz** — He, Shang, Guo, Zhou, *Electronics* 15(11):2309. MDPI returns 403; abstract only, label as such.
  Offline LLM use to normalise PoCs and classify endpoints; no authorization oracle mentioned.
- **arXiv:2604.01759** (Volkswagen industrial experience with EvoMaster): open-problems list unread beyond the abstract.
- **arXiv:2608.16239** — Sahin & Arcuri, *Validating HTTP Semantics in REST APIs With Constructed Call Sequence
  Scenarios*: unread. Author names, title and id are copied from upstream `docs/publications.md` (commit
  `a132f13f8`, 2026-08-18).
- Fallback ground (not related work): Zhang, Shen, Arcuri & Yue (2026), arXiv:2603.28452, verified first-party.
- Prior comparison: Kim, Xin, Sinha & Orso, *No Time to Rest Yet*, ISSTA 2022, doi:10.1145/3533767.3534401.
- OWASP API Security Top 10 (2023): API1 BOLA, API5 BFLA. Datasets: WFD <https://github.com/WebFuzzing/Dataset>,
  VAmPI <https://github.com/erev0s/VAmPI>, crAPI <https://github.com/OWASP/crAPI>.
