# Tier-2 seeded benchmark & head-to-head — design plan

> Current numbers: `docs/results.md`. Numbers in §6 onward are from earlier builds and are superseded.
> §4 is the reference for the `vampi-seeded` target: users `admin/pass1`, `superadmin/pass1` (ADMIN),
> `name1/pass1`, `name2/pass2`; spec `/openapi.json`; ground truth `200/200/200` on :5002, `200/200/403` on :5003.

> Status: **§4 seed BUILT and smoke-verified (2026-08-06)** — `infra/vampi-seeded/` exists, both
> variants run, and the oracle fires on vuln / stays silent on fixed at seed 1. §5 run matrix is the
> remaining work. This doc plans thesis deliverable **(4)** — *"a small seeded benchmark of
> stateful-authz bugs"* — and the **head-to-head vs the Şahin baseline** (§4.4, evaluation Tier-2).

---

## 1. What Tier-2 must prove

Tier-1 (`reports-api`) is *our own* controlled positive: it shows the oracle fires on a bug we planted.
Tier-2 answers the two questions Tier-1 cannot, on a **third-party community target**:

- **Recall** — does the oracle still construct the triple and fire on an app we did **not** write?
- **Precision / false-positive rate** — on a *fixed* variant of that same app, does it stay silent?
- **The head-to-head delta** — run the **Şahin baseline oracles** on the same target; they should score
  **0** on the stateful bug (structurally blind, §6). Our oracle scoring > 0 where they score 0 *is* the
  contribution, made visible on someone else's code.

## 2. The gating fact — seeding is mandatory, not optional

The oracle's construction needs three things present in the target (§7.8 / evomaster-ext README):

