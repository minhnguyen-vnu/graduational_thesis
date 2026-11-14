---
name: em-batch
description: Run EvoMaster black-box against the thesis targets, one run or a batch - containers, reseed, auth config, flags for oracle 970, nohup launch, monitoring, then audit, replay and backup. Use before starting any EvoMaster run.
---

# Running EvoMaster on the thesis targets

## Targets

| Target | Vulnerable | Fixed | Reseed | Spec | Auth config |
|---|---|---|---|---|---|
| reports-api | :8080 | :8081 | `POST /reset` | `/v3/api-docs` | `infra/em-config/reports-auth.yaml` |
| vampi-seeded | :5002 | :5003 | `GET /createdb` | `/openapi.json` | `infra/em-config/vampi-seeded-auth.yaml` |
| pyLoad | :8090 | :8091 | `POST /thesis/reset` | `file://…/infra/pyload-cve/openapi-merged.json` | `infra/em-config/pyload-auth.yaml` |
| artifact-keeper | :8080, commit `e56d3aa7e2` | :8080, vendor patch `e64cc5c608` | `infra/em-results/artifactkeeper-20261001/reseed.sh full` | `file://…/infra/em-results/m2-wave2-20261108/openapi-trimmed.json` | `infra/em-results/m2-wave2-20261108/artifactkeeper-auth-proxied.yaml` |

Build and start: `infra/reports-api/README.md`, `infra/vampi-seeded/THESIS-SEED.md`,
`docs/tier2b-pyload-target.md` §3, `docs/artifact-keeper-target.md` §3. Port 5000 is taken by macOS AirPlay.
artifact-keeper also listens on :8080: stop the reports-api vulnerable container first. One artifact-keeper variant
runs at a time; switching commits needs the full reseed (it wipes the database volume).

## One run

```bash
curl -s -X POST http://localhost:8080/reset >/dev/null
JAVA_HOME=$(/usr/libexec/java_home -v 17) java -Xmx2g -jar /Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-ND-07ebf19f.jar \
  --blackBox true --bbSwaggerUrl http://localhost:8080/v3/api-docs --bbTargetUrl http://localhost:8080 \
  --configPath infra/em-config/reports-auth.yaml \
  --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
  --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 1 \
  --outputFolder infra/em-results/<new-folder>
```

| Target | `--maxTime` | `--ratePerMinute` | `--extraPhaseBudgetPercentage` | Other |
|---|---|---|---|---|
| reports-api, vampi-seeded | 150s | 120 | 0.6 | |
| pyLoad | 10m | 200 | 0.6 | `--endpointExclude "/api/kill,/api/restart"` |
| artifact-keeper | 1200s | 600 | 0.25 | `--bbTargetUrl http://localhost:8212` through `infra/evomaster-ext/selftest/capture_proxy.py 8212 localhost 8080 <traffic.jsonl>`, to count logins per account |

- 970 is experimental: without `--useExperimentalOracles true` it never fires.
- The security phase gets `extraPhaseBudgetPercentage × maxTime`; below ~0.6 at 150 s construction starves.
- `--security` requires `--minimize`.
- Jar SR and later (M2 and ND included) have no `statefulAuthz*` option and reject `--statefulAuthzResetEndpoint`,
  `--statefulAuthzTransition` and `--statefulAuthzTwoCredentialJudgment` with `is not a recognized option`. Those
  exist only on P2f and earlier jars.
- Builder diagnostics: `-Dlogback.configurationFile=infra/em-config/logback-builder-debug.xml`.
- Baseline arms: released v6.1.1, `infra/em-venv/bin/evomaster` (security oracles on by default).
- Auth config keys (WFC, v6.1.1): `extractFrom: body`, `extractSelector: /token` (JSON Pointer), `sendIn: header`,
  `sendName: Authorization`, `sendTemplate: "Bearer {token}"`. v6.1.1 rejects `extractFromField`,
  `httpHeaderName`, `headerPrefix`.

## Batch

1. Copy an existing harness into a **new** folder under `infra/em-results/`: `m2-wave1-20261108/m2_wave1.sh`
   (reports-api, vampi-seeded, pyLoad; it starts six lanes in parallel) or
   `m2-wave2-20261108/ak_vuln.sh`, `ak_fixed.sh` (artifact-keeper). Harnesses `rm -rf` their output.
2. The harness checks the jar's sha256 before the first run.
3. The harness text states what is measured, never the expected outcome.
   It also states the early-stop rule (CLAUDE.md §2), e.g. "first 3 seeds of every arm: one pattern and 0 valid
   triples, stop". The harness is stopped when it fires; the stop is recorded in the folder's `PROTOCOL.md`.
4. Diff the full command lines of any two arms: they differ in one variable.
5. Launch detached under `caffeinate`: `nohup caffeinate -dims zsh <harness> > <folder>/nohup.out 2>&1 & disown`
   (the harness's own shell). Never `run_in_background`. `setsid` does not exist on macOS. The harness stops itself
   when `pmset -g log` shows a new `Entering Sleep` while a row runs. Keep the charger plugged in: at 1% battery the
   host sleeps despite `caffeinate`.
6. Monitor both the done marker in `progress.log` and `kill -0 <pid>`. Check: `ps -eo pid,etime,command | grep evomaster`.
7. Wall clock per run: reports-api and vampi-seeded ~5 min, pyLoad ~19 min, artifact-keeper ~38 min with its reseed
   (`m2-wave1-20261108/progress.log`, `m2-wave2-20261108/progress-ak.log`). For another app, estimate
   reseed + `maxTime` + `extraPhaseBudgetPercentage × maxTime` + minimization, and state each phase. Minimization
   replays every kept test against the live SUT, so it is bound by app latency, not `--ratePerMinute`
   (artifact-keeper ~3 requests/s). Java near 0% CPU during minimization is waiting on sockets:
   check that the traffic line count grows.
8. Keep the lid open. `caffeinate` prevents idle sleep only; a closed lid lets runs finish with wrong elapsed
   time and lower coverage.

Record per run: target, arm, seed, `det970` (970 in `report.json`), triples (count `Assembled` log lines only; the
"proven by an attempt" line repeats each triple), VOID attempts, restores accepted and refused, triple statuses,
fault codes.

## After a batch

1. Audit the emitted tests: `python3 infra/em-results/audit970_seeded.py <folder>/tests/* > <folder>/audit970.out`.
   Revalidate the checker on broken copies if the parser changed. pyLoad (session cookie) is not parseable.
2. Integrity: no 970 without an assembled triple; log counts equal the CSV.
3. Replay 970 tests against a freshly reseeded SUT with pytest (template `tier1-clean-remeasure/replay_t1.sh`).
4. Snapshot:
   `cd /Users/minhnguyen/IdeaProjects && tar --exclude 'graduational-thesis/infra/em-venv' -czf ~/thesis-backups/thesis-full-$(date +%Y%m%d-%H%M).tar.gz graduational-thesis`,
   then write its `.sha256`.
5. Update `docs/results.md` in place, naming the jar. Run incidents stay in the folder's `PROTOCOL.md`.
