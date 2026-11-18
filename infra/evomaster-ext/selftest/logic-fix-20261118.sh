#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:?JAR must name the jar under test}
REFJAR=${REFJAR:-$EM/evomaster-ND-07ebf19f.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
SELF=$THESIS/infra/evomaster-ext/selftest
OUT=${1:-$THESIS/infra/em-results/logic-fix-selftest-$(date +%Y%m%d-%H%M%S)}
MODES=(${=MODES:-post-source login-name enum-lower two-role-fields bool-victim first-404 query-username nested-role num-enum c4-intact no-path-id source-401})
PORT=${PORT:-18181}
STOP=(--stoppingCriterion ACTION_EVALUATIONS --maxEvaluations ${EVALS:-300})
DEBUG=-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml
B=core/src/main/kotlin/org/evomaster/core/problem/rest/service/RestSecurityBuilder.kt
O=core/src/main/kotlin/org/evomaster/core/problem/rest/oracle/RestSecurityOracle.kt
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
START=$(date '+%Y-%m-%d %H:%M:%S')

mkdir -p $OUT
cd $OUT
FAILED=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1  --  $2"; FAILED=1; }

lines() { grep -nF -- "$2" $EM/$1 | cut -d: -f1 | tr '\n' ',' | sed 's/,$//'; }
echo "exercises RestSecurityBuilder.kt" \
  "guardedSources :$(lines $B 'listOf(HttpVerb.PUT, HttpVerb.PATCH, HttpVerb.POST)'),$(lines $B '|| looksLikePermissionReducingTransition(op)')" \
  "loginName :$(lines $B 'private fun findLoginName('),$(lines $B 'if (seenInResponses(p.first, p.second))')" \
  "reducedRoleValues :$(lines $B 'v != "EVOMASTER" && lowMinusHigh(v) >= 0.0'),$(lines $B '"bool" -> listOf("false")')" \
  "victimField :$(lines $B 'val score = fieldScore("victim", f)')" \
  "setRoleFieldToReduced :$(lines $B 'for (other in restoreFields(action))')" \
  "trimToTargetFields :$(lines $B 'k.startsWith(f.key + ".")'),$(lines $B 'if (setField(f, login)) kept.add(f.key)')" \
  "404 :$(lines $B 'refusedTransitionVictims.add(transitionDef.getName() to victimAuth.name)')" \
  "C4 :$(lines $B 'val lastObserved = lastVictimStatus('),$(lines $B 'privilegeReducedInPhase.remove(victimAuth.name)')" \
  "RestSecurityOracle.kt anchored :$(lines $O 'val source = actions[followUpIndex - 2]')"
echo "jar-new $(shasum -a 256 $JAR | cut -c1-16)  jar-ref $(shasum -a 256 $REFJAR | cut -c1-16)"

for spec in \
  "$B|private fun routeLooksMissing(" \
  "$B|private fun keepOnlyTargetFields(" \
  "$B|private fun setUserNameFieldsToVictim(" \
  "$B|private fun anyAuthenticatedSuccess(" \
  "$B|private fun lastRecordedStatus(" \
  "$B|transitionNotFoundSeen" \
  "$B|opEvidenceCache" \
  "$B|stopSources" \
  "$B|if (best == null || score > bestScore)" \
  "$O|for (srcIndex in actions.indices)" \
  "$O|for (tIndex in"; do
  f=${spec%%|*}
  pat=${spec#*|}
  before=$(git -C $EM show HEAD:$f | grep -cF -- "$pat")
  after=$(grep -cF -- "$pat" $EM/$f)
  if [ $before -gt 0 ] && [ $after = 0 ]; then
    pass "gone      [$pat]  HEAD $before, tree 0"
  else
    fail "gone      [$pat]" "HEAD $before, tree $after"
  fi
done

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
n1=$(cls $JAR trimToTargetFields); n2=$(cls $JAR routeLooksMissing); r1=$(cls $REFJAR trimToTargetFields); r2=$(cls $REFJAR routeLooksMissing)
if [ $n1 -gt 0 ] && [ $n2 = 0 ] && [ $r1 = 0 ] && [ $r2 -gt 0 ]; then
  pass "jar-has-change new jar: trimToTargetFields $n1, routeLooksMissing 0; ref jar: trimToTargetFields 0, routeLooksMissing $r2"
else
  fail "jar-has-change" "new trimToTargetFields $n1 routeLooksMissing $n2; ref trimToTargetFields $r1 routeLooksMissing $r2"
fi

if [ "${STATICONLY:-0}" = 1 ]; then
  echo "static checks only"
  exit $FAILED
fi

auth_yaml() {
  local f=$1
  shift
  echo "auth:" > $f
  for u in $@; do
    local name=${u%%:*}
    local user=${u#*:}
    cat >> $f <<EOF
  - name: $name
    loginEndpointAuth:
      payloadUserPwd:
        username: $user
        password: "${user}pass"
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

for mode in $MODES; do
  if [ $mode = login-name ]; then
    auth_yaml $OUT/auth-$mode.yaml alice:alice boss:boss opr:bob eve:eve
  elif [ $mode = source-401 ]; then
    auth_yaml $OUT/auth-$mode.yaml alice:alice boss:boss eve:eve bob:bob
  else
    auth_yaml $OUT/auth-$mode.yaml alice:alice boss:boss bob:bob eve:eve
  fi
  lockafter=-1
  tags=(nd lf)
  [ $mode = source-401 ] && tags=(cal nd lf)
  for tag in $tags; do
    j=$JAR
    [ $tag != lf ] && j=$REFJAR
    if [ $tag = nd ] && [ $mode = source-401 ]; then
      lockafter=$(python3 -I $SELF/logicfix_checks.py --lock-point $OUT $mode-cal)
      echo "source-401 lock point $lockafter" > $OUT/$mode-lockpoint.txt
    fi
    rm -f $OUT/$mode-$tag-req.jsonl
    python3 -I $SELF/logicfix_stub.py $mode $PORT $OUT/$mode-$tag-req.jsonl $lockafter > $OUT/$mode-$tag-stub.err 2>&1 &
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
      --configPath $OUT/auth-$mode.yaml
      --useExperimentalOracles true --extraPhaseBudgetPercentage 1.0
      --outputFormat PYTHON_UNITTEST $STOP --seed 1
      --outputFolder $OUT/$mode-$tag)
    echo "${cmd[*]}" > $OUT/$mode-$tag.cmd
    "${cmd[@]}" > $OUT/$mode-$tag.log 2>&1
    echo $? > $OUT/$mode-$tag.exit
    kill $sp 2>/dev/null
    wait $sp 2>/dev/null
  done
  echo "ran $mode nd=$(cat $OUT/$mode-nd.exit) lf=$(cat $OUT/$mode-lf.exit)"
done

python3 -I $SELF/logicfix_checks.py $OUT || FAILED=1

sleeps=$(pmset -g log | awk -v s="$START" 'substr($0, 1, 19) >= s && /Entering Sleep/' | wc -l | tr -d ' ')
if [ $sleeps = 0 ]; then
  pass "no-sleep       0 'Entering Sleep' in pmset log since $START"
else
  fail "no-sleep" "$sleeps sleep entries since $START"
fi

echo "output $OUT"
exit $FAILED
