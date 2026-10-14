#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:-$EM/core/target/evomaster.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
HERE=$THESIS/infra/evomaster-ext/selftest
BT=$THESIS/infra/bamf-target
OUT=${1:-$THESIS/infra/em-results/emptyroles-selftest-$(date +%Y%m%d-%H%M%S)}
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
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 1 \
    --outputFolder $OUT/$name > $OUT/$name.log 2>&1
  echo $?
}

bamf() {
  local name=$1
  $BT/up.sh bamf-selftest 8120 8221 15434 16381 $OUT/$name-target dotless > $OUT/$name-up.txt 2>&1
  if [ $(grep -c "^login .* 200$" $OUT/$name-up.txt) != 3 ]; then
    echo up-failed
    return
  fi
  python3 -c "
import json
s=json.load(open('$OUT/$name-target/openapi.json'))
del s['paths']['/api/v1/role-assignments']['put']
del s['paths']['/api/v1/users/{email}']['delete']
del s['components']['schemas']['UserUpdate']['properties']['password']
del s['paths']['/api/v1/role-assignments/{provider_name}/{email}/{role_name}']['delete']
json.dump(s,open('$OUT/$name-target/openapi-nokill.json','w'))"
  python3 $HERE/capture_proxy.py 8222 localhost 8120 $OUT/$name-traffic.jsonl &
  local px=$!
  kill $(cat $OUT/$name-target/shim.pid)
  $BT/.venv/bin/python $BT/login_shim.py 8221 http://localhost:8222 > $OUT/$name-shim.log 2>&1 &
  local sh=$!
  sed 's#localhost:8211#localhost:8221#' $THESIS/infra/em-config/bamf-auth-dotless.yaml > $OUT/bamf-auth.yaml
  sleep 2
  java $DEBUG -jar $JAR --blackBox true \
    --bbSwaggerUrl file://$OUT/$name-target/openapi-nokill.json \
    --bbTargetUrl http://localhost:8222 \
    --configPath $OUT/bamf-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 600 --maxTime 600s --seed 1 \
    --outputFolder $OUT/$name > $OUT/$name.log 2>&1
  local e=$?
  kill $px $sh
  $BT/down.sh bamf-selftest > /dev/null 2>&1
  echo $e
}

for p in 8080 8081; do
  if [ "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:$p/)" = "000" ]; then
    echo "FAIL  target-up  --  cong $p khong tra loi, khong chay duoc self-test"
    exit 1
  fi
done
for p in 8120 8221 8222 15434 16381; do
  if lsof -nP -iTCP:$p -sTCP:LISTEN > /dev/null 2>&1; then
    echo "FAIL  port-free  --  cong $p dang bi chiem"
    exit 1
  fi
done

echo "jar $(shasum -a 256 $JAR | cut -c1-16)"

E=$(bamf bamf-seed1)
L=$OUT/bamf-seed1.log
T=$OUT/bamf-seed1-traffic.jsonl
[ "$E" = 0 ] && pass "bamf-exit-0  (bamf seed 1 qua proxy, exit 0)" || fail "bamf-exit-0" "exit $E"

N=$(grep -c "could not target victim 'victim' on PATCH:/api/v1/users/{email}" $L)
[ "$N" = 0 ] && pass "bamf-email-param-targeted  (setUserInParams, userEmailParamSignals: 0 dong could not target)" || fail "bamf-email-param-targeted" "$N dong could not target"

