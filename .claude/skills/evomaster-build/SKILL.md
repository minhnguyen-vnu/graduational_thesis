---
name: evomaster-build
description: Build the EvoMaster core jar for the thesis, identify and preserve jars, rehearse a rollback, and commit on the stateful-authz-oracle branch. Use before building, before picking a jar for a run, or before changing code that can move existing numbers.
---

# EvoMaster: build, jars, rollback, git

Repo: `/Users/minhnguyen/IdeaProjects/EvoMaster`, branch `stateful-authz-oracle`, base tag `v6.1.1`.

## Build

Only after the user approved the code, and only when no batch is running.

```bash
JAVA_HOME=$(/usr/libexec/java_home -v 17) mvn -f /Users/minhnguyen/IdeaProjects/EvoMaster/pom.xml \
  -pl core -am package -Dmaven.test.skip=true
```

- Output `core/target/evomaster.jar`, ~110 MB, ~2.5 min.
- Pin JDK 17. Homebrew Maven defaults to JDK 26; EvoMaster targets 17 (Kotlin 2.2.20).
- A build overwrites `core/target/evomaster.jar`, which `regression_check.sh` reads.

## Preserve and identify

- Copy a jar that will produce quoted numbers to `EvoMaster/evomaster-<label>-<sha8>.jar` with a `.sha256`.
  Batches run the copy.
- Identify a jar by the options compiled into `EMConfig`, never by filename or mtime:

```bash
unzip -p <jar> 'org/evomaster/core/EMConfig*.class' | strings | grep -o "statefulAuthz[A-Za-z]*" | sort -u
```

| Jar | Commit | Use |
|---|---|---|
| `evomaster-P2e-6ae8277b.jar` | `a544c996ac` (HEAD, not pushed) | every current number, on a merged set with a declared deviation (`docs/results.md` §0) |
| `evomaster-AF2-6b5606d4.jar` | `8d6cf8431f` | provenance; quoted 2026-10-04 to 10-14; replay in `docs/results.md` §3 (`af2-full-remeasure-20261003/`) |
| `evomaster-R-5bce137f.jar` | `007e5e09f9` | provenance; AF2 reproduces §4 per-seed |
| `evomaster-B-06c70147.jar` | `8436f6dba6` | superseded Tier-2b round |
| `evomaster-frozen-769c16d.jar` | `6dd65f3706` | superseded Tier-1/Tier-2 rounds |
| `evomaster-0e-bf26b653.jar` sha256 `7974e8031991e0af…` | source of `bf26b65322` (HEAD `6a43a852d0` + 0e patch) | gate 21/21 on 2026-09-13; no batch |

The filenames of `B`, `R`, `AF2` and `P2e` carry the first 8 hex digits of the jar's sha256; `frozen` and `0e` carry
commit hashes from before the 2026-09-01 history rewrite. The commit column is current.

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
