#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:-$EM/evomaster-P2f-64ee8ffc.jar}
BASE=$THESIS/infra/em-results/artifactkeeper-machine-20261014
RESEED=$THESIS/infra/em-results/artifactkeeper-20261001/reseed.sh
PROXY=$THESIS/infra/evomaster-ext/selftest/capture_proxy.py
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
JH=$(/usr/libexec/java_home -v 17)
ARM=${ARM:-vuln}
SEEDS=${SEEDS:-"1 2 3 4 5"}
MAXT=${MAXT:-1200s}
RATE=${RATE:-600}
PROG=$BASE/progress-fixjar-$ARM.log
CSV=$BASE/runs-fixjar-$ARM.csv
say(){ echo "$(date +%H:%M:%S) $*" | tee -a $PROG; }

say "BATCH fix-jar P2f-64ee8ffc arm=$ARM seeds=[$SEEDS] maxTime=$MAXT rate=$RATE jar=$JAR:t"
say "MEASURES per seed: det970, assembled triples, PATCH:/users/{id} transition-chosen, UNCONFIRMED discards, PATCH-200 is_admin body false/null/other"
say "EARLY-STOP: if the first 3 seeds all show det970=0 and 0 assembled triples, stop and record a deviation"
say "SLEEP-STOP: if pmset logs a new Entering Sleep across a run, stop and record a deviation"

pgrep -f "evomaster.*\.jar" >/dev/null && { say "abort evomaster-already-running"; exit 1; }
[ -f $CSV ] || echo "arm,seed,exit,det970,assembled,chosen,unconfirmed,patch200_false,patch200_null,patch200_other,slept" > $CSV

n=0; fires=0; asmsum=0
for SEED in ${=SEEDS}; do
  n=$((n+1))
  TAG=fixjar-$ARM-seed$SEED
  OUT=$BASE/$TAG
  bash $RESEED full > $OUT-reseed.txt 2>&1
  grep -q "victim login is_admin=True" $OUT-reseed.txt || { say "$TAG reseed-failed"; echo "$ARM,$SEED,NA,NA,NA,NA,NA,NA,NA,NA,NA" >> $CSV; continue; }
  VID=$(grep -oE "victim id=[0-9a-f-]+" $OUT-reseed.txt | head -1 | cut -d= -f2)
  [ "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:8080/health)" = 200 ] || { say "$TAG target-down"; echo "$ARM,$SEED,NA,NA,NA,NA,NA,NA,NA,NA,NA" >> $CSV; continue; }
  python3 $PROXY 8212 localhost 8080 $OUT-traffic.jsonl 2>$OUT-proxy.err &
  PX=$!
  sleep 2
  rm -rf $OUT
  SS=$(pmset -g log 2>/dev/null | grep -c "Entering Sleep")
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
  SE=$(pmset -g log 2>/dev/null | grep -c "Entering Sleep")
  SLEPT=0; [ "$SE" -gt "$SS" ] && SLEPT=1
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
    print("patch200_false=NA patch200_null=NA patch200_other=NA"); sys.exit()
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
  F=$(echo $BODY | grep -oE 'patch200_false=[A-Za-z0-9]+' | cut -d= -f2)
  N=$(echo $BODY | grep -oE 'patch200_null=[A-Za-z0-9]+' | cut -d= -f2)
  O=$(echo $BODY | grep -oE 'patch200_other=[A-Za-z0-9]+' | cut -d= -f2)
  say "$TAG exit=$E det970=$D assembled=$ASM chosen=$CHOSEN unconfirmed=$UNCONF $BODY slept=$SLEPT"
  echo "$ARM,$SEED,$E,$D,$ASM,$CHOSEN,$UNCONF,$F,$N,$O,$SLEPT" >> $CSV
  [ "$D" = 1 ] && fires=$((fires+1))
  [ "$ASM" != "" ] && asmsum=$((asmsum+ASM))
  [ "$SLEPT" = 1 ] && { say "SLEEP-DETECTED during $TAG; stopping batch (deviation)"; break; }
  if [ $n -ge 3 ] && [ $fires -eq 0 ] && [ $asmsum -eq 0 ]; then
    say "EARLY-STOP first-3 seeds 0 fires 0 assembled; stopping batch (deviation)"; break
  fi
done
say "BATCH DONE fires=$fires over $n seeds (arm=$ARM)"
