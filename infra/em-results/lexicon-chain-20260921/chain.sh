#!/usr/bin/env zsh
set -u
# Do gi: jar moi mang bo tu vung rut tu corpus thay cho 2 danh sach cung, va xep hang transition thay cho
# firstOrNull. Chuoi nay do: 12 kiem tra self-test; 21 dong cong hoi quy; seeds 1-10 tren Tier-1 va Tier-2,
# ca ban loi va ban da va, khong reset; seeds 1-10 tren pyLoad ban loi. Moi lan chay ghi mot dong vao runs.csv.
# Dung chuoi khi self-test hong, hoac khi cong hoi quy lech o mot dong cua ban da va.
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=$EM/core/target/evomaster.jar
BASE=$THESIS/infra/em-results/lexicon-chain-20260921
LEX=$THESIS/infra/analysis/lexicon-rules/lexicon-20260921-audited/stateful-authz-lexicon.csv
RES=$EM/core/src/main/resources/stateful-authz-lexicon.csv
GBASE=$THESIS/infra/em-results/regression-check
JH=$(/usr/libexec/java_home -v 17)
PROG=$BASE/progress.log
CSV=$BASE/runs.csv
mkdir -p $BASE/logs $BASE/tests

say () { echo "$(date +%H:%M:%S) $*" >> $PROG }
die () { say "DUNG CHUOI: $*"; echo "CHAIN STOPPED $(date)" >> $PROG; exit 1 }

echo "chuoi lexicon start $(date)" > $PROG
echo "tier,arm,seed,d1,det970,assembled,void_count,probe_lines,probe_403,statuses,faults" > $CSV

for p in 8080 8081 5002 5003 8090 8091; do
  c=$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:$p/ 2>/dev/null)
  [ "$c" = "000" ] && die "cong $p khong tra loi"
  say "cong $p tra $c"
done

PRE=$EM/evomaster-prelexicon-2c343573.jar
[ -f $PRE ] || die "khong thay jar truoc khi doi: $PRE"
say "jar truoc khi doi da giu: $(basename $PRE)"

mkdir -p $(dirname $RES)
cp $LEX $RES
NP=$(grep -c "^path," $RES)
NQ=$(grep -c "^param," $RES)
say "chep bo tu vung: $NP path, $NQ param"

say "giai doan 1: build"
JAVA_HOME=$JH mvn -f $EM/pom.xml -pl core -am package -Dmaven.test.skip=true > $BASE/logs/build.log 2>&1 \
  || die "build hong, xem logs/build.log"
NEWSHA=$(shasum -a 256 $JAR | cut -c1-16)
say "build xong, jar $NEWSHA"

say "giai doan 2: self-test"
zsh $THESIS/infra/evomaster-ext/selftest/lexicon-rank.sh $BASE/selftest > $BASE/logs/selftest.log 2>&1
STEXIT=$?
grep -E '^(PASS|FAIL)' $BASE/logs/selftest.log >> $PROG
[ $STEXIT -eq 0 ] || die "self-test hong, xem logs/selftest.log"
say "self-test dat het"

say "giai doan 3: cong hoi quy"
ARCH=$GBASE/archive-20260921-pre-lexicon
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
[ "$2" = "0" ] || die "cong hoi quy lech $2 dong ban da va: day la dau hieu bao dong gia"
say "khong dong ban da va nao lech, chay tiep"

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

say "giai doan 4: Tier-1 va Tier-2 ban loi, seeds 1-10"
for s in $(seq 1 10); do t1 $s vuln 8080; done
for s in $(seq 1 10); do t2 $s vuln 5002; done

say "giai doan 5: Tier-1 va Tier-2 ban da va, seeds 1-10"
for s in $(seq 1 10); do t1 $s fixed 8081; done
for s in $(seq 1 10); do t2 $s fixed 5003; done

say "giai doan 6: pyLoad ban loi, seeds 1-10"
for s in $(seq 1 10); do t2b $s; done

say "giai doan 7: sao luu"
cd /Users/minhnguyen/IdeaProjects
TAR=~/thesis-backups/thesis-full-$(date +%Y%m%d-%H%M).tar.gz
tar --exclude 'graduational-thesis/infra/em-venv' -czf $TAR graduational-thesis
shasum -a 256 $TAR > $TAR.sha256
say "sao luu $TAR"
echo "CHAIN DONE $(date)" >> $PROG
