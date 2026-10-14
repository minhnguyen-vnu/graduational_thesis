#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:-$EM/core/target/evomaster.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
OUT=${1:-$THESIS/infra/em-results/lowpriv-selftest-$(date +%Y%m%d-%H%M%S)}
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
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
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 10 \
    --outputFolder $OUT/$name > $OUT/$name.log 2>&1
  echo $?
}

for p in 8080 8081; do
  if [ "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:$p/)" = "000" ]; then
    echo "FAIL  target-up  --  cong $p khong tra loi, khong chay duoc self-test"
    exit 1
  fi
done

echo "jar $(shasum -a 256 $JAR | cut -c1-16)"

E=$(tier1 tier1-vuln-seed10 8080)
L=$OUT/tier1-vuln-seed10.log
[ "$E" = 0 ] && pass "exit-0  (Tier-1 ban loi seed 10, exit 0)" || fail "exit-0" "exit $E"

C=$(grep -o "victim 'superadmin' current roles \[[^]]*\], reduced role values \[[^]]*\]" $L | head -1)
if [ -n "$C" ] && ! echo "$C" | grep -q "current roles \[[^]]*VIEWER" && echo "$C" | grep -q "reduced role values \[[^]]*VIEWER"; then
  pass "low-priv-not-current  (isLowPrivRole trong buildStatefulAuthzTriple: $C)"
else
  fail "low-priv-not-current" "${C:-khong co dong current roles cua superadmin}"
fi

R=$(grep -o "reduced role values: \[[^]]*\]" $L | head -1)
if echo "$R" | grep -q "^reduced role values: \[VIEWER"; then
  pass "harvest-order-unchanged  (lowPrivEnum qua isLowPrivRole: $R)"
else
  fail "harvest-order-unchanged" "${R:-khong co}"
fi

D=$(det970 $OUT/tier1-vuln-seed10)
[ "$D" = 1 ] && pass "tier1-seed10-970  (Tier-1 ban loi seed 10 co 970)" || fail "tier1-seed10-970" "det970=$D"

E=$(tier1 tier1-fixed-seed10 8081)
L=$OUT/tier1-fixed-seed10.log
D=$(det970 $OUT/tier1-fixed-seed10)
S=$(grep -o "statuses [0-9/]*" $L | tr '\n' ';')
[ "$E" = 0 ] && [ "$D" = 0 ] && pass "tier1-fixed-seed10-no-970  (Tier-1 ban da va seed 10, $S)" || fail "tier1-fixed-seed10-no-970" "exit $E det970=$D $S"
echo "$S" | grep -q "200/200/403" && pass "tier1-fixed-seed10-triple  (bo ba hop le tren ban da va: $S)" || fail "tier1-fixed-seed10-triple" "${S:-khong co bo ba}"

exit $FAILED
