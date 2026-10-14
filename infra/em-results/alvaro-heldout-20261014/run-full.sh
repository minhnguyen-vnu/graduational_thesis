#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-P2e-6ae8277b.jar
WANT=6ae8277bef22957486cbf3059c68f45f72e1582da837a79a933ba8a4617c751e
BASE=$THESIS/infra/em-results/alvaro-heldout-20261014
RESEED=$BASE/reseed.sh
PROXY=$THESIS/infra/evomaster-ext/selftest/capture_proxy.py
SPEC=$BASE/openapi-nokill.json
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
JH=$(/usr/libexec/java_home -v 17)
ARM=${ARM:-auto}
SEEDS=(${=SEEDS:-1 2 3 4 5 6 7 8 9 10})
MAXT=${MAXT:-600s}
RATE=${RATE:-600}
NEED_TESTS=${NEED_TESTS:-150}
CSV=$BASE/runs-$ARM.csv
PROG=$BASE/progress-$ARM.log
say(){ echo "$(date +%H:%M:%S) $*" | tee -a $PROG; }

[ "$(shasum -a 256 $JAR | cut -d' ' -f1)" = "$WANT" ] || { echo "JAR SHA MISMATCH"; exit 1; }
[ -f $SPEC ] || { echo "SPEC MISSING $SPEC"; exit 1; }
pgrep -f "evomaster.*\.jar" >/dev/null && { echo "EvoMaster khac dang chay"; exit 1; }
[ -f $CSV ] || echo "arm,seed,maxtime,exit,det970,assembled,void,unconfirmed,evaluated,victim_login,operator_login,low_login,sleep,transition" > $CSV

run(){
  local seed=$1
  local name=$ARM-seed$seed-$MAXT
  bash $RESEED > $BASE/logs/$name-reseed.txt 2>&1
  grep -q "RESEED_OK victim_role=ADMIN" $BASE/logs/$name-reseed.txt || { say "$name reseed hong"; echo "$ARM,$seed,$MAXT,RESEED,ERR,0,0,0,NA,NA,NA,NA,NA,NA" >> $CSV; return; }
  local T0=$(date +%s)
  python3 $PROXY 8212 localhost 3000 $BASE/traffic/$name.jsonl 2>$BASE/traffic/$name-proxy.err & local px=$!
  sleep 2
  local OUT=$BASE/tests/$name; rm -rf $OUT
  local log=$BASE/logs/$name.log
  local XTRA=()
  [ "$ARM" = declared ] && XTRA=(--statefulAuthzTransition "PATCH /user/role email=victim@test.com role=USER")
  JAVA_HOME=$JH java $DEBUG -jar $JAR --blackBox true \
    --bbSwaggerUrl file://$SPEC \
    --bbTargetUrl http://localhost:8212 \
    --configPath $THESIS/infra/em-config/alvaro-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.25 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute $RATE --maxTime $MAXT --seed $seed \
    $XTRA \
    --outputFolder $OUT > $log 2>&1
  local e=$?
  kill $px 2>/dev/null
  local d=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")
  local ac=$(grep -cE "transition [A-Z]+.*statuses" $log)
  local vc=$(grep -c "Discarded a VOID stateful" $log)
  local uc=$(grep -c "Discarded an UNCONFIRMED stateful" $log)
  local ev=$(grep -a "Evaluated tests" $log | tail -1 | awk '{print $NF}')
  local lg=$(python3 - $BASE/traffic/$name.jsonl <<'PY'
import json,sys,os
m={"admin@test.com":"operator","victim@test.com":"victim","plain@test.com":"low"}
n={"victim":0,"operator":0,"low":0}
if os.path.exists(sys.argv[1]):
  for l in open(sys.argv[1],encoding="utf-8"):
    try: r=json.loads(l)
    except: continue
    if not r.get("path","").endswith("/login"): continue
    try: em=json.loads(r.get("req_body") or "{}").get("email")
    except: em=None
    if r.get("status")==201 and em in m: n[m[em]]+=1
    elif r.get("status")==200 and em in m: n[m[em]]+=1
print(n["victim"],n["operator"],n["low"])
PY
)
  set -- ${=lg}; local vl=${1:-0} ol=${2:-0} ll=${3:-0}
  local tr=$(grep -oE "transition [A-Z]+:[^,]*, statuses [0-9/]*" $log | tr '\n' ';')
  local sl=$(pmset -g log | awk -v a="$(date -r $T0 '+%Y-%m-%d %H:%M:%S')" '($1" "$2)>=a' | grep -c "Entering Sleep")
  echo "$ARM,$seed,$MAXT,$e,$d,$ac,$vc,$uc,${ev:-NA},$vl,$ol,$ll,$sl,${tr:-NA}" >> $CSV
  say "$name exit=$e det970=$d assembled=$ac void=$vc evaluated=${ev:-NA} logins=v:$vl,o:$ol,l:$ll sleep=$sl transition=${tr:-none}"
  [ "$sl" = 0 ] || { say "DUNG: may ngu trong $name"; exit 1; }
  if [ "$seed" = "${SEEDS[1]}" ]; then
    [ "$vl" -gt 0 ] && [ "$ol" -gt 0 ] || { say "DUNG SOM: seed $seed thieu login victim/operator (v:$vl o:$ol)"; exit 1; }
    [ "${ev:-0}" -ge $NEED_TESTS ] || say "CANH BAO: seed $seed evaluated ${ev:-NA} < $NEED_TESTS"
  fi
}
say "START arm=$ARM seeds=$SEEDS maxTime=$MAXT rate=$RATE jar=P2e-6ae8277b D1=off"
for s in $SEEDS; do run $s; done
say "DONE arm=$ARM det970 per seed: $(awk -F, -v a=$ARM '$1==a{print $2\":\"$5}' $CSV | tr '\n' ' ')"
