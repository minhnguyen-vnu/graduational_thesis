#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:-$EM/core/target/evomaster.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
OUT=${1:-$THESIS/infra/em-results/postfallback-selftest-$(date +%Y%m%d-%H%M%S)}
export JAVA_HOME=$(/usr/libexec/java_home -v 17)

SOURCES="Stateful-authorization guarded source candidates:"
VICTIMS="Stateful-authorization source "
RF_AIRFLOW_LOG=$THESIS/infra/em-results/airflow-3users-20260924/logs/rf-3users-seed1.log
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"

mkdir -p $OUT
FAILED=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1  --  $2"; FAILED=1; }

det970() {
  python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$1/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')"
}

tier1() {
  local name=$1 port=$2
  curl -s -X POST http://localhost:$port/reset > /dev/null
  java $DEBUG -jar $JAR \
    --blackBox true --bbSwaggerUrl http://localhost:$port/v3/api-docs --bbTargetUrl http://localhost:$port \
    --configPath $THESIS/infra/em-config/reports-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 1 \
    --outputFolder $OUT/$name > $OUT/$name.log 2>&1
  echo $?
}

airflow() {
  local name=$1
  zsh $THESIS/infra/airflow-target/reset-3users.sh http://localhost:8082 > $OUT/$name-reset.txt 2>&1
  if ! grep -q "victim roles \['Op'\]" $OUT/$name-reset.txt || ! grep -q "viewer roles \['Viewer'\]" $OUT/$name-reset.txt; then
    echo reset-failed
    return
  fi
  java $DEBUG -jar $JAR --blackBox true \
    --bbSwaggerUrl file://$THESIS/infra/airflow-target/airflow-merged-nodelete.json \
    --bbTargetUrl http://localhost:8082 \
    --configPath $THESIS/infra/em-config/airflow-auth-3users.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 60 --maxTime 600s --seed 1 \
    --outputFolder $OUT/$name > $OUT/$name.log 2>&1
  echo $?
}

for p in 8080 8081 8082; do
  if [ "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:$p/)" = "000" ]; then
    echo "FAIL  target-up  --  cong $p khong tra loi, khong chay duoc self-test"
    exit 1
  fi
done
[ -f $RF_AIRFLOW_LOG ] || { echo "FAIL  baseline-log  --  khong thay $RF_AIRFLOW_LOG"; exit 1; }

echo "jar $(shasum -a 256 $JAR | cut -c1-16)"

RF_LINE=$(grep "$SOURCES" $RF_AIRFLOW_LOG | tail -1)
RF_NONEMPTY=$(grep "$VICTIMS" $RF_AIRFLOW_LOG | grep -E "^.* victims \[.+\]" | grep -vc "victims \[\]")
if [ -n "$RF_LINE" ] && ! echo "$RF_LINE" | grep -q "POST:" && [ "$RF_NONEMPTY" = 0 ]; then
  pass "rf-baseline-putpatch-only  (jar RF, Airflow: nguon chi PUT/PATCH, khong nguon nao co nan nhan)"
else
  fail "rf-baseline-putpatch-only" "dong nguon jar RF: ${RF_LINE:-khong co}; nguon co nan nhan: $RF_NONEMPTY"
fi

E=$(airflow airflow-seed1)
AF_LINE=$(grep "$SOURCES" $OUT/airflow-seed1.log | tail -1)
if [ "$E" = 0 ] && echo "$AF_LINE" | grep -q "POST:"; then
  pass "airflow-post-considered  (RestSecurityBuilder.kt:542-550: $(echo "$AF_LINE" | grep -o 'candidates: [0-9]*'), co POST)"
else
  fail "airflow-post-considered" "exit $E; dong nguon: ${AF_LINE:-khong co}"
fi
if echo "$AF_LINE" | grep -q -E "PUT:|PATCH:"; then
  fail "airflow-putpatch-replaced" "danh sach con PUT/PATCH: $AF_LINE"
else
  pass "airflow-putpatch-replaced  (khong nguon PUT/PATCH nao co nan nhan nen danh sach chi con POST)"
fi

E=$(tier1 tier1-vuln 8080)
T1_LINE=$(grep "$SOURCES" $OUT/tier1-vuln.log | head -1)
T1_VICTIM=$(grep "$VICTIMS" $OUT/tier1-vuln.log | grep -E "source (PUT|PATCH):" | grep -vc "victims \[\]")
if [ "$E" = 0 ] && [ -n "$T1_LINE" ] && ! echo "$T1_LINE" | grep -q "POST:" && [ "$T1_VICTIM" -gt 0 ]; then
  pass "tier1-putpatch-kept  (co nguon PUT/PATCH co nan nhan, danh sach khong co POST)"
else
  fail "tier1-putpatch-kept" "exit $E; dong nguon: ${T1_LINE:-khong co}; nguon PUT/PATCH co nan nhan: $T1_VICTIM"
fi
D=$(det970 $OUT/tier1-vuln)
[ "$D" = 1 ] && pass "tier1-970  (Tier-1 ban loi seed 1 van no 970)" || fail "tier1-970" "det970=$D"

E=$(tier1 tier1-fixed 8081)
D=$(det970 $OUT/tier1-fixed)
[ "$E" = 0 ] && [ "$D" = 0 ] && pass "tier1-fixed-no-970  (Tier-1 ban da va seed 1 khong co 970)" || fail "tier1-fixed-no-970" "exit $E det970=$D"

exit $FAILED
