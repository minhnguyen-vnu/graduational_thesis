#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:-$EM/core/target/evomaster.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
HERE=$THESIS/infra/evomaster-ext/selftest
A=$THESIS/infra/aicc-target
OUT=${1:-$THESIS/infra/em-results/rolevalue-selftest-$(date +%Y%m%d-%H%M%S)}
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
APP_PORT=8098
PROXY_PORT=8198

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

aicc() {
  local name=$1
  $A/up.sh aicc-selftest $APP_PORT > $OUT/$name-up.txt 2>&1
  if ! grep -q "^user victim [0-9a-f-]* ADMIN ACTIVE$" $OUT/$name-up.txt; then
    echo up-failed
    return
  fi
  python3 $HERE/capture_proxy.py $PROXY_PORT localhost $APP_PORT $OUT/$name-traffic.jsonl &
  local px=$!
  sleep 2
  java $DEBUG -jar $JAR --blackBox true \
    --bbSwaggerUrl file://$A/aicc-47116cf6-nokill.json \
    --bbTargetUrl http://localhost:$PROXY_PORT \
    --configPath $THESIS/infra/em-config/aicc-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 600 --maxTime 300s --seed 1 \
    --outputFolder $OUT/$name > $OUT/$name.log 2>&1
  local e=$?
  kill $px
  for u in admin:aiccseedpass victim:victimpassw0rd viewer:viewerpassw0rd; do
    echo "after login ${u%%:*} $(curl -s -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' \
      -d "{\"username\":\"${u%%:*}\",\"password\":\"${u##*:}\"}" http://localhost:$APP_PORT/api/v1/auth/login)" >> $OUT/$name-up.txt
  done
  docker rm -f aicc-selftest aicc-selftest-db > /dev/null 2>&1
  docker network rm aicc-selftest-net > /dev/null 2>&1
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

E=$(aicc aicc-seed1)
L=$OUT/aicc-seed1.log
T=$OUT/aicc-seed1-traffic.jsonl
U=$OUT/aicc-seed1-up.txt
[ "$E" = 0 ] && pass "aicc-exit-0  (callcenter seed 1 qua proxy, exit 0)" || fail "aicc-exit-0" "exit $E"

R=$(python3 - "$L" "$U" <<'PY'
import re, sys
log, up = sys.argv[1], sys.argv[2]
roles = {m.group(1): m.group(2) for m in re.finditer(r"^user (\S+) \S+ (\S+) \S+$", open(up).read(), re.M)}
lines = re.findall(r"victim '(\w+)' current roles \[([^\]]*)\], reduced role values \[([^\]]*)\]", open(log).read())
read = [v for v, cur, _ in lines if roles.get(v) in [c.strip() for c in cur.split(",")]]
kept = [v for v, _, vals in lines if roles.get(v) in [x.strip() for x in vals.split(",")]]
print(len(lines), len(read), len(kept), ";".join(f"{v}:[{c}]".replace(" ", "") for v, c, _ in lines[:3]) or "-")
PY
)
set -- ${=R}
if [ "$1" -gt 0 ] && [ "$2" = "$1" ]; then
  pass "aicc-current-role-read  (victimRoleValues: $2/$1 dong co vai tro hien tai theo up.sh; $4)"
else
  fail "aicc-current-role-read" "dong=$1 doc_dung=$2 $4"
fi
if [ "$1" -gt 0 ] && [ "$3" = 0 ]; then
  pass "aicc-current-role-excluded  (buildStatefulAuthzTriple roleValues: 0/$1 dong con vai tro hien tai)"
else
  fail "aicc-current-role-excluded" "dong=$1 con_vai_tro_hien_tai=$3"
fi

CHOSEN=$(grep "transition chosen: PUT:/api/v1/users/{userId}" $L | head -1 | cut -c1-8)
P=$(python3 - "$T" "$U" "$CHOSEN" "$L" <<'PY'
import datetime, json, re, sys
path, up, chosen, log = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
acc = {m.group(2): (m.group(1), m.group(3)) for m in re.finditer(r"^user (\S+) (\S+) (\S+) \S+$", open(up).read(), re.M)}
restores = set(re.findall(r"Privilege-restore accepted for '(\w+)' by '\w+' with role '(\w+)'", open(log).read()))
rows = [json.loads(l) for l in open(path, encoding="utf-8")]
if not chosen or not rows:
    print(-1, 0, 0); sys.exit()
last = datetime.datetime.fromtimestamp(rows[-1]["ts"])
hh, mm, ss = (int(x) for x in chosen.split(":"))
start = last.replace(hour=hh, minute=mm, second=ss, microsecond=0).timestamp()
n = same_role = name_kept = 0
for r in rows:
    m = re.match(r"^/api/v1/users/([^/?]+)$", r["path"])
    if r["ts"] < start or r["method"] != "PUT" or not m or m.group(1) not in acc:
        continue
    name, role = acc[m.group(1)]
    try:
        b = json.loads(r["req_body"] or "{}")
    except Exception:
        b = {}
    if (name, b.get("role")) in restores:
        continue
    n += 1
    same_role += b.get("role") == role
    name_kept += b.get("username", name) == name
print(n, same_role, name_kept)
PY
)
set -- ${=P}
if [ "$1" -gt 0 ] && [ "$2" = 0 ]; then
  pass "aicc-transition-role-not-current  (traffic: 0/$1 PUT /api/v1/users/{id} tai khoan cau hinh, tru lenh khoi phuc da chap nhan, gui vai tro hien tai)"
else
  fail "aicc-transition-role-not-current" "chosen=${CHOSEN:-khong} put=$1 cung_vai_tro=$2"
fi
if [ "$1" -gt 0 ] && [ "$3" = "$1" ]; then
  pass "aicc-username-kept  (setUserNameFieldsToVictim: $3/$1 PUT giu username dung ten tai khoan)"
else
  fail "aicc-username-kept" "put=$1 giu_ten=$3"
fi
if grep -q "set user-name fields \[username\] to '[a-z]*' on PUT:/api/v1/users/{userId}" $L; then
  pass "aicc-username-log  (setUserNameFieldsToVictim ghi dong debug tren PUT:/api/v1/users/{userId})"
else
  fail "aicc-username-log" "khong co dong set user-name fields"
fi
echo "INFO  aicc triple codes: $(grep -o "victim '[a-z]*', operator '[a-z]*'[^)]*" $L | tr '\n' ';')"
echo "INFO  aicc logins after run: $(grep '^after login' $U | awk '{print $3"="$4}' | tr '\n' ' ')"

E=$(tier1 tier1-vuln 8080)
D=$(det970 $OUT/tier1-vuln)
[ "$E" = 0 ] && [ "$D" = 1 ] && pass "tier1-970  (Tier-1 ban loi seed 1 van no 970)" || fail "tier1-970" "exit $E det970=$D"
if grep -q "current roles \[[^]]*\], reduced role values" $OUT/tier1-vuln.log; then
  pass "tier1-role-filter-ran  ($(grep -o "victim '[a-z]*' current roles \[[^]]*\], reduced role values \[[^]]*\]" $OUT/tier1-vuln.log | head -1))"
else
  fail "tier1-role-filter-ran" "khong co dong current roles"
fi

E=$(tier1 tier1-fixed 8081)
D=$(det970 $OUT/tier1-fixed)
[ "$E" = 0 ] && [ "$D" = 0 ] && pass "tier1-fixed-no-970  (Tier-1 ban da va seed 1 khong co 970)" || fail "tier1-fixed-no-970" "exit $E det970=$D"

exit $FAILED
