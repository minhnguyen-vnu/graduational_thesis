# Tier-1 Controlled Target — Build Specification

> **Audience:** an implementation agent (or engineer) who will build this app end-to-end.
> **Author of spec:** thesis working session, 2026-07-14.
> **Parent context:** graduation thesis extending EvoMaster with a *stateful authorization
> oracle*. This app is **Tier-1** in the evaluation plan (CLAUDE.md §4.4): a self-built app with a
> *planted, known-reachable* role-downgrade bug. It is the controlled ground truth — the one target
> where we are certain the bug exists and is reachable, so our future oracle has a guaranteed positive
> to detect and the baseline has a guaranteed miss.
>
> **Golden rule for the implementer:** build EXACTLY what is in this spec. Do not add features,
> endpoints, frameworks, or "hardening" beyond what is written. If something here is ambiguous, ask —
> do not invent. Scope is "acceptable and finishable," not exceptional.

---

## 0. TL;DR — what you are building

A minimal **Spring Boot 3 / Java 17** REST API called **`reports-api`** that:

1. Issues **JWT bearer tokens** on login, with the user's role baked into the token.
2. Exposes a small **Reports** CRUD where write/delete operations require the **ADMIN** role.
3. Exposes an **admin-only "change a user's role"** endpoint — this is the *permission-reducing
   transition*.
4. Contains **one deliberately planted bug (A1):** after a user is demoted ADMIN → VIEWER, the token
   they were issued *while they were an admin still works* for admin-only operations. It should return
   `403` but returns `2xx`.
5. Ships the bug behind a **config flag** so the same binary can run in **VULNERABLE** mode (default,
   bug present) or **PATCHED** mode (bug fixed). This one flag is what lets the thesis show "oracle
   fires on the vulnerable build, stays silent on the patched build" (i.e. true positive + no false
   positive).
6. Publishes an **OpenAPI 3 spec** at `/v3/api-docs` so EvoMaster can fuzz it black-box, and a
   **`/reset`** endpoint so state can be reseeded between fuzzing runs (this directly fixes the
   "state pollution" pain we already hit against VAmPI).

That's the whole app. Nothing else.

---

## 1. The business scenario (plain language)

A company has an internal **"Reports" service**. There are two kinds of people:

- **Admins** — can read reports **and** create, edit, and delete them.
- **Viewers** — can only read reports.

A person's role can change over time. In particular, an admin can be **demoted to viewer** (they
changed teams, left a project, were caught doing something they shouldn't). The security expectation
is obvious and non-negotiable:

> **The moment someone is demoted from admin to viewer, they must immediately lose the ability to
> create, edit, or delete reports.**

The planted bug breaks exactly this expectation. Because the user's role is written into their login
token, and the server trusts the token instead of re-checking the user's *current* role, a demoted
admin keeps full admin power until their old token expires. This is the real-world class of bug the
thesis targets (OWASP API Top 10 — broken function-level authorization, in its **stateful** form),
and it is invisible to any fuzzer that only checks authorization at a single frozen instant.

### 1.1 The one bug we plant — "A1: privilege persists after a role downgrade"

Concretely, the sequence that must misbehave:

```
1. alice logs in.                         → she is ADMIN, gets token T (role=ADMIN inside it)
2. alice deletes report #1 with token T.  → 204 No Content   (correct: she is admin)
3. alice's role is changed to VIEWER.      → 200 OK           (the permission-reducing transition)
4. alice deletes report #2 with token T.  → *** 204 No Content ***   ← THE BUG
                                             (should be 403 Forbidden: she is now a viewer)
```

In **PATCHED** mode, step 4 returns `403 Forbidden`. Same token, same request — only the config flag
differs.

> **We plant ONLY A1.** The plan mentions A2 (ownership transfer) and A3 (entitlement expiry) as
> "if time permits" — **do not build them.** The role model and the transition endpoint below leave
> room to add them later, but that is out of scope for this task.

---

## 2. The planted bug — exact mechanism (implementer must follow this)

The bug is **not** random; it has a specific, realistic root cause so it is defensible in the thesis.

**Root cause: the authorization check trusts the role claim inside the JWT and never re-reads the
user's current role from the data store.**

- On **login**, the server mints a JWT whose claims include `role = <the user's role at login time>`.
- On **every subsequent request**, an authentication filter decodes the JWT and, in the vulnerable
  path, takes the caller's role **straight from the token's `role` claim**.
