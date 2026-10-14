# Metamorphic Authorization Relations (MR-A)

> Working spec for the thesis oracle. Written in English for now; the thesis chapter
> will be the Vietnamese adaptation of this. Grounded throughout in the Tier-1
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
| ③ | **Follow-up test** — repeat the action after the change | **same token** as ①, `DELETE /reports/2` |
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

MR-A1 turns into a **`grant → transition → re-attempt` triple**. This is the operational
form the generalized generator (future work) has to emit for any API:

```
1. reset                          # clean, known state; MUST restore p to the HIGHER
                                  #   privilege, and seed >=2 resources a can act on
2. login p           → capture c  # the credential we will keep
3. do a with c       → expect ALLOWED    [① source: prove the action works while permitted]
4. apply T (by someone still allowed to) → reduces p's permission   [② the transition]
5. do a with c AGAIN → observe           [③ follow-up: SAME c, do NOT re-login;
                                  #        act on a DIFFERENT seeded resource than step 3]
6. verdict:  ALLOWED in step 3 AND DENIED   in step 5  → PASS (🟢)
             ALLOWED in step 3 AND ALLOWED  in step 5  → BUG  (🔴)
             any step yields 401 (INCONCLUSIVE)        → VOID: discard the triple, retry
             step 3 not ALLOWED (guard/setup failed)   → VOID: the source never held
```

Steps 1–5 are **construction** (build the scenario). Step 6 is **judgment** (the oracle).
The PoC hard-codes construction for alice/reports; step 6 is already the real, reusable
oracle.

---

## 4. The family — one relation, three flavors

MR-A1 is the instance where the "permission" being removed is a **role**. Swap what gets
removed and you get the whole family — same shape, same oracle, different `T`:

| ID | What is removed / reduced (`T`) | Concrete story | Priority |
|---|---|---|---|
| **A1** | a **role / privilege level** (ADMIN → VIEWER) | demoted admin still deletes reports | **core target** |
| **A2** | an **ownership** relation (owner → not owner) | after transferring a wallet to B, A can still withdraw | if time permits |
| **A3** | an **entitlement's validity** (valid → expired) | premium expires, premium endpoint still returns 200 | if time permits |

**General schema (MR-A):**

> If removing/reducing **X** takes away the permission needed for action `a`, then an `a`
> that was **ALLOWED** while `p` had **X** must become **DENIED** once **X** is gone —
> using the **same credential** throughout.

A1/A2/A3 are just `X ∈ {role, ownership, entitlement}`. Proving the schema (not only A1)
is what makes the contribution a *class* of relations rather than one special case.

