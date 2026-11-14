#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:?JAR must name the jar under test}
REFJAR=${REFJAR:-$EM/evomaster-DC-a872a464.jar}
LEXJAR=${LEXJAR:-$EM/evomaster-SR-77465fe5.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
SELF=$THESIS/infra/evomaster-ext/selftest
PRE=$THESIS/infra/evomaster-ext/wip/thesis-comments-pre-shorten-20261112.patch
DCRUN=$THESIS/infra/em-results/redundant-code-selftest-20261103/run
OUT=${1:-$THESIS/infra/em-results/shorten-logic-selftest-$(date +%Y%m%d-%H%M%S)}
GAPS="route-missing current-false current-held restore-snapshot user-name-field num-id body-user-path-id"
ABPORT=${ABPORT:-18171}
ABSTOP=(${=ABSTOP:---stoppingCriterion ACTION_EVALUATIONS --maxEvaluations 300})
PARTS=${PARTS:-all}
B=core/src/main/kotlin/org/evomaster/core/problem/rest/service/RestSecurityBuilder.kt
O=core/src/main/kotlin/org/evomaster/core/problem/rest/oracle/RestSecurityOracle.kt
F=core/src/main/kotlin/org/evomaster/core/problem/enterprise/ExperimentalFaultCategory.kt
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
START=$(date '+%Y-%m-%d %H:%M:%S')

mkdir -p $OUT
cd $OUT
FAILED=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1  --  $2"; FAILED=1; }

lines() { grep -nF -- "$2" $EM/$1 | cut -d: -f1 | tr '\n' ',' | sed 's/,$//'; }
echo "exercises RestSecurityBuilder.kt walkBody :$(lines $B 'val container = if (v is ArrayGene'),$(lines $B 'walkBody("$prefix.')" \
  "transitionScore :$(lines $B 'prior("op") + opEvidenceCache')" \
  "buildStatefulAuthzTriple :$(lines $B 'if (outcome != RoleAttempt.NEXT)')" \
  "tryReducedRoles/restoreOperatorsAndRetry :$(lines $B 'if (hasPhaseTimedOut() || !attemptAllowed())')" \
  "bestField :$(lines $B 'private fun bestField(') roleField :$(lines $B 'bestField(a, "role", false)')" \
  "setUserTargetToVictim :$(lines $B 'bestField(action, "victim", true)')" \
  "setField :$(lines $B 'val accepted = try { f.value.setFromStringValue')" \
  "victimObjects :$(lines $B 'victimObjectCache.getOrPut(')" \
  "victimGetObjects :$(lines $B 'private fun victimGetObjects('),$(lines $B 'victimGetObjects(victimAuth, transition)');" \
  "RestSecurityOracle.kt handleStatefulAuthorization :$(lines $O '|| !isAllowed(followUp)) {')"
echo "jar-new $(shasum -a 256 $JAR | cut -c1-16)  jar-ref $(shasum -a 256 $REFJAR | cut -c1-16)"

head_count() { git -C $EM show HEAD:$1 | grep -cF -- "$2"; }
tree_count() { grep -cF -- "$2" $EM/$1; }

for spec in \
  "$B|fun transitionEvidence(" \
  "$B|private fun trySetFromStringValue(" \
  "$B|private fun getObjects(" \
  "$B|val cached = victimObjectCache[cacheKey]" \
  "$B|var pathScore = 0.0" \
  "$B|walkBody(\"\$name[].\${child.name}\"" \
  "$B|if (outcome == RoleAttempt.STOP_VICTIM) {" \
  "$B|if (!attemptAllowed()) return RoleAttempt.STOP_VICTIM" \
  "$O|if (!isAllowed(followUp)) {"; do
  f=${spec%%|*}
  pat=${spec#*|}
  before=$(head_count $f "$pat")
  after=$(tree_count $f "$pat")
  if [ $before -gt 0 ] && [ $after = 0 ]; then
    pass "gone     [$pat]  HEAD $before, tree 0"
  else
    fail "gone     [$pat]" "HEAD $before, tree $after"
  fi
done

for spec in \
  "$B|1|private fun bestField(a: RestCallAction, model: String, onPath: Boolean)" \
  "$B|1|bestField(a, \"role\", false)" \
  "$B|1|bestField(action, \"victim\", true)" \
  "$B|1|victimObjectCache.getOrPut(" \
  "$B|1|private fun victimGetObjects(" \
  "$B|2|victimGetObjects(victimAuth, transition)" \
  "$B|2|if (outcome != RoleAttempt.NEXT) {" \
  "$B|2|if (hasPhaseTimedOut() || !attemptAllowed()) return RoleAttempt.STOP_VICTIM" \
  "$B|1|val accepted = try { f.value.setFromStringValue(value) } catch (e: Exception) { false }" \
  "$B|1|walkBody(\"\$prefix.\${child.name}\"" \
  "$B|1|prior(\"op\") + opEvidenceCache.getOrPut(a.getName())" \
  "$O|1||| !isAllowed(followUp)) {"; do
  f=${spec%%|*}
  rest=${spec#*|}
  n=${rest%%|*}
  pat=${rest#*|}
  before=$(head_count $f "$pat")
  after=$(tree_count $f "$pat")
  if [ $before = 0 ] && [ $after = $n ]; then
    pass "new      [$pat]  HEAD 0, tree $after"
  else
    fail "new      [$pat]" "HEAD $before, tree $after, want $n"
  fi
done

for spec in \
  "$B|doInitialize(randomness)" \
  "$B|computeWholeAchievedCoverageForPostProcessing" \
  "$B|archive.addIfNeeded" \
  "$B|randomness" \
  "$B|log.debug(" \
  "$B|log.warn(" \
  "$B|getInfoLogger()" \
  "$B|StatusGroup.G_2xx.isInGroup" \
  "$O|isAllowed(" \
  "$O|looksLikePermissionReducingTransition" \
  "$O|addFault("; do
  f=${spec%%|*}
  pat=${spec#*|}
  before=$(head_count $f "$pat")
  after=$(tree_count $f "$pat")
  if [ $before -gt 0 ] && [ $before = $after ]; then
    pass "kept     [$pat]  HEAD $before, tree $after"
  else
    fail "kept     [$pat]" "HEAD $before, tree $after"
  fi
done

for pat in 'fieldScore(' 'schemaFields('; do
  before=$(head_count $B "$pat")
  after=$(tree_count $B "$pat")
  if [ $before -gt 1 ] && [ $after = $((before - 1)) ]; then
    pass "merged   [$pat]  HEAD $before, tree $after: the roleField loop and the path-field loop became one bestField loop"
  else
    fail "merged   [$pat]" "HEAD $before, tree $after, want HEAD - 1"
  fi
done

pre_lines=$(grep -E '^\+' $PRE | grep -vE '^\+\+\+' | grep -F 'THESIS' | sed -E 's/^\+[[:space:]]*//')
pre_n=$(echo "$pre_lines" | grep -c .)
missing=0
first_missing=""
while IFS= read -r l; do
  [ -z "$l" ] && continue
  if ! cat $EM/$B $EM/$O $EM/$F | grep -qF -- "$l"; then
    missing=$((missing + 1))
    [ -z "$first_missing" ] && first_missing=$l
  fi
done <<< "$pre_lines"
tree_n=$(cat $EM/$B $EM/$O $EM/$F | grep -c 'THESIS')
if [ $pre_n -gt 0 ] && [ $missing = 0 ] && [ $tree_n -ge $pre_n ]; then
  pass "thesis-comments-kept  $pre_n THESIS lines before the change, all present; tree has $tree_n"
else
  fail "thesis-comments-kept" "$missing of $pre_n missing, first [${first_missing:0:100}]; tree has $tree_n"
fi

added() { git -C $EM diff HEAD -- core/src/main/kotlin | grep -E '^\+' | grep -vE '^\+\+\+' | grep -vF 'THESIS'; }
removed() { git -C $EM diff HEAD -- core/src/main/kotlin | grep -E '^-' | grep -vE '^---' | grep -vF 'THESIS'; }

added_comments=$(added | grep -cE '^\+[[:space:]]*(//|/\*|\*|#)')
removed_comments=$(removed | grep -cE '^-[[:space:]]*(//|/\*|\*)')
if [ $added_comments = 0 ] && [ $removed_comments = 0 ]; then
  pass "no-comments    0 non-THESIS comment lines added, 0 removed"
else
  fail "no-comments" "added $added_comments, removed $removed_comments"
fi

prints=$(added | grep -cE 'println|printStackTrace|System\.out')
if [ $prints = 0 ]; then
  pass "no-prints      0 added"
else
  fail "no-prints" "$prints added"
fi

lam='\.(map|mapNotNull|flatMap|filter|filterNot|forEach|forEachIndexed|any|all|none|associate|fold|reduce|sumOf|maxBy|minBy|maxByOrNull|minByOrNull|firstOrNull|first|find|count|joinToString)[[:space:]]*[\{\(]'
lam_new=$(added | grep -cE "$lam")
lam_rem=$(removed | grep -cE "$lam")
if [ $lam_new = 0 ]; then
  pass "no-new-stream  0 stream calls added ($lam_rem removed)"
else
  fail "no-new-stream" "$lam_new added: $(added | grep -E "$lam" | head -2 | tr '\n' ' ')"
fi

log_changed=$( { added; removed; } | grep -cE 'log\.(debug|warn|info)|getInfoLogger')
if [ $log_changed = 0 ]; then
  pass "logs-untouched 0 log statements added or removed"
else
  fail "logs-untouched" "$log_changed log lines in the diff"
fi

ours() { git -C $EM diff $1 -- $B $O $F | grep -E '^\+' | grep -vE '^\+\+\+' | grep -vF 'THESIS' | grep -vcE '^\+[[:space:]]*$'; }
loc_head=$(ours "v6.1.1..HEAD")
loc_tree=$(ours "v6.1.1")
if [ $loc_tree -lt $loc_head ]; then
  pass "shorter        non-blank non-THESIS lines we add over v6.1.1: HEAD $loc_head, tree $loc_tree"
else
  fail "shorter" "HEAD $loc_head, tree $loc_tree"
fi

model_new=$(unzip -p $JAR stateful-authz-model.csv | shasum -a 256 | cut -c1-16)
model_ref=$(unzip -p $REFJAR stateful-authz-model.csv | shasum -a 256 | cut -c1-16)
if [ $model_new = $model_ref ]; then
  pass "model-same     stateful-authz-model.csv $model_new in both jars"
else
  fail "model-same" "$model_new vs $model_ref"
fi

cls() { unzip -p $1 'org/evomaster/core/problem/rest/service/RestSecurityBuilder*.class' | strings | grep -c "$2"; }
nb=$(cls $JAR bestField); nt=$(cls $JAR transitionEvidence); rb=$(cls $REFJAR bestField); rt=$(cls $REFJAR transitionEvidence)
if [ $nb -gt 0 ] && [ $nt = 0 ] && [ $rb = 0 ] && [ $rt -gt 0 ]; then
  pass "jar-has-change new jar: bestField $nb, transitionEvidence 0; ref jar: bestField 0, transitionEvidence $rt"
else
  fail "jar-has-change" "new bestField $nb transitionEvidence $nt; ref bestField $rb transitionEvidence $rt"
fi

if [ "${STATICONLY:-0}" = 1 ]; then
  echo "static checks only"
  exit $FAILED
fi

if [ $PARTS = all ]; then
JAR=$JAR REFJAR=$REFJAR LEXJAR=$LEXJAR REFLABEL=DC STATIC=0 GAPMODES=$GAPS \
  zsh $SELF/refactor-simplify-20261027.sh $OUT/run || FAILED=1

P2MODES= CANDMODES= SETMODES= PATHMODES= GAPMODES=query-role \
  STOP="--stoppingCriterion ACTION_EVALUATIONS --maxEvaluations 300" \
  JAR=$JAR REFJAR=$REFJAR LEXJAR=$LEXJAR REFLABEL=DC STATIC=0 PORT=18162 \
  zsh $SELF/refactor-simplify-20261027.sh $OUT/query-role-evals > $OUT/query-role-evals.out 2>&1
grep -E '^(PASS|FAIL|INFO)  gaps-query-role' $OUT/query-role-evals.out
if grep -qE '^FAIL  gaps-query-role' $OUT/query-role-evals.out || ! grep -qE '^PASS  gaps-query-role-trace-identical' $OUT/query-role-evals.out; then
  fail "query-role-evals" "see $OUT/query-role-evals.out"
else
  pass "query-role-evals  query-role under --maxEvaluations 300: trace identical to DC"
fi
fi

AB=$OUT/ab/gaps
mkdir -p $AB
cat > $AB/auth-array-body.yaml <<EOF
auth:
EOF
for u in alice boss bob eve; do
  cat >> $AB/auth-array-body.yaml <<EOF
  - name: $u
    loginEndpointAuth:
      payloadUserPwd:
        username: $u
        password: "${u}pass"
        usernameField: username
        passwordField: password
EOF
done
cat >> $AB/auth-array-body.yaml <<EOF
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
for tag in new refA refB; do
  j=$JAR
  [ $tag != new ] && j=$REFJAR
  python3 -I $SELF/array_body_stub.py array-body $ABPORT > $AB/array-body-$tag-stub.err 2>&1 &
  sp=$!
  up=0
  for i in {1..50}; do
    [ "$(curl -s -o /dev/null --max-time 1 -w '%{http_code}' http://localhost:$ABPORT/openapi.json)" = 200 ] && up=1 && break
    sleep 0.2
  done
  if [ $up = 0 ]; then
    echo "stub-down" > $AB/array-body-$tag.exit
    kill $sp 2>/dev/null
    continue
  fi
  cmd=(java -Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml -jar $j --blackBox true
    --bbSwaggerUrl http://localhost:$ABPORT/openapi.json --bbTargetUrl http://localhost:$ABPORT
    --configPath $AB/auth-array-body.yaml
    --useExperimentalOracles true --extraPhaseBudgetPercentage 1.0
    --outputFormat PYTHON_UNITTEST $ABSTOP --seed 1
    --outputFolder $AB/array-body-$tag)
  echo "${cmd[*]}" > $AB/array-body-$tag.cmd
  "${cmd[@]}" > $AB/array-body-$tag.log 2>&1
  echo $? > $AB/array-body-$tag.exit
  kill $sp 2>/dev/null
  wait $sp 2>/dev/null
done
echo "ran array-body new=$(cat $AB/array-body-new.exit) refA=$(cat $AB/array-body-refA.exit) refB=$(cat $AB/array-body-refB.exit)"
REFLABEL=DC python3 $SELF/refactor_compare.py $OUT/ab "" "" "" "" "array-body" > $OUT/ab/compare.txt 2>&1 || FAILED=1
cat $OUT/ab/compare.txt
marker='roleField body:members[].role victimField body:members[].username'
in_new=$(grep -cF -- "$marker" $AB/array-body-new.log)
in_ref=$(grep -cF -- "$marker" $AB/array-body-refA.log)
if [ $in_new -gt 0 ] && [ $in_ref -gt 0 ]; then
  pass "array-body-reached  walkBody array branch named the fields '$marker' in new and DC"
else
  fail "array-body-reached" "marker in new $in_new, in DC $in_ref"
fi

if [ $PARTS = all ]; then
for kind in p2 cand setfield; do
  mine=$OUT/run/$kind-checks.txt
  dc=$DCRUN/$kind-checks.txt
  a=$(grep -E '^(PASS|FAIL)' $mine 2>/dev/null | awk '{print $1, $2}' | sort)
  b=$(grep -E '^(PASS|FAIL)' $dc 2>/dev/null | awk '{print $1, $2}' | sort)
  if [ -n "$b" ] && [ "$a" = "$b" ]; then
    pass "legacy-$kind-same-as-DC  $(echo "$a" | grep -c '^PASS') PASS, $(echo "$a" | grep -c '^FAIL') FAIL, same names as the DC self-test"
  else
    fail "legacy-$kind-same-as-DC" "$(diff <(echo "$a") <(echo "$b") | head -4 | tr '\n' ' ')"
  fi
done

SENS=$OUT/sensitivity
mkdir -p $SENS/cand
M=noop-decoy
for f in old refA refB; do
  cp $OUT/run/cand/$M-$f.log $OUT/run/cand/$M-$f.cmd $SENS/cand/
  cp -R $OUT/run/cand/$M-$f $SENS/cand/
done
cp $SENS/cand/$M-old.log $SENS/cand/$M-new.log
cp $SENS/cand/$M-old.cmd $SENS/cand/$M-new.cmd
cp -R $SENS/cand/$M-old $SENS/cand/$M-new
REFLABEL=DC python3 $SELF/refactor_compare.py $SENS "" "$M" "" "" "" > $SENS/compare.txt 2>&1
sens_exit=$?
if [ $sens_exit = 1 ] && grep -qE "^FAIL  cand-$M-trace-identical" $SENS/compare.txt; then
  pass "compare-can-fail  AF2 logs swapped in as new make the trace check fail: $(grep -E "^FAIL  cand-$M-trace-identical" $SENS/compare.txt | cut -c1-140)"
else
  fail "compare-can-fail" "comparator exit $sens_exit on the older jar AF2; see $SENS/compare.txt"
fi
fi

sleeps=$(pmset -g log | awk -v s="$START" 'substr($0, 1, 19) >= s && /Entering Sleep/' | wc -l | tr -d ' ')
if [ $sleeps = 0 ]; then
  pass "no-sleep       0 'Entering Sleep' in pmset log since $START"
else
  fail "no-sleep" "$sleeps sleep entries since $START"
fi

echo "output $OUT"
exit $FAILED
