#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=$EM/evomaster-TT-129a7a56.jar
WANT_JAR=129a7a56fce83df8
BASE=$THESIS/infra/em-results/pyload-vuln-tt-12-20-20260927
JH=$(/usr/libexec/java_home -v 17)
PROG=$BASE/progress.log
CSV=$BASE/runs.csv
S=/private/tmp/claude-501/-Users-minhnguyen-IdeaProjects-graduational-thesis/c11063a7-7e2e-4959-9c5f-34c7cf5787b5/scratchpad
mkdir -p $BASE/logs $BASE/tests

say () { echo "$(date +%H:%M:%S) $*" >> $PROG }
die () { say "DUNG: $*"; echo "RUN STOPPED $(date)" >> $PROG; exit 1 }

echo "pyLoad ban loi, jar TT, seeds 12-20 (tiep chuoi transitiontrim-chain-20260927c), start $(date)" > $PROG
echo "tier,arm,seed,d1,det970,assembled,void_count,probe_lines,probe_403,statuses,faults,read_timeouts" > $CSV
while pgrep -f "evomaster.*\.jar" > /dev/null; do sleep 30; done
[ "$(shasum -a 256 $JAR | cut -c1-16)" = "$WANT_JAR" ] || die "jar sha sai"

pyload_up () {
  local c=$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:8090/)
  [ "$c" != "000" ] && return 0
  say "pyLoad ban loi khong tra loi, dung container, thay file pid cu, start"
  docker stop pyload-vuln >> $PROG 2>&1
  printf '999999' > $S/pyload-vuln.pid
  docker cp $S/pyload-vuln.pid pyload-vuln:/tmp/pyLoad/pyload.pid >> $PROG 2>&1
  docker start pyload-vuln >> $PROG 2>&1
  for i in $(seq 1 60); do
    [ "$(curl -s -o /dev/null --max-time 3 -w '%{http_code}' http://localhost:8090/)" != "000" ] && { say "pyLoad len lai"; return 0; }
    sleep 2
  done
  say "pyLoad khong len lai"
  return 1
}

for seed in $(seq 12 20); do
  pyload_up || { echo "tier2b,vuln,$seed,false,ERR,0,0,0,0,NA,ERR,NA" >> $CSV; say "tier2b vuln seed=$seed ERR"; continue; }
  curl -s -o /dev/null -X POST http://localhost:8090/thesis/reset
  OUT=$BASE/tests/t2b-vuln-seed$seed; rm -rf $OUT
  log=$BASE/logs/t2b-vuln-seed$seed.log
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl file://$THESIS/infra/pyload-cve/openapi-merged.json --bbTargetUrl http://localhost:8090 \
    --configPath $THESIS/infra/em-config/pyload-auth.yaml \
    --endpointExclude "/api/kill,/api/restart" \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 200 --maxTime 10m --seed $seed \
    --outputFolder $OUT > $log 2>&1
  st=$(grep -o "statuses [0-9?/-]*" $log | awk '{print $2}' | paste -sd';' -); [ -z "$st" ] && st=NA
  ac=$(grep -c "Assembled .* statuses" $log)
  vc=$(grep -c "Discarded a VOID stateful-authorization" $log)
  pl=$(grep -c "fresh-credential probe:" $log)
  p4=$(grep "fresh-credential probe:" $log | grep -c "=403")
  to=$(grep -c "Read timed out" $log)
  d=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")
  fl=$(python3 -c "
import json
try: print('|'.join(str(x) for x in sorted({x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']})))
except Exception: print('ERR')")
  echo "tier2b,vuln,$seed,false,$d,$ac,$vc,$pl,$p4,$st,$fl,$to" >> $CSV
  say "tier2b vuln seed=$seed det970=$d assembled=$ac void=$vc statuses=$st read_timeouts=$to"
done

cd /Users/minhnguyen/IdeaProjects
TAR=~/thesis-backups/thesis-full-$(date +%Y%m%d-%H%M).tar.gz
tar --exclude 'graduational-thesis/infra/em-venv' -czf $TAR graduational-thesis
shasum -a 256 $TAR > $TAR.sha256
say "sao luu $TAR"
echo "RUN DONE $(date)" >> $PROG
