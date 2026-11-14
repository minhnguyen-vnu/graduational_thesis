# Context eval — expected answers

| # | Expected | Source |
|---|---|---|
| 1 | No: show the code and wait for the user's OK before writing or building | `CLAUDE.md` §2 |
| 2 | No. Added code carries no comments; the guard hook refuses it | `CLAUDE.md` §2; `.claude/hooks/guard.py` |
| 3 | `evomaster-ND-07ebf19f.jar` = HEAD `2c3f281f13` plus `wip/nodup-tokens-20261113-tree.patch` (`THESIS` comments and the ND change; the ND change alone, `nodup-tokens-20261113.patch`, is taken against the commented tree; not committed: `f:` without path params, `tokens` without regex, no-duplication model); runs 2026-11-13 in `nd-wave1-20261113/`, `nd-wave2-20261113/` | `CLAUDE.md` §5; `docs/results.md` §0 |
| 4 | reports-api, vampi-seeded, pyLoad, artifact-keeper; pyLoad (CVE-2026-41133) and artifact-keeper (vendor bug #1821, vendor patch as control) | `CLAUDE.md` §1, §4 |
| 5 | 0 FP in 48 fixed-target runs, over 30 triples performed on patched code. The vendor patch gives 0 TN: the old token gets 401 (INCONCLUSIVE), so no triple is performed | `CLAUDE.md` §4; `docs/results.md` §1 |
| 6 | INCONCLUSIVE, never a verdict | `CLAUDE.md` §3 |
| 7 | No | `CLAUDE.md` §3 |
| 8 | Source not 2xx, transition not 2xx, or follow-up with no status or 401 | `CLAUDE.md` §3 |
| 9 | Without the guard an action still allowed to the reduced role (e.g. `GET /reports`) reads as a bug | `CLAUDE.md` §3 |
| 10 | `nohup caffeinate -dims zsh <harness> > <folder>/nohup.out 2>&1 & disown`; never `run_in_background`; stop on `Entering Sleep` | skill `em-batch` |
| 11 | No. It shows nothing broke on those 12 rows, never that nothing improved | skill `regression-gate` |
| 12 | Not by itself. Repeat it interleaved against the reference jar | skill `regression-gate` |
| 13 | A new folder under `infra/em-results/`: harnesses delete their output folder | `CLAUDE.md` §2; skill `em-batch` |
| 14 | Open the source first-party and match the exact words; a web-fetch summary does not count | `CLAUDE.md` §2 |
| 15 | None directly; the applicable subset is written in `CLAUDE.md` §2 | `CLAUDE.md` §2 Context setup |
| 16 | Only when the user asks. `origin` is the user's fork `minhnguyen-vnu/evomaster-stateful-authz` | skill `evomaster-build` |
| 17 | `docs/tier2b-pyload-target.md` §3; `docs/artifact-keeper-target.md` §2 | `CLAUDE.md` §7 |
| 18 | No. On reports-api the probe's 403 comes from `POST /reports` | `CLAUDE.md` §4; `docs/results.md` §7 |
| 19 | None. No TDD or coverage requirement; use the `thesis-*` agents | `CLAUDE.md` §2 Context setup |
| 20 | No. `EMConfig.kt` is identical to v6.1.1, so the jar rejects every `statefulAuthz*` option. The verdict uses the C4 probe (the thesis calls it the re-login step) | `CLAUDE.md` §1, §5; skill `em-batch` |
| 21 | No. The thesis reports final results and how they were measured; run incidents stay in the run folder's `PROTOCOL.md` | `CLAUDE.md` §2 Viết; `docs/results.md` header |
