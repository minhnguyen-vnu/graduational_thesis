# `infra/vampi-seeded/` — Tier-2 seeded benchmark target

A thesis fork of **VAmPI** carrying a planted **stateful/temporal authorization bug (A1)**: privilege
persists after a role downgrade, because authorization trusts a role claim snapshotted into an
already-issued JWT.

- **Upstream:** <https://github.com/erev0s/VAmPI> @ commit `f16052dce83f05847133ec98f01c5193a41de7d8`
  (vendored, not a submodule; upstream `.git` removed). Upstream licence: see `LICENSE`.
- **Design rationale, verification results, and the run matrix:** `docs/tier2-seeded-benchmark-plan.md`.
- **Every seeded line is marked `THESIS SEED`** in the source — `git`-less diffing against a fresh upstream
  clone is therefore unnecessary; grep for the marker.

## What was changed

| File | Change |
|---|---|
| `app.py` | `statefulrolecheck` env flag (0 = vulnerable, 1 = fixed) |
| `models/user_model.py` | `admin` claim added to the JWT payload; `set_role()`; `superadmin` seeded; deterministic starter-book titles |
| `api_views/users.py` | `is_caller_admin()` (the bug's single decision point); `set_user_role()` — the transition endpoint |
| `api_views/books.py` | `update_book_secret()` — the guarded, non-consuming admin-only write |
| `openapi_specs/openapi3.yml` | specs for the two new endpoints (role enum `['admin','user']`) |
| `Dockerfile` | `tokentimetolive` 60 → 3600; `statefulrolecheck=0` |

Note that the deterministic starter-book title is an **upstream bug fix, not part of the seed**: stock
`register_user()` picks `bookTitle<randrange(100)>` against a UNIQUE column, so `GET /createdb` returns
**500** at random — harmless in casual use, fatal to a 20-run measurement batch.

## Run

```bash
docker build -t vampi-seeded infra/vampi-seeded
docker run -d --name vampi-seeded       -p 5002:5000 vampi-seeded                        # VULNERABLE
docker run -d --name vampi-seeded-fixed -e statefulrolecheck=1 -p 5003:5000 vampi-seeded # FIXED

curl -s http://localhost:5002/createdb   # reseed before EVERY run
```

Users: `admin/pass1`, `superadmin/pass1` (both admin), `name1/pass1`, `name2/pass2` (non-admin).

## Ground truth (verify by hand before trusting a run)

`source → transition → follow-up with the SAME pre-transition token`:

| Target | Expected |
|---|---|
| :5002 VULNERABLE | `200 / 200 / 200` ← the bug |
| :5003 FIXED | `200 / 200 / 403` |

```bash
P=5002
curl -s localhost:$P/createdb >/dev/null
TOK=$(curl -s -X POST localhost:$P/users/v1/login -H 'Content-Type: application/json' \
      -d '{"username":"admin","password":"pass1"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["auth_token"])')
OP=$(curl -s -X POST localhost:$P/users/v1/login -H 'Content-Type: application/json' \
      -d '{"username":"superadmin","password":"pass1"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["auth_token"])')
curl -s -o /dev/null -w 'source=%{http_code}\n'     -X PUT localhost:$P/books/v1/bookTitle1/secret -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' -d '{"secret":"s1"}'
curl -s -o /dev/null -w 'transition=%{http_code}\n' -X PUT localhost:$P/users/v1/admin/role        -H "Authorization: Bearer $OP"  -H 'Content-Type: application/json' -d '{"role":"user"}'
curl -s -o /dev/null -w 'followup=%{http_code}\n'   -X PUT localhost:$P/books/v1/bookTitle1/secret -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' -d '{"secret":"s2"}'
```

## Run the oracle against it

```bash
curl -s http://localhost:5002/createdb >/dev/null
JAVA_HOME=$(/usr/libexec/java_home -v 17) java -jar ~/IdeaProjects/EvoMaster/core/target/evomaster.jar \
  --blackBox true --bbSwaggerUrl http://localhost:5002/openapi.json --bbTargetUrl http://localhost:5002 \
  --configPath infra/em-config/vampi-seeded-auth.yaml \
  --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
  --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 1 \
  --outputFolder infra/em-results/<run>
```

Verified at seed 1 (2026-08-06): **:5002 → fault 970** plus the failing test
`test_19_put_on_secret_stillAllowedAfterPermissionRevoked`; **:5003 → no 970**.

## Known caveat

The generator picked `superadmin` as the demotion **victim** and `admin` as the operator — the reverse of
the intended assignment. The triple is still valid (both are admins), but nothing reserves `superadmin` as
an undemotable operator, so the state-isolation hazard is mitigated only by the per-run reseed. A stranded
run is a false *negative*, never a false positive.
