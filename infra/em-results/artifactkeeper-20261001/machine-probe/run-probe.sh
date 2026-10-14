#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-ER-06b48c30.jar
WANT=06b48c300e333cdd450e251f56388f13cfb6f65c83ab92a9ab56a8ee820eb83a
BASE=$THESIS/infra/em-results/artifactkeeper-20261001/machine-probe
PROXY=$THESIS/infra/evomaster-ext/selftest/capture_proxy.py
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
JH=$(/usr/libexec/java_home -v 17)
SEED=${SEED:-1}
MAXT=${MAXT:-1200s}
RATE=${RATE:-600}
NEED_TESTS=389
NAME=seed$SEED-$MAXT
LOG=$BASE/logs/$NAME.log
OUT=$BASE/tests/$NAME
TRAF=$BASE/traffic/$NAME.jsonl
T0=$(date +%s)

[ "$(shasum -a 256 $JAR | cut -d' ' -f1)" = "$WANT" ] || { echo "JAR SHA MISMATCH"; exit 1; }
pgrep -f "evomaster.*\.jar" >/dev/null && { echo "EvoMaster khac dang chay"; exit 1; }
[ "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/health)" = 200 ] || { echo "backend not up"; exit 1; }

python3 $PROXY 8212 localhost 8080 $TRAF & PX=$!
sleep 2
rm -rf $OUT
echo "START $(date) seed=$SEED maxTime=$MAXT rate=$RATE" | tee $BASE/progress.log
JAVA_HOME=$JH java $DEBUG -jar $JAR --blackBox true \
  --bbSwaggerUrl file://$BASE/openapi-trimmed.json \
  --bbTargetUrl http://localhost:8212 \
  --configPath $BASE/artifactkeeper-auth-proxied.yaml \
  --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
  --outputFormat PYTHON_UNITTEST --ratePerMinute $RATE --maxTime $MAXT --seed $SEED \
  --outputFolder $OUT > $LOG 2>&1
E=$?
kill $PX 2>/dev/null

DET=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception as e: print('ERR')")
AC=$(grep -c "Assembled .* statuses" $LOG)
VC=$(grep -c "Discarded a VOID stateful-authorization" $LOG)
UC=$(grep -c "Discarded an UNCONFIRMED stateful-authorization" $LOG)
EV=$(grep -a "Evaluated tests" $LOG | tail -1 | awk '{print $NF}')
LG=$(python3 - $TRAF <<'PY'
import json,sys
n={"victim":0,"admin":0,"viewer":0}; bad=0
for l in open(sys.argv[1],encoding="utf-8"):
    try: r=json.loads(l)
    except Exception: continue
    if not r.get("path","").endswith("/auth/login"): continue
    try: who=json.loads(r.get("req_body") or "{}").get("username")
    except Exception: who=None
    if r.get("status")==200 and who in n: n[who]+=1
    elif who in n: bad+=1
print(n["victim"],n["admin"],n["viewer"],bad)
PY
)
set -- ${=LG}; VL=$1 AL=$2 WL=$3 FL=$4
SL=$(pmset -g log | awk -v a="$(date -r $T0 '+%Y-%m-%d %H:%M:%S')" '($1" "$2)>=a' | grep -c "Entering Sleep")

{
echo "DONE $(date) exit=$E"
echo "det970=$DET assembled=$AC void=$VC unconfirmed=$UC evaluated_tests=${EV:-NA}"
echo "logins victim=$VL admin=$AL viewer=$WL failed=$FL sleep_events=$SL"
echo "--- early-stop eval ---"
[ "$VL" -gt 0 ] && [ "$AL" -gt 0 ] && [ "$WL" -gt 0 ] && echo "rule1 OK (3 accounts logged in)" || echo "rule1 DUNG: missing account login"
[ "${EV:-0}" -ge $NEED_TESTS ] && echo "rule2 OK (evaluated_tests ${EV:-NA} >= $NEED_TESTS)" || echo "rule2 WARN: evaluated_tests ${EV:-NA} < $NEED_TESTS (tang maxTime)"
[ "$AC" -gt 0 ] || [ "$VC" -gt 0 ] || [ "$UC" -gt 0 ] && echo "rule3 OK (>=1 triple attempt)" || echo "rule3 DUNG: 0 triple -> doc builder-debug"
echo "RESULT: det970=$DET"
} | tee -a $BASE/progress.log
