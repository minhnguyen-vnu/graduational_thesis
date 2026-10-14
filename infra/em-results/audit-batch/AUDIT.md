# Hand-audit of the Tier-1 / Tier-2 evaluation — 2026-09-01/02

Jar `evomaster-R-5bce137f.jar` (commit `007e5e09f9`). 160 runs, 8 arms × 20 seeds, flags copied
verbatim from `restore-remeasure/remeasure.sh` and `restore-reset-remeasure/reset_remeasure.sh`;
the **only** changed variable is that the generated tests are kept instead of `rm -rf`-ed.

Started 17:10:15, finished 08:00 the next morning. Data: `runs.csv`, `progress.log`, `logs/`,
`tests/`, `replay.csv`. Checker: `../audit970_seeded.py`.

---

## 1. Reproduction against the recorded batch

| Arm | This batch | `restore-*-remeasure/` | |
|---|---|---|---|
| tier1-vuln | 19 det / 19 triples | 19 / 19 | match |
| tier1-fixed | 0 det / 19 triples | 0 / 19 | match |
| tier1-vuln +reset | 20 det / 20 triples | 20 / 20 | match |
| tier1-fixed +reset | 0 det / 20 triples | 0 / 20 | match |
| tier2-ours-vuln | **6 det / 6 triples** | **7 / 7** | **one seed apart** |
| tier2-ours-fixed | 0 det / 7 triples | 0 / 7 | match |
| tier2-ours-vuln +reset | 13 det / 13 triples | 13 / 13 | match, **same 13 seeds** |
| tier2-ours-fixed +reset | 0 det / 13 triples | 0 / 13 | match |

Seven of eight arms reproduce exactly. The Tier-2 vulnerable no-reset arm differs on **seed 15
only**, the seed §6.1 already documents as unstable. Its log names the cause without inference:

    victim 'name1', operator 'admin',      codes 401/403/401
    victim 'name1', operator 'superadmin', codes 401/404/401
    victim 'name1', operator 'name2',      codes 401/403/401

`401` at the source means the login failed — `name1` had been **deleted** during the search. That is
the deletion mechanism of §6.2.2, the one the operator restore provably cannot repair.

**Report Tier-2 black-box recall as a range, 30–35% (6–7/20), not a point estimate.** Two independent
measurements on the same jar and config differ by one seed; a single figure overstates the precision
of the experiment.

The reset arm reproduced the **identical set of 13 seeds** (1 3 5 7 8 9 10 11 12 16 17 19 20), so the
seven non-detecting seeds are the six "no candidate pair in the archive" seeds of §6.1 plus seed 15.
Those six have now held across two builds and three independent measurements.

## 2. Structural audit of every firing

`audit970_seeded.py` reads the **emitted tests**, never the tool's log, and requires of each 970:
**A** source and follow-up carry the same credential variable · **B** no login call between them ·
**C** the transition is performed by a different credential · **D** statuses 2xx/2xx/2xx.

| | firings | PASS | FAIL | UNPARSED |
|---|---|---|---|---|
| **All 8 arms** | **58** | **58** | **0** | **0** |

### The checker is validated, not trusted

Five deliberately broken copies of a known-good test, each of which must flip exactly one check:

| Mutant | Expected | Result |
|---|---|---|
| untouched control | PASS | PASS |
| re-login injected between source and follow-up | fail **B** | FAIL(B) |
| transition performed by the victim's own credential | fail **C** | FAIL(C) |
| follow-up asserts 403 | fail **D** | FAIL(D) |
| transition call deleted | unparseable | UNPARSED |

⚠️ The first re-login mutant was **missed**, because it used a variable name (`res_relogin`) that
EvoMaster never emits, so the parser skipped it. Rewritten in the real `res_<n>` form it was caught.
**Re-run this validation whenever the parser changes** — the near-miss is the reason the check exists.

Path normalisation ignores a minus sign, so a negative id is not folded into `{id}`. Re-running the
whole audit with `/-?\d+` gives **58 / 0 / 0 / 57**, identical, so the defect is cosmetic. It is
conservative in any case: it can only make the checker miss a triple, never pass a bad one.

## 3. False-positive opportunity on the patched targets

The audit also scans the fixed arms for **silent triples** — the same structure with no 970 — so
"0 FP" is backed by demonstrated opportunity rather than by absence of evidence.

