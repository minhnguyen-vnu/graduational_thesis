#!/usr/bin/env zsh
set -u
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
AF2=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-AF2-6b5606d4.jar
P2C=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-P2c-b2ade764.jar
BASE=$THESIS/infra/em-results/p2c-interleave-seeds-20261012
JH=$(/usr/libexec/java_home -v 17)
CSV=$BASE/runs.csv; PROG=$BASE/progress.log
mkdir -p $BASE/logs $BASE/tests
echo "jar,seed,rep,det970,assembled,void,restore_ok,restore_no,statuses" > $CSV
{
  echo "interleave reports vuln-noreset seeds 10,13,16  AF2 vs P2c  start $(date)"
  echo "af2=$(shasum -a 256 $AF2 | cut -c1-16)  p2c=$(shasum -a 256 $P2C | cut -c1-16)"
  echo "question: are seeds 10,13,16 (P2c missed, AF2 fired in single remeasure) a SYSTEMATIC P2c gap or stochastic?"
  echo "arm = reports vuln :8080, reset once before each run, NO --statefulAuthzResetEndpoint; only jar+seed vary"
  echo "READ: AF2 fires most AND P2c misses most -> systematic B2 value-selection gap; both mixed -> stochastic (P2c at low end of AF2 16-19/20)"
} > $PROG

one () {
  local lbl=$1 jar=$2 s=$3 rep=$4
  curl -s -o /dev/null -X POST http://localhost:8080/reset
  local OUT=$BASE/tests/$lbl-seed$s-r$rep; rm -rf $OUT
  local log=$BASE/logs/$lbl-seed$s-r$rep.log
  JAVA_HOME=$JH java -jar $jar --blackBox true \
    --bbSwaggerUrl http://localhost:8080/v3/api-docs --bbTargetUrl http://localhost:8080 \
    --configPath $THESIS/infra/em-config/reports-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $s \
    --outputFolder $OUT > $log 2>&1
  local d=$(python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$OUT/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')")
  local ac=$(grep -c "Assembled .* statuses" $log)
  local vc=$(grep -c "Discarded a VOID stateful-authorization" $log)
  local rok=$(grep -c "Privilege-restore accepted" $log)
  local rno=$(grep -c "Privilege-restore refused" $log)
  local st=$(grep -v "proven by an attempt with" $log | grep -o "statuses [0-9?/-]*" | awk '{print $2}' | paste -sd';' -); [ -z "$st" ] && st=NA
  echo "$lbl,$s,$rep,$d,$ac,$vc,$rok,$rno,$st" >> $CSV
  echo "$(date +%H:%M:%S) $lbl seed=$s rep=$rep det970=$d assembled=$ac void=$vc restore_ok=$rok restore_no=$rno statuses=$st" >> $PROG
  rm -rf $OUT
}

for s in 10 13 16; do
  for rep in 1 2 3; do
    one af2 $AF2 $s $rep
    one p2c $P2C $s $rep
  done
done
echo "INTERLEAVE DONE $(date)" >> $PROG
python3 - "$CSV" >> $PROG <<'PY'
import csv,sys
rows=list(csv.DictReader(open(sys.argv[1])))
for jar in ("af2","p2c"):
    for s in ("10","13","16"):
        f=[r for r in rows if r["jar"]==jar and r["seed"]==s]
        fired=sum(1 for r in f if r["det970"]=="1")
        print(f"SUMMARY {jar} seed {s}: {fired}/{len(f)} fired")
PY
