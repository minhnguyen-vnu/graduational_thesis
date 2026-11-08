# pyLoad CVE-2026-41133: a real, third-party stateful-authorization bug

> Numbers: `docs/results.md` §1, §4 (jar M2). The other target with a bug we did not write:
> `docs/artifact-keeper-target.md`.
>
> Setup facts: `/api/*` answers an authorization failure with **401** (INCONCLUSIVE), `/json/*` with **403**, so
> guard endpoints come from `/json/*`. Runs use `infra/pyload-cve/openapi-merged.json` (104 paths, 107 operations)
> and `infra/em-config/pyload-auth.yaml`. The hand ground truth (`verify_ground_truth.sh`) uses guard
> `POST /json/generate_apikey` and transition `POST /json/update_users`; the tool infers
> `POST /api/set_user_permission`.

## 1. Why this target exists

`reports-api` and `vampi-seeded` carry a bug we planted, so a reader can say the tool finds the bug it was built
around. pyLoad answers that with a real third-party bug that has a CVE. The vulnerable code is upstream; the fixed
variant, the reseed endpoint and the `/json/*` spec are ours (§3).

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
(`docs/results.md` §4).
Between runs they are restored over HTTP by the injected `/thesis/reset` endpoint (deviation 4).

**Five** deviations from a plain out-of-the-box run. Each must be stated in the write-up; none of
them creates, hides, or moves the bug. They are not of one kind, and the write-up must not blur
them together — the **Where** column is the distinction that matters. Deviations 1–4 change the
system under test or its specification; 5 only changes how the tool is invoked.

| # | Where | Deviation | Why it is needed | Why it does not affect the result |
|---|---|---|---|---|
| 1 | SUT, **both** variants | `WTF_CSRF_METHODS = []` added to `BaseConfig` | The vulnerable path is session-authenticated and CSRF-guarded, so a non-browser client cannot reach it at all. `csrf.protect()` ignores `WTF_CSRF_ENABLED` (that flag is only read inside CSRFProtect's `before_request` hook) but does return early when the method is absent from `WTF_CSRF_METHODS`. | Anti-forgery is orthogonal to authorization, and it is applied to **both** variants, so it cancels out of the differential. The same endpoints are already reachable CSRF-free through the `X-API-Key` scheme. |
| 2 | SUT, **fixed only** | The fixed variant is a control **we wrote** | Upstream published no working fix (see §2), so there is no patched build to diff against. | The patch is not invented: it applies to the session branches exactly the fresh-database read that the `X-API-Key` branch of `apikey_auth()` already performs. It is applied to *both* authorization paths (`parse_permissions` and `apikey_auth`) so the control does not depend on which surface a request uses. |
| 3 | Input (not the SUT) | The OpenAPI specification for `/json/*` is hand-written | pyLoad generates a specification for its `/api/*` RPC surface only; `/json/*` is real, authenticated and undocumented. | A specification is an **input** to black-box fuzzing, not part of the system under test. To avoid spoon-feeding, `infra/pyload-cve/openapi-json-routes.json` describes **all 20 routes / 23 operations**, not only the three the triple needs; a script cross-checks it against the blueprint in both directions. The `/api/*` half of the merged document is pyLoad's own generated specification, unmodified — 84 of the 104 merged paths. |
| 4 | SUT, **both** variants | `POST\|GET /thesis/reset` injected into `json_blueprint.py` | Each run starts from a clean account state, and stock pyLoad has no HTTP endpoint that restores it. The two seeded targets have one — `reports-api`'s `POST /reset` (ours) and VAmPI's `GET /createdb` (**upstream VAmPI's own**). | It writes to the `users` table only and contains no authorization logic, so it cannot change any verdict; it is present in **both** variants, so it cancels out of the differential. It is unauthenticated, like the other two targets' reseed endpoints: a reseed requiring an admin session would be unusable after the search has demoted every administrator. It is called once before each run. |
| 5 | Tool invocation | `--endpointExclude "/api/kill,/api/restart"` | pyLoad's RPC surface exposes process lifecycle as ordinary endpoints. `kill` sets `_do_exit` and `restart` sets `_do_restart`, so the fuzzer terminates the system under test within the first minute — and pyLoad's self-restart leaves the webserver dead, so the container stays "up" while answering nothing. Observed directly: the first attempted run ended in `Failed to connect API with TCP`. | `endpointExclude` is a **stock EvoMaster option**, not something added for this thesis, and its documented purpose is exactly this. Only the two endpoints that terminate the process are excluded — verified by reading their implementations; the similarly-named `restart_file`, `restart_package`, `pause_server` and `stop_all_downloads` only affect downloads and are left in. |

**The bug is third-party. The control, the specification and the reseed fixture are ours; one
deviation is a tool flag.** State it that way.

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
with **401** (api_blueprint.py:51), which the oracle treats as INCONCLUSIVE (`CLAUDE.md` §3) — had only `/api/*` existed,
this target would have been unusable.

## 5. Result

Numbers: `docs/results.md` §1, §4 (jar M2). The builder before the changes below missed this bug. Five builder changes
let the tool find it: role and victim binding on query parameters, ranked role values with numeric fallbacks, POST as
a fallback source, the C4 re-login probe, and retries over operator and value. They were written while running this
target, so pyLoad is a development target, like artifact-keeper. The full record of that work, with numbers from
earlier jars: `docs/archive/pyload-journal-pre-M2.md`.

## 6. Limitations of this target

- The **control** is ours, so the differential is not fully third-party (§3, deviation 2).
- CSRF is disabled (§3, deviation 1). The honest framing is that the fuzzer could not reach the
  session-authenticated surface of stock pyLoad at all — which is itself a limitation of black-box
  fuzzing against CSRF-protected APIs, worth one sentence in the write-up.
- The seeded accounts give two administrators, which the relation requires (a victim and an
  operator). Stock pyLoad ships exactly one account.
