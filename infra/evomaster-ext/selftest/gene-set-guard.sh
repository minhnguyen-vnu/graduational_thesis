#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:-$EM/core/target/evomaster.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
OUT=${1:-$THESIS/infra/em-results/genesetguard-selftest-$(date +%Y%m%d-%H%M%S)}
export JAVA_HOME=$(/usr/libexec/java_home -v 17)

PF_AIRFLOW_LOG=$THESIS/infra/em-results/postfallback-selftest-20260925-b/airflow-seed1.log
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
[ -f $PF_AIRFLOW_LOG ] || { echo "FAIL  baseline-log  --  khong thay $PF_AIRFLOW_LOG"; exit 1; }

echo "jar $(shasum -a 256 $JAR | cut -c1-16)"

if grep -q "JsonParseException" $PF_AIRFLOW_LOG && grep -q "setAllRoleFieldsTo" $PF_AIRFLOW_LOG; then
  pass "pf-baseline-crashes  (jar PF, Airflow: JsonParseException trong setAllRoleFieldsTo)"
else
  fail "pf-baseline-crashes" "log jar PF khong co JsonParseException trong setAllRoleFieldsTo"
fi

E=$(airflow airflow-seed1)
L=$OUT/airflow-seed1.log
[ "$E" = 0 ] && pass "airflow-exit-0  (Airflow seed 1 chay het, exit 0)" || fail "airflow-exit-0" "exit $E"
if grep -q "terminated abruptly" $L; then
  fail "airflow-no-abrupt-end" "$(grep -m1 -A1 'terminated abruptly' $L | tail -1 | cut -c1-200)"
else
  pass "airflow-no-abrupt-end  (khong co dong 'terminated abruptly')"
fi
R=$(grep -c "Privilege-restore" $L)
if [ "$R" -gt 0 ]; then
  pass "airflow-restore-reached  (RestSecurityBuilder.kt setAllRoleFieldsTo/trySetFromStringValue: $R dong Privilege-restore)"
else
  fail "airflow-restore-reached" "khong co dong Privilege-restore, nhanh khoi phuc quyen khong chay toi"
fi

E=$(tier1 tier1-vuln 8080)
D=$(det970 $OUT/tier1-vuln)
[ "$E" = 0 ] && [ "$D" = 1 ] && pass "tier1-970  (Tier-1 ban loi seed 1 van no 970)" || fail "tier1-970" "exit $E det970=$D"

E=$(tier1 tier1-fixed 8081)
D=$(det970 $OUT/tier1-fixed)
[ "$E" = 0 ] && [ "$D" = 0 ] && pass "tier1-fixed-no-970  (Tier-1 ban da va seed 1 khong co 970)" || fail "tier1-fixed-no-970" "exit $E det970=$D"

exit $FAILED
