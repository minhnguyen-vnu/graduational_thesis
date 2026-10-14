# Context eval — expected answers

| # | Expected | Source |
|---|---|---|
| 1 | No: show the code and wait for the user's OK before writing or building | `CLAUDE.md` §2 |
| 2 | No. Added code carries no comments; the guard hook refuses it | `CLAUDE.md` §2; `.claude/hooks/guard.py` |
| 3 | `evomaster-P2e-6ae8277b.jar`, commit `a544c996ac`, on a merged set with a declared deviation (AF2 `8d6cf8431f` and jar `R` kept as provenance) | `CLAUDE.md` §5; `docs/results.md` §0 |
| 4 | 30–35% (P2e and AF2: 7/20 no reset) | `CLAUDE.md` §4; `docs/results.md` §1 |
| 5 | No. Tier-2 exact McNemar p = 0.070, not significant at 0.05 | `docs/results.md` §4 |
| 6 | No. Replayable from clean state in 55/59 | `docs/results.md` §3 |
| 7 | 0 FP in 90 fixed-target runs, over 116 triples performed on patched code (AF2: 99) | `docs/results.md` §1 |
| 8 | INCONCLUSIVE, never a verdict | `CLAUDE.md` §3 |
| 9 | No | `CLAUDE.md` §3 |
| 10 | Source not 2xx, transition not 2xx, or follow-up not conclusive | `CLAUDE.md` §3 |
| 11 | Without the guard an action still allowed to the reduced role (e.g. `GET /reports`) reads as a bug | `CLAUDE.md` §3 |
| 12 | `nohup caffeinate -dims zsh <harness> > <folder>/nohup.out 2>&1 & disown`; never `run_in_background`; stop on `Entering Sleep` | skill `em-batch` |
| 13 | No. One heavy job at a time: `--maxTime` is wall-clock; the guard hook refuses it | `CLAUDE.md` §2; skill `em-batch` |
| 14 | No. It shows nothing broke on those rows, never that nothing improved | skill `regression-gate` |
| 15 | Not by itself. Repeat it interleaved against the reference jar | skill `regression-gate` |
| 16 | A new folder under `infra/em-results/`: harnesses delete their output folder | `CLAUDE.md` §2; skill `em-batch` |
| 17 | Open the source first-party and match the exact words; a web-fetch summary does not count | `CLAUDE.md` §2 |
| 18 | None directly; the applicable subset is written in `CLAUDE.md` §2 | `CLAUDE.md` §2 Context setup |
| 19 | Only when the user asks. `origin` is the user's fork `minhnguyen-vnu/evomaster-stateful-authz` | skill `evomaster-build` |
| 20 | `docs/tier2b-pyload-target.md` §3 | `CLAUDE.md` §7 |
| 21 | No. On Tier-1 the probe's 403 comes from `POST /reports` | `CLAUDE.md` §4; `docs/results.md` §6 |
| 22 | None. No TDD or coverage requirement; use the `thesis-*` agents | `CLAUDE.md` §2 Context setup |