> **A2/A3 are not free reskins — two structural differences to handle when we get there.**
> (1) **Who triggers `T`:** in A1 a third party demotes `p` (superadmin → alice); in A2 the
> subject transfers ownership *themselves*. (2) **Instance-uniformity breaks:** A1 authz is
> role-uniform across resource instances, so the follow-up may use a *different* report
> (§5.4); A2/A3 are **per-object / per-subscription**, so the follow-up must reuse the
> **same** wallet or plan, and "already spent/consumed" noise must be handled another way.
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
  the observation is void and the triple must be retried. This matters because our whole
  premise is a *still-valid* stale token — `reports-api` uses a 1 h TTL precisely so the
  token outlives `T`; a shorter TTL (VAmPI's 60 s burned us once) would turn real bugs into
  401s and silently drop them.
- **We deliberately do not treat 404 as denial.** A 404 could mean "you may not, but I'm
  hiding that" *or* "the resource isn't there" — ambiguous. We avoid the ambiguity by
  relying on this app's verified ordering: **authorization is checked *before* resource
  existence**, so a forbidden call returns **403, not a masking 404**. (Confirmed live for
  `reports-api`; `CLAUDE.md` §3, `infra/analysis/denial-codes-2026-09-17.md`.) For a target that returns 404-as-denial, that must be
  configured explicitly rather than assumed.

### 5.2 What is a "permission-reducing transition", and how we recognize one

`T` is permission-reducing if it moves `p` to a state with **fewer** rights over `a`. The
generalized tool infers candidate `T`s from the **OpenAPI spec + endpoint naming**:

- **Naming signals:** `demote`, `downgrade`, `revoke`, `expire`, `disable`, `deactivate`,
  `remove` (a member/role), `transfer` (ownership), `cancel` (a subscription), `leave`.
- **Shape signals:** a `PUT`/`PATCH`/`DELETE` on a *user / membership / role /
  subscription / ownership* resource, or a body field like `role`, `plan`, `owner`,
  `active`.
- For the thesis core we **scope A1 to an explicit role-change endpoint** (`PUT
  /users/{u}/role` with a "lower" role value), where "reducing" is unambiguous. Broader
  inference is future work / configurable seeds.

### 5.3 The same-credential rule (restating the crux as an instruction)

- Capture `c` **once**, before `T` (step 2 of the recipe).
- Reuse that exact `c` in the follow-up (step 5).
- **Never** re-authenticate between `T` and the follow-up. Re-login defeats the whole test.

### 5.4 Why a violation is a **true** bug, not a false positive (the precision argument)

We only raise a bug when **all three** hold:

1. We **observed** the action ALLOWED before the transition (step 3) — we did not assume it.
2. `T` is a **known** permission reduction (§5.2), applied successfully.
3. The follow-up uses the **same credential**, targets a **valid resource the action would
   legitimately act on if permitted** (e.g. a real, existing report — so a `2xx` means "it
   worked", not "nothing to do"), and `a` is one the **post-transition privilege is not
   entitled to** (the §2.3 guard).

Under role-downgrade scoping, the API's own rule is unambiguous — *a VIEWER must not delete
a report* — so a `2xx` follow-up is a genuine authorization violation, by the app's own
contract. False-positive risks we neutralise:

- **State pollution across runs** → the harness reseeds the target (`POST /reset`) before each run. A reset before
  every triple is only the ablation arm (`--statefulAuthzResetEndpoint`, off by default; `docs/results.md` §4).
- **"Already done" noise** (e.g. deleting a resource that was already gone) → the follow-up
  acts on a **different, existing** resource than the source (`/reports/2`, not `/reports/1`).
  This is valid **only because `reports-api` authorization is role-uniform across report
  instances** (allowed to delete one report ⇒ allowed to delete any) — a load-bearing
  assumption (V2 in §5.5). It does **not** hold for per-object authz like A2 (see §4).
- **404 masking** → handled by §5.1.

### 5.5 Validity conditions (when a verdict is trustworthy)

A 🔴/🟢 verdict is only meaningful when **all** of these hold; if any fails, the triple is
**VOID**, not a result:

| | Condition | Enforced by |
|---|---|---|
| **V1** | the credential `c` stays valid (not expired) across `T` — no 401 | long TTL + retry on 401 (§5.1) |
| **V2** | authorization is **role-uniform across resource instances** (so source and follow-up may target different ids) | property of `reports-api`; must be checked per target (§5.4) — **breaks for A2** |
| **V3** | authorization is checked **before** resource existence, so denial is 403, not a masking 404 | verified for `reports-api` (§5.1) |
| **V4** | `T` actually **took effect** server-side (the role change returned 2xx *and* persisted) | assert the transition's own response |
| **V5** | `a` is **gated by the removed privilege** (the §2.3 guard) — the post-`T` role is not entitled to `a` on its own | scoping `a` to an admin-only endpoint (§5.2) |

V5 is the one that turns the relation from *almost right* into *exactly right*; V1–V2 are
the ones most likely to bite on a real, unfamiliar target.

---

## 6. What this does NOT claim (honest scope)

- It does **not** find *cross-user* bugs (BOLA/BFLA "wrong person now") — that's the Şahin
  axis; we are complementary, not a replacement.
- **Recognizing** a permission-reducing transition automatically is heuristic; for the core
  we rely on an explicit, scoped role-change endpoint rather than perfect inference.
- The ALLOWED/DENIED reading assumes the target uses standard status codes (2xx / 403, with
  401 read as inconclusive per §5.1); a non-standard API needs explicit configuration.
- A1 is proven end-to-end; **A2 and A3 are defined here but demonstrated only if time
  permits** — they exist to show the schema generalizes, not as committed deliverables.

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