- The **"change role"** endpoint updates only the user record in the data store. It has no way to
  reach back and rewrite tokens that were already issued.
- Therefore a token minted while `role=ADMIN` continues to assert `role=ADMIN` for its full lifetime,
  even after the data store says the user is now a `VIEWER`.

**The fix (PATCHED mode)** is a single behavioral change in the authorization filter: instead of
reading the role from the token, read the **username** (`sub`) from the token, then **look up that
user's current role in the data store** and authorize on that. After a demotion the store says
`VIEWER`, so admin-only routes return `403`.

### 2.1 The config flag

| Property | Default | Meaning |
|---|---|---|
| `app.security.stateful-role-check` | `false` | `false` = **VULNERABLE** (role read from JWT claim). `true` = **PATCHED** (role read from data store by username). |

Both modes must be reachable by flipping only this one property (via `application.yml` or
`-Dapp.security.stateful-role-check=true` / env var). No other code path may differ between modes.

### 2.2 Token lifetime (important — learned from VAmPI)

Against VAmPI we were bitten by a **60-second JWT expiry**: tokens died mid-fuzz-run and the tool kept
having to re-login. For this app, the token must comfortably outlive both a fuzzing run and the
grant→transition→re-attempt window.

| Property | Default | Meaning |
|---|---|---|
| `app.jwt.ttl-seconds` | `3600` | Token lifetime in seconds (1 hour). Long on purpose. |
| `app.jwt.secret` | (see §7) | HMAC-SHA256 signing secret. Read from config/env, **never** hard-coded in a committed file with a real value; ship a dev default in `application.yml` and document it. |

> **Why long expiry matters for the bug:** the whole point of A1 is that the *stale* token keeps
> working after the transition. If the token expired between steps 3 and 4, the demoted user would be
> forced to re-login and receive a fresh `role=VIEWER` token — which would hide the bug. A long TTL
> keeps the stale token alive so the bug is observable.

---

## 3. Technology choices (and why)

| Choice | Decision | Why |
|---|---|---|
| Language | **Java 17** | Author's day job; matches EvoMaster's bundled Corretto JDK 17; zero Kotlin. |
| Framework | **Spring Boot 3.3.x** | Standard, well-known, boots via `SpringApplication.run` (also what a future EvoMaster white-box driver will wrap). |
| Build | **Maven** | Ubiquitous; single `mvn package` produces a runnable fat jar. |
| Auth wiring | **A custom `OncePerRequestFilter`, NOT Spring Security** | We need *exact, explicit* control over the `401` vs `403` vs `404` ordering and over the vulnerable-vs-patched role lookup. Spring Security's defaults would obscure the bug and fight us on status-code ordering. A ~40-line filter we own is clearer and fully deterministic. |
| JWT library | **`io.jsonwebtoken:jjwt` 0.12.x** (`jjwt-api`, `jjwt-impl`, `jjwt-jackson`) | Mature, standard HS256 support. Confirm the current 0.12.x version at build time. |
| Persistence | **In-memory stores** (`ConcurrentHashMap` behind `UserStore` / `ReportStore` interfaces) | Fully deterministic; trivial to reseed via `/reset`; no DB to stand up. The authz bug is about roles-vs-tokens, not storage. (H2/JPA is explicitly **out of scope** — do not add it.) |
| API docs | **springdoc-openapi 2.6.x** (`springdoc-openapi-starter-webmvc-ui`) | Auto-publishes the OpenAPI 3 JSON at `/v3/api-docs`, which EvoMaster consumes as `--bbSwaggerUrl`. Confirm current 2.x version at build time. |

> Version numbers above are "latest known stable" as of this spec; the implementer should confirm the
> current 2.x (springdoc) / 0.12.x (jjwt) / 3.3.x (Spring Boot) releases when generating `pom.xml`
> rather than trusting these literally.

---

## 4. Domain model

### 4.1 Role
```
enum Role { ADMIN, VIEWER }
```

### 4.2 User
| Field | Type | Notes |
|---|---|---|
| `username` | String | unique id / primary key; also the JWT `sub` |
| `password` | String | plain text is acceptable here (this is a deliberately simple test target, not production) |
| `role` | Role | the user's **current** role in the store |

### 4.3 Report
| Field | Type | Notes |
|---|---|---|
| `id` | long | server-assigned, auto-increment starting at 1 |
| `title` | String | free text |
| `owner` | String | username of creator |
| `classification` | enum `{ PUBLIC, CONFIDENTIAL }` | free-form label; no special authz meaning (keep it simple) |

