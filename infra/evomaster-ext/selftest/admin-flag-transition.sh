#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:-$EM/core/target/evomaster.jar}
OLDJAR=${OLDJAR:-$EM/evomaster-ER-06b48c30.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
RESEED=$THESIS/infra/em-results/artifactkeeper-20261001/reseed.sh
AUTH=$THESIS/infra/em-config/artifactkeeper-auth.yaml
AUTHPROXY=$THESIS/infra/em-results/artifactkeeper-machine-20261001/artifactkeeper-auth-proxied.yaml
PROXYPY=$THESIS/infra/evomaster-ext/selftest/capture_proxy.py
OUT=${1:-$THESIS/infra/em-results/adminflag-selftest-$(date +%Y%m%d-%H%M%S)}
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

if [ "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:8080/health)" != 200 ]; then
  echo "FAIL  target-up  --  artifact-keeper khong tra loi tren 8080"
  exit 1
fi

echo "=== build trimmed openapi (source + transition + victim-id harvest) ==="
curl -s http://localhost:8080/api/v1/openapi.json | python3 -c "
import sys,json
s=json.load(sys.stdin); p=s['paths']
keep={
 '/api/v1/auth/login':['post'],
 '/api/v1/users':['get'],
 '/api/v1/users/{id}':['get','patch'],
 '/api/v1/admin/analytics/snapshot':['post'],
 '/api/v1/admin/reindex':['post'],
 '/api/v1/admin/cleanup':['post'],
}
np={}
for path,methods in keep.items():
    if path in p:
        np[path]={m:p[path][m] for m in methods if m in p[path]}
s['paths']=np
json.dump(s,open('$OUT/openapi-focus.json','w'))
print('focus operations', sum(len(v) for v in np.values()))
"

run() {
  local tag=$1 jar=$2
  bash $RESEED full > $OUT/$tag-reseed.txt 2>&1
  grep -q "victim login is_admin=True" $OUT/$tag-reseed.txt || { echo "reseed-failed"; return; }
  rm -rf $OUT/$tag
  python3 $PROXYPY 8212 localhost 8080 $OUT/$tag-traffic.jsonl 2>$OUT/$tag-proxy.err &
  local px=$!
  sleep 2
  java $DEBUG -jar $jar --blackBox true \
    --bbSwaggerUrl file://$OUT/openapi-focus.json \
    --bbTargetUrl http://localhost:8212 \
    --configPath $AUTHPROXY \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 600 --maxTime 180s --seed 1 \
    --outputFolder $OUT/$tag > $OUT/$tag.log 2>&1
  local e=$?
  kill $px 2>/dev/null
  echo $e
}

echo "jar-new $(shasum -a 256 $JAR | cut -c1-16)"
echo "jar-old $(shasum -a 256 $OLDJAR | cut -c1-16)"

echo "=== ARM 1: NEW jar (expect fire) ==="
E=$(run new $JAR)
L=$OUT/new.log
[ "$E" = 0 ] && pass "new-exit-0  (EvoMaster ban moi chay xong exit 0)" || fail "new-exit-0" "exit $E"

if grep -qE "transition candidate PATCH:/api/v1/users/\{id\} score 0\.6" $L; then
  pass "score-boost  (transitionScore: PATCH:/users/{id} is_admin duoc cham 0.6 >= nguong top-8)"
else
  fail "score-boost" "khong thay PATCH:/users/{id} score 0.6: $(grep -o 'transition candidate PATCH:/api/v1/users/{id}[^u]*userParam' $L | head -1)"
fi

RV=$(grep -oE "transition candidate PATCH:/api/v1/users/\{id\} score 0\.6 userParam [a-z]+ reducedRoleValues [0-9]+" $L | grep -oE "reducedRoleValues [0-9]+" | awk '{print $2}' | head -1)
if [ -n "$RV" ] && [ "$RV" -ge 1 ]; then
  pass "harvest-false  (harvestReducedRoleCandidates: PATCH:/users/{id} reducedRoleValues=$RV, nhanh BooleanGene+adminFalse)"
else
  fail "harvest-false" "reducedRoleValues=${RV:-khong} tren PATCH:/users/{id}"
fi

if grep -q "transition chosen: PATCH:/api/v1/users/{id}" $L; then
  pass "transition-chosen  (PATCH:/users/{id} is_admin duoc chon lam transition)"
else
  fail "transition-chosen" "chosen=$(grep -o 'transition chosen: [^ ]*' $L | head -1)"
fi

D=$(det970 $OUT/new)
if [ "$D" = 1 ]; then
  pass "new-970  (setRoleFieldToReduced+keepOnlyTargetFields: bo ba is_admin no 970 tren artifact-keeper vuln)"
else
  fail "new-970" "det970=$D; triple codes: $(grep -o "victim '[a-z]*', operator '[a-z]*'[^)]*" $L | tr '\n' ';')"
fi

BF=$(python3 - "$OUT/new-traffic.jsonl" <<'PY2'
import json,re,sys
ok_false=no_null=0
for l in open(sys.argv[1],encoding="utf-8"):
    try: r=json.loads(l)
    except: continue
    if r.get("method")=="PATCH" and re.match(r"^/api/v1/users/[0-9a-f-]{36}$", r.get("path","")) and r.get("status")==200:
        b=(r.get("req_body") or "").replace(" ","")
        if '"is_admin":false' in b: ok_false+=1
        if '"is_admin":null' in b: no_null+=1
print(ok_false, no_null)
PY2
)
set -- ${=BF}
if [ "$1" -ge 1 ] && [ "$2" = 0 ]; then
  pass "demote-body-false  (setAdminFlagActive: PATCH 200 co is_admin=false, 0 lan null -> wrapper nullable duoc ep present)"
else
  fail "demote-body-false" "PATCH200 is_admin=false=$1 null=$2 (fix setter chua chac)"
fi

echo "=== ARM 2: OLD jar ER (falsifiability, expect NO fire) ==="
E=$(run old $OLDJAR)
L2=$OUT/old.log
[ "$E" = 0 ] && pass "old-exit-0  (EvoMaster ER chay xong exit 0)" || fail "old-exit-0" "exit $E"

D2=$(det970 $OUT/old)
if [ "$D2" = 0 ]; then
  pass "old-no-970  (jar ER khong co boolean admin-flip: cung cau hinh KHONG no 970 -> fire la do thay doi nay)"
else
  fail "old-no-970" "det970=$D2 (ER lai no? falsifiability hong)"
fi

if grep -qE "transition candidate PATCH:/api/v1/users/\{id\} score 0\.6" $L2; then
  fail "old-no-boost" "jar ER lai cham PATCH:/users/{id} = 0.6 (khong the)"
else
  pass "old-no-boost  (jar ER khong boost PATCH:/users/{id}; xac nhan score-boost la cua thay doi nay)"
fi

echo "INFO  new triple codes: $(grep -o "victim '[a-z]*', operator '[a-z]*'[^)]*" $L | tr '\n' ';')"
bash $RESEED full > /dev/null 2>&1
exit $FAILED
