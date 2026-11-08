# Context eval — expected answers

| # | Expected | Source |
|---|---|---|
| 1 | No: show the code and wait for the user's OK before writing or building | `CLAUDE.md` §2 |
| 2 | No. Added code carries no comments; the guard hook refuses it | `CLAUDE.md` §2; `.claude/hooks/guard.py` |
| 3 | `evomaster-M2-917c57dd.jar` = HEAD `9c4be5b1dc` with model M2 in place of `stateful-authz-model.csv` (M2 is in no commit); runs 2026-11-08 in `m2-wave1-20261108/`, `m2-wave2-20261108/` | `CLAUDE.md` §5; `docs/results.md` §0 |
| 4 | 30–35% (M2, P2f, P2e and AF2: 7/20) | `CLAUDE.md` §4; `docs/results.md` §1 |
| 5 | reports-api, vampi-seeded, pyLoad, artifact-keeper; pyLoad (CVE-2026-41133) and artifact-keeper (vendor bug #1821, vendor patch as control) | `CLAUDE.md` §1, §4 |
| 6 | No. Replayable from clean state in 55/59 | `docs/results.md` §3 |
| 7 | 0 FP in 48 fixed-target runs, over 30 triples performed on patched code. The vendor patch gives 0 TN: the old token gets 401 (INCONCLUSIVE), so no triple is performed | `CLAUDE.md` §4; `docs/results.md` §1 |
| 8 | INCONCLUSIVE, never a verdict | `CLAUDE.md` §3 |
| 9 | No | `CLAUDE.md` §3 |
| 10 | Source not 2xx, transition not 2xx, or follow-up not conclusive | `CLAUDE.md` §3 |
| 11 | Without the guard an action still allowed to the reduced role (e.g. `GET /reports`) reads as a bug | `CLAUDE.md` §3 |
| 12 | `nohup caffeinate -dims zsh <harness> > <folder>/nohup.out 2>&1 & disown`; never `run_in_background`; stop on `Entering Sleep` | skill `em-batch` |
| 13 | No. One heavy job at a time: `--maxTime` is wall-clock; the guard hook refuses it | `CLAUDE.md` §2; skill `em-batch` |
| 14 | No. It shows nothing broke on those 12 rows, never that nothing improved | skill `regression-gate` |
| 15 | Not by itself. Repeat it interleaved against the reference jar | skill `regression-gate` |
| 16 | A new folder under `infra/em-results/`: harnesses delete their output folder | `CLAUDE.md` §2; skill `em-batch` |
| 17 | Open the source first-party and match the exact words; a web-fetch summary does not count | `CLAUDE.md` §2 |
| 18 | None directly; the applicable subset is written in `CLAUDE.md` §2 | `CLAUDE.md` §2 Context setup |
| 19 | Only when the user asks. `origin` is the user's fork `minhnguyen-vnu/evomaster-stateful-authz` | skill `evomaster-build` |
| 20 | `docs/tier2b-pyload-target.md` §3; `docs/artifact-keeper-target.md` §2 | `CLAUDE.md` §7 |
| 21 | No. On reports-api the probe's 403 comes from `POST /reports` | `CLAUDE.md` §4; `docs/results.md` §7 |
| 22 | None. No TDD or coverage requirement; use the `thesis-*` agents | `CLAUDE.md` §2 Context setup |
| 23 | No. Jar SR and later (M2 included) reject all `statefulAuthz*` options; judgment is C4 only. Fallback jar: P2f (`evomaster-P2f-64ee8ffc.jar`, `f73010103b`) | `CLAUDE.md` §5; skill `em-batch` |
| 24 | No. The thesis reports final results and how they were measured; run incidents stay in the run folder's `PROTOCOL.md` | `CLAUDE.md` §2 Viết; `docs/results.md` header |