### 4.4 Seed data (created at startup and by `POST /reset`)

**Users:**

| username | password | role |
|---|---|---|
| `alice` | `alicepass` | `ADMIN` |
| `superadmin` | `superpass` | `ADMIN` |
| `bob` | `bobpass` | `VIEWER` |

- `alice` is the **demotion victim** used in the canonical A1 sequence.
- `superadmin` is a **stable admin** (never demoted) so that, if needed, roles can be promoted back
  and there is always at least one admin. Useful for reseeding logic and for future promote-back tests.
- `bob` is a plain viewer — the negative control (a genuine viewer must always get `403` on writes,
  in both modes; this is what proves the app's authorization works at all).

**Reports:** five seeded reports, ids `1..5`, titled `"Report 1" .. "Report 5"`, `owner = alice`,
classification alternating `PUBLIC` / `CONFIDENTIAL`. (Five so that a fuzzer/oracle always has a live
report to re-attempt a delete against even after some are deleted.)

---

## 5. Authorization rules (the contract every endpoint obeys)

Three outcomes, in this **strict order** — the ordering is part of the spec because the future oracle
depends on it:

1. **`401 Unauthorized`** — no token, malformed token, bad signature, or expired token. Checked
   **first**, before anything else.
2. **`403 Forbidden`** — token is valid but the caller's *effective role* is not allowed for this
   operation. Checked **second — BEFORE the resource is looked up.** So a viewer calling
   `DELETE /reports/999` (which does not exist) must get **`403`, not `404`.** This keeps "the demoted
   user must be denied" an unambiguous signal that never gets masked by a `404`.
3. **`404 Not Found`** — only reached by a caller who *passed* the authorization check, for a resource
   id that does not exist.

**"Effective role"** is where the bug lives:
- **VULNERABLE mode:** effective role = the `role` claim inside the JWT.
- **PATCHED mode:** effective role = the current role of `sub` looked up in `UserStore`.

Per-operation required role:

| Operation | Required effective role |
|---|---|
| login | (none — public) |
| read reports (`GET`) | any authenticated user (ADMIN or VIEWER) |
| create / edit / delete report (`POST` / `PUT` / `DELETE /reports/**`) | **ADMIN** |
| change a user's role (`PUT /users/{username}/role`) | **ADMIN** |
| who am I (`GET /users/me`) | any authenticated user |
| reset (`POST /reset`) | (none — public, so fuzzers can reseed freely) |

---

## 6. API reference (request / response, in full)

Base URL in local dev: `http://localhost:8080`. All request/response bodies are JSON
(`Content-Type: application/json`). Bearer token sent as `Authorization: Bearer <jwt>`.

A shared **error body** is used for all non-2xx responses:
```json
{ "error": "human readable message" }
```

---

### 6.1 `POST /auth/login` — obtain a token
Public.

**Request**
```json
{ "username": "alice", "password": "alicepass" }
```

**Response `200 OK`**
```json
{ "token": "<jwt>", "username": "alice", "role": "ADMIN" }
```
`role` here is the role at login time (also the value baked into the token).

**Response `401 Unauthorized`** — unknown username or wrong password
```json
{ "error": "invalid credentials" }
```

---

### 6.2 `GET /reports` — list reports
Any authenticated user.

**Response `200 OK`**
```json
[
  { "id": 1, "title": "Report 1", "owner": "alice", "classification": "PUBLIC" },
  { "id": 2, "title": "Report 2", "owner": "alice", "classification": "CONFIDENTIAL" }
]
```
**`401`** if not authenticated.

---

### 6.3 `GET /reports/{id}` — read one report
Any authenticated user.

**Response `200 OK`**
```json
{ "id": 1, "title": "Report 1", "owner": "alice", "classification": "PUBLIC" }
```
**`401`** if not authenticated. **`404`** `{ "error": "report not found" }` if id unknown.

---

### 6.4 `POST /reports` — create a report
**ADMIN only.**

**Request**
```json
{ "title": "Q3 revenue", "classification": "CONFIDENTIAL" }
```

**Response `201 Created`**
```json
{ "id": 6, "title": "Q3 revenue", "owner": "alice", "classification": "CONFIDENTIAL" }
```
`owner` = the caller's `sub`. `id` = next auto-increment.
**`401`** if not authenticated. **`403`** `{ "error": "admin role required" }` if effective role ≠ ADMIN.

---

### 6.5 `PUT /reports/{id}` — edit a report (non-destructive admin action)
**ADMIN only.**

**Request**
```json
{ "title": "Q3 revenue (final)", "classification": "CONFIDENTIAL" }
```

**Response `200 OK`** — the updated report.
**`401`** unauth. **`403`** if effective role ≠ ADMIN (checked **before** existence).
**`404`** if id unknown (only after passing authz).

> This endpoint exists as a **non-destructive** admin action the oracle can repeat safely: unlike
> DELETE, editing report #2 twice leaves #2 in place, so the grant→transition→re-attempt sequence can
> be replayed without exhausting the seed data.

---

### 6.6 `DELETE /reports/{id}` — delete a report (the canonical A1 action)
**ADMIN only.**

**Response `204 No Content`** — deleted.
**`401`** unauth.
**`403`** `{ "error": "admin role required" }` if effective role ≠ ADMIN — **checked before existence,
so a viewer deleting a non-existent id still gets `403`.**
**`404`** `{ "error": "report not found" }` only if the caller is an admin and the id is unknown.

> **This is the endpoint that exhibits the bug.** In VULNERABLE mode, a demoted alice using her old
> admin token gets `204`; in PATCHED mode she gets `403`.

---

### 6.7 `PUT /users/{username}/role` — change a user's role (THE TRANSITION)
**ADMIN only.**

**Request**
```json
{ "role": "VIEWER" }
```
`role` ∈ `{ ADMIN, VIEWER }`. Demoting = `VIEWER`; promoting = `ADMIN`. An admin may change **any**
user's role, **including their own** (self-demotion is allowed and is exactly what drives the
automated A1 sequence).

