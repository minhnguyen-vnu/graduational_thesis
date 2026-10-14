#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:-$EM/core/target/evomaster.jar}
OLDJAR=${OLDJAR:-$EM/evomaster-AF2-6b5606d4.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
SELF=$THESIS/infra/evomaster-ext/selftest
OUT=${1:-$THESIS/infra/em-results/candidate-iteration-selftest-$(date +%Y%m%d-%H%M%S)}
PORT=${PORT:-18080}
MODES=(${=MODES:-noop-decoy reject-decoy restore-budget protected-victim revoke proven-404 alpha cap20 bool-flag})
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"

mkdir -p $OUT
FAILED=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1  --  $2"; FAILED=1; }

echo "jar-new $(shasum -a 256 $JAR | cut -c1-16)  jar-old $(shasum -a 256 $OLDJAR | cut -c1-16)"
unzip -p $JAR stateful-authz-lexicon.csv > $OUT/lexicon.csv

auth_yaml() {
  local mode=$1 f=$OUT/auth-$1.yaml
  local users=(alice:alicepass boss:bosspass bob:bobpass)
  [ $mode = proven-404 ] && users+=(carol:carolpass)
  echo "auth:" > $f
  for u in $users; do
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
  local mode=$1 tag=$2 jar=$3
  python3 $SELF/candidate_stub.py $mode $PORT > $OUT/$mode-$tag-stub.err 2>&1 &
  local sp=$!
  if ! stub_up; then
    kill $sp 2>/dev/null
    echo "stub-down" > $OUT/$mode-$tag.exit
    return
  fi
  local reset=()
  [ $mode = cap20 ] && reset=(--statefulAuthzResetEndpoint "POST http://localhost:$PORT/reset")
  java $DEBUG -jar $jar --blackBox true \
    --bbSwaggerUrl http://localhost:$PORT/openapi.json --bbTargetUrl http://localhost:$PORT \
    --configPath $OUT/auth-$mode.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 1.0 "${reset[@]}" \
    --outputFormat PYTHON_UNITTEST --maxTime 30s --seed 1 \
    --outputFolder $OUT/$mode-$tag > $OUT/$mode-$tag.log 2>&1
  echo $? > $OUT/$mode-$tag.exit
  kill $sp 2>/dev/null
  wait $sp 2>/dev/null
}

for mode in $MODES; do
  auth_yaml $mode
  python3 $SELF/candidate_stub.py $mode $PORT > /dev/null 2>&1 &
  sp=$!
  if stub_up && python3 $SELF/candidate_scores.py $OUT/lexicon.csv http://localhost:$PORT/openapi.json $mode > $OUT/$mode-scores.txt; then
    pass "$mode-fixture             $(tail -1 $OUT/$mode-scores.txt); $(head -1 $OUT/$mode-scores.txt | cut -c1-150)"
  else
    fail "$mode-fixture" "$(cat $OUT/$mode-scores.txt 2>/dev/null | tr '\n' ' ')"
  fi
  kill $sp 2>/dev/null
  wait $sp 2>/dev/null
  run $mode new $JAR
  run $mode old $OLDJAR
  echo "ran $mode new=$(cat $OUT/$mode-new.exit) old=$(cat $OUT/$mode-old.exit)"
done

python3 $SELF/candidate_checks.py $OUT $MODES || FAILED=1

SWAP=$OUT/swapped
mkdir -p $SWAP
for mode in $MODES; do
  for pair in new:old old:new; do
    a=${pair%%:*}
    b=${pair#*:}
    ln -sf $OUT/$mode-$b.log $SWAP/$mode-$a.log
    ln -sf $OUT/$mode-$b.exit $SWAP/$mode-$a.exit
    ln -sfn $OUT/$mode-$b $SWAP/$mode-$a
  done
done
python3 $SELF/candidate_checks.py $SWAP $MODES > $OUT/swapped-checks.txt
NEWCODE=(noop-decoy-next-candidate noop-decoy-mark-cleared reject-decoy-cap5 reject-decoy-true-fires
  restore-budget-per-candidate restore-budget-refused-pair restore-budget-true-fires protected-victim-skip
  revoke-label proven-404-keeps-candidate alpha-no-cut cap20-total bool-flag-restore-unavailable)
present=0
missed=()
for c in $NEWCODE; do
  if grep -q "^FAIL  $c " $OUT/swapped-checks.txt; then
    present=$((present + 1))
  elif grep -q "^PASS  $c " $OUT/swapped-checks.txt; then
    missed+=($c)
  fi
done
if [ $present -gt 0 ] && [ ${#missed} = 0 ]; then
  pass "checks-can-fail              with the old jar's logs in place of the new jar's, all $present checks on new code print FAIL"
else
  fail "checks-can-fail" "these checks still pass on the old jar's logs: ${missed[*]}"
fi

echo "NOTE  not exercised by a run: noStatusRecorded :789 (codes -/-/-), reLoginProbeInconclusive :1058, restoreSkipped :1179"
echo "output $OUT"
exit $FAILED
