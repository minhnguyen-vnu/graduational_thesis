# reports-api — Tier-1 controlled target

A minimal **Spring Boot 3 / Java 17** REST API with **one deliberately planted authorization bug
(A1): privilege persists after a role downgrade.** It is the controlled ground-truth target for a
thesis extending EvoMaster with a stateful authorization oracle. See `app-detail.md` for the full
build specification.

## The planted bug (A1) in one sentence

The user's role is baked into their JWT at login; in **VULNERABLE** mode the authorization filter
trusts that stale claim, so a demoted admin keeps admin power until the token expires. In **PATCHED**
mode the filter re-reads the user's *current* role from the store, so a demoted admin is immediately
denied.

The two modes are the **same binary**, toggled by a single flag:

| Property | Default | Meaning |
|---|---|---|
| `app.security.stateful-role-check` | `false` | `false` = VULNERABLE (role from JWT claim), `true` = PATCHED (role from store) |
| `app.jwt.ttl-seconds` | `3600` | token lifetime (1h, long on purpose so stale tokens stay alive) |
| `app.jwt.secret` | dev placeholder | HS256 secret; override with `APP_JWT_SECRET` in real deployments |

## Build & run

```bash
./mvnw clean package
java -jar target/reports-api-*.jar                                   # VULNERABLE (default), :8080
java -jar target/reports-api-*.jar --app.security.stateful-role-check=true   # PATCHED
```

OpenAPI 3 spec (consumed by EvoMaster as `--bbSwaggerUrl`):

```bash
curl -s http://localhost:8080/v3/api-docs | head -c 300     # OpenAPI 3 JSON
```

## Endpoints

| Method | Path | Auth |
|---|---|---|
| `POST` | `/auth/login` | public |
| `GET` | `/reports`, `/reports/{id}` | any authenticated |
| `POST` / `PUT` / `DELETE` | `/reports`, `/reports/{id}` | ADMIN |
| `PUT` | `/users/{username}/role` | ADMIN (the permission-reducing transition) |
| `GET` | `/users/me` | any authenticated |
| `POST` | `/reset` | public (reseeds to the initial state) |

Status ordering is **401 → 400 → 403 → 404**. Writes authorize before existence: a demoted user
deleting a missing id gets `403`. Body validation runs before authorization: a viewer sending an invalid
body gets `400`, a valid body `403`.

### Spec and validation (cleanup of 2026-09-10)

- `CurrentUser` is hidden from springdoc (`web/OpenApiConfig.java`), so no operation publishes a `caller` param.
- `RoleUpdateRequest.role` declares `enum: ["ADMIN","VIEWER"]` and stays a `String`, so an unknown value
  returns `400 {"error":"invalid role"}`.
- Every operation declares the statuses it returns; error bodies are `ErrorResponse`; none declares 500.
  Login `200/400/401`; `/reset` `200`; `GET /reports` `200/401`; `POST /reports` `201/400/401/403`;
  `GET|PUT|DELETE /reports/{id}` add `400/404`; `/users/me` `200/401`; `PUT /users/{u}/role` `200/400/401/403/404`.
- Input is validated with `@Valid`: `POST /reports {}` and `POST /auth/login {"password":"x"}` return 400.
  `ApiExceptionHandler` maps validation, type-mismatch and unreadable-body failures to `{"error":…}`.
- Reduced-role inference depends on the declared enum: `stringRoleCandidates` is lowercase-only and
  `UserController.parseRole` uses `Role.valueOf`, so `VIEWER` is the only reduced value the server accepts.

### Seed data (startup and `POST /reset`)

- Users: `alice/alicepass` (ADMIN, demotion victim), `superadmin/superpass` (ADMIN, stable),
  `bob/bobpass` (VIEWER, negative control).
- Reports: ids `1..5`, owner `alice`, classification alternating `PUBLIC`/`CONFIDENTIAL`;
  next id is `6`.

## Manual bug-demo (the acceptance test)

Run against a fresh **VULNERABLE** instance:

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
      -XDELETE localhost:8080/reports/2 -H "Authorization: Bearer $T"     # VULNERABLE: 204  <- BUG
```

Expected VULNERABLE output — the last line is bug A1:

```
delete#1 (admin):    204
demote alice:        200
delete#2 (demoted):  204      <-- should have been 403
```

Re-run the same three requests against a **PATCHED** instance (`--app.security.stateful-role-check=true`)
→ the last line reads `403`.

## Docker

```bash
docker build -t reports-api:latest .
docker run -d --name reports-api       -p 8080:8080 reports-api:latest                          # vulnerable
docker run -d --name reports-api-fixed -p 8081:8080 \
       -e APP_SECURITY_STATEFUL_ROLE_CHECK=true reports-api:latest                              # patched
```

## Tests

```bash
./mvnw test
```

- `StatefulDowngradeBugTest` — the A1 sequence, asserting `204` (vulnerable) and `403` (patched).
- `ViewerCannotWriteTest` — a genuine viewer (`bob`) is always `403` on writes, in both modes.
- `AuthzOrderingTest` — `401` (no/garbage/expired token) and `403`-before-`404` ordering.
- `InputValidationTest` — invalid input returns 400, never 500; lowercase `viewer` is rejected.
- `OpenApiContractTest` — no `caller` param, the role enum, the exact declared statuses per operation.

28 tests, `mvn test` green (2026-09-10).
