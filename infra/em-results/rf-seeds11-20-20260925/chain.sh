#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=$EM/evomaster-RF-7f9d977e.jar
BASE=$THESIS/infra/em-results/rf-seeds11-20-20260925
WANT_JAR=7f9d977e4849080a
JH=$(/usr/libexec/java_home -v 17)
PROG=$BASE/progress.log
CSV=$BASE/runs.csv
mkdir -p $BASE/logs $BASE/tests

say () { echo "$(date +%H:%M:%S) $*" >> $PROG }
die () { say "DUNG CHUOI: $*"; echo "CHAIN STOPPED $(date)" >> $PROG; exit 1 }

echo "chuoi jar RF seeds 11-20 start $(date)" > $PROG
echo "tier,arm,seed,d1,det970,assembled,void_count,probe_lines,probe_403,statuses,faults" > $CSV

for p in 8080 8081 5002 5003 8090 8091; do
  c=$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:$p/ 2>/dev/null)
  [ "$c" = "000" ] && die "cong $p khong tra loi"
  say "cong $p tra $c"
done

JARSHA=$(shasum -a 256 $JAR | cut -c1-16)
[ "$JARSHA" = "$WANT_JAR" ] || die "jar sha $JARSHA, cho $WANT_JAR"
say "jar $JARSHA"


NP=$(unzip -p $JAR stateful-authz-lexicon.csv | grep -c "^path,")
NQ=$(unzip -p $JAR stateful-authz-lexicon.csv | grep -c "^param,")
[ "$NP" -gt 0 ] && [ "$NQ" -gt 0 ] || die "bo tu vung khong co trong jar"
say "bo tu vung trong jar: $NP path, $NQ param"

collect () {
  local log=$1 out=$2 tier=$3 arm=$4 seed=$5
  local st=$(grep -o "statuses [0-9?/-]*" $log | awk '{print $2}' | paste -sd';' -); [ -z "$st" ] && st=NA
  local ac=$(grep -c "Assembled .* statuses" $log)
  local vc=$(grep -c "Discarded a VOID stateful-authorization" $log)
  local pl=$(grep -c "fresh-credential probe:" $log)
  local p4=$(grep "fresh-credential probe:" $log | grep -c "=403")
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
  echo "$tier,$arm,$seed,false,$d,$ac,$vc,$pl,$p4,$st,$fl" >> $CSV
  say "$tier $arm seed=$seed det970=$d assembled=$ac void=$vc statuses=$st"
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

t2b () {
  local seed=$1
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

say "giai doan 1: Tier-1 va Tier-2 ban loi, seeds 11-20"
for s in $(seq 11 20); do t1 $s vuln 8080; done
for s in $(seq 11 20); do t2 $s vuln 5002; done

say "giai doan 2: Tier-1 va Tier-2 ban da va, seeds 11-20"
for s in $(seq 11 20); do t1 $s fixed 8081; done
for s in $(seq 11 20); do t2 $s fixed 5003; done

say "giai doan 3: pyLoad ban loi, seeds 11-20"
for s in $(seq 11 20); do t2b $s; done

say "giai doan 4: sao luu"
cd /Users/minhnguyen/IdeaProjects
TAR=~/thesis-backups/thesis-full-$(date +%Y%m%d-%H%M).tar.gz
tar --exclude 'graduational-thesis/infra/em-venv' -czf $TAR graduational-thesis
shasum -a 256 $TAR > $TAR.sha256
say "sao luu $TAR"
echo "CHAIN DONE $(date)" >> $PROG