1. a **permission-reducing transition** endpoint (a write that lowers a principal's role/entitlement),
2. a **guarded, non-consuming write** (PUT/PATCH) that is admin-allowed but viewer-denied (the source/guard),
3. the **stateful bug** itself: authorization trusts a claim carried in the already-issued token instead of
   re-reading current state, so a pre-transition token keeps working after the downgrade.

**Neither stock VAmPI nor stock crAPI ships (1).** VAmPI's `admin` flag is not mutable through any API
endpoint; there is no `PUT /users/{u}/role`. crAPI has richer role semantics (user vs mechanic) but no
self-serve *downgrade* transition either. So on the stock images our oracle has **nothing to construct
against** — an expected true-negative, and precisely why the community "lacks a benchmark." Tier-2 is
therefore a **fork-and-seed** exercise, mirroring exactly what we already did for `reports-api`.

## 3. Target selection

| Choice | Role | Why |
|---|---|---|
| **VAmPI-seeded** (fork of `erev0s/VAmPI`) | **PRIMARY** | Single Flask container, trivial to edit; already wired for EvoMaster black-box (`infra/em-config/vampi-auth.yaml`, §7.3). Lowest operational risk → guaranteed Tier-2 result. |
| **crAPI-seeded** | **STRETCH (only if time permits)** | Native user/mechanic roles → more "realistic," but a heavy multi-container stack (identity + community + workshop + Postgres + Mongo). High setup cost, uncertain black-box reachability. Defer unless VAmPI lands with time to spare. |

Recommendation: **commit Tier-2 to VAmPI-seeded**; treat crAPI as optional colour, consistent with the
A2/A3 "demonstrate only if time permits" posture.

## 4. The VAmPI seed — BUILT (`infra/vampi-seeded/`)

Vendored fork of `erev0s/VAmPI` @ `f16052dc`, patched with the smallest change that reproduces the A1
shape. **Deliberate departure from the original de-risking advice in §8:** the endpoints were named in
**VAmPI's own idiom**, *not* copied from `reports-api`. Mimicking `reports-api` would have re-proved what
Tier-1 already proves; naming naturally is the only way the run tests **transition inference** rather than
the author's memory of his own keyword list. It fired unchanged (§4.1), so the risk paid off.

Every seeded line is marked `THESIS SEED` in the source. What was added:

1. **Transition endpoint** — `PUT /users/v1/{username}/role`, body `{"role": "admin"|"user"}`, admin-only.
   Sits naturally beside VAmPI's existing `/email` and `/password` sub-resources.
2. **Guarded non-consuming write** — `PUT /books/v1/{book_title}/secret`, admin-only (non-admin ⇒ 403),
   updating `Book.secret_content`. Repeatable on the same resource, so the follow-up can replay it.
3. **The stateful bug** — login now snapshots the role into the JWT as an `admin` claim (stock VAmPI's
   token carries only `sub`, so the bug class could not exist). `is_caller_admin()` in `api_views/users.py`
   is the single decision point, toggled by env `statefulrolecheck`:
   - `0` (default) **VULNERABLE** — trust the stale claim ⇒ a demoted admin's old token still writes.
   - `1` **FIXED** — re-read the role from the store by username on every request.
4. **JWT TTL 60 s → 3600 s** (`tokentimetolive`). Disclosed seeding choice: token lifetime is orthogonal
   to the authorization bug, and a 60 s TTL expires mid-triple (401 = INCONCLUSIVE, never a verdict, §5.3).
5. **403-before-404 verified** — a non-admin hitting a *nonexistent* book still gets 403, never a masking 404.
6. **Stable operator `superadmin`** — a fourth seeded admin (see the caveat in §4.1).
7. **Deterministic reseed (bug fix, not a seed)** — stock `register_user` picks the starter book title with
   `randrange(100)` against a UNIQUE column; a 4th user made collisions frequent enough that `GET /createdb`
   returned **500** at random, which would have silently corrupted a 20-run batch. Seeded users now pass an
   explicit `book_suffix`; ad-hoc registrations keep the original random behaviour.

Ports: **:5002 = VULNERABLE**, **:5003 = FIXED** (same image, `-e statefulrolecheck=1`). Auth config:
`infra/em-config/vampi-seeded-auth.yaml` (4 users; separate from stock `vampi-auth.yaml`).

```bash
docker build -t vampi-seeded infra/vampi-seeded
docker run -d --name vampi-seeded       -p 5002:5000 vampi-seeded
docker run -d --name vampi-seeded-fixed -e statefulrolecheck=1 -p 5003:5000 vampi-seeded
curl -s http://localhost:5002/createdb   # reseed before every run
```

### 4.1 Smoke verification (2026-08-06, seed 1, `--maxTime 150s`)

Ground truth by hand — `source / transition / follow-up (stale token)`:
**:5002 → `200 / 200 / 200` (BUG)** · **:5003 → `200 / 200 / 403` (FIXED)**.

EvoMaster with `--useExperimentalOracles true --extraPhaseBudgetPercentage 0.6`:

| Variant | Fault codes | 970 | Endpoint coverage |
|---|---|---|---|
| :5002 VULNERABLE | 100, 101, 209, **970** | **fires** | 16/16 (100%) |
| :5003 FIXED | 100, 101, 209 | silent | 16/16 (100%) |

**The generator inferred the transition on an app the author did not write** — it matched
`PUT /users/v1/{username}/role` on the path signal + `username` param, harvested `user` as the reduced value
from the `['admin','user']` enum, and picked `PUT /books/v1/{book_title}/secret` as the guard. The emitted
test `test_19_put_on_secret_stillAllowedAfterPermissionRevoked` is a well-formed triple: both tokens are
captured up front, `superadmin` writes the secret (200), `admin` demotes `superadmin` to `user` (200), then
`superadmin` **replays the pre-transition token** and still writes (200 — should be 403).

**Caveat found by the run — the stable-operator mitigation does not bind.** The generator picked
`superadmin` as the *victim* and `admin` as the operator, i.e. the reverse of the intended assignment. Both
are admins so the triple is valid, but nothing reserves `superadmin` as an undemotable operator; the
state-isolation hazard of §7 is therefore mitigated only by the per-run reseed, not by the seeded role split.
Harmless here (a stranded run is a false *negative*, never a false positive), and worth one line in the
write-up.

## 5. Run matrix (head-to-head)

Two tools × two variants × N seeds, reusing the shape of `infra/em-results/tier1-trials/tier1_trials.sh`:

| Arm | Target variant | EvoMaster flags | Expected |
|---|---|---|---|
| **Ours — vuln** | VAmPI-seeded VULNERABLE **:5002** | `--useExperimentalOracles true --extraPhaseBudgetPercentage 0.6` | 970 fires (recall) |
| **Ours — fixed** | VAmPI-seeded FIXED **:5003** | same | no 970 (FP rate) |
| **Baseline — vuln** | VAmPI-seeded VULNERABLE **:5002** | **without** `--useExperimentalOracles` (Şahin oracles only) | **no** stateful finding on the bug (the blindness delta) |
| **Baseline — fixed** | VAmPI-seeded FIXED **:5003** | same as baseline-vuln | (control) |

Common flags carried from the verified Tier-1 recipe: `--blackBox true`, `--maxTime 150s`,
`--ratePerMinute 120`, `--configPath infra/em-config/vampi-seeded-auth.yaml`,
`--outputFormat PYTHON_UNITTEST`, `GET /createdb` reseed **before every run** (VAmPI's `POST /reset`
equivalent), N = 20 seeds per arm for a stable rate (same N as Tier-1). A `tier2_trials.sh` cloned from
`tier1_trials.sh` — swap ports, reseed verb (`GET /createdb`), and add the baseline arms.

## 6. Metrics — MEASURED (2026-08-08, N=20 per arm, seeds 1–20)

Data: `infra/em-results/tier2-trials/runs.csv`; integrity confirmed (80/80 rows, no duplicate `(arm,seed)`
pairs, arms sequential, 0 WARN reseeds, 0 nonzero exits). All four ours-vuln firings hand-audited via
`baseline_blindness.py`; construction-blindness confirmed across all 20 base-vuln runs.

### Head-to-head (stateful bug, Tier-2 VAmPI-seeded)

| Tool | Detection on vuln | 95% Wilson CI | FP on fixed | Other security faults found |
|---|---|---|---|---|
| **Ours (970)** | **4/20 = 20%** | [8%, 42%] | **0/20 = 0%** (upper 16%) | F205 × 3 runs, F209 × 17 runs |
| **Şahin baseline** | **0/20 = 0%** | — | — (control) | F205 × 3 runs, F209 × 17 runs |

Construction rate (ours-vuln): 4/20 = 20%. Every detection = a successfully constructed triple; no
detection occurred without construction (a correctly assembled, token-replaying triple reveals the bug
**deterministically** on the vulnerable target, as on Tier-1). The recall gap is entirely a
**construction-phase miss** — the generator found the transition signal on 4 of 20 seeds.

Endpoint coverage: mean 95% across all four arms (min 88%, max 100%), confirming both tools exercise
comparable surface.

### Construction-blindness confirmation (Stage 3)

`baseline_blindness.py` scanned all 20 base-vuln test files: **0/20 runs constructed an MR-A1 triple**,
even in the 3 seed-19 tests that contained both a role-write and a guard-write in the same generated test.
In those near-misses the two writes used different auth variables in a scrambled order — the MR-A1 recipe
(source-with-victim → downgrade-victim → follow-up-with-same-victim-token) was never assembled. This is the
structural blindness claim, measured independently of the disabled fault code.

### Audit of all four ours-vuln firings (hand-verified)

| Seed | Victim | Operator | Guarded resource | Triple shape |
|---|---|---|---|---|
| 1 | superadmin | admin | `/books/v1/bookTitle3/secret` | PUT(superadmin 200) → PUT role→user(admin 200) → PUT(superadmin 200) |
| 10 | admin | superadmin | `/books/v1/bookTitle1/secret` | PUT(admin 200) → PUT role→user(superadmin 200) → PUT(admin 200) |
| 17 | superadmin | admin | `/books/v1/bookTitle3/secret` | PUT(superadmin 200) → PUT role→user(admin 200) → PUT(superadmin 200) |
| 20 | admin | superadmin | `/books/v1/bookTitle1/secret` | PUT(admin 200) → PUT role→user(superadmin 200) → PUT(admin 200) |

All four: `same-token-replay = True`, `transition-present = True`. No false positives.

### Comparison with Tier-1

| Metric | Tier-1 (`reports-api`) | Tier-2 (`vampi-seeded`) |
|---|---|---|
| Detection (ours, vuln) | **16/20 = 80%** [58%, 92%] | **4/20 = 20%** [8%, 42%] |
| False positives (ours, fixed) | **0/20** (upper 16%) | **0/20** (upper 16%) |
| Baseline stateful detection | 0/20 | 0/20 |
| Construction rate | 16/20 = 80% | 4/20 = 20% |

The Tier-2 recall gap vs Tier-1 (20% vs 80%) is a **construction-phase difference**, consistent with Tier-2
being a genuinely different app whose endpoint vocabulary the generator has to infer without prior tuning.
Broadening the naming/parameter signal is the single bounded fix; this is §10's priority optional extension.
The precision result is identical (0 FP on both fixed targets); the oracle's judgment rule does not false-alarm.

### Key contrast for the thesis write-up

The Şahin baseline finds F209 (`SECURITY_LEAKED_STACK_TRACES`) in 17/20 runs on VAmPI-seeded, proving the
baseline is correctly configured and actively finding security bugs. Its **0/20 on the stateful bug** is not
misconfiguration — it is structural blindness. This makes the head-to-head contrast publishable and its
interpretation clean.

## 7. Risks & carry-over caveats

- **State-isolation (black-box)** — no per-triple reset, so an earlier constructed triple can incidentally
  demote a user later reused as the transition *operator* → a **missed** triple (false negative, never a
  false positive). Carried verbatim from `evomaster-ext/README.md`. Mitigate by reseeding per run (already
  in the matrix) and by seeding a **dedicated stable-admin operator** (VAmPI analogue of `superadmin`) that
  no constructed triple downgrades.
- **Inference generalization** — the generator was verified only against `reports-api`. If it fails to
  construct on VAmPI-seeded, that is a *finding about the generator*, and the fix (broaden the naming/param
  signal) is bounded and in-scope; keep the endpoint names close to `reports-api` first, then widen.
- **crAPI scope creep** — do not start crAPI until VAmPI-seeded is green with time to spare.

## 8. Contingency — RESOLVED: it fires

Recorded because the reasoning still belongs in the write-up. The risk was never the bug's presence (we
seed it) but whether the generator would *recognize* a transition it had never been tuned against. Outcome
at seed 1 (§4.1): **it fires unchanged, on VAmPI-idiom endpoint names** — the "Fires ✅ / bonus strength"
row below, and the strongest available generalization evidence short of an unseeded real app. The other
rows are retained as the contingency that did not materialize.

