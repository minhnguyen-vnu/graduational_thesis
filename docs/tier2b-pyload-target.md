# Tier-2b — pyLoad CVE-2026-41133: a real, third-party stateful-authorization bug

> Current numbers: `docs/results.md` §5. Numbers below §4 are from earlier builds and are superseded.
>
> Setup facts: `/api/*` answers an authorization failure with **401** (INCONCLUSIVE), `/json/*` with **403**, so
> guard endpoints come from `/json/*`. Runs use `infra/pyload-cve/openapi-merged.json` (104 paths, 107 operations)
> and `infra/em-config/pyload-auth.yaml`. The hand ground truth (`verify_ground_truth.sh`) uses guard
> `POST /json/generate_apikey` and transition `POST /json/update_users`, which matches none of the tool's
> transition keywords; the tool infers `POST /api/set_user_permission`.

> Status: target built and ground truth verified 2026-08-16. Pre-extension measurement recorded
> below. This is the only target in the evaluation whose **bug we did not write**.

## 1. Why this target exists

Tier-1 (`reports-api`) and Tier-2 (`vampi-seeded`) both carry a bug **we planted**. That is a
construct-validity threat no amount of careful writing can remove: the sharpest reading of the
results is *"the bug you find is the bug you planted"*. Tier-2b answers that objection as far as it
can honestly be answered — the vulnerability here is real, third-party, and has a CVE.

It does **not** answer it completely, and §4 says exactly where the line falls.

## 2. The vulnerability

