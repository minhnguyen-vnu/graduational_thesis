---
name: em-batch
description: Run EvoMaster black-box against the thesis targets, one run or a batch - containers, reseed, auth config, flags for oracle 970, reset ablation, declared transition, nohup launch, monitoring, then audit, replay and backup. Use before starting any EvoMaster run.
---

# Running EvoMaster on the thesis targets

## Targets

| Target | Vulnerable | Fixed | Reseed | Spec | Auth config |
|---|---|---|---|---|---|
| Tier-1 `reports-api` | :8080 | :8081 | `POST /reset` | `/v3/api-docs` | `infra/em-config/reports-auth.yaml` |
| Tier-2 `vampi-seeded` | :5002 | :5003 | `GET /createdb` | `/openapi.json` | `infra/em-config/vampi-seeded-auth.yaml` |
| Tier-2b pyLoad | :8090 | :8091 | `POST /thesis/reset` | `file://…/infra/pyload-cve/openapi-merged.json` | `infra/em-config/pyload-auth.yaml` |

Build and start: `infra/reports-api/README.md`, `docs/tier2-seeded-benchmark-plan.md` §4,
`docs/tier2b-pyload-target.md` §3. Port 5000 is taken by macOS AirPlay.

## One run

```bash
curl -s -X POST http://localhost:8080/reset >/dev/null
JAVA_HOME=$(/usr/libexec/java_home -v 17) java -jar /Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-P2e-6ae8277b.jar \
  --blackBox true --bbSwaggerUrl http://localhost:8080/v3/api-docs --bbTargetUrl http://localhost:8080 \
  --configPath infra/em-config/reports-auth.yaml \
  --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
  --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 1 \
  --outputFolder infra/em-results/<new-folder>
```

- 970 is experimental: without `--useExperimentalOracles true` it never fires.
- The security phase gets `extraPhaseBudgetPercentage × maxTime`; below ~0.6 at 150 s construction starves.
- `--security` requires `--minimize`.
- pyLoad: add `--endpointExclude "/api/kill,/api/restart"`; recorded runs used `--ratePerMinute 200 --maxTime 10m`.
- Reset ablation: `--statefulAuthzResetEndpoint "POST http://localhost:8080/reset"` (Tier-1),
  `"GET http://localhost:5002/createdb"` (Tier-2), `"POST http://localhost:8090/thesis/reset"` (Tier-2b).
  Off by default. Each call logs `SUT state reset via … -> 200`.
- Declared transition: `--statefulAuthzTransition "<VERB> <PATH> k=v k=v"` with `<victim>`/`<operator>`.
  It also raises the attempt ceiling to 40 (inferred: 20 on P2e, 8 on AF2) and orders guards. Never quote a black-box recall from it.
- Baseline arms: released v6.1.1, `infra/em-venv/bin/evomaster` (security oracles on by default).
- Auth config keys (WFC, v6.1.1): `extractFrom: body`, `extractSelector: /token` (JSON Pointer), `sendIn: header`,
  `sendName: Authorization`, `sendTemplate: "Bearer {token}"`. v6.1.1 rejects `extractFromField`,
  `httpHeaderName`, `headerPrefix`.

## Batch

1. Copy an existing harness into a **new** folder under `infra/em-results/`
   (`tier1-clean-remeasure/remeasure_t1.sh`, `restore-remeasure/remeasure.sh`,
   `tier2b-restore-trials/tier2b_restore_trials.sh`). Harnesses `rm -rf` their output.
2. The harness text states what is measured, never the expected outcome.
   It also states the early-stop rule (CLAUDE.md §2), e.g. "first 3 seeds of every arm: one pattern and 0 valid
   triples, stop". The harness is stopped when it fires; the stop is a recorded deviation.
3. Diff the full command lines of any two arms: they differ in one variable.
4. Launch detached under `caffeinate`: `nohup caffeinate -dims zsh <harness> > <folder>/nohup.out 2>&1 & disown`
   (the harness's own shell). Never `run_in_background`. `setsid` does not exist on macOS. The harness stops itself
   when `pmset -g log` shows a new `Entering Sleep` while a row runs (`check` in `p2e-full-20261014/p2e_full.sh`).
5. Monitor both the done marker in `progress.log` and `kill -0 <pid>`. Check: `ps -eo pid,etime,command | grep evomaster`.
6. ~5 min per run wall-clock; 80 runs ≈ 6.5 h.
7. Keep the lid open. `caffeinate` prevents idle sleep only; a closed lid lets runs finish with wrong elapsed
   time and lower coverage.
8. One heavy job at a time. The guard hook refuses `mvn`, `docker build`, `pytest` and a second run while a batch runs.

Record per run: `tier,arm,seed,reset,det970,assembled,void_count,resets,restores_ok,restores_no,statuses,faults`.

## After a batch

1. Audit the emitted tests: `python3 infra/em-results/audit970_seeded.py <folder>/tests/* > <folder>/audit970.out`.
   Revalidate the checker on broken copies if the parser changed.
2. Integrity: no 970 without an assembled triple; log counts equal `runs.csv`.
3. Replay 970 tests against a freshly reseeded SUT with pytest (template `tier1-clean-remeasure/replay_t1.sh`).
4. Snapshot:
   `cd /Users/minhnguyen/IdeaProjects && tar --exclude 'graduational-thesis/infra/em-venv' -czf ~/thesis-backups/thesis-full-$(date +%Y%m%d-%H%M).tar.gz graduational-thesis`,
   then write its `.sha256`.
5. Update `docs/results.md` in place, naming the jar.
