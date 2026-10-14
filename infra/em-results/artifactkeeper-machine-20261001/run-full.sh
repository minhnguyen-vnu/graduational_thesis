#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-AF2-6b5606d4.jar
WANT=6b5606d42481fcadb1d3e667a7c0db78fd58da909c9549b57188549b2a671e5d
BASE=$THESIS/infra/em-results/artifactkeeper-machine-20261001
RESEED=$THESIS/infra/em-results/artifactkeeper-20261001/reseed.sh
PROXY=$THESIS/infra/evomaster-ext/selftest/capture_proxy.py
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
JH=$(/usr/libexec/java_home -v 17)
ARM=${ARM:-vuln}
SEEDS=(${=SEEDS:-1 2 3 4 5})
MAXT=${MAXT:-600s}
RATE=${RATE:-600}
NEED_TESTS=389
CSV=$BASE/runs-$ARM.csv
PROG=$BASE/progress-$ARM.log
say(){ echo "$(date +%H:%M:%S) $*" | tee -a $PROG; }

[ "$(shasum -a 256 $JAR | cut -d' ' -f1)" = "$WANT" ] || { echo "JAR SHA MISMATCH"; exit 1; }
pgrep -f "evomaster.*\.jar" >/dev/null && { echo "EvoMaster khac dang chay"; exit 1; }
[ -f $CSV ] || echo "arm,seed,maxtime,exit,det970,assembled,void,unconfirmed,evaluated,victim_login,admin_login,viewer_login,sleep,triple" > $CSV

run(){
  local seed=$1
  local name=$ARM-seed$seed-$MAXT
  bash $RESEED full > $BASE/logs/$name-reseed.txt 2>&1
  grep -q "victim login is_admin=True" $BASE/logs/$name-reseed.txt || { say "$name reseed hong"; echo "$ARM,$seed,$MAXT,RESEED,ERR,0,0,0,NA,NA,NA,NA,NA,NA" >> $CSV; return; }
  local T0=$(date +%s)
  python3 $PROXY 8212 localhost 8080 $BASE/traffic/$name.jsonl 2>$BASE/traffic/$name-proxy.err & local px=$!
  sleep 2
  local OUT=$BASE/tests/$name; rm -rf $OUT
  local log=$BASE/logs/$name.log
  JAVA_HOME=$JH java $DEBUG -jar $JAR --blackBox true \
    --bbSwaggerUrl file://$BASE/openapi-trimmed.json \
    --bbTargetUrl http://localhost:8212 \
    --configPath $BASE/artifactkeeper-auth-proxied.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.25 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute $RATE --maxTime $MAXT --seed $seed \
    --outputFolder $OUT > $log 2>&1
  local e=$?
  kill $px 2>/dev/null
  local d=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")
  local ac=$(grep -c "statuses .* " $log 2>/dev/null); ac=$(grep -c "transition PATCH.* statuses" $log)
  local vc=$(grep -c "Discarded a VOID stateful" $log)
  local uc=$(grep -c "Discarded an UNCONFIRMED stateful" $log)
  local ev=$(grep -a "Evaluated tests" $log | tail -1 | awk '{print $NF}')
  local lg=$(python3 - $BASE/traffic/$name.jsonl <<'PY'
import json,sys
n={"victim":0,"admin":0,"viewer":0}
for l in open(sys.argv[1],encoding="utf-8"):
    try: r=json.loads(l)
    except: continue
    if not r.get("path","").endswith("/auth/login"): continue
    try: who=json.loads(r.get("req_body") or "{}").get("username")
    except: who=None
    if r.get("status")==200 and who in n: n[who]+=1
print(n["victim"],n["admin"],n["viewer"])
PY
)
  set -- ${=lg}; local vl=$1 al=$2 wl=$3
  local tr=$(grep -o "transition PATCH:[^,]*, statuses [0-9/]*" $log | tr '\n' ';')
  local sl=$(pmset -g log | awk -v a="$(date -r $T0 '+%Y-%m-%d %H:%M:%S')" '($1" "$2)>=a' | grep -c "Entering Sleep")
  echo "$ARM,$seed,$MAXT,$e,$d,$ac,$vc,$uc,${ev:-NA},$vl,$al,$wl,$sl,${tr:-NA}" >> $CSV
  say "$name exit=$e det970=$d assembled=$ac void=$vc evaluated=${ev:-NA} logins=v:$vl,a:$al,w:$wl sleep=$sl triple=${tr:-none}"
  [ "$sl" = 0 ] || { say "DUNG: may ngu trong $name"; exit 1; }
  if [ "$seed" = "${SEEDS[1]}" ]; then
    [ "$vl" -gt 0 ] && [ "$al" -gt 0 ] && [ "$wl" -gt 0 ] || { say "DUNG SOM: seed $seed thieu login tai khoan"; exit 1; }
    [ "${ev:-0}" -ge $NEED_TESTS ] || say "CANH BAO: seed $seed evaluated ${ev:-NA} < $NEED_TESTS"
  fi
}
say "START arm=$ARM seeds=$SEEDS maxTime=$MAXT jar=AF2-6b5606d4"
for s in $SEEDS; do run $s; done
say "DONE arm=$ARM det970 per seed: $(awk -F, -v a=$ARM '$1==a{print $2":"$5}' $CSV | tr '\n' ' ')"