| Fixed arm | triples per `runs.csv` | verified in tests | 970 emitted |
|---|---|---|---|
| tier1-fixed | 19 | 19 | 0 |
| tier1-fixed +reset | 20 | **18** | 0 |
| tier2-ours-fixed | 7 | 7 | 0 |
| tier2-ours-fixed +reset | 13 | 13 | 0 |
| **total** | **59** | **57** | **0** |

On Tier-1 the two sides are structurally identical, cell for cell, differing only in the follow-up:

| | vulnerable | patched |
|---|---|---|
| 9× `PUT /reports/{id}`, victim alice, operator superadmin | 200/200/**200** → 970 | 200/200/**403** → silent |
| 9× `PUT /reports/{id}`, victim superadmin, operator alice | 200/200/**200** → 970 | 200/200/**403** → silent |
| 1× `PUT /reports/-1983371463` | 200/200/**200** → 970 | 200/200/**403** → silent |

⚠️ **Two of the 59 could not be verified from the tests** (tier1-fixed +reset, seeds 11 and 14). The
log records an assembled triple `200/200/403`, but no emitted test contains the three-step sequence:
**EvoMaster's minimizer drops a test that carries no fault and adds no coverage.** Those two
opportunities are attested only by the tool's own log — which is the very thing this audit exists not
to rely on. State the number as **57 verified in generated tests, 2 log-only**.

This cannot weaken the FP claim itself: minimization can never hide a 970, because carrying a fault is
precisely why a test is retained.

## 4. Replay from clean state — a claim that had never been measured

CLAUDE.md §6 said a *"reproducible failing test"* is emitted. Nobody had ever run one. All 58 were
replayed against a freshly reseeded SUT (`POST /reset`, `GET /createdb`) with pytest. See `replay.csv`.

| | replayed | PASS | FAIL |
|---|---|---|---|
| Tier-1 (both arms) | 39 | **39** | 0 |
| Tier-2 (both arms) | 19 | 17 | **2** |
| **total** | **58** | **56** | **2** |

The two failures are `t2-ours-vuln-seed5-r0` and `seed11-r0`, and both fail at the **transition**
step, `assert res_1.status_code == 200` → `403`. Neither fails at the follow-up.

**Cause, established rather than assumed.** Both use `name2` as the transition operator. `name2` is
seeded as a plain user; the seeded role endpoint is genuinely guarded (`if not is_caller_admin(resp):
403`, verified in `infra/vampi-seeded/api_views/users.py`). In the same run's `others_Test.py` the
same `auth_name2` gets `403 "Only Admins may change roles!"` on the same endpoint — and **no role
write anywhere in the emitted tests targets `name2`**. So the search had promoted `name2` to admin
through a call the minimizer discarded, and the emitted test depends on state it does not itself
establish. This is the §6.1 seed-15 phenomenon — state corruption that *manufactures* a precondition
— applied to the **operator** rather than the victim.

**What this does and does not touch.**
- The 970 verdicts stay correct. MR-A1 does not require the operator to be authorized, only that the
  permission is actually removed, and the test asserts `data.role == "user"` at the transition.
- The differential stays intact. A promotion is a real database write, so the patched variant, which
  re-reads the database, honours it identically — and indeed the patched arm built triples with
  `operator=name2` too.
- What must be narrowed is the wording: **"reproducible failing test" is measured at 56/58 (100% on
  Tier-1, 17/19 on Tier-2)**, not assumed at 100%.

## 5. What this audit does not establish

- It does **not** re-audit the recorded rows of `restore-remeasure/`. The search is wall-clock
  bounded, so a re-run is a fresh sample of the same configuration. Like `tier1-audit/` before it,
  this establishes that *this configuration* produces structurally genuine firings. Claim no more.
- It checks the same four conditions the handler checks, so it breaks the "trust the tool's log"
  circle but **not** the deeper "is this the right relation" question. That one is answered by
  argument plus the guard evidence, the C4 probe, and 0 FP over the matched triples — never by this.
- Tier-2b (pyLoad) is audited separately in `tier2b-inference-trials/AUDIT.md`.

## Reproduce

    infra/em-results/audit-batch/audit_batch.sh                       # 160 runs, ~15h
    python3 infra/em-results/audit970_seeded.py infra/em-results/audit-batch/tests/*
