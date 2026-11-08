# Diagnosis: C5 abandons a victim one attempt too early, and loses the reset that would have revived it

**Status: FIXED 2026-08-24 by option B (§7), verified through the gate (§8). Kept as the record of
what the gate caught and why the fix is shaped the way it is.**
Measured 2026-08-24 00:00–02:25. Raw data: `infra/em-results/reproducibility/`.

## 1. What was observed

The 21-row regression check on the C1–C5 build reproduced 20 rows and failed one:
`tier2 ours-fixed-reset seed=3`, recorded as `200/200/403` with no fault 970, came back `NA` — no
triple built at all. Zero verdicts changed anywhere in the check, in either round.

Repeating that single row on both jars, **interleaved** so machine load and time-of-night hit both
equally:

| Jar | Correct (`200/200/403`) | Runs | Rate |
|---|---|---|---|
| frozen `769c16d` | 12 | 12 | **100%** |
| C1–C5 build | 3 | 15 | **20%** |

Fisher exact, one-sided: **p = 2.6 × 10⁻⁵**. The pre-registered reading rule ("p < 0.05 and the new
rate clearly lower ⇒ real regression ⇒ stop, do not change code") is therefore triggered.

## 2. The mechanism

Two logs from the same interleaved batch, same seed, same config
(`example-frozen-succeeds.log`, `example-new-fails.log`):

```
FROZEN                                                        NEW
1  victim superadmin, op admin   404/200/403  VOID            1  victim superadmin, op admin  404/200/403  VOID
2  victim superadmin, op name1   404/403/404  VOID            2  victim admin, op name1       200/403/200  VOID
3  victim superadmin, op name2   404/403/404  VOID            3  victim admin, op name2       200/403/200  VOID
4  victim admin, op SUPERADMIN   200/200/403  ASSEMBLED       -- no further candidates --
```

In attempt 1 the source is `404` (the book chosen from archive evidence no longer exists after the
reset), so the triple is VOID — **but the transition itself returned 200**, so `superadmin` is
recorded in `privilegeReducedInPhase` and is thereafter skipped as an operator.

That record is not permanent. `resetSutState()` clears it:

```kotlin
// The reset undid every demotion this phase performed, so the users we were skipping are
// privileged again. Not clearing this would keep discarding candidates the reset just revived.
if (status in 200..299) { privilegeReducedInPhase.clear() }
```

**But the reset runs at the START of the next attempt, inside `executeStatefulAuthzTriple`.** So the
record is cleared only if another attempt is actually made.

Frozen makes two more attempts on the same victim (operators `name1`, `name2`). Both are VOID and
both look wasteful — and both perform a reset, which clears `superadmin` from the set. By the time
frozen reaches victim `admin`, the operator list is unfiltered again, `superadmin` is available, and
attempt 4 succeeds.

C5 added an early exit that skips exactly those two attempts:

```kotlin
if (privilegeReducedInPhase.contains(victimAuth.name)) {
    return false    // the transition landed; the victim is spent
}
```

The reasoning is sound in isolation — a victim whose privilege is already gone cannot yield another
triple. What it missed is that those attempts were doing **a second job**: each one resets the SUT,
and the reset is what un-marks the operator. Skipping them leaves `superadmin` marked, so victim
`admin` is left with only `name1` and `name2`, neither of which can perform the transition (403), and
the run ends empty.

**In one line: the early exit saves two wasted attempts and loses the reset that those attempts were
implicitly buying.**

## 3. Why it stayed hidden until now

- It only bites when a reset endpoint is configured — with no reset there is nothing to lose.
- It only bites when the *first* victim's transition succeeds while the triple is VOID for some other
  reason (here: a `404` source, itself the archive-evidence-vs-reset-state mismatch already recorded
  as the seed-15 limitation in `CLAUDE.md` §6.1).
- The regression check samples 3 seeds per arm, and this row is the only one of the 21 that satisfies
  both conditions.

## 4. Two corrections to earlier statements in this investigation

1. **"`privilegeReducedInPhase` is not cleared by the reset — a pre-existing bug."** Wrong. It is
   cleared, identically in both builds. The bug is not a missing clear; it is that the clear is
   reached only via an attempt that C5 now skips.
2. **"Frozen reproduces, new does not, deterministically."** Also wrong as first stated — it was
   claimed from 3 runs. The new build succeeds 20% of the time, so a 2-run sample could and did
   mislead. The rate difference is real; "deterministic" was not.

Both are instances of the failure mode recorded in the `negative-result-hygiene` memory, made while
writing that memory.

## 5. What is NOT affected

- The 200 recorded runs of the Tier-1/Tier-2 evaluation. Untouched files, verified by mtime.
- Every verdict: across both regression rounds (42 row-checks) **no 970 outcome changed** — no
  detection was lost and no false positive appeared. The defect costs *construction opportunities*,
  never correctness of judgment.
- The frozen jar, which still reproduces 12/12.

## 6. Options for the fix (NOT applied)

| | Approach | Note |
|---|---|---|
| A | Delete the C5 early exit | Restores frozen behaviour exactly. Gives up the attempt-budget saving that motivated it |
| B | Call `resetSutState()` before building the operator list, instead of only inside an attempt | Addresses the cause rather than the symptom, and would also help the seed-15 case in §6.1 — candidates would be selected against the state the triple will actually run on |
| C | Clear the victim's own mark on the early exit | Smallest diff, but treats bookkeeping as the problem when the real issue is *when* the reset happens |

**B is the most principled**, but it changes the reset cadence, so the reset arms would need
re-measuring. A is the safe minimum.

Whichever is chosen, the gate is unchanged: rebuild → 21-row regression check → and for this row
specifically, repeat it interleaved against the frozen jar, because one run of it proves nothing.

### Correction to this table

B is described above as "would also help the seed-15 case in §6.1". **That is overstated.**
Seed 15 fails because the *archive evidence* is stale — the search had promoted victim `name1` to
admin, and the reset returns it to a plain user, so the source the archive says was `200` comes back
`403`. No reset repairs the archive; only re-validating candidate evidence live after a reset can,
which is a larger change and remains future work (`CLAUDE.md` §9 item 4). What B actually fixes is
narrower: the *in-phase bookkeeping* is made consistent with the reset. That is the cause of this
defect, but it is not the §6.1 limitation.

## 7. Chosen fix: B, applied 2026-08-24

One hunk in `RestSecurityBuilder.buildStatefulAuthzTriple`, immediately after the `NoAuth` check and
**before** both the victim check and the operator list:

```kotlin
resetSutState()
```

Placement matters twice over. Before the *victim* check, so a victim this phase demoted is revived
rather than skipped. Before the *operator* list, so the user that performed the last transition is
available again. And it is a real call rather than the cheaper shortcut of "the next attempt will
reset anyway, so ignore the set": `privilegeReducedInPhase.clear()` is gated on a 2xx from the reset
endpoint, so performing the reset here means a *failed* reset correctly falls back to conservative
filtering, whereas assuming one would select candidates on a premise that never held.

Inert on the no-reset path by construction — `resetSutState()` returns at `spec.isBlank()` — so every
§6 headline number is untouched by this change. Cost on the reset path: one extra idempotent reset per
victim candidate actually tried. Read off the recorded runs, that is +1 call on Tier-1 (all 40 reset
runs made exactly 1 reset, 1 assembled, 0 void) and a handful at worst on Tier-2 (22/40 runs made 1
reset; the worst made 7), against a ~330 s run.

### Why the second candidate hunk was rejected

C5's early exit (`return false` once the transition has landed) was also going to be made conditional
on a reset endpoint being configured, so the reset arms would try the next operator the way the
frozen build did. **Analysis says that is wrong, so it was not applied.**

After a transition that landed, the triple can only be VOID because the source was not 2xx or the
follow-up was 401. Both depend on the victim slice and on SUT state — **neither depends on the
operator**. A different operator therefore cannot rescue that triple. The frozen build's attempts 2
and 3 in §2 are the evidence: both came back `404/403/404`, the source `404` again, exactly as
operator-independence predicts. Their only contribution was the side-effect reset, and hunk 1 now
supplies that directly. Re-adding the retry would have re-added provably useless attempts, spending
budget that matters on a 105-endpoint target such as pyLoad.

### Residual case, deliberately not coded

`privilegeReducedInPhase.add()` fires on any transition that returns 2xx, whether or not it actually
*reduced* privilege. A value drawn from the schema vocabulary that raises the role instead (the
`enumVocab - lowPrivEnum` tail of the C2 candidate list) would mark the victim spent and skip the
remaining values, one of which might be the genuinely lower role. C2 orders low-privilege values
first, so this is unlikely rather than impossible, and no instance has been measured. Recorded rather
than fixed: it is a construction miss (a false negative), never a false positive, and the re-login
probe already refuses to report a fault on such an attempt.

## 8. Gate for the fix

`infra/em-results/gate-B.sh`, run 2026-08-24 07:26–10:50. Phase 1 was 8 interleaved frozen-vs-B pairs on
the row that exposed the defect, with the reading rule fixed before the first run (`new >= frozen - 1`
⇒ proceed). Phase 2 was the 21-row regression check, gated on phase 1. Round 2's evidence is preserved
under `regression-check/archive-2026-08-23-round2-c5defect/`.

**Phase 1 — passed.** frozen **8/8**, option B **8/8**. Against the defective build's 3/15 on the same row:
Fisher one-sided **p = 3.4 × 10⁻⁴**. Against frozen's 12/12: no deficit at all.

**Phase 2 — passed.** **21/21 reproduced, 0 mismatches**, including `tier2 ours-fixed-reset seed=3`, the row
that had failed. Data: `infra/em-results/reproducibility/verify-B/result.log` and
`regression-check/progress.log`. Jar preserved as `EvoMaster/evomaster-B-06c70147.jar`.

**A confirmation that was not part of the criterion.** On that row B logs `resets=4, void=1` where frozen
logs `resets=4, void=3`, run after run. That is the diagnosed trace exactly: victim `superadmin` costs one
VOID attempt, then the reset at the top of the next `buildStatefulAuthzTriple` revives `superadmin` as
operator and victim `admin` assembles — 2 victims × (1 selection reset + 1 attempt reset) = 4 resets, 1 VOID.
Frozen reaches the same verdict only via two extra useless attempts. This was **not** pre-registered, so it
is corroboration of the mechanism, not evidence for it; the pre-registered criterion was the pass rate alone.
Note also that B varies run to run like everything else here (one pair came back `resets=2, void=0`) — the
variation is within the correct verdict, not between correct and wrong.
