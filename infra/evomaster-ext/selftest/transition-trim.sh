#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:-$EM/core/target/evomaster.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
HERE=$THESIS/infra/evomaster-ext/selftest
OUT=${1:-$THESIS/infra/em-results/transitiontrim-selftest-$(date +%Y%m%d-%H%M%S)}
export JAVA_HOME=$(/usr/libexec/java_home -v 17)

GG_AIRFLOW_LOG=$THESIS/infra/em-results/genesetguard-chain-20260925/selftest-geneguard/airflow-seed1.log
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
PROXY_PORT=8184

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
  rm -f $OUT/$name-traffic.jsonl
  python3 $HERE/capture_proxy.py $PROXY_PORT localhost 8082 $OUT/$name-traffic.jsonl &
  local px=$!
  sleep 2
  java $DEBUG -jar $JAR --blackBox true \
    --bbSwaggerUrl file://$THESIS/infra/airflow-target/airflow-merged-nodelete.json \
    --bbTargetUrl http://localhost:$PROXY_PORT \
    --configPath $THESIS/infra/em-config/airflow-auth-3users.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 60 --maxTime 600s --seed 1 \
    --outputFolder $OUT/$name > $OUT/$name.log 2>&1
  local e=$?
  kill $px
  zsh $THESIS/infra/airflow-target/reset-3users.sh http://localhost:8082 > $OUT/$name-reset-after.txt 2>&1
  echo $e
}

for p in 8080 8081 8082; do
  if [ "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:$p/)" = "000" ]; then
    echo "FAIL  target-up  --  cong $p khong tra loi, khong chay duoc self-test"
    exit 1
  fi
done
if [ "$(curl -s -o /dev/null --max-time 2 -w '%{http_code}' http://localhost:$PROXY_PORT/)" != "000" ]; then
  echo "FAIL  proxy-port-free  --  cong $PROXY_PORT dang bi chiem"
  exit 1
fi
[ -f $GG_AIRFLOW_LOG ] || { echo "FAIL  baseline-log  --  khong thay $GG_AIRFLOW_LOG"; exit 1; }

echo "jar $(shasum -a 256 $JAR | cut -c1-16)"

if grep -q "victim 'victim', operator 'admin', codes 204/422/204" $GG_AIRFLOW_LOG; then
  pass "gg-baseline-422  (jar GG, Airflow: transition cua cap victim/admin tra 422)"
else
  fail "gg-baseline-422" "log jar GG khong co dong 204/422/204 cho victim/admin"
fi

E=$(airflow airflow-seed1)
L=$OUT/airflow-seed1.log
T=$OUT/airflow-seed1-traffic.jsonl
[ "$E" = 0 ] && pass "airflow-exit-0  (Airflow seed 1 qua proxy, exit 0)" || fail "airflow-exit-0" "exit $E"

R=$(grep -o "removed optional fields \[[^]]*\] from PATCH:/auth/fab/v1/users/{username}" $L | grep -v "fields \[\]" | head -1)
if [ -n "$R" ]; then
  pass "airflow-fields-removed  (RestSecurityBuilder.kt keepOnlyTargetFields: $R)"
else
  fail "airflow-fields-removed" "khong co dong 'removed optional fields [...]' khac rong tren PATCH users"
fi

CHOSEN=$(grep "Stateful-authorization transition chosen" $L | head -1 | cut -c1-8)
V=$(python3 - "$T" "$CHOSEN" <<'PY'
import datetime, json, sys
path, chosen = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(path, encoding="utf-8")]
start = None
if chosen and rows:
    last = datetime.datetime.fromtimestamp(rows[-1]["ts"])
    hh, mm, ss = (int(x) for x in chosen.split(":"))
    c = last.replace(hour=hh, minute=mm, second=ss, microsecond=0)
    if c > last:
        c -= datetime.timedelta(days=1)
    start = c.timestamp()
n = bad = 0
keys = set()
for r in rows:
    if start is None or r["ts"] < start:
        continue
    if r["method"] != "PATCH" or not r["path"].startswith("/auth/fab/v1/users/"):
        continue
    n += 1
    try:
        k = set(json.loads(r["req_body"]).keys()) if r["req_body"] else set()
    except Exception:
        k = {"<not-json>"}
    q = "?" in r["path"]
    keys |= k
    if not k <= {"roles"} or q:
        bad += 1
print(n, bad, ",".join(sorted(keys)) or "-")
PY
)
set -- ${=V}
if [ -n "$CHOSEN" ] && [ "$1" -gt 0 ] && [ "$2" = 0 ]; then
  pass "airflow-sent-roles-only  ($1 PATCH users sau $CHOSEN, khoa trong body: $3, khong query)"
else
  fail "airflow-sent-roles-only" "chosen=$CHOSEN patch=$1 sai=$2 khoa=$3"
fi
GR=$(grep -c "Privilege-restore" $GG_AIRFLOW_LOG)
NR=$(grep -c "Privilege-restore" $L)
if [ "$GR" -gt 0 ] && [ "$NR" = 0 ]; then
  pass "airflow-no-empty-restore  (RestSecurityBuilder.kt setAllRoleFieldsTo bo qua ArrayGene<ObjectGene>: jar GG $GR dong Privilege-restore, jar moi 0)"
else
  fail "airflow-no-empty-restore" "jar GG $GR dong, jar moi $NR dong Privilege-restore"
fi
echo "INFO  airflow triple codes: $(grep -o "victim '[a-z]*', operator '[a-z]*', [a-z ]*[0-9/-]*" $L | tr '\n' ';')"
echo "INFO  airflow restore: $(grep -o "Privilege-restore [a-z]* .* -> [0-9-]*" $L | tr '\n' ';')"

E=$(tier1 tier1-vuln 8080)
D=$(det970 $OUT/tier1-vuln)
[ "$E" = 0 ] && [ "$D" = 1 ] && pass "tier1-970  (Tier-1 ban loi seed 1 van no 970)" || fail "tier1-970" "exit $E det970=$D"
if grep -q "removed optional fields \[\] from PUT:/users/{username}/role" $OUT/tier1-vuln.log; then
  pass "tier1-nothing-removed  (Tier-1: transition PUT /users/{username}/role khong mat truong nao)"
else
  fail "tier1-nothing-removed" "$(grep -o 'removed optional fields.*' $OUT/tier1-vuln.log | head -1)"
fi

E=$(tier1 tier1-fixed 8081)
D=$(det970 $OUT/tier1-fixed)
[ "$E" = 0 ] && [ "$D" = 0 ] && pass "tier1-fixed-no-970  (Tier-1 ban da va seed 1 khong co 970)" || fail "tier1-fixed-no-970" "exit $E det970=$D"

exit $FAILED