| Outcome | Meaning | Thesis impact |
|---|---|---|
| Fires ✅ | Oracle generalizes to an app we did not write | Bonus strength |
| Doesn't fire — naming/param mismatch | Honest, *bounded, fixable* limitation of transition inference | Still a valid finding + concrete future work |
| Broaden the signal, then it fires | Even stronger generalization story | Strongest version |

De-risk order: **superseded by the §4.1 result** — the naming gamble was taken up front and paid off, so
there is no need to start from `reports-api`-lookalike names. Optional future probe: rename the seeded
endpoints to genuinely off-vocabulary terms to measure how far the inference stretches (a recall
experiment for §10, not a prerequisite).

## 9. Open decisions (need a call before building)

1. **Tier-2 target = VAmPI-seeded only, crAPI as optional stretch?** (recommended) — vs invest in crAPI now.
2. **Fork granularity** — minimal Flask patch on stock VAmPI (recommended, fastest) vs a cleaner re-lift.
3. **N and maxTime for Tier-2** — reuse Tier-1's N=20 / 150 s (recommended, comparable) vs larger budget for
   a harder target.

## 10. Optional extensions — NOT required for an acceptable thesis

Recorded so they are not re-derived. Each raises the ceiling toward "works on an arbitrary app"; none is
needed for the core contribution (which is complete + verified on Tier-1). Do only if time remains after the
head-to-head.