**Response `200 OK`**
```json
{ "username": "alice", "role": "VIEWER" }
```
**`401`** unauth. **`403`** `{ "error": "admin role required" }` if caller's effective role ≠ ADMIN.
**`404`** `{ "error": "user not found" }` if `username` unknown (after passing authz).
**`400`** `{ "error": "invalid role" }` if the body role is not one of the two enum values.

> **Why this is the "permission-reducing transition":** calling it with `{"role":"VIEWER"}` on an
> admin is precisely the state change our metamorphic oracle keys on. Note it changes only the
> **store**; it deliberately does **not** invalidate outstanding tokens — that omission *is* the bug in
> VULNERABLE mode, and is harmless in PATCHED mode because authorization re-reads the store anyway.

---

### 6.8 `GET /users/me` — who the server thinks you are
Any authenticated user.

**Response `200 OK`**
```json
{ "username": "alice", "role": "ADMIN" }
```
The `role` returned here follows the **same effective-role logic as authorization**: in VULNERABLE
mode it echoes the (possibly stale) token claim; in PATCHED mode it echoes the current store role.
This endpoint is a convenient, human-readable window onto the bug — after demotion, `GET /users/me`
still says `ADMIN` in vulnerable mode.

**`401`** if not authenticated.

---

### 6.9 `POST /reset` — reseed to initial state
Public (no auth), on purpose.

**Response `200 OK`**
```json
{ "status": "reset" }
```
Restores users and reports to the §4.4 seed (roles back to defaults, reports `1..5` recreated,
auto-increment counter reset to 6). Mirrors VAmPI's `/createdb`. **This is how every fuzzing run
starts from a clean, known state**, which is the fix for the state-pollution problem we saw against
VAmPI (where the fuzzer deleted its own login users mid-run).

---

## 7. Configuration (`application.yml`)

```yaml
server:
  port: 8080

app:
  security:
    stateful-role-check: false     # false = VULNERABLE (default). true = PATCHED.
  jwt:
    secret: "dev-only-change-me-please-32bytes-min"   # HS256 secret; override via APP_JWT_SECRET
    ttl-seconds: 3600                                   # 1h so tokens outlive a fuzz run

springdoc:
  api-docs:
    path: /v3/api-docs
```
- All three `app.*` values must be overridable via environment variables / `-D` system properties.
- The committed secret is an obvious dev placeholder; document that a real deployment would inject
  `APP_JWT_SECRET`. (For this test target, the dev default is fine to run with.)

---

## 8. Suggested project layout (many small files > few large files)

