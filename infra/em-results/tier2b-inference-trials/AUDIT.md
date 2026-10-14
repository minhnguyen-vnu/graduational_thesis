# Hand-audit of the Tier-2b (pyLoad) firings

`audit970.py <glob-of-output-dirs>` reads the **generated Python tests**, not the status strings the
harness scraped, and checks the four things CLAUDE.md §5.2 requires of an MR-A1 triple:

| | check |
|---|---|
| A | source and follow-up carry the **same** credential variable |
| B | **no `/login`** between them — the stale-credential replay is the entire point |
| C | the transition is performed by a **different** credential |
| D | statuses are 2xx / 2xx / 2xx — a fault, not a pass and not a VOID |

Anything it cannot parse is reported as `UNPARSED`, never silently skipped.

## Instrument validation (do not delete this section)

A checker that only ever prints PASS proves nothing, so it was run against three deliberately broken
copies of `vuln-reset-seed1`. Each mutation flipped **exactly one** test to FAIL and left the other
seven PASS:

| mutation | what it breaks | result |
|---|---|---|
| a `/login` inserted between source and follow-up | B — replay premise | FAIL 1 / PASS 7 |
| follow-up assertion changed to `403` | D — it is then a correct denial | FAIL 1 / PASS 7 |
| transition performed with the victim's own cookie | C — no third party demoted anyone | FAIL 1 / PASS 7 |

## Result — arm `vuln-reset`, 5 seeds

**36 tests carry fault 970; 36/36 PASS all four checks, 0 UNPARSED.**

- victim → operator: `pyload` → `alice` in all 36
- transition: `POST /api/set_user_permission` in all 36
- guarded endpoints, 8 distinct: `POST /json/{package_order, status, links, abort_link, link_order,
  move_package, edit_package, set_captcha}`

Independently, the builder logs **0 `Discarded an UNCONFIRMED …` lines**, i.e. the C4 re-login probe
confirmed every one: after the transition the victim logged in **again**, with a fresh credential, and
was **403** on the same endpoint. Only the pre-transition credential still worked. That string is
emitted on the same INFO logger as the `Assembled …` lines that do appear, so its absence is evidence
here rather than silence.

## Caveat that must reach the write-up

The transition URL is `user=pyload&permission=1&role=716`. `716` is not a role: `roleFieldSignals`
matches `permission` **before** `role` and binds the reduced value there, leaving `role` at whatever
value the search happened to carry. pyLoad treats role `0` as admin and anything else as not, so the
demotion still took effect.

State it plainly: the tool did **not** infer the correct role value. It found *a* value the SUT
accepted, and then let the SUT confirm the privilege was gone. That is precisely what the re-login
probe is for, and without it this firing would be a lucky guess rather than a checked claim.

## Result — arm `fixed-reset`, 5 seeds (the control that decides everything)

**0 tests carry fault 970**, across all 5 seeds, while the arm assembled **36 triples — exactly as many
as the vulnerable arm**, on the same victim/operator pair and the same 8 guarded endpoints. Every one
came back `200/200/403`.

That equality is the point. The oracle had **36 matched opportunities** to raise a false alarm on
third-party code and raised none; the two sides differ in one line of pyLoad and in nothing the tool
did. FP per triple **0/36** (95% upper bound 10%), FP per run **0/5**.

## The no-reset arms

`vuln-noreset` and `fixed-noreset` are **identical**: 0 triples assembled, 40 VOID attempts each. The
search destroys the preconditions completely on this target, independently of whether the bug is
present. All recall loss is in construction; the judgment rule never gets a triple to judge.
