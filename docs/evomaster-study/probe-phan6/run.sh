#!/bin/sh
set -e
cd "$(dirname "$0")"
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster-upstream/evomaster-upstream-master-b6307c2d.jar
CFG=/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/em-config/reports-auth.yaml
JAVA="$(/usr/libexec/java_home -v 17)/bin/java"
SEED=${1:-5}
OUT="$(pwd)/tests-seed$SEED"
rm -rf "$OUT"
shasum -a 256 "$JAR" | cut -c1-16
curl -s -o /dev/null -w "reset before: %{http_code}\n" -X POST http://localhost:8080/reset
python3 -I proxy.py 18080 8080 traffic-seed$SEED.log &
PROXY_PID=$!
trap 'kill $PROXY_PID 2>/dev/null || true' EXIT
sleep 1
"$JAVA" -Xmx2g -jar "$JAR" --blackBox true \
  --bbSwaggerUrl http://localhost:18080/v3/api-docs --bbTargetUrl http://localhost:18080 \
  --configPath "$CFG" \
  --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
  --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $SEED \
  --outputFolder "$OUT" 2>&1 | python3 -I mark.py 18080 > baseline-seed$SEED.log
kill $PROXY_PID 2>/dev/null || true
curl -s -o /dev/null -w "reset after: %{http_code}\n" -X POST http://localhost:8080/reset
echo "done -> baseline-seed$SEED.log, traffic-seed$SEED.log, $OUT"
