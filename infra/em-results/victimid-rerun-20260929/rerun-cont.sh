#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EM=/Users/minhnguyen/IdeaProjects/EvoMaster
BASE=$THESIS/infra/em-results/victimid-rerun-20260929
GBASE=$THESIS/infra/em-results/regression-check
MM=$THESIS/infra/em-results/mattermost-heldout-20260928
JAR=$EM/evomaster-VI-d2325da7.jar
WANT_JAR=$(cut -c1-16 $JAR.sha256)
JH=$(/usr/libexec/java_home -v 17)
PROG=$BASE/progress.log
CSV=$BASE/runs.csv
S=/private/tmp/claude-501/-Users-minhnguyen-IdeaProjects-graduational-thesis/c11063a7-7e2e-4959-9c5f-34c7cf5787b5/scratchpad
mkdir -p $BASE/logs $BASE/tests

say () { echo "$(date +%H:%M:%S) $*" >> $PROG }
die () { say "DUNG CHUOI: $*"; echo "CHAIN STOPPED $(date)" >> $PROG; exit 1 }

collect () {
  local log=$1 out=$2 tier=$3 arm=$4 seed=$5
  local st=$(grep -o "statuses [0-9?/-]*" $log | awk '{print $2}' | paste -sd';' -); [ -z "$st" ] && st=NA
  local ac=$(grep -c "Assembled .* statuses" $log)
  local vc=$(grep -c "Discarded a VOID stateful-authorization" $log)
  local pl=$(grep -c "fresh-credential probe:" $log)
  local p4=$(grep "fresh-credential probe:" $log | grep -c "=403")
  local to=$(grep -c "Read timed out" $log)
  local d=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$out/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")
  local fl=$(python3 -c "
import json
try: print('|'.join(str(x) for x in sorted({x['code'] for f in json.load(open('$out/report.json'))['faults']['foundFaults'] for x in f['faultCategories']})))
except Exception: print('ERR')")
  echo "$tier,$arm,$seed,false,$d,$ac,$vc,$pl,$p4,$st,$fl,$to" >> $CSV
  local ev=$(grep -a "Evaluated tests" $log | tail -1 | awk '{print $NF}')
  local sl=$(pmset -g log | awk -v a="$(date -r $T0 '+%Y-%m-%d %H:%M:%S')" '($1" "$2)>=a' | grep -c "Entering Sleep")
  say "$tier $arm seed=$seed det970=$d assembled=$ac void=$vc statuses=$st read_timeouts=$to evaluated_tests=$ev sleep_events=$sl"
  [ "$sl" = "0" ] || die "may ngu trong luot $tier $arm seed=$seed"
}

t1 () {
  T0=$(date +%s)
  local seed=$1 arm=$2 port=$3
  curl -s -o /dev/null -X POST http://localhost:$port/reset
  local OUT=$BASE/tests/t1-$arm-seed$seed; rm -rf $OUT
  local log=$BASE/logs/t1-$arm-seed$seed.log
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:$port/v3/api-docs --bbTargetUrl http://localhost:$port \
    --configPath $THESIS/infra/em-config/reports-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $seed \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT tier1 $arm $seed
}

t2 () {
  T0=$(date +%s)
  local seed=$1 arm=$2 port=$3
  if [ "$(curl -s -o /dev/null --max-time 10 -w '%{http_code}' http://localhost:$port/openapi.json)" != "200" ]; then
    say "cong $port khong tra spec truoc tier2 $arm seed=$seed, docker start"
    [ "$port" = "5003" ] && docker start vampi-seeded-fixed >> $PROG 2>&1
    [ "$port" = "5002" ] && docker start vampi-seeded >> $PROG 2>&1
    for i in $(seq 1 30); do [ "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:$port/openapi.json)" = "200" ] && break; sleep 2; done
    say "sau docker start cong $port tra $(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:$port/openapi.json)"
  fi
  curl -s -o /dev/null http://localhost:$port/createdb
  local OUT=$BASE/tests/t2-$arm-seed$seed; rm -rf $OUT
  local log=$BASE/logs/t2-$arm-seed$seed.log
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:$port/openapi.json --bbTargetUrl http://localhost:$port \
    --configPath $THESIS/infra/em-config/vampi-seeded-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $seed \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT tier2 $arm $seed
}

pyload_up () {
  local c=$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:8090/)
  [ "$c" != "000" ] && return 0
  say "pyLoad khong tra loi, dung container, thay file pid cu, start"
  docker stop pyload-vuln >> $PROG 2>&1
  printf '999999' > $S/pyload.pid
  docker cp $S/pyload.pid pyload-vuln:/tmp/pyLoad/pyload.pid >> $PROG 2>&1
  docker start pyload-vuln >> $PROG 2>&1
  for i in $(seq 1 60); do
    [ "$(curl -s -o /dev/null --max-time 3 -w '%{http_code}' http://localhost:8090/)" != "000" ] && { say "pyLoad len lai"; return 0; }
    sleep 2
  done
  say "pyLoad khong len lai"
  return 1
}

t2b () {
  T0=$(date +%s)
  local seed=$1
  pyload_up || { echo "tier2b,vuln,$seed,false,ERR,0,0,0,0,NA,ERR,NA" >> $CSV; say "tier2b vuln seed=$seed ERR pyLoad khong len"; return; }
  curl -s -o /dev/null -X POST http://localhost:8090/thesis/reset
  local OUT=$BASE/tests/t2b-vuln-seed$seed; rm -rf $OUT
  local log=$BASE/logs/t2b-vuln-seed$seed.log
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl file://$THESIS/infra/pyload-cve/openapi-merged.json --bbTargetUrl http://localhost:8090 \
    --configPath $THESIS/infra/em-config/pyload-auth.yaml \
    --endpointExclude "/api/kill,/api/restart" \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 200 --maxTime 10m --seed $seed \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT tier2b vuln $seed
}

backup () {
  cd /Users/minhnguyen/IdeaProjects
  local TAR=~/thesis-backups/thesis-full-$(date +%Y%m%d-%H%M).tar.gz
  tar --exclude 'graduational-thesis/infra/em-venv' -czf $TAR graduational-thesis
  shasum -a 256 $TAR > $TAR.sha256
  say "sao luu $TAR"
  cd $BASE
}

stuck () {
  python3 - $CSV $1 <<'PY'
import csv, sys
rows=[r for r in csv.DictReader(open(sys.argv[1])) if r['tier']==sys.argv[2]]
print(1 if len(rows)==3 and all(r['assembled']=='0' for r in rows) else 0)
PY
}

say "tiep tuc sau dung chu dich 10:04: pyLoad seeds 4-10, Tier-2 ban da seeds 4-10"
pgrep -f "evomaster.*\.jar" > /dev/null && die "dang co EvoMaster chay"
[ "$(shasum -a 256 $JAR | cut -c1-16)" = "$WANT_JAR" ] || die "jar sha khac"
for s in $(seq 4 10); do t2b $s; done
say "Tier-2 ban da va seeds 4-10"
for s in $(seq 4 10); do t2 $s fixed 5003; done
backup
echo "RERUN DONE $(date)" >> $PROG
