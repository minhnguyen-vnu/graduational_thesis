#!/bin/sh
set -e
cd "$(dirname "$0")"
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-TR2-3beccb00.jar
JAVA="$(/usr/libexec/java_home -v 17)/bin/java"
for p in Dump Genes Triple TripleUnflat; do
  "$JAVA" -cp "$JAR" "$p.java" reports-api-openapi.json 2>&1 | grep -v "^SLF4J\|DEBUG\|^\s*at \|There are 9" > "$p.rerun.out"
  echo "$p -> $p.rerun.out"
done