- **Broaden transition inference (recall).** Today the generator matches endpoint *names* against a keyword
  list, so a real downgrade endpoint with an off-vocabulary name is **missed** (a false negative, never a
  false positive — a miss just means "no triple constructed"). Cheap deterministic widening: also inspect
  **body-field names** (`role/level/plan/owner/active`), **enum values**, **method + resource type**, and the
  OpenAPI **`description`/`summary`** text. (§5.3 already gestures at this.)
- **Offline, cached LLM transition inference (recall, stronger).** Run an LLM **once** over the spec →
  `endpoint → {is_transition, subject_param, reduced_value}` → **cache/pin to disk** → feed the deterministic
  generator. Keeps the fuzzing loop + oracle reproducible (non-determinism quarantined to a one-time step).
  This is the RESTGPT-style pattern. **Caution:** an LLM over-guesses, which introduces a *false-positive*
  risk the conservative keyword list does not have — so pair it with the precision guard below. Also verify
  the live literature first (EvoMaster+LLM / ARMeta move fast, postdate the training cutoff); keep the novelty
  framed as *the temporal authz relation*, not "an LLM metamorphic REST tool" (that is ARMeta's claim, §8.2).
- **Fresh-vs-stale precision guard (precision on *uncontrolled* apps).** Operationalizes the §5.3 validity
  condition *"the transition actually took effect."* After the transition, also probe with a **fresh** login
  token and compare to the replayed **stale** token: fire **only** on `stale ALLOWED + fresh DENIED`; if
  `stale ALLOWED + fresh ALLOWED`, the transition was a no-op → **suppress** (this is what kills a
  mis-identified-transition false positive). **Not needed for measuring effectiveness on controlled/seeded
  targets** (Tier-1/2 have known ground truth, so detection/FP rates are counted against the answer key). It
  only matters for real/unknown apps (Tier-3 / real-world use), and it is the safety net that makes broadening
  inference or adding the LLM *safe*. Cost: one extra login + one extra probe per triple.

---

*Execution order once the Tier-1 batch clears: fold Tier-1's three rates into §6 → build `infra/vampi-seeded/`
(§4) → `tier2_trials.sh` (§5) → run the four arms → tabulate (§6). Extensions in §10 only if time remains.*