R=$(python3 - "$T" "$L" <<'PY'
import datetime, json, re, sys
path, log = sys.argv[1], sys.argv[2]
m = re.search(r"^(\d\d:\d\d:\d\d)\.\d+ .*transition chosen: PATCH:/api/v1/users/\{email\}", open(log).read(), re.M)
rows = [json.loads(l) for l in open(path, encoding="utf-8")]
if not m or not rows:
    print("0 -"); sys.exit()
last = datetime.datetime.fromtimestamp(rows[-1]["ts"])
hh, mm, ss = (int(x) for x in m.group(1).split(":"))
start = last.replace(hour=hh, minute=mm, second=ss, microsecond=0).timestamp()
hits = [(r["status"], (r["req_body"] or "")[:60]) for r in rows
        if r["ts"] >= start and r["method"] == "PATCH"
        and r["path"] == "/api/v1/users/victim"]
print(len(hits), ";".join(f"{s}:{b}" for s, b in hits[:4]) or "-")
PY
)
set -- ${=R}
[ "$1" -gt 0 ] && pass "bamf-transition-on-victim  ($1 PATCH /users/victim sau khi chon transition; ${@:2})" || fail "bamf-transition-on-victim" "0 PATCH toi victim"

A=$(grep -cE "Assembled .* statuses|Discarded a VOID stateful-authorization|Discarded an UNCONFIRMED stateful-authorization" $L)
[ "$A" -gt 0 ] && pass "bamf-triple-attempted  ($A lan thu bo ba: $(grep -oE "(codes|statuses) [0-9/]*" $L | tr '\n' ';'))" || fail "bamf-triple-attempted" "0 lan thu bo ba"

V=$(grep -o "reduced role values: .*" $L | head -1)
echo "$V" | grep -q "values: \[\[\]" && pass "empty-role-value-harvested  (harvestReducedRoleCandidates, roleArrays: $V)" || fail "empty-role-value-harvested" "${V:-khong co}"

R=$(python3 - "$T" "$L" <<'PY2'
import datetime, json, re, sys
path, log = sys.argv[1], sys.argv[2]
m = re.search(r"^(\d\d:\d\d:\d\d)\.\d+ .*transition chosen: PATCH:/api/v1/users/\{email\}", open(log).read(), re.M)
rows = [json.loads(l) for l in open(path, encoding="utf-8")]
if not m or not rows:
    print("0 0"); sys.exit()
last = datetime.datetime.fromtimestamp(rows[-1]["ts"])
hh, mm, ss = (int(x) for x in m.group(1).split(":"))
start = last.replace(hour=hh, minute=mm, second=ss, microsecond=0).timestamp()
sent = ok = 0
for r in rows:
    if r["ts"] < start or r["method"] != "PATCH" or r["path"] != "/api/v1/users/victim":
        continue
    try:
        b = json.loads(r["req_body"] or "{}")
    except Exception:
        continue
    if b.get("roles") == []:
        sent += 1
        ok += 1 if 200 <= r["status"] < 300 else 0
print(sent, ok)
PY2
)
set -- ${=R}
[ "$1" -gt 0 ] && pass "empty-roles-sent  (clearRoleArrays: $1 PATCH /users/victim voi roles [])" || fail "empty-roles-sent" "0 PATCH roles []"
[ "$2" -gt 0 ] && pass "empty-roles-accepted  ($2 PATCH roles [] tra 2xx)" || fail "empty-roles-accepted" "sent=$1 ok=$2"
TR=$(grep -oE "(codes|statuses) 2[0-9][0-9]/2[0-9][0-9]/[0-9]+" $L | tr '\n' ';')
[ -n "$TR" ] && pass "bamf-valid-triple  (bo ba co source va transition 2xx: $TR)" || fail "bamf-valid-triple" "khong co bo ba source va transition 2xx"
echo "INFO  bamf-970 det970=$(det970 $OUT/bamf-seed1)"

E=$(tier1 tier1-vuln 8080)
D=$(det970 $OUT/tier1-vuln)
[ "$E" = 0 ] && [ "$D" = 1 ] && pass "tier1-970  (Tier-1 ban loi seed 1 van no 970)" || fail "tier1-970" "exit $E det970=$D"

E=$(tier1 tier1-fixed 8081)
D=$(det970 $OUT/tier1-fixed)
[ "$E" = 0 ] && [ "$D" = 0 ] && pass "tier1-fixed-no-970  (Tier-1 ban da va seed 1 khong co 970)" || fail "tier1-fixed-no-970" "exit $E det970=$D"

exit $FAILED
