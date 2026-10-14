#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=$EM/evomaster-PF-0607485b.jar
WANT_JAR=0607485b6286ab24
BASE=$THESIS/infra/em-results/postfallback-chain-20260925
WAITFOR=$THESIS/infra/em-results/genesetguard-chain-20260925/progress.log
JH=$(/usr/libexec/java_home -v 17)
PROG=$BASE/rerun-progress.log
CSV=$BASE/runs-t2b-rerun.csv
S=/private/tmp/claude-501/-Users-minhnguyen-IdeaProjects-graduational-thesis/c11063a7-7e2e-4959-9c5f-34c7cf5787b5/scratchpad

say () { echo "$(date +%H:%M:%S) $*" >> $PROG }

echo "chay lai pyLoad seeds 3-10 start $(date), doi chuoi gene-set-guard xong" > $PROG
echo "tier,arm,seed,d1,det970,assembled,void_count,probe_lines,probe_403,statuses,faults" > $CSV

while true; do
  grep -q -E "CHAIN DONE|CHAIN STOPPED" $WAITFOR 2>/dev/null && break
  sleep 60
done
while pgrep -f "evomaster.*\.jar" > /dev/null; do sleep 30; done
say "chuoi gene-set-guard xong: $(grep -E 'CHAIN DONE|CHAIN STOPPED' $WAITFOR)"

JARSHA=$(shasum -a 256 $JAR | cut -c1-16)
[ "$JARSHA" = "$WANT_JAR" ] || { say "jar sha $JARSHA, cho $WANT_JAR"; exit 1; }
say "jar $JARSHA"

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

collect () {
  local log=$1 out=$2 seed=$3
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
  local to=$(grep -c "Read timed out" $log)
  echo "tier2b,vuln,$seed,false,$d,$ac,$vc,$pl,$p4,$st,$fl" >> $CSV
  say "tier2b vuln seed=$seed det970=$d assembled=$ac void=$vc statuses=$st read_timeouts=$to"
}

for seed in $(seq 3 10); do
  pyload_up || { echo "tier2b,vuln,$seed,false,ERR,0,0,0,0,NA,ERR" >> $CSV; continue; }
  curl -s -o /dev/null -X POST http://localhost:8090/thesis/reset
  OUT=$BASE/tests/rerun-t2b-vuln-seed$seed; rm -rf $OUT
  log=$BASE/logs/rerun-t2b-vuln-seed$seed.log
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl file://$THESIS/infra/pyload-cve/openapi-merged.json --bbTargetUrl http://localhost:8090 \
    --configPath $THESIS/infra/em-config/pyload-auth.yaml \
    --endpointExclude "/api/kill,/api/restart" \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 200 --maxTime 10m --seed $seed \
    --outputFolder $OUT > $log 2>&1
  collect $log $OUT $seed
done

say "sao luu"
cd /Users/minhnguyen/IdeaProjects
TAR=~/thesis-backups/thesis-full-$(date +%Y%m%d-%H%M).tar.gz
tar --exclude 'graduational-thesis/infra/em-venv' -czf $TAR graduational-thesis
shasum -a 256 $TAR > $TAR.sha256
say "sao luu $TAR"
echo "RERUN DONE $(date)" >> $PROG
