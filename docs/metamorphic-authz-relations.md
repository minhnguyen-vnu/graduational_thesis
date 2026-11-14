# Metamorphic Authorization Relations (MR-A)

> Working spec for the thesis oracle; thesis chapter 3 is the Vietnamese version. Grounded throughout in the
> `reports-api` app so every abstract line has a concrete example.
> Companion: the runnable PoC at `infra/oracle-poc/temporal_oracle_poc.sh`.

---

## 0. The idea in one breath

We cannot look at a single API response and know it's a bug — a `200 OK` looks fine
whether or not the caller was *supposed* to be allowed. So instead of judging one
response, we judge **how a response is allowed to change when we change one thing on
purpose**. The one thing we change: we **take a permission away**. The rule: once a
permission is removed, any action that **needed** that permission must be **refused** —
even by a login that was issued while the permission still held. If an action was allowed,
and we then remove the permission it relied on, the *same* action must now be refused. If
it still succeeds → the removal was never enforced → **bug**.

That rule is the **oracle**. This document defines it precisely and shows it is one
member of a small family (A1/A2/A3).

---

## 1. The vocabulary (kept to five words)

We only need five things. Each is one sentence plus a `reports-api` example.

| Symbol | Name | Meaning | Example in `reports-api` |
|---|---|---|---|
| `p` | **principal** | the user doing something | `alice` |
| `c` | **credential** | the token `p` carries to prove who they are | alice's JWT, issued at login |
| `a` | **action** | one HTTP request: a method + a path | `DELETE /reports/{id}` |
| `s` | **state** | the server's current permission facts | "alice is an ADMIN" |
| `T` | **transition** | an operation that changes the state | `PUT /users/alice/role {VIEWER}` |

And one observation function — the only thing we ever measure:

> **`Obs(a, c, s)`** = what happens when the credential `c` (which identifies its
> principal `p`) performs action `a` against the server in state `s`. Its value is
> **ALLOWED** or **DENIED** — or **INCONCLUSIVE** if the credential is not honored at all,
> in which case the observation is void.

We read the outcome straight off the HTTP status code (see §5.1):

- **ALLOWED** = the server carried the action out → **2xx** (e.g. `204 No Content`).
- **DENIED** = the server refused on authorization grounds → **403 Forbidden**.
- **INCONCLUSIVE** = the credential was not accepted as a login at all → **401
  Unauthorized** (e.g. the token expired mid-test). This is not a verdict; the triple is
  discarded and retried, never scored.

(`a` is an *endpoint template* — a method + a path like `DELETE /reports/{id}`; which
concrete resource id we use can vary between observations, see §5.4/§5.5.)

That's the entire vocabulary. Everything below is built from these.

---

## 2. The core relation — MR-A1 (privilege persists after a downgrade)

### 2.1 Plain English

> If a user was allowed to do something **that requires the privilege they are about to
> lose**, and we then **demote** that user, they must **no longer** be allowed to do it —
> *when they keep using the same login they already had*.

### 2.2 The four parts (we break a metamorphic relation into four)

| Part | Generic name | MR-A1 instance in `reports-api` |
|---|---|---|
| ① | **Source test** — observe a baseline | alice (ADMIN) does `DELETE /reports/1` → **ALLOWED (204)** |
| ② | **Transformation** — change one thing, on purpose | superadmin runs `PUT /users/alice/role {VIEWER}` → alice's permission is **reduced** |
| ③ | **Follow-up test** — repeat the action after the change | **same token** as ①, same request as ① |
| ④ | **Relation** — the rule tying ① and ③ | ① ALLOWED **and** `DELETE` is admin-gated **and** ② removed that privilege ⇒ ③ **must be DENIED**. Still ALLOWED ⇒ **bug**. |

### 2.3 The formal statement (short)

Let `T` be a **permission-reducing transition** that removes `p`'s permission to perform
`a`, and let `s' = T(s)` be the state after it. Then:

```
Guard:           a REQUIRES the permission T removes — the privilege p is left with
                 after T is NOT entitled to a on its own.                (see note)
Precondition:    Obs(a, c, s)  = ALLOWED          (we saw it allowed before)
Expected:        Obs(a, c, s') = DENIED           (it must be refused after)
Violation (bug): Obs(a, c, s') = ALLOWED          (still works → the removal was never
                                                   enforced on the held credential)
```