**pyLoad** (<https://github.com/pyload/pyload>), a widely used download manager with a Python/Flask
web interface. **CVE-2026-41133, CWE-613, CVSS 8.8**, reported April 2026.

Root cause, and it is the same shape as both seeded targets — which is itself a useful finding,
because it means the seeded targets were designed around a mechanism that really occurs:

- `set_session()` copies the user's `role` and `permission` into the Flask session at login.
- Authorization later reads that copy: `parse_permissions()` (used by `login_required`, which guards
  the `/json/*` surface) reads `session.get("role")`, and the session branch of `apikey_auth()`
  (which guards `/api/*`) reads `s["role"]`.
- `set_user_permission()` writes the new role to the database and **never invalidates any session**.

So a demoted administrator keeps administrative power for the entire life of the session cookie.
This is precisely MR-A1: a permission is removed, and an already-issued credential still carries it.

**Upstream never fixed it.** The advisory claims a fix in `0.5.0b3.dev98`, but `is_authenticated` is
byte-identical across `dev97`, `dev98`, `dev99`, `dev100`, `dev101` (newest on PyPI) **and** the
`develop` branch. That is worth a sentence in the thesis on its own: an advisory declared this class
of bug patched when it was not, which is an argument for an automated oracle rather than review.

## 3. Build, run, and the declared deviations

    docker build --build-arg STATEFUL_ROLE_CHECK=0 -t pyload-vuln  infra/pyload-cve
    docker build --build-arg STATEFUL_ROLE_CHECK=1 -t pyload-fixed infra/pyload-cve
    docker run -d --name pyload-vuln  -p 8090:8000 pyload-vuln
    docker run -d --name pyload-fixed -p 8091:8000 pyload-fixed
    infra/pyload-cve/verify_ground_truth.sh          # prints the triple for both variants

Both images are built from the **same** upstream release, `0.5.0b3.dev97`. Accounts (`alice` the
victim, `superadmin` the operator, both ADMIN) are seeded at image build time by `seed_users.py`; these are the
roles of the hand ground truth (`verify_ground_truth.sh`). `pyload-auth.yaml` also lists pyLoad's own ADMIN `pyload`,
and the inferred builder picks its own pair: victim `pyload`, operator `alice` in the recorded runs
(`docs/results.md` §5).
Between runs they are restored over HTTP by the injected `/thesis/reset` endpoint (deviation 4).

**Six** deviations from a plain out-of-the-box run. Each must be stated in the write-up; none of
them creates, hides, or moves the bug. They are not of one kind, and the write-up must not blur
them together — the **Where** column is the distinction that matters. Deviations 1–4 change the
system under test or its specification; 5–6 only change how the tool is invoked.

| # | Where | Deviation | Why it is needed | Why it does not affect the result |
|---|---|---|---|---|
| 1 | SUT, **both** variants | `WTF_CSRF_METHODS = []` added to `BaseConfig` | The vulnerable path is session-authenticated and CSRF-guarded, so a non-browser client cannot reach it at all. `csrf.protect()` ignores `WTF_CSRF_ENABLED` (that flag is only read inside CSRFProtect's `before_request` hook) but does return early when the method is absent from `WTF_CSRF_METHODS`. | Anti-forgery is orthogonal to authorization, and it is applied to **both** variants, so it cancels out of the differential. The same endpoints are already reachable CSRF-free through the `X-API-Key` scheme. |
| 2 | SUT, **fixed only** | The fixed variant is a control **we wrote** | Upstream published no working fix (see §2), so there is no patched build to diff against. | The patch is not invented: it applies to the session branches exactly the fresh-database read that the `X-API-Key` branch of `apikey_auth()` already performs. It is applied to *both* authorization paths (`parse_permissions` and `apikey_auth`) so the control does not depend on which surface a request uses. |
| 3 | Input (not the SUT) | The OpenAPI specification for `/json/*` is hand-written | pyLoad generates a specification for its `/api/*` RPC surface only; `/json/*` is real, authenticated and undocumented. | A specification is an **input** to black-box fuzzing, not part of the system under test. To avoid spoon-feeding, `infra/pyload-cve/openapi-json-routes.json` describes **all 20 routes / 23 operations**, not only the three the triple needs; a script cross-checks it against the blueprint in both directions. The `/api/*` half of the merged document is pyLoad's own generated specification, unmodified — 84 of the 104 merged paths. |
| 4 | SUT, **both** variants | `POST\|GET /thesis/reset` injected into `json_blueprint.py` | The state-reset ablation (`docs/results.md` §4) needs an HTTP endpoint that restores account state, and stock pyLoad has none. The two seeded targets do have one — `reports-api`'s `POST /reset` (ours, we wrote the app) and VAmPI's `GET /createdb` (**upstream VAmPI's own**) — so this deviation exists only because the third-party target was not built for testing. | It writes to the `users` table only and contains no authorization logic, so it cannot change any verdict; it is present in **both** variants, so it cancels out of the differential. It is deliberately unauthenticated, exactly like the other two targets' reset endpoints: a reset requiring an admin session would be unusable precisely when it is needed, i.e. after the search has demoted every administrator. ⚠️ It is used in **two distinct roles** that must not be conflated — once per run to establish a clean start (all arms, uncontroversial) and, only when `--statefulAuthzResetEndpoint` is passed, before *each* triple attempt (the ablation variable). |
| 5 | Tool invocation | `--endpointExclude "/api/kill,/api/restart"` | pyLoad's RPC surface exposes process lifecycle as ordinary endpoints. `kill` sets `_do_exit` and `restart` sets `_do_restart`, so the fuzzer terminates the system under test within the first minute — and pyLoad's self-restart leaves the webserver dead, so the container stays "up" while answering nothing. Observed directly: the first attempted run ended in `Failed to connect API with TCP`. | `endpointExclude` is a **stock EvoMaster option**, not something added for this thesis, and its documented purpose is exactly this. Only the two endpoints that terminate the process are excluded — verified by reading their implementations; the similarly-named `restart_file`, `restart_package`, `pause_server` and `stop_all_downloads` only affect downloads and are left in. |
| 6 | Tool invocation, **§5.2 arms only** | `--statefulAuthzTransition "POST /api/set_user_permission user=<victim> role=1 permission=0"` | This is the heaviest deviation on the list and the write-up must say so. It hands the tool the one thing it failed to infer on this target (§5): *which* action reduces a permission, and how to aim it at a victim. `role=1` demotes ADMIN→USER; `permission=0` additionally clears the whole `Perms` bitmask (`ADD`, `DELETE`, `STATUS`, `LIST`, `MODIFY`, `DOWNLOAD`, `SETTINGS`, `ACCOUNTS`, `LOGS`) — a maximal demotion. | It does **not** cancel out, and no detection rate may be quoted from an arm that uses it. It is **absent** from the pre-extension measurement in §5, which is the honest Tier-2b recall figure (0/5). Its legitimate use is narrower: with construction's one broken step supplied externally, §5.2 measures whether everything downstream of it works on third-party code. ⚠️ Because `permission=0` strips *every* permission, any permission-gated endpoint — not merely an admin-only one — becomes a legitimate guard under the §5.1 definition; that is sound but widens the guard set considerably, and must be stated before an examiner infers it. |

**The bug is third-party. The control, the specification and the reset fixture are ours; two
deviations are tool flags, not changes to pyLoad.** State it that way.

The boundary is sharper than the list makes it look, and it is checkable. In the **vulnerable**
variant the only patched files are `webui/app/config.py` (the CSRF line) and
`webui/app/blueprints/json_blueprint.py` (the reset route). The file holding the entire
authorization decision, `webui/app/helpers.py`, is **untouched upstream code** — it carries zero
`THESIS` markers in `pyload-vuln` and exactly two in `pyload-fixed`, which is the control:

    docker exec pyload-vuln  grep -c THESIS .../pyload/webui/app/helpers.py   # -> 0
    docker exec pyload-fixed grep -c THESIS .../pyload/webui/app/helpers.py   # -> 2

So the scaffolding is ours and the code under test is theirs. What the deviations buy is *reachability
and aim*, not the verdict.

## 4. Ground truth (verified by hand, over HTTP only)

`infra/pyload-cve/verify_ground_truth.sh`:

```
                       source / transition / follow-up
VULNERABLE (:8090)     200 / 200 / 200      alice role after transition: 1
FIXED      (:8091)     200 / 200 / 403      alice role after transition: 1
```

- **source** `POST /json/generate_apikey` — admin-only, a write, and **non-consuming**: each call
  mints a new key, so it is repeatable with identical parameters. (`/json/add_user` is unusable as
  the guard: repeating it answers 500 on the duplicate, not 200, so the bug would not show.)
- **transition** `POST /json/update_users` by `superadmin`, marking every *other* admin as admin;
  a user absent from that list is reduced to role USER.
- **follow-up** the same call, replaying alice's **pre-transition cookie**, with no re-login.

The role check after the transition is part of the script on purpose: without it, a PASS could be a
transition that silently did nothing.

`403` is what makes this target usable at all. The `/json/*` surface denies through
`login_required` → `403` (helpers.py:276). The `/api/*` surface answers an authorization failure
with **401** (api_blueprint.py:51), which §5.3 treats as INCONCLUSIVE — had only `/api/*` existed,
this target would have been unusable.

## 5. Pre-extension result: the tool does NOT find it, and why

Measured with the **frozen** builder — the exact build that produced the Tier-1 and Tier-2 numbers,
before any change was made to accommodate pyLoad. That ordering is the point: this arm records what
the tool does on a real bug it was never tuned against. Configuration and harness:
`infra/em-results/tier2b-trials/`.

Config held identical across both arms: `--useExperimentalOracles true`,
`--extraPhaseBudgetPercentage 0.6`, `--ratePerMinute 200`, `--maxTime 6m`, seeds 1–5, reseeded before
every run. (The budget is 6m rather than Tier-1/Tier-2's 150s because pyLoad answers more slowly and
the SECURITY phase timed out at 150s. It is the same on both arms, so the arms still pair.)

| Arm | Runs | Fault 970 | Transition found | Builder log lines | Endpoint coverage |
|---|---|---|---|---|---|
| `pyload-vuln` :8090 | 5 | **0/5** | 0/5 | 0 *(see ⚠️)* | 78–83% |
| `pyload-fixed` :8091 | 5 | **0/5** | 0/5 | 0 *(see ⚠️)* | 65–83% |

> ⚠️ **The "0 builder log lines" column proves nothing and must not be quoted as evidence.**
> EvoMaster's shipped `logback.xml` sets `<root level="warn">`, and every diagnostic the builder
> emits on this path is `log.debug`. A run that skipped construction and a run that never reached
> the builder at all are therefore *indistinguishable* in these logs — the column records the log
> configuration, not the tool's behaviour. Worse, the harness header pre-declared the expectation
> ("expect no builder log lines at all"), so the column was written down as confirmation of
> something it could not test. It is kept here only because deleting it would hide the mistake;
> the corrected diagnosis, measured with debug logging actually enabled, is §5.3.

Every run produced the identical fault set (`100 \| 101 \| 209`), so the miss is **deterministic**, not
seed-dependent luck.

**The endpoints were reached; they were never composed.** This is the same measurement that showed
the Şahin baseline cannot construct A1 on Tier-1, applied to ourselves. Counting per generated test
method (not per file) across the five vulnerable runs, in each run:

- **10** tests call the guard `POST /json/generate_apikey`
- **10** tests call the transition `POST /json/update_users`
- **0** tests call **both**, and **0** contain a `guard → transition → guard` sequence

So this is not a reachability failure — coverage is 78–83% and both endpoints are exercised roughly
ten times per run. The generator simply never puts them in one sequence with a replayed credential.

> ⚠️ Sample-size honesty: the 95% Wilson upper bound on 0/5 is **43%** (0/10 pooled: 28%). Five seeds
> per arm cannot by themselves establish "never detects". The claim rests on the **structural cause**
> read from `RestSecurityBuilder` below, which the empty builder log confirms directly; the seeds show
> the cause is not seed-dependent. Do not present the interval as the evidence.

The result is 0 detections. Reading `RestSecurityBuilder`, three candidate causes were identified —
**all three by code inspection, none of them measured at the time.** §5.3 later tested them directly
and only one survived intact:

1. **Transition vocabulary.** `looksLikePermissionReducingTransition` matches
   `TRANSITION_PATH_SIGNALS = role / permission / member / subscription / plan / owner / grant /
   access`. pyLoad's transition is `POST /json/update_users` — **none of the eight matches**.
2. **Transition idiom.** `setUserTargetToVictim` and `setRoleFieldToReduced` bind **named** path or
   body parameters, and `harvestReducedRoleValue` needs a role enum in the schema. pyLoad instead
   uses a **bulk desired-state** idiom: the body is `{"update_data": {...}}` whose *keys* carry the
   victim (`"alice|admin"`), and demotion is expressed by a key's **absence**. There is no user
   field and no role field to bind. This cause is *not* reachable by widening a keyword list.
3. **Source verb.** Construction considers only `PUT`/`PATCH` as the guarded source, on the
   reasoning that they are the non-consuming writes. pyLoad's `/json/*` surface is **RPC-style over
   POST and GET only** — not one PUT, PATCH or DELETE among 23 operations — so no source candidate
   is ever considered.

Causes 2 and 3 are construction-only. Cause 1 blocks **both** halves: the judgment handler calls the
same shared predicate, so it would reject `/json/update_users` too.

**Read cause 1 with its scope attached.** This arm was run against
`infra/pyload-cve/openapi-json-routes.json`, a hand-written spec covering the **20 `/json/*` routes
only**. `POST /api/set_user_permission` — pyLoad's own named-parameter role endpoint, the one the CVE
advisory points at — **is not in that spec at all**, so the only transition candidate on offer really
was `/json/update_users`, and cause 1 really did fire. What does *not* follow, and was wrongly implied
here, is that pyLoad as an application defeats transition inference: given a spec that includes its
`/api/*` surface, inference finds the transition immediately (§5.3).

> ⚠️ Do **not** write "the oracle would have caught it if only construction had built the triple."
> The by-hand verification in §4 establishes that **the system under test exhibits the relation** —
> a fact about pyLoad, not about our handler. With the frozen build, judgment is blocked as well.

### 5.1 An unplanned observation: the transition here is far more destructive than on the seeded targets

After the batch, the database was inspected directly. **Both** `alice` and `superadmin` had been
reduced to role USER, alongside roughly fifty junk accounts the fuzzer had created. Only pyLoad's own
`pyload` account was still an administrator — so an admin-only endpoint answered 403 to every account
the evaluation depends on.

The cause is in the idiom itself. `update_users` takes the **desired state of every user at once**,
and demotes anyone not explicitly marked as admin — so a single call with an incomplete body demotes
*everybody*. On Tier-1 and Tier-2 the transition is `PUT /users/{u}/role`, which can only reduce one
named user per call, and §6 of `CLAUDE.md` measures the damage that does to later triples. Here the
same number of transition calls destroys the entire account set at once.

This sharpens the §6 limitation rather than adding a new one: *the search destroys the preconditions
of its own temporal test*, and how fast it does so depends on the **blast radius of the transition
endpoint**, which is a property of the application, not of the fuzzer. It also means any Tier-2b arm
must reseed before every run — `seed_users.py` does, and the harness calls it.

### 5.2 With the transition declared: the rest of the pipeline does work on third-party code

The pre-extension arm above leaves one question open. Three causes were identified, but all three sit
in *transition handling* — so it could not be told whether the rest of construction (victim choice,
guard discovery, credential replay, VOID-and-retry, judgment) would work on an application we did not
write, or whether pyLoad would break it somewhere else too.

`--statefulAuthzTransition` answers that by supplying the one thing that could not be inferred:

    POST /api/set_user_permission user=<victim> role=1 permission=0

This is pyLoad's own endpoint — the one the CVE advisory names — and it is usable here precisely
because it has **named query parameters**, which the `/json/update_users` bulk idiom does not. Two
further changes were needed for a 105-operation surface, both gated on the declaration so that no
earlier measurement is affected: the attempt ceiling was raised from 8 to 40, and guard candidates
are ordered by how restricted they look. Full arm: `infra/em-results/tier2b-declared-trials/`,
5 seeds × {vulnerable, fixed} × {reset, no reset}.

> ⚠️ **"Everything else held identical" was claimed here and is false.** This arm also swapped the
> spec: §5 ran on the 20-route `openapi-json-routes.json`, this one on the 104-path
> `openapi-merged.json`. So the two arms differ in **two** variables — the declaration flag *and* the
> visible endpoint surface — and no clean causal claim can be attributed to the flag alone from this
> pair. It does not weaken what §5.2 actually claims (that the *downstream* pipeline works on
> third-party code, which the reset arms demonstrate directly); it does mean the pair cannot be used
> to argue that declaration was *necessary*. §5.3 is the arm that isolates that variable.

| Arm | 970 | Triples built | VOID attempts | Triple statuses |
|---|---|---|---|---|
| vulnerable, no reset | 0/5 | 0 | **138** | — (none ran) |
| **vulnerable, reset** | **5/5** | 5 | 0 | `200/200/200` |
| fixed, no reset | 0/5 | 0 | **138** | — (none ran) |
| **fixed, reset** | **0/5** | 5 | 0 | `200/200/403` |

Integrity check: **no run raised 970 without having assembled a triple.**

**What may be claimed, and what may not.**

- **May not:** a detection rate. The transition was declared, so this measures nothing about
  black-box recall. The honest recall figure for Tier-2b is the pre-extension **0/5** in §5.
- **May:** *given* the transition, everything downstream works on third-party code — victim and
  operator selection, guard discovery, same-credential replay and the judgment rule all ran unchanged
  and produced a correct verdict on both variants.
- **May, and this is the one accuracy number here:** **0 false positives on 5 fixed-target runs that
  each built a real triple.** Those are genuine opportunities to cry wolf; the no-reset arms are not,
  because they built no triple at all and so must not be counted as true negatives (§6 of `CLAUDE.md`).
  With n=5 the 95% Wilson upper bound is 43%, so this supports "no false positive was observed",
  not "the false-positive rate is low".

**State destruction is starker here than on either seeded target.** The reset moves detection from
**0/5 to 5/5**, where on Tier-1 it moved 80%→100% and on Tier-2 25%→65%. The difference is the blast
radius described in §5.1: `update_users` demotes every unlisted account at once, so without a reset
there is not merely a *shortage* of privileged operators but **none at all** — 138 attempts across
the five runs came back `200/401/200`, the transition itself refused. And the reset did not buy recall
with precision: the fixed arm built triples at exactly the same rate (5/5, zero VOID), i.e. the oracle
had just as many chances to be wrong, and was not wrong once.

**A worked example, hand-audited.** Seed 1's `test_56_post_on_status_stillAllowedAfterPermissionRevoked`
logs in `pyload` and `alice`, calls `POST /json/status` as `pyload` (200), has `alice` demote `pyload`
via `set_user_permission?user=pyload&permission=0&role=1` (200), then repeats `POST /json/status` with
**the same `cookies_pyload`** and asserts 200. Running that same sequence by hand against the fixed
variant gives 403 at the last step, with the database confirming `('pyload', 1, 0)`. So the guard holds
and this is a true positive, not the §5.1 false positive: `/json/status` requires the `LIST` permission,
and after `permission=0` the user has none.

> ⚠️ Note what the declaration does to the guard. Setting `permission=0` strips **all** permissions,
> not merely the admin role, so *every* permission-gated endpoint becomes a legitimate guard — which
> is why `/json/status` qualifies despite not being admin-only. The relation is not weakened by this
> (a removed permission is still removed), but a reader who expects the guard to be admin-only will
> ask, so state it before they do.

Note also that the tool did not follow the triple this target was designed around: it chose `pyload`
as the victim rather than `alice`, and `/json/status` as the guard rather than the admin-only
`/json/generate_apikey`. That is evidence the construction is doing its own search rather than
replaying a scripted scenario.

### 5.3 The corrected diagnosis: inference reaches the transition, and dies one step later

§5 read its causes off the source and was confirmed by a log column that could not have shown
anything (see the ⚠️ above). This section replaces that with a direct measurement.

**Method.** One run, deliberately minimal, changing only what had to change: the **frozen** jar
(`evomaster-frozen-769c16d.jar` — the build behind every published number, so nothing here is an
artefact of later edits), the **merged** spec so the `/api/*` surface is visible, **no**
`--statefulAuthzTransition` so inference is genuinely on trial, and a logback file that raises
`RestSecurityBuilder` and `RestSecurityOracle` to `DEBUG`. Seed 1, 6m, target :8090.

**Result — the entire builder output was one line:**

    DEBUG o.e.c.p.r.s.RestSecurityBuilder - Skipping stateful-authorization:
    no reduced role value in the schema vocabulary

Faults `[100, 201]`, no 970. Coverage 89/105 (85%), and `/api/set_user_permission` appears **67
times** in the generated tests.

**What this overturns.** The transition was **found**, by inference, unaided:
`POST /api/set_user_permission` matches `TRANSITION_PATH_SIGNALS` on *permission* and exposes a
`user` parameter, so `findPermissionReducingTransition` returns it. Construction then stops at the
**very next step** — `harvestReducedRoleValue`, which harvests low-privilege values out of the
schema's **enum** vocabulary, and pyLoad declares `role` as a plain `integer`. There is no enum, so
the function returns null and the whole phase is abandoned before a single request is composed.

So the pre-extension failure on pyLoad is **not** "a real app defeats keyword inference." It is a
**chain of three narrow blockers**, each independently fatal, each mechanical:

| | Blocker | Where | Status |
|---|---|---|---|
| **R1** | Reduced-role value harvested from **enum values only**; `role: integer` yields nothing | `harvestReducedRoleValue` | the one that actually fired |
| **R2** | Victim/role binding searches **path and body params only**; pyLoad puts both in the **query string** | `setUserTargetToVictim`, `setRoleFieldToReduced` | would have fired next |
| **R3** | Guarded source restricted to **PUT/PATCH**; pyLoad's surface is POST/GET | `sourceVerbs` | would have fired after that |

R2 is worth singling out, because it also explains why the declared arm (§5.2) worked at all:
`applyDeclaredBindings` binds over `allGenes(action)`, which covers **every** parameter including
query — while the two inference-side setters do not. The same job, written twice, one of them
narrower. That is a plain defect in the generator, not a property of pyLoad.

**Why this reframing matters for the write-up.** The §5/§6 story was "the generator encodes RESTful
assumptions a real app violates on three independent axes" — a genuine external-validity finding, but
it drew the line in the wrong place. What a real app violates is not the *concept* of the relation
nor the *inference of the transition*; it is three implementation assumptions about **how a schema
spells things** (enum-named roles, path-or-body parameters, PUT-shaped updates). Stated that way the
limitation is sharper, more honest, and — unlike the original framing — **actionable**, which is what
the extension in §5.4 acts on.

### 5.4 The extension: removing the three blockers, and one soundness change that pays for it

§5.3 turns the pyLoad miss into a short, concrete list, so it can be answered. Five changes, all in
`RestSecurityBuilder.kt`, made **after** every number in §5 and §5.2 was recorded and gated behind
the regression check (`infra/em-results/regression-check/`) before any existing figure may be
re-quoted from the new jar.

| | Change | Answers |
|---|---|---|
| **C1** | victim/role binding also matches **top-level query parameters** | R2 |
| **C2** | `harvestReducedRoleValue` → `harvestReducedRoleCandidates`: a ranked **list** of proposals, with numeric and string fallbacks when the schema names no roles | R1 |
| **C3** | `POST` admitted as a guarded source when **PUT/PATCH yield no guarded candidate** (fallback, not addition — see below) | R3 |
| **C4** | the **re-login probe** (below) | soundness cost of C1–C3 |
| **C5** | construction retries over operator × proposed value, distinguishing "value not accepted by the schema" from "transition rejected by the SUT" | makes C2 usable |

**C1 carries a trap worth recording.** Query parameters were excluded *deliberately*, and the
original comment says why: Tier-1's springdoc publishes the controller's internal `CurrentUser`
argument as a `caller` query parameter carrying nested `username`/`role` fields **that the
application ignores**. Binding a transition into `caller.role` would return 200 while demoting
nobody — a transition that never happened, recorded as one, which is precisely the FALSE POSITIVE
§5.3 of `metamorphic-authz-relations.md` exists to exclude. The fix is therefore narrower than
"allow query params": only a **top-level** query parameter is matched, never a field nested inside
one. A real RPC parameter is flat (`?user=x&role=1`); the springdoc artefact is not.

**C3 was first written as an addition, and the regression check forced it back to a fallback — which
is the clearest thing this gate has done so far.** Admitting POST *alongside* PUT/PATCH costs no
precision, and the measurement says so directly: 21 regression rows, **3 moved, 0 verdicts changed**.
But all three were Tier-1 *reset* arms, and they moved for a reason worth recording — `POST /reports`
became a second guarded endpoint, so the phase built a **second** valid triple (`201/200/403` on the
fixed target, `201/200/201` on the vulnerable one). On the fixed target those are strictly *more*
opportunities to raise a false alarm, and none was taken; the cost was that the recorded status
strings for those arms no longer reproduced. Preferring PUT/PATCH and reaching for POST only when
they yield **no guarded candidate at all** restores exact reproducibility on both seeded targets and
still serves the surface this exists for: pyLoad declares **zero** PUT/PATCH operations in either
spec (62 POST / 45 GET in the merged one), so it reaches the fallback either way. The archived
failing run is kept at `infra/em-results/regression-check/archive-2026-08-23-postAsAddition/`.

It is also the more faithful reading of the original rationale, which said POST should be admitted
because "excluding POST excludes every possible source" on an RPC API — i.e. as a last resort, which
is what a fallback is and what an addition is not.

**C4 is the reason C1–C3 do not simply trade precision for recall.** Each of the three heuristics
upstream *guesses* — which endpoint is a transition, which value is the lesser role, which action is
privilege-gated — and loosening all three at once widens every guess simultaneously. The probe makes
the SUT settle it: after the triple has run, the victim **logs in again** and re-attempts the same
guarded action with a **fresh** credential.

- fresh credential **denied (403)** ⇒ the privilege really is gone *and* this action really is gated
  by it ⇒ the premise holds
- fresh credential **allowed** ⇒ either nothing was taken away, or the action is gated by something
  else (ownership, say, not role) ⇒ VOID, no fault reported

It is **not circular**: the oracle asks what the *old* credential can still do, the probe asks what a
*new* one can do. On a vulnerable SUT those have different answers — which is the whole mechanism of
this bug class, privileges snapshotted into a credential at issue time, so a credential issued after
the transition always reflects current state on vulnerable and fixed targets alike.

Two properties keep it from disturbing the existing evaluation:

1. It runs **only when the follow-up was allowed** — the branch on which a fault would otherwise be
   raised. It can therefore only ever *withhold* a 970, never manufacture one, so it cannot create a
   false positive and cannot touch a triple that already passes.
2. It reads the **last action that actually ran**, not the guard by position. Black-box aborts a test
   at its first failing resource-creating call, and the slice usually opens with a privileged setup
   call; on a victim who really was demoted the probe is typically denied *there*, leaving the guard
   with no result at all. Insisting on a status for the guard would discard genuine detections —
   whereas being denied earlier in the same chain is if anything stronger evidence. *(This was found
   by review before measurement, not after: the first version of the probe had exactly that defect
   and would have taken Tier-1 from 16/20 to 0/20.)*

**Status.** Implemented and built. The 21-row regression check is the gate before any number in this
document or in `docs/results.md` is re-quoted from the new jar; the first pass against the
POST-as-addition build returned 18/21 with 0 verdict changes and produced the correction above, and
the fallback build is being re-checked. After that: re-measure Tier-2b with **inference** (no
`--statefulAuthzTransition`), which is the arm this whole extension exists to make possible.

## 6. What this establishes

The generator encodes **assumptions about how a schema spells things** — roles named by an enum,
target and role carried in path or body parameters, updates shaped as PUT/PATCH — and a real, widely
deployed application violates all three. Everything the evaluation says about recall on Tier-1 and
Tier-2 is therefore conditional on targets that share those conventions, and Tier-2b is the
measurement that shows the condition is not vacuous.

This is a negative result, and it is worth more than the positive one it replaced. The existing
limitation in the thesis — "a real downgrade endpoint with an off-vocabulary name is missed" — was
an argument from reading the code. It is now an observation on third-party code, and the true
picture is three times larger than the argument predicted.

**Two corrections to how this was first written up, both load-bearing** (see §5.3):

- The miss is **not** a failure of transition *inference*. Given pyLoad's own `/api/*` surface,
  inference identifies `POST /api/set_user_permission` unaided. The original write-up concluded
  otherwise from an arm whose spec did not contain that endpoint.
- The blockers are therefore **not** deep conceptual limits of the approach but three narrow
  implementation assumptions — which is a weaker claim about the world and a stronger one about the
  work, because it made them fixable (§5.4). The honest thesis sentence is that the *relation* and
  the *inference of the transition* generalised to third-party code on the first attempt, while the
  *parameter-binding conventions* did not.

## 7. Limitations of this target

- **No true positive on a non-self-seeded bug.** That remains open, and §5 explains why.
- The **control** is ours, so the differential is not fully third-party (§3, deviation 2).
- CSRF is disabled (§3, deviation 1). The honest framing is that the fuzzer could not reach the
  session-authenticated surface of stock pyLoad at all — which is itself a limitation of black-box
  fuzzing against CSRF-protected APIs, worth one sentence in the write-up.
- The seeded accounts give two administrators, which the relation requires (a victim and an
  operator). Stock pyLoad ships exactly one account.
