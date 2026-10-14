#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EM=/Users/minhnguyen/IdeaProjects/EvoMaster
F1=core/src/main/kotlin/org/evomaster/core/EMConfig.kt
F2=core/src/main/kotlin/org/evomaster/core/problem/rest/service/RestSecurityBuilder.kt
WIP=$THESIS/infra/evomaster-ext/wip
FULL=$WIP/d1-lexicon-field-harvest-rolefield-postfallback-geneguard-transtrim-20260927b.patch
BASE=$THESIS/infra/em-results/transitiontrim-chain-20260927b
GBASE=$THESIS/infra/em-results/regression-check
OVN=$THESIS/infra/em-results/gg-overnight-20260926
WANT_TREE=bea33bab3ae9effb
PREV_JAR=evomaster-GG-a6839ada.jar
JH=$(/usr/libexec/java_home -v 17)
PROG=$BASE/progress.log
CSV=$BASE/runs.csv
S=/private/tmp/claude-501/-Users-minhnguyen-IdeaProjects-graduational-thesis/c11063a7-7e2e-4959-9c5f-34c7cf5787b5/scratchpad
mkdir -p $BASE/logs $BASE/tests

say () { echo "$(date +%H:%M:%S) $*" >> $PROG }
die () { say "DUNG CHUOI: $*"; echo "CHAIN STOPPED $(date)" >> $PROG; exit 1 }

echo "chuoi transition-trim lan 3 start $(date), doi lan 2 dung sau self-test" > $PROG

PREVCHAIN=$THESIS/infra/em-results/transitiontrim-chain-20260927/progress.log
while true; do
  grep -qE "CHAIN STOPPED|CHAIN DONE|giai doan 2" $PREVCHAIN 2>/dev/null && break
  sleep 20
done
grep -q "giai doan 2" $PREVCHAIN && die "lan 1 da qua self-test, khong chay lan 3"
while pgrep -f "evomaster.*\.jar" > /dev/null; do sleep 5; done
say "lan 2: $(grep -E 'DUNG CHUOI' $PREVCHAIN)"

for p in 8080 8081 5002 5003 8090 8082; do
  c=$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:$p/ 2>/dev/null)
  [ "$c" = "000" ] && die "cong $p khong tra loi"
  say "cong $p tra $c"
done

TREE=$(git -C $EM diff | shasum -a 256 | cut -c1-16)
[ "$TREE" = "$WANT_TREE" ] || die "cay lam viec sha $TREE, cho $WANT_TREE"
[ -f $EM/$PREV_JAR ] || die "khong thay jar truoc khi doi: $PREV_JAR"
git -C $EM diff > $FULL
git -C $EM checkout -- $F1 $F2
[ "$(git -C $EM diff HEAD | wc -l | tr -d ' ')" = "0" ] || die "rollback: git diff HEAD khong rong"
git -C $EM apply $FULL || die "rollback: git apply lai hong"
cmp -s <(git -C $EM diff) $FULL || die "rollback: diff sau khi ap lai khac patch da luu"
say "tap rollback dat: sha $(git -C $EM diff | shasum -a 256 | cut -c1-16) truoc va sau, patch $FULL"

say "build"
JAVA_HOME=$JH mvn -q -f $EM/pom.xml -pl core -am package -Dmaven.test.skip=true > $BASE/logs/build.log 2>&1 || die "build hong, xem logs/build.log"
JAR=$EM/core/target/evomaster.jar
JARSHA=$(shasum -a 256 $JAR | cut -c1-16)
KEEP=$EM/evomaster-TT-${JARSHA[1,8]}.jar
cp $JAR $KEEP
shasum -a 256 $KEEP > $KEEP.sha256
unzip -p $JAR 'org/evomaster/core/problem/rest/service/RestSecurityBuilder.class' | strings | grep -q keepOnlyTargetFields || die "jar khong co keepOnlyTargetFields"
say "jar $JARSHA, giu o $KEEP, class co keepOnlyTargetFields"
JAR=$KEEP

say "giai doan 1: self-test transition-trim"
JAR=$JAR zsh $THESIS/infra/evomaster-ext/selftest/transition-trim.sh $BASE/selftest-transtrim > $BASE/logs/selftest-transtrim.log 2>&1
E1=$?
grep -E '^(PASS|FAIL|INFO)' $BASE/logs/selftest-transtrim.log >> $PROG
[ $E1 -eq 0 ] || die "self-test transition-trim hong, xem logs/selftest-transtrim.log"

say "giai doan 2: cong hoi quy"
ARCH=$GBASE/archive-20260926-geneguard
mkdir -p $ARCH
for f in observed.csv progress.log logs; do
  [ -e $GBASE/$f ] && mv $GBASE/$f $ARCH/ 2>/dev/null
done
zsh $GBASE/regression_check.sh > $BASE/logs/gate.log 2>&1
GEXIT=$?
cp $GBASE/observed.csv $BASE/logs/gate-observed.csv 2>/dev/null
VERDICT=$(python3 - "$GBASE/observed.csv" <<'PY'
import csv, io, sys
rows = list(csv.DictReader(io.open(sys.argv[1], encoding='utf-8')))
bad_fixed = [r for r in rows if 'fixed' in r['arm'] and r['verdict'] != 'MATCH']
bad_vuln = [r for r in rows if 'fixed' not in r['arm'] and r['verdict'] != 'MATCH']
print('%d %d %d' % (len(rows), len(bad_fixed), len(bad_vuln)))
PY
)
set -- ${=VERDICT}
say "cong hoi quy: $1 dong, ban da va lech $2, ban loi lech $3 (exit $GEXIT)"
[ "$2" = "0" ] || die "cong hoi quy lech $2 dong ban da va"

echo "tier,arm,seed,d1,det970,assembled,void_count,probe_lines,probe_403,statuses,faults,read_timeouts" > $CSV

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

backup () {
  cd /Users/minhnguyen/IdeaProjects
  local TAR=~/thesis-backups/thesis-full-$(date +%Y%m%d-%H%M).tar.gz
  tar --exclude 'graduational-thesis/infra/em-venv' -czf $TAR graduational-thesis
  shasum -a 256 $TAR > $TAR.sha256
  say "sao luu $TAR"
  cd $BASE
}

block () {
  local a=$1 b=$2
  say "seeds $a-$b: Tier-1 va Tier-2 ban loi"
  for s in $(seq $a $b); do t1 $s vuln 8080; done
  for s in $(seq $a $b); do t2 $s vuln 5002; done
  say "seeds $a-$b: Tier-1 va Tier-2 ban da va"
  for s in $(seq $a $b); do t1 $s fixed 8081; done
  for s in $(seq $a $b); do t2 $s fixed 5003; done
  say "seeds $a-$b: pyLoad ban loi"
  for s in $(seq $a $b); do t2b $s; done
  backup
  echo "BLOCK $a-$b DONE $(date)" >> $PROG
}

block 1 10
block 11 20
echo "CHAIN DONE $(date)" >> $PROG