```
reports-api/
├── pom.xml
├── Dockerfile
├── README.md                         # how to build/run + the manual bug-demo curl sequence (§10)
└── src/
    ├── main/java/com/thesis/reportsapi/
    │   ├── ReportsApiApplication.java            # main(); SpringApplication.run
    │   ├── model/
    │   │   ├── Role.java
    │   │   ├── User.java
    │   │   └── Report.java
    │   ├── store/
    │   │   ├── UserStore.java                    # in-memory, seedable, reset()
    │   │   └── ReportStore.java                  # in-memory, auto-increment id, reset()
    │   ├── security/
    │   │   ├── JwtService.java                   # mint + parse HS256 tokens
    │   │   ├── AuthFilter.java                   # OncePerRequestFilter: 401 handling; sets CurrentUser
    │   │   ├── CurrentUser.java                  # request-scoped: username + effectiveRole()
    │   │   └── Authz.java                        # helper: requireAdmin() -> throws 403
    │   ├── web/
    │   │   ├── AuthController.java               # POST /auth/login
    │   │   ├── ReportController.java             # /reports CRUD
    │   │   ├── UserController.java               # PUT /users/{u}/role, GET /users/me
    │   │   ├── ResetController.java              # POST /reset
    │   │   └── ApiExceptionHandler.java          # maps exceptions -> {error} bodies + status codes
    │   └── dto/
    │       ├── LoginRequest.java / LoginResponse.java
    │       ├── ReportRequest.java / ReportResponse.java
    │       ├── RoleUpdateRequest.java / RoleResponse.java
    │       └── MeResponse.java / ErrorResponse.java
    └── test/java/com/thesis/reportsapi/
        ├── AuthzOrderingTest.java                # 401-before-403, 403-before-404 orderings
        ├── ViewerCannotWriteTest.java            # bob (real viewer) always 403 on writes (both modes)
        └── StatefulDowngradeBugTest.java         # THE key test — see §9
```

Keep files small and single-purpose (project rule: 200–400 lines typical, split anything larger).

---

## 9. Tests to include (write these; keep them focused)

Minimum meaningful tests — enough to *prove the planted bug exists and the flag toggles it*, not
exhaustive coverage:

1. **`StatefulDowngradeBugTest`** (the important one), run **twice** via the flag:
   - Login as `alice` → capture token `T`.
   - `DELETE /reports/1` with `T` → expect `204`.
   - `PUT /users/alice/role {VIEWER}` with `T` → expect `200`.
   - `DELETE /reports/2` with the **same** `T`:
     - with `app.security.stateful-role-check=false` (VULNERABLE) → **expect `204`** (documents the bug).
     - with `app.security.stateful-role-check=true` (PATCHED) → **expect `403`** (documents the fix).
   - Assert `GET /users/me` after demotion returns `ADMIN` in vulnerable mode, `VIEWER` in patched mode.

2. **`ViewerCannotWriteTest`** — `bob` (a genuine viewer) gets `403` on `POST/PUT/DELETE /reports/**`
   in **both** modes. (Proves the app's normal authorization works; the bug is *specifically* the
   stale-token case, not a blanket authz failure.)

3. **`AuthzOrderingTest`** — `401` with no/expired/garbage token; `403` before `404`
   (viewer deleting a non-existent id → `403`, not `404`).

> Do not chase the 80% coverage target with filler tests here; this is a deliberately tiny target app
> whose job is to *host a bug*, and the three tests above capture its entire contract.

---

## 10. After coding — infrastructure to start testing

Yes, there is a small setup step after the code is written, mirroring what we already did for VAmPI.
Do these in order.

### 10.1 Build & run locally
```bash
cd reports-api
mvn clean package
java -jar target/reports-api-*.jar          # starts on :8080 in VULNERABLE mode (default)
# patched build:
java -jar target/reports-api-*.jar --app.security.stateful-role-check=true
```

### 10.2 Sanity-check the OpenAPI spec is live (EvoMaster needs this)
```bash
curl -s http://localhost:8080/v3/api-docs | head -c 300     # must return OpenAPI 3 JSON
```

