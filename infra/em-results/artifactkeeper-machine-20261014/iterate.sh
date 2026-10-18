#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:-$EM/core/target/evomaster.jar}
BASE=$THESIS/infra/em-results/artifactkeeper-machine-20261014
RESEED=$THESIS/infra/em-results/artifactkeeper-20261001/reseed.sh
PROXY=$THESIS/infra/evomaster-ext/selftest/capture_proxy.py
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
JH=$(/usr/libexec/java_home -v 17)
SEED=${SEED:-1}
MAXT=${MAXT:-1200s}
RATE=${RATE:-600}
TAG=${TAG:-iter-$(date +%H%M%S)}
OUT=$BASE/$TAG
say(){ echo "$(date +%H:%M:%S) $*" | tee -a $BASE/iterate.log; }

[ "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:8080/health)" = 200 ] || { say "$TAG target-down"; exit 1; }
pgrep -f "evomaster.*\.jar" >/dev/null && { say "$TAG evomaster-already-running"; exit 1; }

bash $RESEED full > $OUT-reseed.txt 2>&1
grep -q "victim login is_admin=True" $OUT-reseed.txt || { say "$TAG reseed-failed"; exit 1; }
VID=$(grep -oE "victim id=[0-9a-f-]+" $OUT-reseed.txt | head -1 | cut -d= -f2)

python3 $PROXY 8212 localhost 8080 $OUT-traffic.jsonl 2>$OUT-proxy.err &
PX=$!
sleep 2
rm -rf $OUT
JAVA_HOME=$JH java $DEBUG -jar $JAR --blackBox true \
  --bbSwaggerUrl file://$BASE/openapi-trimmed.json \
  --bbTargetUrl http://localhost:8212 \
  --configPath $BASE/artifactkeeper-auth-proxied.yaml \
  --useExperimentalOracles true --extraPhaseBudgetPercentage 0.25 \
  --statefulAuthzTwoCredentialJudgment false \
  --outputFormat PYTHON_UNITTEST --ratePerMinute $RATE --maxTime $MAXT --seed $SEED \
  --outputFolder $OUT > $OUT.log 2>&1
E=$?
kill $PX 2>/dev/null

D=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")
BODY=$(python3 - "$OUT-traffic.jsonl" "$VID" <<'PY'
import json,sys,re
p=sys.argv[1]
f=n=other=0
try:
    lines=open(p,encoding="utf-8",errors="ignore")
except Exception:
    print("patch200_false=NA patch200_null=NA"); sys.exit()
for l in lines:
    try: r=json.loads(l)
    except: continue
    if r.get("method")!="PATCH": continue
    if not re.match(r"^/api/v1/users/[0-9a-f-]{36}$", r.get("path","")): continue
    if r.get("status")!=200: continue
    b=(r.get("req_body") or "").replace(" ","")
    if '"is_admin":false' in b: f+=1
    elif '"is_admin":null' in b: n+=1
    else: other+=1
print(f"patch200_false={f} patch200_null={n} patch200_other={other}")
PY
)
CHOSEN=$(grep -ac "transition chosen: PATCH:/api/v1/users/{id}" $OUT.log)
ASM=$(grep -c "transition PATCH.* statuses" $OUT.log)
UNCONF=$(grep -c "Discarded an UNCONFIRMED" $OUT.log)
say "$TAG exit=$E det970=$D assembled=$ASM patch_chosen=$CHOSEN unconfirmed=$UNCONF $BODY"
