# Hand measurement: can the triple's precondition be rebuilt through the target's own API?

**Measured 2026-08-24, before any code was written.** Script and captured output:
`infra/pyload-cve/measure_self_provisioning.sh` / `.out`. The chains on `reports-api` and
`vampi-seeded` were run interactively the same day; the script covers pyLoad, which is the target
the decision turns on.

## 1. The question

`CLAUDE.md` §6/§6.1 record that the search destroys the preconditions of its own temporal test, and
§6.1 proves that causally with a reset endpoint. But every reset endpoint in the evaluation is a
**deviation**: `reports-api`'s `/reset` is ours because we wrote the app, and pyLoad's
`/thesis/reset` is injected (declared deviation 4). Only VAmPI's `/createdb` is upstream's own.

So: **can the tool rebuild what it needs using only the API surface the target already publishes?**
If yes, the reset hook leaves the critical path, and the sharpest objection to the Tier-2b result
— *"your tool only works because you gave the app a reset endpoint"* — loses its force.

## 2. What the failure actually is — and the correction it forced

The mechanism was assumed to be the one measured on the seeded targets: the search **demotes the
victim**, the guarded source comes back 403, and black-box aborts the test before the transition is
even sent. The proposed fix was therefore "promote the victim back".

**On pyLoad that is wrong.** Every VOID attempt in the recorded no-reset arms carries one signature:

```
$ grep -h "Discarded a VOID" logs/vuln-noreset-seed*.log | grep -o "codes [0-9/-]*" | sort | uniq -c
  40 codes 200/401/200          # identical on the fixed arm: 40 codes 200/401/200
```

Source **200** — the victim `pyload` kept its privilege throughout. Transition **401** — the
*operators* (`alice`, `superadmin`) had been demoted by the search, and pyLoad's `/api/*` surface
answers a non-admin session with 401. Only two pairs were ever tried, 20 attempts each:
`victim=pyload, operator=alice` and `victim=pyload, operator=superadmin`.

**The failure is in the OPERATOR, not the victim — the mirror image of Tier-1/Tier-2.** Any fix aimed
only at the victim would not have moved pyLoad at all.

## 3. Results

`POST /api/set_user_permission` accepts an **upward** value (`role=0` = admin), verified against the
database, not just by status code.

**A — restore the victim** (the Tier-1/Tier-2 mechanism). Demote alice, confirm the dead end (fresh
login → source **403**), promote her back, then run the triple:

| Variant | Triple |
|---|---|
| vulnerable :8090 | **200 / 200 / 200** |
| fixed :8091 | **200 / 200 / 403** |

**B — restore the operator** (pyLoad's real mechanism). The corrupted state is reproduced first and
**reproduces the recorded signature exactly** — `200/401/200` on both variants — so the simulation is
shown to be faithful before the rescue is applied. The surviving admin `pyload` then promotes the
operator `alice`, and the triple runs:

| Variant | Reproduced failure | After rescue |
|---|---|---|
| vulnerable :8090 | 200/401/200 | **200 / 200 / 200** |
| fixed :8091 | 200/401/200 | **200 / 200 / 403** |

**No `/thesis/reset` call anywhere in either part.**

**C — two further findings.**
- `POST /api/add_user?...&role=0` lets an admin create a **brand-new admin**, and that account passes
  the guarded source immediately (200). A second provisioning route that repairs no existing account.
- **The ceiling:** with every admin demoted, a fresh login can no longer promote anyone — **401**.

## 4. What this establishes, and what it does not

1. **The precondition is rebuildable through the published API on all three targets.** Verified by
   hand on each, before writing code.
2. **The rescue does not depend on the bug under test.** It uses a **freshly issued** credential, and
   it works **identically on the patched variant**. This was the validity hazard worth pre-empting: a
   rescue that only worked through stale-session privilege would succeed more often on the vulnerable
   arm than the fixed one, and would silently weaken the false-positive claim by building fewer
   triples on the fixed side. It does not.
3. **One primitive, two trigger points.** *Call the transition endpoint upward on user X, using any
   credential that currently still holds the privilege.* Triggered by a 403 source (restore the
   victim) or by a 401/403 transition (restore the operator).
4. **It raises recall; it does not guarantee it.** At least one credential must still be privileged.
   On pyLoad `pyload` survived — and the runs prove it, since its source was 2xx in all 40 attempts —
   but nothing made that inevitable. When no privileged credential remains, the run is barren exactly
   as before: **a false negative, never a false positive.**
5. **It is not a measurement of the tool.** These are hand-issued HTTP calls establishing that a path
   exists. Whether construction can find that path unaided is what an implementation would have to
   show, under the usual gate.
