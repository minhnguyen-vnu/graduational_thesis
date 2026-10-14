#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:-$EM/core/target/evomaster.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
HERE=$THESIS/infra/evomaster-ext/selftest
TT=$THESIS/infra/truthy-target
OUT=${1:-$THESIS/infra/em-results/numrole-selftest-$(date +%Y%m%d-%H%M%S)}
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
APP_PORT=8101
PROXY_PORT=8201

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

truthy() {
  local name=$1
  $TT/up.sh truthy-selftest $APP_PORT > $OUT/$name-up.txt 2>&1
  if ! grep -q "^user victim [0-9]* superuser active$" $OUT/$name-up.txt; then
    echo up-failed
    return
  fi
  python3 $HERE/capture_proxy.py $PROXY_PORT localhost $APP_PORT $OUT/$name-traffic.jsonl &
  local px=$!
  sleep 2
  java $DEBUG -jar $JAR --blackBox true \
    --bbSwaggerUrl file://$TT/truthy-9b9a61be-nokill2.json \
    --bbTargetUrl http://localhost:$PROXY_PORT \
    --configPath $THESIS/infra/em-config/truthy-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 600 --maxTime 300s --seed 1 \
    --outputFolder $OUT/$name > $OUT/$name.log 2>&1
  local e=$?
  kill $px
  docker rm -f truthy-selftest truthy-selftest-db truthy-selftest-redis > /dev/null 2>&1
  docker network rm truthy-selftest-net > /dev/null 2>&1
  echo $e
}

for p in 8080 8081; do
  if [ "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:$p/)" = "000" ]; then
    echo "FAIL  target-up  --  cong $p khong tra loi, khong chay duoc self-test"
    exit 1
  fi
done
for p in $APP_PORT $PROXY_PORT; do
  if [ "$(curl -s -o /dev/null --max-time 2 -w '%{http_code}' http://localhost:$p/)" != "000" ]; then
    echo "FAIL  port-free  --  cong $p dang bi chiem"
    exit 1
  fi
done

echo "jar $(shasum -a 256 $JAR | cut -c1-16)"

E=$(truthy truthy-seed1)
L=$OUT/truthy-seed1.log
T=$OUT/truthy-seed1-traffic.jsonl
U=$OUT/truthy-seed1-up.txt
[ "$E" = 0 ] && pass "truthy-exit-0  (truthy seed 1 qua proxy, exit 0)" || fail "truthy-exit-0" "exit $E"

V=$(grep -o "reduced role values: \[[^]]*\]" $L | head -1)
if echo "$V" | grep -q "\[1, 0, 2,"; then
  pass "truthy-numeric-values  (harvestReducedRoleCandidates, NumberGene: $V)"
else
  fail "truthy-numeric-values" "${V:-khong co dong reduced role values}"
fi

C=$(grep -o "victim '[a-z]*' current roles \[[^]]*\]" $L | head -3 | tr '\n' ';')
if grep -q "victim 'victim' current roles \[1, superuser\]" $L; then
  pass "truthy-role-object-read  (victimRoleValues, roleObjectFields: $C)"
else
  fail "truthy-role-object-read" "${C:-khong co dong current roles}"
fi

VID=$(grep -o "^user victim [0-9]*" $U | awk '{print $3}')
IDS=$(grep -o "victim 'victim' identifiers \[[^]]*\]" $L | head -1)
if [ -n "$VID" ] && echo "$IDS" | grep -qE "\[$VID(,|\])"; then
  pass "truthy-victim-id-first  (victimObjects, namedByUserField: $IDS, id tu up.sh $VID)"
else
  fail "truthy-victim-id-first" "up.sh id=$VID, log: ${IDS:-khong co}"
fi

R=$(python3 - "$T" "$U" "$L" <<'PY'
import datetime, json, re, sys
path, up, log = sys.argv[1], sys.argv[2], sys.argv[3]
acc = {m.group(2): m.group(1) for m in re.finditer(r"^user (\S+) (\S+) \S+ \S+$", open(up).read(), re.M)}
text = open(log).read()
m = re.search(r"^(\d\d:\d\d:\d\d)\.\d+ .*transition chosen: PUT:/users/\{id\}", text, re.M)
rows = [json.loads(l) for l in open(path, encoding="utf-8")]
if not m or not rows:
    print("0 0 0 -"); sys.exit()
last = datetime.datetime.fromtimestamp(rows[-1]["ts"])
hh, mm, ss = (int(x) for x in m.group(1).split(":"))
start = last.replace(hour=hh, minute=mm, second=ss, microsecond=0).timestamp()
seq = []
for r in rows:
    p = re.match(r"^/users/(\d+)$", r["path"])
    if r["ts"] < start or r["method"] != "PUT" or not p or p.group(1) not in acc:
        continue
    try:
        b = json.loads(r["req_body"] or "{}")
    except Exception:
        b = {}
    seq.append((acc[p.group(1)], b.get("roleId"), r["status"]))
rejected_then_next = sum(1 for a, b in zip(seq, seq[1:])
                         if a[0] == b[0] and a[2] not in (200, 401, 403, 404) and a[2] >= 400 and a[1] != b[1])
ok = sum(1 for s in seq if s[2] == 200 and s[1] is not None and float(s[1]) == 2.0)
print(len(seq), rejected_then_next, ok, ";".join(f"{a}:{b}:{c}" for a, b, c in seq[:8]) or "-")
PY
)
set -- ${=R}
if [ "$2" -gt 0 ]; then
  pass "truthy-next-value-after-reject  (transitionRejectedRoleValue: $2 lan PUT /users/{id} bi tu choi roi thu gia tri khac; $4)"
else
  fail "truthy-next-value-after-reject" "put=$1 $4"
fi
if [ "$3" -gt 0 ]; then
  pass "truthy-demotion-accepted  ($3 PUT /users/{id} roleId=2 tra 200)"
else
  fail "truthy-demotion-accepted" "put=$1 $4"
fi
TR=$(grep -o "victim '[a-z]*', operator '[a-z]*'[^)]*" $L | tr '\n' ';')
if echo "$TR" | grep -qE "(codes|statuses) 2[0-9][0-9]/2[0-9][0-9]/[0-9]+"; then
  pass "truthy-valid-triple  (bo ba co source va transition 2xx: $TR)"
else
  fail "truthy-valid-triple" "${TR:-khong co bo ba}"
fi

E=$(tier1 tier1-vuln 8080)
D=$(det970 $OUT/tier1-vuln)
[ "$E" = 0 ] && [ "$D" = 1 ] && pass "tier1-970  (Tier-1 ban loi seed 1 van no 970)" || fail "tier1-970" "exit $E det970=$D"

E=$(tier1 tier1-fixed 8081)
D=$(det970 $OUT/tier1-fixed)
[ "$E" = 0 ] && [ "$D" = 0 ] && pass "tier1-fixed-no-970  (Tier-1 ban da va seed 1 khong co 970)" || fail "tier1-fixed-no-970" "exit $E det970=$D"

exit $FAILED
