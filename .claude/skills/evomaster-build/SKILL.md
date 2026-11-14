---
name: evomaster-build
description: Build the EvoMaster core jar for the thesis, identify and preserve jars, rehearse a rollback, and commit on the stateful-authz-oracle branch. Use before building, before picking a jar for a run, or before changing code that can move existing numbers.
---

# EvoMaster: build, jars, rollback, git

Repo: `/Users/minhnguyen/IdeaProjects/EvoMaster`, branch `stateful-authz-oracle`, base tag `v6.1.1`.

## Build

Only after the user approved the code.

```bash
JAVA_HOME=$(/usr/libexec/java_home -v 17) mvn -f /Users/minhnguyen/IdeaProjects/EvoMaster/pom.xml \
  -pl core -am package -Dmaven.test.skip=true
```

- Output `core/target/evomaster.jar`, ~110 MB, ~2.5 min.
- Pin JDK 17. Homebrew Maven defaults to JDK 26; EvoMaster targets 17 (Kotlin 2.2.20).
- A build overwrites `core/target/evomaster.jar`. The 12-row gate takes its jar from `JAR=`.

## Preserve and identify

- Copy a jar that will produce quoted numbers to `EvoMaster/evomaster-<label>-<sha8>.jar` with a `.sha256`.
  Batches run the copy.
- Identify a jar by the options compiled into `EMConfig`, never by filename or mtime:

```bash
unzip -p <jar> 'org/evomaster/core/EMConfig*.class' | strings | grep -o "statefulAuthz[A-Za-z]*" | sort -u
```

  Jars from SR on print nothing: their `EMConfig.kt` equals v6.1.1. Tell them apart by the model:
  `unzip -p <jar> stateful-authz-model.csv | shasum -a 256` gives `dcc77b59ed0f…` for ND and `b2deef150bf8…` for M2.

| Jar | Commit | Use |
|---|---|---|
| `evomaster-ND-07ebf19f.jar` | HEAD `2c3f281f13` + `wip/nodup-tokens-20261113-tree.patch` (not committed; `THESIS` comments plus the ND change, which alone is `nodup-tokens-20261113.patch` against the commented tree): `f:` without path params, `tokens` without regex, no-duplication model (`infra/analysis/lexicon-rules/m2-nodup-20261112/`) | every current number from 2026-11-13 (`docs/results.md`); no reset, declared transition or D1 |
| `evomaster-M2-917c57dd.jar` | `9c4be5b1dc` + model M2 (`infra/analysis/lexicon-rules/m2-model-20261107/stateful-authz-model.csv`, not committed; the tree holds M1) | fallback; quoted 2026-11-08 to 11-13 |

The filename carries the first 8 hex digits of the jar's sha256. Every other jar: `infra/evomaster-ext/jars.md`.

## Rollback rehearsal

Before any change that can move an existing number:

1. `git -C /Users/minhnguyen/IdeaProjects/EvoMaster diff > infra/evomaster-ext/wip/<name>-<yyyymmdd>.patch`
2. `git checkout --` the touched files; `git diff HEAD` is empty.
3. `git apply` the patch; `git diff` equals the saved patch byte for byte.

Redo it whenever the patch grows.

## Git

- `origin` = `github.com/minhnguyen-vnu/evomaster-stateful-authz` (the user's fork); the branch tracks
  `origin/stateful-authz-oracle`. Commit and push only when the user asks.
- Message `<type>: <description>`, types feat, fix, refactor, docs, test, chore, perf, ci. No attribution trailer.
- Added lines carry no comments. Upstream comments stay.
