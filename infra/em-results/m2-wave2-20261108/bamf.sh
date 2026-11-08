#!/usr/bin/env zsh
set -u
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-M2-917c57dd.jar
WANT_JAR=$(cut -c1-16 $JAR.sha256)
BASE=$THESIS/infra/em-results/m2-wave2-20261108
T=$THESIS/infra/bamf-target
PROXY=$THESIS/infra/evomaster-ext/selftest/capture_proxy.py
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
JH=$(/usr/libexec/java_home -v 17)
PROG=$BASE/progress-bamf.log
CSV=$BASE/runs-bamf.csv
MAXT=600s
RATE=600
NEED_TESTS=237
SEEDS=(1 2 3 4 5 6 7 8 9 10)
WD=$BASE/wd-bamf
mkdir -p $BASE/logs $BASE/tests $BASE/traffic $WD && cd $WD

say () { echo "$(date +%H:%M:%S) $*" >> $PROG }
die () { say "DUNG: $*"; $T/down.sh bamf-heldout >> $PROG 2>&1; echo "RUN STOPPED $(date)" >> $PROG; exit 1 }

say "start bamf jar=$(basename $JAR) seeds=$SEEDS maxTime=$MAXT rate=$RATE (D1 off, no flag, proxy 8213)"
echo "seed,maxtime,exit,det970,assembled,void,unconfirmed,evaluated_tests,victim_logins,admin_logins,viewer_logins,failed_logins,triples" > $CSV
JARSHA=$(shasum -a 256 $JAR | cut -c1-16)
[ "$JARSHA" = "$WANT_JAR" ] || die "jar sha $JARSHA, cho $WANT_JAR"
SLEEP0=$(pmset -g log | grep "Entering Sleep" | tail -1)

run () {
  local seed=$1
  local name=bamf-seed$seed-$MAXT
  $T/up.sh bamf-heldout 8110 8211 15433 16380 $BASE/logs/$name-target dotless > $BASE/logs/$name-up.txt 2>&1
  if [ $(grep -c "^login .* 200$" $BASE/logs/$name-up.txt) != 3 ] || [ "$(grep -c "^user victim roles \[.admin.\]$" $BASE/logs/$name-up.txt)" != 1 ]; then
    echo "$seed,$MAXT,UP,ERR,0,0,0,NA,NA,NA,NA,NA,NA" >> $CSV
    say "$name up hong"
    return
  fi
  grep "^spec " $BASE/logs/$name-up.txt >> $PROG
  python3 -c "
import json
s=json.load(open('$BASE/logs/$name-target/openapi.json'))
del s['paths']['/api/v1/role-assignments']['put']
del s['paths']['/api/v1/users/{email}']['delete']
del s['components']['schemas']['UserUpdate']['properties']['password']
del s['paths']['/api/v1/role-assignments/{provider_name}/{email}/{role_name}']['delete']
json.dump(s,open('$BASE/logs/$name-target/openapi-nokill.json','w'))
print('nokill ops',sum(1 for p in s['paths'].values() for m in p if m in ('get','post','put','patch','delete')))" >> $PROG
  python3 $PROXY 8213 localhost 8110 $BASE/traffic/$name.jsonl &
  local px=$!
  kill $(cat $BASE/logs/$name-target/shim.pid)
  $T/.venv/bin/python $T/login_shim.py 8211 http://localhost:8213 > $BASE/logs/$name-target/shim-proxied.log 2>&1 &
  local sh=$!
  sleep 2
  local OUT=$BASE/tests/$name; rm -rf $OUT
  local log=$BASE/logs/$name.log
  JAVA_HOME=$JH java -Xmx2g $DEBUG -jar $JAR --blackBox true \
    --bbSwaggerUrl file://$BASE/logs/$name-target/openapi-nokill.json \
    --bbTargetUrl http://localhost:8213 \
    --configPath $THESIS/infra/em-config/bamf-auth-dotless.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute $RATE --maxTime $MAXT --seed $seed \
    --outputFolder $OUT > $log 2>&1
  local e=$?
  kill $px $sh 2>/dev/null
  local d=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")
  local ac=$(grep -c "Assembled .* statuses" $log)
  local vc=$(grep -c "Discarded a VOID stateful-authorization" $log)
  local uc=$(grep -c "Discarded an UNCONFIRMED stateful-authorization" $log)
  local ev=$(grep -a "Evaluated tests" $log | tail -1 | awk '{print $NF}')
  local lg=$(python3 - $BASE/traffic/$name.jsonl <<'PY'
import json, sys
n = {"victim": 0, "admin": 0, "viewer": 0}
bad = 0
for l in open(sys.argv[1], encoding="utf-8"):
    r = json.loads(l)
    if r["path"] != "/api/v1/auth/local/authorize":
        continue
    try:
        who = json.loads(r["req_body"] or "{}").get("email")
    except Exception:
        who = None
    if r["status"] == 200 and who in n:
        n[who] += 1
    elif who in n:
        bad += 1
print(n["victim"], n["admin"], n["viewer"], bad)
PY
)
  set -- ${=lg}
  local vl=$1 al=$2 wl=$3 fl=$4
  local tr=$(grep -o "victim '[^']*', operator '[^']*'[^)]*" $log | sed "s/victim '\([^']*\)', operator '\([^']*\)'.* \([0-9/-]*\)$/\1<\2:\3/" | paste -sd';' -)
  echo "$seed,$MAXT,$e,$d,$ac,$vc,$uc,${ev:-NA},$vl,$al,$wl,$fl,${tr:-NA}" >> $CSV
  say "$name exit=$e det970=$d assembled=$ac void=$vc unconfirmed=$uc evaluated_tests=${ev:-NA} logins=victim:$vl,admin:$al,viewer:$wl failed_logins=$fl triples=${tr:-NA}"
  $T/down.sh bamf-heldout > /dev/null 2>&1
  [ "$(pmset -g log | grep 'Entering Sleep' | tail -1)" != "$SLEEP0" ] && die "may ngu trong luot $name"
  [ "$e" = "0" ] || die "EvoMaster exit $e o $name"
  if [ "$seed" = "${SEEDS[1]}" ]; then
    [ "$vl" -gt 0 ] && [ "$al" -gt 0 ] && [ "$wl" -gt 0 ] || die "DUNG SOM: seed $seed thieu dang nhap mot tai khoan"
    [ "${ev:-0}" -ge $NEED_TESTS ] || die "DUNG SOM: seed $seed evaluated_tests ${ev:-NA} < $NEED_TESTS"
    [ "$ac" -gt 0 ] || [ "$vc" -gt 0 ] || [ "$uc" -gt 0 ] || die "DUNG SOM: seed $seed 0 lan thu bo ba"
  fi
}

for seed in $SEEDS; do run $seed; done
echo "RUN DONE $(date)" >> $PROG
