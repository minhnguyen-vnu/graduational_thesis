#!/bin/bash
set -x
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
BASE=$THESIS/infra/em-results/wagoe-smoke-20261001
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-ER-06b48c30.jar
JH=$(/usr/libexec/java_home -v 17)
SPEC=$BASE/wagoe-openapi-smoke.json
OUT=$BASE/tests-seed1
LOG=$BASE/seed1.log

curl -s http://localhost:3000/swagger.json -o $BASE/swagger-full.json
python3 -c "
import json
s=json.load(open('$BASE/swagger-full.json'))
keep={
 '/api/v1/auth/login':['post'],
 '/api/v1/users':['get','post'],
 '/api/v1/users/{id}':['get','put'],
}
np={}
for p,methods in keep.items():
    if p in s['paths']:
        np[p]={m:s['paths'][p][m] for m in methods if m in s['paths'][p]}
s['paths']=np
json.dump(s,open('$SPEC','w'))
print('kept ops', sum(len(v) for v in np.values()))
"

rm -rf $OUT
JAVA_HOME=$JH java -jar $JAR --blackBox true \
  --bbSwaggerUrl file://$SPEC \
  --bbTargetUrl http://localhost:3000 \
  --configPath $THESIS/infra/em-config/wagoe-auth.yaml \
  --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
  --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 1 \
  --outputFolder $OUT > $LOG 2>&1
echo "EXIT $? $(date)" >> $LOG
echo "=== SMOKE DONE ==="
grep -aE "Assembled .* statuses|Discarded a VOID|Discarded an UNCONFIRMED|SECURITY_STATEFUL_AUTHORIZATION|Evaluated tests|Covered targets" $LOG | tail -30
