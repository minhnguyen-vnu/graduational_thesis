# VOID — do not use these numbers

This Tier-2 batch (2026-08-07, 06:23–13:47) is **invalid** and is kept only as a record.

## What happened

The first overnight attempt was stopped with `pkill -f overnight.sh`, which killed the parent
but **not** its child `tier2_trials.sh`. That child was orphaned and kept running for ~4 hours
(visible in the retained mtimes: `tests/ours-vuln-seed10` 03:27, `seed17` 04:06, `seed20` 04:24 —
all after the run was believed dead).

At 06:23 a second batch started, wiped `runs.csv`, and began its `ours-*` arms while the orphan
was in its `base-*` arms. From then on **two processes fuzzed the same two containers
(:5002 / :5003) concurrently**, each calling `GET /createdb` to reseed under the other, on a SUT
that also exposes `DELETE /users/v1/{username}`.

## Evidence

- `progress.log` interleaves arms in wall-clock order (06:25:28 base-vuln → 06:29:18 ours-vuln →
  06:30:55 base-vuln → 06:35:00 ours-vuln …). A sequential script cannot produce this.
- 39 duplicate `(arm, seed)` pairs in the base arms; `base-fixed` has 40 rows for N=20.
- Only one `batch start` line, so the duplicates came from a second writer, not a restart.

## Why the numbers are not merely "noisy" but void

The reported `ours-vuln` detection of **5/20 (25%)** was measured while another fuzzer was
resetting the database and deleting users mid-run. Construction needs a stable victim, a stable
operator and a live guarded resource, so this figure is a **lower bound of unknown tightness**,
not a property of the generator. It must not be cited.

## Not affected

**Tier-1 is clean.** The orphan only touched ports 5002/5003; Tier-1 runs against 8080/8081.
Per-seed detection is identical to the pre-fix archive and wall-clock runtimes differ by only a
few seconds, so CPU contention was mild. Tier-1's 16/20 and 0/20 stand.

## Fix applied

`tier2_trials.sh` now takes a PID lockfile and refuses to start if another instance is alive, and
its signal trap kills only its own children (`pkill -P $$`) — `kill 0` would have taken out the
invoking `overnight.sh` on a normal exit.
