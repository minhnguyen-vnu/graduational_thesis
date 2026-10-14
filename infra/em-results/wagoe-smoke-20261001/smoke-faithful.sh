#!/bin/bash
set -x
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
BASE=$THESIS/infra/em-results/wagoe-smoke-20261001
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-ER-06b48c30.jar
JH=$(/usr/libexec/java_home -v 17)
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
SPEC=$BASE/wagoe-openapi-faithful.json
OUT=$BASE/tests-seed1-faithful
LOG=$BASE/seed1-faithful.log
: > "$LOG"

for i in $(seq 1 60); do curl -sf -o /dev/null http://localhost:3000/swagger.json && { echo "wagoe up ${i}s">>"$LOG"; break; }; sleep 2; done
echo "=== reseed ===" >> "$LOG"; bash $BASE/reseed.sh >> "$LOG" 2>&1

echo "=== enrich spec (faithful to server validation) ===" >> "$LOG"
curl -s http://localhost:3000/swagger.json -o $BASE/swagger-full.json
python3 - "$BASE/swagger-full.json" "$SPEC" >> "$LOG" 2>&1 <<'PY'
import json,sys
s=json.load(open(sys.argv[1]))
keep={'/api/v1/auth/login':['post'],'/api/v1/users':['get','post'],'/api/v1/users/{id}':['get','put']}
s['paths']={p:{m:s['paths'][p][m] for m in ms if m in s['paths'][p]} for p,ms in keep.items() if p in s['paths']}
for pth,meths in {'/api/v1/users':['post'],'/api/v1/users/{id}':['put'],'/api/v1/auth/login':['post']}.items():
    for mm in meths:
        s['paths'][pth][mm]['consumes']=['application/json']
def body(path,method):
    for pr in s['paths'][path][method].get('parameters',[]):
        if pr.get('in')=='body': return pr['schema']
    return None
def enrich(props):
    if 'name' in props: props['name']={'type':'string','pattern':'^[A-Za-z]{3,15}$'}
    if 'role' in props: props['role']={'type':'string','enum':['admin','user']}
    if 'email' in props: props['email']={'type':'string','pattern':'^[a-z]{4,10}@acme\\.test$'}
    if 'password' in props: props['password']={'type':'string','minLength':6,'pattern':'^[A-Za-z0-9]{6,12}$'}
    if 'timeFormat' in props: props['timeFormat']={'type':'string','enum':['12h','24h']}
    if 'dateFormat' in props: props['dateFormat']={'type':'string','enum':['iso','us','eu']}
    if 'theme' in props: props['theme']={'type':'string','enum':['light','dark','auto']}
    if 'language' in props: props['language']={'type':'string','pattern':'^[a-z]{2}$'}
    if 'timezone' in props: props['timezone']={'type':'string','enum':['UTC','Europe/Paris']}
c=body('/api/v1/users','post'); c['required']=['email','name','password','role']; enrich(c['properties'])
u=body('/api/v1/users/{id}','put'); enrich(u['properties'])
json.dump(s,open(sys.argv[2],'w'))
print('enriched create required:',c['required'],'| create keys enriched:',[k for k in ('name','role','email','password','timeFormat','dateFormat','theme','language','timezone') if k in c['properties']])
PY

rm -rf $OUT
JAVA_HOME=$JH java $DEBUG -jar $JAR --blackBox true \
  --bbSwaggerUrl file://$SPEC \
  --bbTargetUrl http://localhost:3000 \
  --configPath $THESIS/infra/em-config/wagoe-auth.yaml \
  --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
  --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 1 \
  --outputFolder $OUT >> $LOG 2>&1
echo "EXIT $? $(date)" >> $LOG
echo "=== SMOKE-FAITHFUL DONE ===" >> $LOG
