# Round 2 of the C1–C5 regression check (POST demoted to a fallback)

20/21 reproduced, 0 verdict changes. The single failure — `tier2 ours-fixed-reset seed=3`,
recorded `200/200/403`, observed `NA` — was then repeated 27 times interleaved against the frozen
jar: frozen 12/12, this build 3/15, Fisher one-sided p = 2.6e-5.

Root cause: `docs/diagnosis-c5-victim-abandon.md` (C5's "victim is spent" early exit also skips the
attempts whose `resetSutState()` would have un-marked the OPERATOR).

Kept because this is the round that caught the defect. Jar: df87e55649cd3f84.
