#!/bin/sh
set -e
cd "$(dirname "$0")"
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-TR2-3beccb00.jar
JAVA="$(/usr/libexec/java_home -v 17)/bin/java"
OUT="$(mktemp -d)"
"$JAVA" --add-opens java.base/java.net=ALL-UNNAMED --add-opens java.base/java.util=ALL-UNNAMED -cp "$JAR" Wiring.java "$OUT" 2>&1 | sed 's/\x1b\[[0-9;]*[A-Za-z]//g' | grep -v "^SLF4J\|DEBUG\|^\s*at " | cut -c1-300 > wiring.rerun.out
echo "Wiring -> wiring.rerun.out"
