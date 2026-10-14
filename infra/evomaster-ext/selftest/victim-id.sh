#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:-$EM/core/target/evomaster.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
HERE=$THESIS/infra/evomaster-ext/selftest
G=$THESIS/infra/grafana-target
OUT=${1:-$THESIS/infra/em-results/victimid-selftest-$(date +%Y%m%d-%H%M%S)}
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
PROXY_PORT=3102

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

grafana() {
  local name=$1
  $G/up.sh grafana-selftest 3001 > $OUT/$name-up.txt 2>&1
  if ! grep -q "victim id 2 role Admin" $OUT/$name-up.txt; then
    echo up-failed
    return
  fi
  python3 $HERE/capture_proxy.py $PROXY_PORT localhost 3001 $OUT/$name-traffic.jsonl &
  local px=$!
  sleep 2
  java $DEBUG -jar $JAR --blackBox true \
    --bbSwaggerUrl file://$G/grafana-12.1.1-nokill.json \
    --bbTargetUrl http://localhost:$PROXY_PORT \
    --configPath $THESIS/infra/em-config/grafana-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 300 --maxTime 300s --seed 1 \
    --outputFolder $OUT/$name > $OUT/$name.log 2>&1
  local e=$?
  kill $px
  docker rm -f grafana-selftest > /dev/null 2>&1
  echo $e
}

for p in 8080 8081; do
  if [ "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:$p/)" = "000" ]; then
    echo "FAIL  target-up  --  cong $p khong tra loi, khong chay duoc self-test"
    exit 1
  fi
done
for p in 3001 $PROXY_PORT; do
  if [ "$(curl -s -o /dev/null --max-time 2 -w '%{http_code}' http://localhost:$p/)" != "000" ]; then
    echo "FAIL  port-free  --  cong $p dang bi chiem"
    exit 1
  fi
done

echo "jar $(shasum -a 256 $JAR | cut -c1-16)"

E=$(grafana grafana-seed1)
L=$OUT/grafana-seed1.log
T=$OUT/grafana-seed1-traffic.jsonl
[ "$E" = 0 ] && pass "grafana-exit-0  (Grafana seed 1 qua proxy, exit 0)" || fail "grafana-exit-0" "exit $E"

if grep -q "transition candidate PUT:/api/access-control/roles/{roleUID} skipped" $L; then
  pass "grafana-route-missing-skipped  (RestSecurityBuilder.kt routeLooksMissing: PUT /api/access-control/roles/{roleUID} bi bo)"
else
  fail "grafana-route-missing-skipped" "khong co dong skipped cho PUT /api/access-control/roles/{roleUID}"
fi

if grep -q "transition candidate PUT:/api/teams/{team_id}/members/{user_id} score" $L \
   && ! grep -q "transition candidate PUT:/api/teams/{team_id}/members/{user_id} skipped" $L; then
  pass "grafana-param-parent-kept  (routeLooksMissing: cha /api/teams/{team_id}/members co tham so, khong bo)"
else
  fail "grafana-param-parent-kept" "$(grep -o 'transition candidate PUT:/api/teams/{team_id}/members/{user_id}.*' $L | head -1)"
fi

VID=$(grep -o "victim id [0-9]*" $OUT/grafana-seed1-up.txt | awk '{print $3}')
IDS=$(grep -o "victim 'victim' identifiers \[[^]]*\]" $L | head -1)
if [ -n "$VID" ] && echo "$IDS" | grep -q "\[$VID,"; then
  pass "grafana-victim-id  (victimIdentifiers: $IDS, id tu up.sh $VID)"
else
  fail "grafana-victim-id" "up.sh id=$VID, log: ${IDS:-khong co}"
fi

CHOSEN=$(grep "transition chosen: PUT:/api/teams/{team_id}/members/{user_id}" $L | head -1 | cut -c1-8)
N=$(python3 - "$T" "$CHOSEN" "$VID" <<'PY'
import datetime, json, re, sys
path, chosen, vid = sys.argv[1], sys.argv[2], sys.argv[3]
rows = [json.loads(l) for l in open(path, encoding="utf-8")]
if not chosen or not rows:
    print(-1); sys.exit()
last = datetime.datetime.fromtimestamp(rows[-1]["ts"])
hh, mm, ss = (int(x) for x in chosen.split(":"))
c = last.replace(hour=hh, minute=mm, second=ss, microsecond=0)
start = c.timestamp()
pat = re.compile(r"^/api/teams/[^/]+/members/(\d+)$")
ids = [pat.match(r["path"].split("?")[0]).group(1) for r in rows
       if r["ts"] >= start and r["method"] == "PUT" and pat.match(r["path"].split("?")[0])]
print(sum(1 for i in ids if i == vid), len(ids))
PY
)
set -- ${=N}
if [ "$1" != "-1" ] && [ "${2:-0}" -gt 0 ] && [ "$1" = "$2" ]; then
  pass "grafana-transition-uses-id  (setUserInParams: $1/$2 PUT /api/teams/*/members/{user_id} sau $CHOSEN mang id $VID)"
else
  fail "grafana-transition-uses-id" "chosen=$CHOSEN khop=$1 tong=${2:-0}"
fi

NF=$(grep -c "returned 404 after a 2xx source; trying the next candidate" $L)
NC=$(grep -c "transition chosen:" $L)
if [ "$NF" -ge 1 ] && { [ "$NC" = $((NF + 1)) ] || [ "$NC" = "$NF" ]; }; then
  pass "grafana-404-next-candidate  (transitionNotFoundSeen: $NF lan chuyen, $NC transition da chon)"
else
  fail "grafana-404-next-candidate" "chuyen=$NF chon=$NC"
fi
echo "INFO  grafana chosen: $(grep -o 'transition chosen: [^ ]*' $L | cut -d' ' -f3 | tr '\n' ' ')"
echo "INFO  grafana triple codes: $(grep -o "victim '[a-z]*', operator '[a-z]*', [a-z ]*[0-9/-]*" $L | tr '\n' ';')"

E=$(tier1 tier1-vuln 8080)
D=$(det970 $OUT/tier1-vuln)
[ "$E" = 0 ] && [ "$D" = 1 ] && pass "tier1-970  (Tier-1 ban loi seed 1 van no 970)" || fail "tier1-970" "exit $E det970=$D"
if grep -q "Assembled .* transition PUT:/users/{username}/role" $OUT/tier1-vuln.log \
   && [ "$(grep -c 'returned 404 after a 2xx source' $OUT/tier1-vuln.log)" = 0 ]; then
  pass "tier1-same-transition  (Tier-1: bo ba dung PUT /users/{username}/role, 0 lan chuyen ung vien)"
else
  fail "tier1-same-transition" "$(grep -o 'Assembled.*' $OUT/tier1-vuln.log | head -1)"
fi

E=$(tier1 tier1-fixed 8081)
D=$(det970 $OUT/tier1-fixed)
[ "$E" = 0 ] && [ "$D" = 0 ] && pass "tier1-fixed-no-970  (Tier-1 ban da va seed 1 khong co 970)" || fail "tier1-fixed-no-970" "exit $E det970=$D"

exit $FAILED