### 10.3 Manually confirm the planted bug (do this BEFORE any fuzzing)
This is the acceptance test for "the bug is real and reachable." Run against a fresh VULNERABLE
instance:
```bash
curl -s -XPOST localhost:8080/reset >/dev/null
T=$(curl -s -XPOST localhost:8080/auth/login \
      -H 'Content-Type: application/json' \
      -d '{"username":"alice","password":"alicepass"}' | jq -r .token)

curl -s -o /dev/null -w "delete#1 (admin):    %{http_code}\n" \
      -XDELETE localhost:8080/reports/1 -H "Authorization: Bearer $T"     # expect 204

curl -s -o /dev/null -w "demote alice:        %{http_code}\n" \
      -XPUT localhost:8080/users/alice/role -H "Authorization: Bearer $T" \
      -H 'Content-Type: application/json' -d '{"role":"VIEWER"}'          # expect 200

curl -s -o /dev/null -w "delete#2 (demoted):  %{http_code}\n" \
      -XDELETE localhost:8080/reports/2 -H "Authorization: Bearer $T"     # VULNERABLE: 204  ← BUG
```
Expected VULNERABLE output:
```
delete#1 (admin):    204
demote alice:        200
delete#2 (demoted):  204      <-- should have been 403; this is A1
```
Re-run the same three lines against a **PATCHED** instance → the last line must read `403`.

### 10.4 Dockerize (Tier-1 must be Docker-runnable, per eval plan §4.4)
`Dockerfile` (multi-stage, `eclipse-temurin:17`):
```dockerfile
# build stage: maven:3.9-eclipse-temurin-17 -> mvn package
# run stage:   eclipse-temurin:17-jre -> COPY jar -> ENTRYPOINT java -jar app.jar
# EXPOSE 8080
```
```bash
docker build -t reports-api:latest .
docker run -d --name reports-api -p 8080:8080 reports-api:latest                    # vulnerable
docker run -d --name reports-api-fixed -p 8081:8080 \
       -e APP_SECURITY_STATEFUL_ROLE_CHECK=true reports-api:latest                  # patched
```

### 10.5 Wire it into EvoMaster (black-box), reusing the VAmPI runbook (CLAUDE.md §7)
Create `infra/em-config/reports-auth.yaml` — same WFC shape as `infra/em-config/vampi-auth.yaml`, but:
- login endpoint `/auth/login`, verb `POST`, contentType `application/json`;
- token block: `extractFrom: body`, `extractSelector: /token` (this app returns `token`, **not**
  `auth_token` like VAmPI), `sendIn: header`, `sendName: Authorization`,
  `sendTemplate: "Bearer {token}"`;
- three users: `alice/alicepass`, `superadmin/superpass`, `bob/bobpass`.

Run (reseed first, exactly like VAmPI):
```bash
curl -s -XPOST http://localhost:8080/reset >/dev/null
infra/em-venv/bin/evomaster --blackBox true \
  --bbSwaggerUrl http://localhost:8080/v3/api-docs --bbTargetUrl http://localhost:8080 \
  --configPath infra/em-config/reports-auth.yaml \
  --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 5m \
  --outputFolder infra/em-results/reports-baseline
```

### 10.6 What to expect from the baseline run (this is the whole point)
The stock EvoMaster security oracles (F200–F210, including the authorization ones F204–F208) will
**find HTTP/schema faults but will NOT flag the A1 stateful-downgrade bug** — because they check
authorization at a single instant and never model the demotion transition. That silence, against a
target where §10.3 proves the bug is real and reachable, is the **documented gap** the thesis oracle
will later fill. Record the baseline `report.json` as evidence of the miss.

---

## 11. Definition of done

- [ ] App builds with `mvn clean package` and boots on `:8080`.
- [ ] All nine endpoints (§6) behave exactly as specified, including the **401→403→404 ordering** and
      **authorize-before-existence** on writes.
- [ ] `/v3/api-docs` serves a valid OpenAPI 3 document.
- [ ] The §10.3 curl sequence prints `204 / 200 / 204` in VULNERABLE mode and `204 / 200 / 403` in
      PATCHED mode — **toggled solely by `app.security.stateful-role-check`.**
- [ ] The three tests in §9 pass (with `StatefulDowngradeBugTest` asserting both modes).
- [ ] `POST /reset` restores the full §4.4 seed.
- [ ] `Dockerfile` builds and both vulnerable + patched containers run.
- [ ] `README.md` documents build/run and includes the §10.3 bug-demo sequence.
- [ ] **Nothing beyond this spec was added.**

---

## 12. Explicitly OUT of scope (do not build)

- A2 (ownership transfer) and A3 (entitlement expiry) scenarios.
- Any database / JPA / H2 / migrations.
- Spring Security, OAuth2, refresh tokens, token revocation lists, password hashing.
- User registration / signup, pagination, filtering, rate limiting, CORS config, HTTPS.
- Any UI beyond springdoc's auto Swagger page.
- The metamorphic oracle itself — **that is the thesis's separate deliverable, not part of this app.**
  This app only needs to *contain* the bug so the oracle has something to catch later.
```
