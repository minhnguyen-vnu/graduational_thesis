#!/bin/sh
set -e
cd "$(dirname "$0")"
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-TR2-3beccb00.jar
JAVA="$(/usr/libexec/java_home -v 17)/bin/java"
OUT="$(mktemp -d)"
curl -s -o /dev/null -w "reset before: %{http_code}\n" -X POST http://localhost:8080/reset
python3 -I proxy.py 18080 8080 traffic.log &
PROXY_PID=$!
trap 'kill $PROXY_PID 2>/dev/null || true' EXIT
sleep 1
"$JAVA" --add-opens java.base/java.net=ALL-UNNAMED --add-opens java.base/java.util=ALL-UNNAMED -cp "$JAR" Secu.java "$OUT" 147 2>&1 \
  | sed 's/\x1b\[[0-9;]*[A-Za-z]//g' \
  | awk '!/^SLF4J/ && !/^[[:space:]]*at / && (!/DEBUG/ || /RestSecurityBuilder/)' \
  | cut -c1-2500 > secu.out
kill $PROXY_PID 2>/dev/null || true
curl -s -o /dev/null -w "reset after: %{http_code}\n" -X POST http://localhost:8080/reset
echo "Secu -> secu.out, traffic.log"
