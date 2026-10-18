#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:-$EM/evomaster-P2f-64ee8ffc.jar}
OLDJAR=${OLDJAR:-$EM/evomaster-P2e-6ae8277b.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
SELF=$THESIS/infra/evomaster-ext/selftest
OUT=${1:-$THESIS/infra/em-results/setfield-selftest-$(date +%Y%m%d-%H%M%S)}
PORT=${PORT:-18150}
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"

mkdir -p $OUT
FAILED=0

echo "exercises RestSecurityBuilder.kt:1360-1361 (setField writes f.value and activates wrappers from that leaf), reached through setRoleFieldToReduced :1556 on is_admin {\"type\":[\"boolean\",\"null\"]}"
echo "jar-new $(shasum -a 256 $JAR | cut -c1-16)  jar-old $(shasum -a 256 $OLDJAR | cut -c1-16)"

auth_yaml() {
  local f=$OUT/auth.yaml
  echo "auth:" > $f
  for u in alice:alicepass boss:bosspass bob:bobpass; do
    cat >> $f <<EOF
  - name: ${u%%:*}
    loginEndpointAuth:
      payloadUserPwd:
        username: ${u%%:*}
        password: "${u#*:}"
        usernameField: username
        passwordField: password
EOF
  done
  cat >> $f <<EOF
authTemplate:
  loginEndpointAuth:
    endpoint: /auth/login
    verb: POST
    contentType: application/json
    token:
      extractFrom: body
      extractSelector: /token
      sendIn: header
      sendName: Authorization
      sendTemplate: "Bearer {token}"
EOF
}

stub_up() {
  for i in {1..50}; do
    [ "$(curl -s -o /dev/null --max-time 1 -w '%{http_code}' http://localhost:$PORT/openapi.json)" = 200 ] && return 0
    sleep 0.2
  done
  return 1
}

run() {
  local tag=$1 jar=$2
  rm -f $OUT/$tag-stub.jsonl
  python3 $SELF/setfield_stub.py $PORT $OUT/$tag-stub.jsonl > $OUT/$tag-stub.err 2>&1 &
  local sp=$!
  if ! stub_up; then
    kill $sp 2>/dev/null
    echo "stub-down" > $OUT/$tag.exit
    return
  fi
  java $DEBUG -jar $jar --blackBox true \
    --bbSwaggerUrl http://localhost:$PORT/openapi.json --bbTargetUrl http://localhost:$PORT \
    --configPath $OUT/auth.yaml \
    --statefulAuthzResetEndpoint "POST http://localhost:$PORT/thesis/reset" \
    --statefulAuthzTwoCredentialJudgment false \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 1.0 \
    --outputFormat PYTHON_UNITTEST --maxTime 30s --seed 1 \
    --outputFolder $OUT/$tag > $OUT/$tag.log 2>&1
  echo $? > $OUT/$tag.exit
  kill $sp 2>/dev/null
  wait $sp 2>/dev/null
}

auth_yaml
run new $JAR
echo "ran new=$(cat $OUT/new.exit)"
run old $OLDJAR
echo "ran old=$(cat $OUT/old.exit)"

python3 $SELF/setfield_checks.py $OUT || FAILED=1
echo "output $OUT"
exit $FAILED
