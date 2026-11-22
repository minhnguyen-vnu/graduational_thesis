#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:?JAR must name the jar under test}
REFJAR=${REFJAR:-$EM/evomaster-LF-d559dc73.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
SELF=$THESIS/infra/evomaster-ext/selftest
OUT=${1:-$THESIS/infra/em-results/c4-source-status-selftest-$(date +%Y%m%d-%H%M%S)}
MODES=(${=MODES:-len1 chain prior-noncreate anon-prefix source-200 op-refused value-reject prior-harmless})
PORT=${PORT:-18281}
STOP=(--stoppingCriterion ACTION_EVALUATIONS --maxEvaluations ${EVALS:-300})
LFRUN=${LFRUN:-$THESIS/infra/em-results/logic-fix-selftest-20261118-014908}
DEBUG=-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml
B=core/src/main/kotlin/org/evomaster/core/problem/rest/service/RestSecurityBuilder.kt
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
START=$(date '+%Y-%m-%d %H:%M:%S')

mkdir -p $OUT
cd $OUT
FAILED=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1  --  $2"; FAILED=1; }

lines() { grep -nF -- "$2" $EM/$1 | cut -d: -f1 | tr '\n' ',' | sed 's/,$//'; }
echo "exercises RestSecurityBuilder.kt" \
  "callsBeforeSourceMatchTriple :$(lines $B 'private fun callsBeforeSourceMatchTriple('),$(lines $B 'val original = statusIn(tripleEi, actions[i]) ?: return false'),$(lines $B 'if (code / 100 != original / 100) {')" \
  "C4 probe :$(lines $B 'if (!callsBeforeSourceMatchTriple(probe, ei, tripleEi))'),$(lines $B 'val sourceCode = statusIn(ei, probe.seeMainExecutableActions().last())')" \
  "C4 control :$(lines $B 'control.seeMainExecutableActions().last().auth = HttpWsNoAuth()'),$(lines $B 'if (!callsBeforeSourceMatchTriple(control, cei, tripleEi))'),$(lines $B 'val anonymousCode = statusIn(cei, control.seeMainExecutableActions().last())')" \
  "tryReducedRoles :$(lines $B 'val code = lastTransitionCode ?: return RoleAttempt.NEXT'),$(lines $B '|| code == 404) {'),$(lines $B 'if (code < 400 || code > 599) {')"
echo "jar-new $(shasum -a 256 $JAR | cut -c1-16)  jar-ref $(shasum -a 256 $REFJAR | cut -c1-16)"

added() { git -C $EM diff HEAD -- core/src/main/kotlin | grep -E '^\+' | grep -vE '^\+\+\+' | grep -vF 'THESIS'; }
added_comments=$(added | grep -cE '^\+[[:space:]]*(//|/\*|\*|#)')
if [ $added_comments = 0 ]; then
  pass "no-comments    0 non-THESIS comment lines added over HEAD"
else
  fail "no-comments" "$added_comments added"
fi
prints=$(added | grep -cE 'println|printStackTrace|System\.out')
if [ $prints = 0 ]; then
  pass "no-prints      0 added"
else
  fail "no-prints" "$prints added"
fi

model_new=$(unzip -p $JAR stateful-authz-model.csv | shasum -a 256 | cut -c1-16)
model_ref=$(unzip -p $REFJAR stateful-authz-model.csv | shasum -a 256 | cut -c1-16)
if [ $model_new = $model_ref ]; then
  pass "model-same     stateful-authz-model.csv $model_new in both jars"
else
  fail "model-same" "$model_new vs $model_ref"
fi

cls() { unzip -p $1 'org/evomaster/core/problem/rest/service/RestSecurityBuilder.class' | strings | grep -c "$2"; }
for spec in "callsBeforeSourceMatchTriple|new" "skippedTransitionVictims|new" "lastVictimStatus|ref" \
  "transitionRejectedRoleValue|ref" "refusedTransitionVictims|ref"; do
  name=${spec%%|*}
  side=${spec#*|}
  n=$(cls $JAR $name)
  r=$(cls $REFJAR $name)
  if { [ $side = new ] && [ $n -gt 0 ] && [ $r = 0 ]; } || { [ $side = ref ] && [ $n = 0 ] && [ $r -gt 0 ]; }; then
    pass "jar-has-change $name: new jar $n, ref jar $r"
  else
    fail "jar-has-change $name" "new jar $n, ref jar $r (expected only in the $side jar)"
  fi
done

if [ "${STATICONLY:-0}" = 1 ]; then
  echo "static checks only"
  exit $FAILED
fi

cat > $OUT/auth.yaml <<EOF
auth:
EOF
for u in alice boss bob eve; do
  cat >> $OUT/auth.yaml <<EOF
  - name: $u
    loginEndpointAuth:
      payloadUserPwd:
        username: $u
        password: "${u}pass"
        usernameField: username
        passwordField: password
EOF
done
cat >> $OUT/auth.yaml <<EOF
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

for mode in $MODES; do
  for tag in cs lf; do
    j=$JAR
    [ $tag = lf ] && j=$REFJAR
    rm -f $OUT/$mode-$tag-req.jsonl
    python3 -I $SELF/c4src_stub.py $mode $PORT $OUT/$mode-$tag-req.jsonl > $OUT/$mode-$tag-stub.err 2>&1 &
    sp=$!
    up=0
    for i in {1..50}; do
      [ "$(curl -s -o /dev/null --max-time 1 -w '%{http_code}' http://localhost:$PORT/openapi.json)" = 200 ] && up=1 && break
      sleep 0.2
    done
    if [ $up = 0 ]; then
      echo "stub-down" > $OUT/$mode-$tag.exit
      kill $sp 2>/dev/null
      continue
    fi
    cmd=(java $DEBUG -jar $j --blackBox true
      --bbSwaggerUrl http://localhost:$PORT/openapi.json --bbTargetUrl http://localhost:$PORT
      --configPath $OUT/auth.yaml
      --useExperimentalOracles true --extraPhaseBudgetPercentage 1.0
      --outputFormat PYTHON_UNITTEST $STOP --seed 1
      --outputFolder $OUT/$mode-$tag)
    echo "${cmd[*]}" > $OUT/$mode-$tag.cmd
    "${cmd[@]}" > $OUT/$mode-$tag.log 2>&1
    echo $? > $OUT/$mode-$tag.exit
    kill $sp 2>/dev/null
    wait $sp 2>/dev/null
  done
  echo "ran $mode cs=$(cat $OUT/$mode-cs.exit) lf=$(cat $OUT/$mode-lf.exit)"
done

python3 -I $SELF/c4src_checks.py $OUT ${=MODES} || FAILED=1

if [ "${REGRESS:-1}" = 1 ]; then
  JAR=$JAR zsh $SELF/logic-fix-20261118.sh $OUT/logicfix > $OUT/logicfix.out 2>&1
  lfexit=$?
  grep -E '^(PASS|FAIL)' $OUT/logicfix.out | grep -vE 'no-sleep|no-comments|no-prints|jar-has-change|gone ' > $OUT/logicfix-checks.txt
  nfail=$(grep -c '^FAIL' $OUT/logicfix-checks.txt)
  npass=$(grep -c '^PASS' $OUT/logicfix-checks.txt)
  if [ $nfail = 0 ] && [ $npass -gt 0 ]; then
    pass "logicfix-behaviour  logic-fix-20261118.sh behaviour checks on the new jar: $npass PASS, 0 FAIL (exit $lfexit)"
  else
    fail "logicfix-behaviour" "$npass PASS, $nfail FAIL; see $OUT/logicfix.out"
  fi
  python3 -I $SELF/c4src_compare.py $LFRUN $OUT/logicfix || FAILED=1
fi

sleeps=$(pmset -g log | awk -v s="$START" 'substr($0, 1, 19) >= s && /Entering Sleep/' | wc -l | tr -d ' ')
if [ $sleeps = 0 ]; then
  pass "no-sleep       0 'Entering Sleep' in pmset log since $START"
else
  fail "no-sleep" "$sleeps sleep entries since $START"
fi

echo "output $OUT"
exit $FAILED
