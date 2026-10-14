#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:-$EM/core/target/evomaster.jar}
OLDJAR=${OLDJAR:-$EM/evomaster-P1-80024675.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
SELF=$THESIS/infra/evomaster-ext/selftest
OUT=${1:-$THESIS/infra/em-results/p2-selftest-$(date +%Y%m%d-%H%M%S)}
PORT=${PORT:-18140}
MODES=(${=MODES:-enum-role bool-restricted num-two path-id-username access-level anon-deny gate-low put-id-source})
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"

mkdir -p $OUT
FAILED=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1  --  $2"; FAILED=1; }

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
  local mode=$1 tag=$2 jar=$3 d1=$4
  python3 $SELF/p2_stub.py $mode $PORT > $OUT/$mode-$tag-stub.err 2>&1 &
  local sp=$!
  if ! stub_up; then
    kill $sp 2>/dev/null
    echo "stub-down" > $OUT/$mode-$tag.exit
    return
  fi
  [ $tag = new ] && python3 $SELF/p2_scores.py http://localhost:$PORT/openapi.json $mode > $OUT/$mode-scores.txt 2>$OUT/$mode-scores.err
  java $DEBUG -jar $jar --blackBox true \
    --bbSwaggerUrl http://localhost:$PORT/openapi.json --bbTargetUrl http://localhost:$PORT \
    --configPath $OUT/auth.yaml \
    --statefulAuthzResetEndpoint "POST http://localhost:$PORT/thesis/reset" \
    --statefulAuthzTwoCredentialJudgment $d1 \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 1.0 \
    --outputFormat PYTHON_UNITTEST --maxTime 30s --seed 1 \
    --outputFolder $OUT/$mode-$tag > $OUT/$mode-$tag.log 2>&1
  echo $? > $OUT/$mode-$tag.exit
  kill $sp 2>/dev/null
  wait $sp 2>/dev/null
}

auth_yaml
for mode in $MODES; do
  run $mode new $JAR false
  echo "ran $mode new=$(cat $OUT/$mode-new.exit)"
done
run enum-role old $OLDJAR false
echo "ran enum-role old=$(cat $OUT/enum-role-old.exit)"
run anon-deny d1 $JAR true
echo "ran anon-deny d1=$(cat $OUT/anon-deny-d1.exit)"

python3 $SELF/p2_checks.py $OUT $MODES || FAILED=1
echo "output $OUT"
exit $FAILED
