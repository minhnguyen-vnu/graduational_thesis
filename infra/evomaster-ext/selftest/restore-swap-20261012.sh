#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:-$EM/core/target/evomaster.jar}
OLDJAR=${OLDJAR:-$EM/evomaster-P2b-93db089f.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
OUT=${1:-$THESIS/infra/em-results/restore-swap-selftest-$(date +%Y%m%d-%H%M%S)}
PORT=8080
SEED=4
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
mkdir -p $OUT
FAILED=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1  --  $2"; FAILED=1; }

echo "exercises RestSecurityBuilder.kt:858 (restore call: restorer=victimAuth, target=operator)"
echo "jar-new $(shasum -a 256 $JAR | cut -c1-16)  jar-old $(shasum -a 256 $OLDJAR | cut -c1-16)"

if [ "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' -X POST http://localhost:$PORT/reset)" != 200 ]; then
  fail "target-up" "reports-api vuln :$PORT did not answer POST /reset with 200"
  echo "output $OUT"; exit 1
fi

runit() {
  local tag=$1 jar=$2
  curl -s -o /dev/null -X POST http://localhost:$PORT/reset
  java -jar $jar --blackBox true \
    --bbSwaggerUrl http://localhost:$PORT/v3/api-docs --bbTargetUrl http://localhost:$PORT \
    --configPath $THESIS/infra/em-config/reports-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $SEED \
    --outputFolder $OUT/$tag > $OUT/$tag.log 2>&1
}
det970() {
  python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$1/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print(0)"
}

runit new $JAR
runit old $OLDJAR
NL=$OUT/new.log; OL=$OUT/old.log
DN=$(det970 $OUT/new); DO=$(det970 $OUT/old)

RESTORER_OK="Privilege-restore accepted for 'alice' by 'superadmin'"
FIRED_SUPER="Assembled a stateful-authorization (MR-A1) triple on PUT:/reports/{id} (victim 'superadmin'"
RESTORER_BAD="Privilege-restore refused for 'superadmin' by 'alice'"

grep -qF "$RESTORER_OK" $NL \
  && pass "restorer-is-victim         new log: $RESTORER_OK" \
  || fail "restorer-is-victim" "new log lacks the swapped-arg restore line (restorer=victim superadmin)"

grep -qF "$FIRED_SUPER" $NL \
  && pass "fires-on-protected-victim  new log assembled a triple on victim 'superadmin' via the restore path" \
  || fail "fires-on-protected-victim" "new log did not assemble a triple on victim 'superadmin'"

[ "$DN" = 1 ] \
  && pass "det970-new                 report.json has fault 970" \
  || fail "det970-new" "new run did not detect 970 (det970=$DN)"

if ! grep -qF "$RESTORER_OK" $OL && [ "$DO" = 0 ]; then
  pass "checks-can-fail            old jar P2b: restore refused ($(grep -oF "$RESTORER_BAD" $OL | head -1)), det970=$DO -> checks above would FAIL on it"
else
  fail "checks-can-fail" "old jar P2b also showed restorer-is-victim or fired (det970=$DO); the checks do not discriminate the swap"
fi

echo "output $OUT"
exit $FAILED