**The one constraint that makes this the whole contribution:** `c` is the **same
credential** in the precondition and the follow-up. We capture the token *before* `T`
and replay it *after* `T`. We do **not** log in again.

> Why this is the crux: a fresh login *after* the demotion hands back a VIEWER token,
> which is correctly refused — so re-logging-in **hides** the bug. The stale, pre-demotion
> token is the attack. Replaying it is the exact move EvoMaster's baseline never makes.

> **Note — why the guard is not optional, and what property this really is.** Without the
> guard the relation is false. Counterexample in `reports-api`: `GET /reports/{id}` is
> allowed to VIEWERs too, so it is ALLOWED before *and* legitimately ALLOWED after a
> demotion — no bug, yet an unguarded "ALLOWED-before ⇒ DENIED-after" would flag it. The
> intuitive slogan *"removing a permission must never increase access"* is **monotonicity**,
> and — subtly — the A1 bug does **not** violate it: alice could `DELETE` before and can
> `DELETE` after, so her access never *grew*. What the bug violates is **enforcement**: a
> permission that was removed is still honored through an already-issued credential. MR-A1
> is therefore a *guarded revocation* check ("an action gated by a removed privilege must
> become denied"), not a monotonicity check. For the core we satisfy the guard by
> **construction** — scoping `a` to an admin-only endpoint (§5.2).

### 2.4 Same-instant vs. across-time (why this is new)

The closest prior oracles (Şahin et al., EvoMaster's F204–F208) ask *"can the **wrong
person** access this **right now**?"* — different people, one instant. MR-A1 asks *"does
the **right person's old key** still work **after it was revoked**?"* — same person, same
key, across a change in time. Same family, orthogonal axis.

| | Prior (differential) | MR-A1 (temporal) |
|---|---|---|
| Compare across… | **users** (Alice vs Bob) | **time** (before vs after a transition) |
| Credential | different per user | **held fixed** (replayed) |
| Question | wrong person has access now? | old permission outlived its removal? |

---

## 3. From relation to test procedure (the recipe the tool must produce)

MR-A1 turns into a **`grant → transition → re-attempt` triple**. The builder emits it on any API where the model
accepts a transition (§5.2):

```
1. known state                    # p holds the HIGHER privilege, and >=2 resources
                                  #   a can act on exist
2. login p           → capture c  # the credential we will keep
3. do a with c       → expect ALLOWED    [① source: prove the action works while permitted]
4. apply T (by someone still allowed to) → reduces p's permission   [② the transition]
5. do a with c AGAIN → observe           [③ follow-up: SAME c, do NOT re-login;
                                  #        same resource and body as step 3]
6. verdict:  step 3 or 4 not 2xx, or step 5 has no status or 401   → VOID: discard, try the next attempt
             step 5 ALLOWED, re-login probe C4 (§5.6) not 403       → UNCONFIRMED: discard
             step 5 ALLOWED, C4 confirms                            → BUG (970)
             step 5 any other status (DENIED = 403)                 → PASS
```

Steps 1–5 are **construction** (build the scenario). Step 6 is **judgment** (the oracle).
The builder takes step 1 from the state the search left behind, restoring a demoted operator
through the target's own API when needed, and constructs steps 2–5 from the archive
(`infra/evomaster-ext/README.md` §3).

---

## 4. The family — one relation, three flavors

MR-A1 is the instance where the "permission" being removed is a **role**. Swap what gets
removed and you get the whole family — same shape, same oracle, different `T`:

| ID | What is removed / reduced (`T`) | Concrete story | Status |
|---|---|---|---|
| **A1** | a **role / privilege level** (ADMIN → VIEWER) | demoted admin still deletes reports | demonstrated |
| **A2** | an **ownership** relation (owner → not owner) | after transferring a wallet to B, A can still withdraw | defined, not demonstrated |
| **A3** | an **entitlement's validity** (valid → expired) | premium expires, premium endpoint still returns 200 | defined, not demonstrated |

**General schema (MR-A):**

> If removing/reducing **X** takes away the permission needed for action `a`, then an `a`
> that was **ALLOWED** while `p` had **X** must become **DENIED** once **X** is gone —
> using the **same credential** throughout.

A1/A2/A3 are just `X ∈ {role, ownership, entitlement}`. Proving the schema (not only A1)
is what makes the contribution a *class* of relations rather than one special case.

> **A2/A3 are not free reskins — two structural differences to handle when we get there.**
> (1) **Who triggers `T`:** in A1 a third party demotes `p` (superadmin → alice); in A2 the
> subject transfers ownership *themselves*. (2) **Instance-uniformity breaks:** A1 authz is
> role-uniform across resource instances; A2/A3 are **per-object / per-subscription**, and
> "already spent/consumed" noise must be handled another way.
> The *oracle* (part ④) is unchanged; only the *construction* differs.

---

## 5. The sharp edges (auxiliary definitions the code will need)

These are the ambiguities pinned down on paper *now*, so the implementation has no room
to guess.

### 5.1 What counts as ALLOWED vs DENIED (and why not 404)

- **ALLOWED = 2xx.** The server actually performed the action.
- **DENIED = 403.** Refused on authorization grounds.
- **401 = INCONCLUSIVE, never a verdict.** A 401 means the credential was not accepted as a
  login at all (typically the token expired mid-triple). It is neither ALLOWED nor DENIED:
  the attempt is VOID and the builder tries the next one. This matters because our whole
  premise is a *still-valid* stale token — `reports-api` uses a 1 h TTL precisely so the
  token outlives `T`; a shorter TTL (VAmPI's is 60 s) would turn real bugs into 401s and
  silently drop them.
- **404 is not a denial.** A 404 can mean "you may not, and I hide it" or "the resource is not there". A follow-up
  that gets 404 completes the triple and never raises 970. In the 98 runs of jar ND no follow-up got 404; follow-ups
  got 200, 401 or 403 (`infra/em-results/nd-wave1-20261113/logs/`, `nd-wave2-20261113/logs/`).
- **The codes are fixed in the tool, not configurable.** A target that denies with another code gives no verdict:
  artifact-keeper's vendor patch answers 401.

### 5.2 What is a "permission-reducing transition", and how we recognize one

`T` is permission-reducing if it moves `p` to a state with **fewer** rights over `a`. The tool
infers candidate `T`s from the OpenAPI spec: a Naive Bayes model scores every write op on its
path, field and verb tokens, and every op with posterior > 0.5 is tried in score order
(`docs/naive-bayes.md`). Examples on the targets: `PUT /users/{username}/role` with a lower enum
value (reports-api), `POST /api/set_user_permission` with a numeric permission (pyLoad),
`PATCH /api/v1/users/{id}` with `{"is_admin": false}` (artifact-keeper). 970 is raised only
after the C4 probe (§5.6) confirms that a fresh login of the victim is denied.

### 5.3 The same-credential rule (restating the crux as an instruction)

- Capture `c` **once**, before `T` (step 2 of the recipe).
- Reuse that exact `c` in the follow-up (step 5).
- **Never** re-authenticate between `T` and the follow-up. Re-login defeats the whole test.

### 5.4 Why a violation is a **true** bug, not a false positive (the precision argument)

We only raise a bug when **all four** hold:

1. We **observed** the action ALLOWED before the transition (step 3) — we did not assume it.
2. `T` is a **known** permission reduction (§5.2), applied successfully.
3. The follow-up uses the **same credential**, targets a **valid resource the action would
   legitimately act on if permitted** (e.g. a real, existing report — so a `2xx` means "it
   worked", not "nothing to do"), and `a` is one the **post-transition privilege is not
   entitled to** (the §2.3 guard).
4. The C4 re-login probe (§5.6) shows that a fresh login of the victim is denied.

Under role-downgrade scoping, the API's own rule is unambiguous — *a VIEWER must not delete
a report* — so a `2xx` follow-up is a genuine authorization violation, by the app's own
contract. False-positive risks we neutralise:

- **State pollution across runs** → the harness reseeds the target (`POST /reset`) before each run.
- **"Already done" noise** → the follow-up repeats the source on the same resource with the same
  body. Sources are PUT/PATCH first, POST only as a fallback, never DELETE, so a repeat is still
  meaningful (`addForStatefulAccessControl`, `guardedSources`, `RestSecurityBuilder.kt`).
- **404 masking** → handled by §5.1.

### 5.5 Validity conditions (when a verdict is trustworthy)

A BUG or PASS verdict is only meaningful when **all** of these hold; if any fails, the triple is
**VOID**, not a result:

| | Condition | Enforced by |
|---|---|---|
| **V1** | the credential `c` stays valid (not expired) across `T` — no 401 | long TTL; a 401 makes the attempt VOID (§5.1) |
| **V2** | repeating the source on the same resource is still meaningful (an update, not a consume) | PUT/PATCH sources first, never DELETE (§5.4) |
| **V3** | the follow-up status is not a masking 404 | no follow-up got 404 in the 98 runs of jar ND (§5.1) |
| **V4** | `T` actually **took effect** server-side (the role change returned 2xx *and* persisted) | assert the transition's own response |
| **V5** | `a` is **gated by the removed privilege** (the §2.3 guard) — the post-`T` role is not entitled to `a` on its own | scoping `a` to an admin-only endpoint (§5.2) |

V5 is the one that turns the relation from *almost right* into *exactly right*; V1–V2 are
the ones most likely to bite on a real, unfamiliar target.

### 5.6 The C4 re-login probe

C4 runs only on a would-be fault: the old credential was still allowed after `T`. The victim logs in again and its
slice of the test is replayed with the fresh credential; then the same slice is sent without credentials
(`reLoginProbeConfirmsPrivilegeRemoved`, `RestSecurityBuilder.kt`).

| Fresh login, last recorded status of the slice | Same slice without credentials | Result |
|---|---|---|
| 403 | a status other than 403 | 970 kept |
| 403 | 403, or no status | UNCONFIRMED |
| anything else, or no status | not run | UNCONFIRMED |

- The probe and the oracle ask different questions of different credentials. The fresh credential shows the privilege
  is gone; the old one shows whether it is still honoured. Neither result alone raises 970.
- The follow-up runs before the re-login. On a target that allows one session per user, a re-login first could kill
  the old credential and turn the follow-up into a 401.
- The 403 can come from an earlier call in the slice than the guarded write. On reports-api it comes from
  `POST /reports` (`CLAUDE.md` §4).
- The anonymous replay removes a 403 that does not depend on who calls.
- The re-login needs no change to authentication: EvoMaster logs every user in at the start of each test
  (`AuthUtils.getTokens()`), so the probe is a second individual.
- Limitation: on a target whose fresh credential still carries the old privilege, the probe reads "not reduced". The
  result is a missed bug, never a false alarm.

---

## 6. What this does NOT claim (honest scope)

- It does **not** find *cross-user* bugs (BOLA/BFLA "wrong person now") — that's the Şahin
  axis; we are complementary, not a replacement.
- The transition is recognized by a learned model (§5.2). A transition it scores at posterior ≤ 0.5 is never tried,
  so a bug behind it is missed.
- The ALLOWED/DENIED reading assumes standard status codes (2xx / 403, 401 inconclusive, §5.1); the codes are not
  configurable.
- A1 is demonstrated end-to-end; **A2 and A3 are defined here and not demonstrated.**

---

## 7. Notation cheat-sheet

```
p            principal (a user)
c            credential p carries (a token) — HELD FIXED across the transition
a            action = one HTTP request (method + path template)
s , s'       server state before / after the transition;  s' = T(s)
T            a permission-reducing transition
Obs(a,c,s)   the observed outcome of doing a with c in state s  ∈ {ALLOWED, DENIED}
ALLOWED      HTTP 2xx      DENIED   HTTP 403      INCONCLUSIVE  HTTP 401 (void, retry)

MR-A1:   Obs(a,c,s)=ALLOWED  ∧  a needs X  ∧  T removes p's X (the permission gating a)
         ⇒  Obs(a,c,s') must = DENIED     (ALLOWED instead ⇒ BUG;  401 ⇒ void)
         where X is the privilege a requires and the post-T role lacks.
```
