#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:-$EM/evomaster-P2d-2e0dbd4d.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
REC=$THESIS/infra/em-results/p2c-vs-af2-debug-20261012
OLD10=${OLD10:-$REC/p2c-seed10-debug.log}
OLD16=${OLD16:-$REC/p2c-seed16-debug.log}
OUT=${1:-$THESIS/infra/em-results/p2d-selftest-$(date +%Y%m%d-%H%M%S)}
PORT=8080
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
mkdir -p $OUT
FAILED=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1  --  $2"; FAILED=1; }

echo "exercises RestSecurityBuilder.kt:1248-1249 (current role kept out of the exclusion when the model scores it low)"
echo "      and RestSecurityBuilder.kt:1261 (operator snapshot skipped for restore when the model scores it low)"
echo "jar-new $(shasum -a 256 $JAR | cut -c1-16)  old = recorded P2c b2ade764 logs, same command: $OLD10 $OLD16"

if [ "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' -X POST http://localhost:$PORT/reset)" != 200 ]; then
  fail "target-up" "reports-api vuln :$PORT did not answer POST /reset with 200"
  echo "output $OUT"; exit 1
fi

runit() {
  local seed=$1
  curl -s -o /dev/null -X POST http://localhost:$PORT/reset
  java -Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:$PORT/v3/api-docs --bbTargetUrl http://localhost:$PORT \
    --configPath $THESIS/infra/em-config/reports-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $seed \
    --outputFolder $OUT/seed$seed > $OUT/seed$seed.log 2>&1
}
det970() {
  python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$1/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print(0)"
}
lowheld() {
  grep -E "current roles \[[^]]*VIEWER[^]]*\], reduced role values" $1 | head -1
}
keeps() {
  lowheld $1 | grep -qE "reduced role values \[[^]]*VIEWER"
}

runit 10
runit 16
N10=$OUT/seed10.log; N16=$OUT/seed16.log
D10=$(det970 $OUT/seed10); D16=$(det970 $OUT/seed16)

ELEV_OK="Privilege-restore accepted for 'bob' by 'alice'"
ELEV_NONE="no elevated role value for the operators of victim 'alice'"

L=$(lowheld $N10)
[ -n "$L" ] \
  && pass "A-exercised     seed 10 read a low current role: ${L##*RestSecurityBuilder - }" \
  || fail "A-exercised" "seed 10 never read VIEWER as a current role; :1248 not exercised on this run"

keeps $N10 \
  && pass "A-keeps-viewer  VIEWER stays a reduced value although the current role read is VIEWER" \
  || fail "A-keeps-viewer" "VIEWER was excluded from the reduced values"

[ "$D10" = 1 ] \
  && pass "A-det970        seed 10 report.json has fault 970" \
  || fail "A-det970" "seed 10 did not detect 970 (det970=$D10)"

if grep -qF "$ELEV_OK" $N16 && ! grep -qF "$ELEV_NONE" $N16; then
  pass "B-elevates-op   seed 16: $ELEV_OK"
else
  fail "B-elevates-op" "seed 16 did not elevate operator bob (restore line absent or '$ELEV_NONE' present)"
fi

[ "$D16" = 1 ] \
  && pass "B-det970        seed 16 report.json has fault 970" \
  || fail "B-det970" "seed 16 did not detect 970 (det970=$D16)"

OLDA=$(lowheld $OLD10)
if [ -n "$OLDA" ] && ! keeps $OLD10 && grep -qF "$ELEV_NONE" $OLD16 && ! grep -qF "$ELEV_OK" $OLD16; then
  pass "checks-can-fail P2c logs: ${OLDA##*RestSecurityBuilder - }; seed 16 '$ELEV_NONE' -> A-keeps-viewer and B-elevates-op FAIL on P2c"
else
  fail "checks-can-fail" "recorded P2c logs pass the same checks; they do not discriminate the change"
fi

echo "output $OUT"
exit $FAILED
