#!/bin/bash
set -x
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
BASE=$THESIS/infra/em-results/wagoe-smoke-20261001
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-ER-06b48c30.jar
JH=$(/usr/libexec/java_home -v 17)
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
SPEC=$BASE/wagoe-openapi-smoke.json
OUT=$BASE/tests-seed1-debug
LOG=$BASE/seed1-debug.log
: > "$LOG"

echo "waiting for wagoe :3000 ..." >> "$LOG"
for i in $(seq 1 60); do
  curl -sf -o /dev/null http://localhost:3000/swagger.json && { echo "wagoe up after ${i}s" >> "$LOG"; break; }
  sleep 2
done

echo "=== reseed ===" >> "$LOG"
bash $BASE/reseed.sh >> "$LOG" 2>&1

echo "=== trim spec ===" >> "$LOG"
curl -s http://localhost:3000/swagger.json -o $BASE/swagger-full.json
python3 -c "
import json
s=json.load(open('$BASE/swagger-full.json'))
keep={'/api/v1/auth/login':['post'],'/api/v1/users':['get','post'],'/api/v1/users/{id}':['get','put']}
s['paths']={p:{m:s['paths'][p][m] for m in ms if m in s['paths'][p]} for p,ms in keep.items() if p in s['paths']}
json.dump(s,open('$SPEC','w'))
print('kept ops', sum(len(v) for v in s['paths'].values()))
" >> "$LOG" 2>&1

rm -rf $OUT
JAVA_HOME=$JH java $DEBUG -jar $JAR --blackBox true \
  --bbSwaggerUrl file://$SPEC \
  --bbTargetUrl http://localhost:3000 \
  --configPath $THESIS/infra/em-config/wagoe-auth.yaml \
  --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
  --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 1 \
  --outputFolder $OUT >> $LOG 2>&1
echo "EXIT $? $(date)" >> $LOG
echo "=== SMOKE-DEBUG DONE ===" >> $LOG
