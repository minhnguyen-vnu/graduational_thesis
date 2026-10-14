#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=$EM/evomaster-GG-a6839ada.jar
BASE=$THESIS/infra/em-results/gg-overnight-20260926
WANT_JAR=a6839ada5b839465
JH=$(/usr/libexec/java_home -v 17)
PROG=$BASE/progress.log
CSV=$BASE/runs.csv
S=/private/tmp/claude-501/-Users-minhnguyen-IdeaProjects-graduational-thesis/c11063a7-7e2e-4959-9c5f-34c7cf5787b5/scratchpad
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
mkdir -p $BASE/logs $BASE/tests $BASE/airflow

say () { echo "$(date +%H:%M:%S) $*" >> $PROG }
die () { say "DUNG CHUOI: $*"; echo "CHAIN STOPPED $(date)" >> $PROG; exit 1 }

echo "chuoi dem 09-26 jar GG start $(date)" > $PROG
echo "tier,arm,seed,d1,det970,assembled,void_count,probe_lines,probe_403,statuses,faults,read_timeouts" > $CSV

pgrep -f "evomaster.*\.jar" > /dev/null && die "con tien trinh EvoMaster dang chay"
for p in 8080 8081 5002 5003 8090 8082; do
  c=$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:$p/ 2>/dev/null)
  [ "$c" = "000" ] && die "cong $p khong tra loi"
  say "cong $p tra $c"
done

JARSHA=$(shasum -a 256 $JAR | cut -c1-16)
[ "$JARSHA" = "$WANT_JAR" ] || die "jar sha $JARSHA, cho $WANT_JAR"
say "jar $JARSHA"

say "giai doan 1: Airflow qua proxy ghi request, seeds 1-2"
for seed in 1 2; do
  zsh $THESIS/infra/airflow-target/reset-3users.sh http://localhost:8082 > $BASE/airflow/seed$seed-reset.txt 2>&1
  if ! grep -q "victim roles \['Op'\]" $BASE/airflow/seed$seed-reset.txt || ! grep -q "viewer roles \['Viewer'\]" $BASE/airflow/seed$seed-reset.txt; then
    say "airflow seed=$seed reset hong, bo qua"
    continue
  fi
  CAP=$BASE/airflow/seed$seed-traffic.jsonl
  python3 $BASE/capture_proxy.py 8182 localhost 8082 $CAP &
  PX=$!
  sleep 2
  JAVA_HOME=$JH java $DEBUG -jar $JAR --blackBox true \
    --bbSwaggerUrl file://$THESIS/infra/airflow-target/airflow-merged-nodelete.json \
    --bbTargetUrl http://localhost:8182 \
    --configPath $THESIS/infra/em-config/airflow-auth-3users.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 60 --maxTime 600s --seed $seed \
    --outputFolder $BASE/airflow/seed$seed > $BASE/airflow/seed$seed.log 2>&1
  E=$?
  kill $PX
  say "airflow seed=$seed exit=$E requests=$(wc -l < $CAP | tr -d ' ') patch_users=$(grep -c '"PATCH", "path": "/auth/fab/v1/users/' $CAP) assembled=$(grep -c 'Assembled .* statuses' $BASE/airflow/seed$seed.log) void=$(grep -c 'Discarded a VOID stateful-authorization' $BASE/airflow/seed$seed.log)"
done
zsh $THESIS/infra/airflow-target/reset-3users.sh http://localhost:8082 > $BASE/airflow/final-reset.txt 2>&1

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
  say "$tier $arm seed=$seed det970=$d assembled=$ac void=$vc statuses=$st read_timeouts=$to"
}

t1 () {
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

say "giai doan 2: Tier-1 va Tier-2 ban loi, seeds 11-20"
for s in $(seq 11 20); do t1 $s vuln 8080; done
for s in $(seq 11 20); do t2 $s vuln 5002; done

say "giai doan 3: Tier-1 va Tier-2 ban da va, seeds 11-20"
for s in $(seq 11 20); do t1 $s fixed 8081; done
for s in $(seq 11 20); do t2 $s fixed 5003; done

say "giai doan 4: pyLoad ban loi, seeds 11-20"
for s in $(seq 11 20); do t2b $s; done

say "giai doan 5: sao luu"
cd /Users/minhnguyen/IdeaProjects
TAR=~/thesis-backups/thesis-full-$(date +%Y%m%d-%H%M).tar.gz
tar --exclude 'graduational-thesis/infra/em-venv' -czf $TAR graduational-thesis
shasum -a 256 $TAR > $TAR.sha256
say "sao luu $TAR"
echo "CHAIN DONE $(date)" >> $PROG
