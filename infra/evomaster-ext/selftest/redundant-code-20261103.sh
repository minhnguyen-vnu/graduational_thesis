#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:?JAR must name the jar under test}
REFJAR=${REFJAR:-$EM/evomaster-SR-77465fe5.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
SELF=$THESIS/infra/evomaster-ext/selftest
OUT=${1:-$THESIS/infra/em-results/redundant-code-selftest-$(date +%Y%m%d-%H%M%S)}
GAPS="route-missing query-role current-false current-held restore-snapshot user-name-field num-id body-user-path-id"
B=core/src/main/kotlin/org/evomaster/core/problem/rest/service/RestSecurityBuilder.kt
O=core/src/main/kotlin/org/evomaster/core/problem/rest/oracle/RestSecurityOracle.kt

mkdir -p $OUT
cd $OUT
FAILED=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1  --  $2"; FAILED=1; }

echo "exercises RestSecurityBuilder.kt tokens, addForStatefulAccessControl, buildStatefulAuthzTriple, tryReducedRoles, restoreOperatorsAndRetry, executeStatefulAuthzTriple, reLoginProbeConfirmsPrivilegeRemoved, rankPermissionReducingTransitions, roleField, victimField, reducedRoleValues, restoreValues, restorePlans, restorePrivilege, loginKeys, findVictimObjects, compareVictimObjects, collectVictimObjects, setUserTargetToVictim, placeVictimValue, keepOnlyTargetFields, setUserNameFieldsToVictim, routeLooksMissing; RestSecurityOracle.kt handleStatefulAuthorization"
echo "jar-new $(shasum -a 256 $JAR | cut -c1-16)  jar-ref $(shasum -a 256 $REFJAR | cut -c1-16)"

gone_b=(
  'victimAuth is NoAuth'
  'followUp.auth = victimAuth'
  'followUp.usePreviousLocationId'
  'individualsInSolution = archive.extractSolution'
  'logModelScores'
  'pair: Pair<String, String>'
  'if (field != null)'
  'if (fields.isEmpty())'
  'if (perField.isEmpty())'
  'if (privilegeRestoreAttempts >= MAX_PRIVILEGE_RESTORES) return false'
  'node != null'
  'data class ScoredObject'
  'class TransitionCandidate'
  'if (idKeys.isEmpty())'
  'prefix.isNotEmpty()'
  'isContainerNode'
  'action !is RestCallAction'
  'val rest = mutableListOf'
  'victimField(a: RestCallAction, role'
  'if (piece.isEmpty())'
  'api.param.Param'
  'best == null || score > bestScore)) {'
  'toSet())'
  'TOKEN_PIECE'
  'enum != null && enumValues'
  'nk != leaf'
  'v.isObject || v.isArray'
)
for pat in $gone_b; do
  before=$(git -C $EM show HEAD:$B | grep -cF -- "$pat")
  after=$(grep -cF -- "$pat" $EM/$B)
  if [ "$pat" = 'toSet())' ]; then
    before=$(git -C $EM show HEAD:$B | grep -c 'keepOnlyTargetFields(.*toSet())')
    after=$(grep -c 'keepOnlyTargetFields(.*toSet())' $EM/$B)
  fi
  if [ $after = 0 ] && [ $before -gt 0 ]; then
    pass "gone-builder  [$pat]  HEAD $before, tree 0"
  else
    fail "gone-builder  [$pat]" "HEAD $before, tree $after"
  fi
done

for pat in 'phase timed out before source' 'phase timed out on source' 'attempt cap $MAX_STATEFUL_TRIPLE_ATTEMPTS reached'; do
  before=$(git -C $EM show HEAD:$B | grep -cF -- "$pat")
  after=$(grep -cF -- "$pat" $EM/$B)
  if [ $before -gt 0 ] && [ $before = $after ]; then
    pass "kept-exit     [$pat]  HEAD $before, tree $after"
  else
    fail "kept-exit     [$pat]" "HEAD $before, tree $after"
  fi
done

if $(/usr/libexec/java_home -v 17)/bin/java $SELF/TokensEquiv.java 2000000 > $OUT/tokens-equiv.txt 2>&1; then
  pass "tokens-equiv  $(cat $OUT/tokens-equiv.txt)"
else
  fail "tokens-equiv" "$(tail -1 $OUT/tokens-equiv.txt)"
fi

for pat in 'statusOf' '.find { it.sourceLocalId == followUp.getLocalId() }' 'isEnabledFaultCategory(ExperimentalFaultCategory.SECURITY_STATEFUL_AUTHORIZATION)' 'listOf(HttpVerb.PUT, HttpVerb.PATCH, HttpVerb.POST, HttpVerb.DELETE)'; do
  before=$(git -C $EM show HEAD:$O | grep -cF -- "$pat")
  after=$(grep -cF -- "$pat" $EM/$O)
  if [ $after = 0 ] && [ $before -gt 0 ]; then
    pass "gone-oracle   [$pat]  HEAD $before, tree 0"
  else
    fail "gone-oracle   [$pat]" "HEAD $before, tree $after"
  fi
done

new_lex=$(unzip -l $JAR | grep -c stateful-authz-lexicon.csv)
ref_lex=$(unzip -l $REFJAR | grep -c stateful-authz-lexicon.csv)
new_mod=$(unzip -l $JAR | grep -c stateful-authz-model.csv)
readers=$(grep -rn "authz-lexicon" $EM/core/src/main/kotlin | wc -l | tr -d ' ')
if [ $new_lex = 0 ] && [ $ref_lex = 1 ] && [ $new_mod = 1 ] && [ $readers = 0 ]; then
  pass "lexicon-gone  new jar 0 lexicon + 1 model, ref jar 1 lexicon, 0 readers in the source"
else
  fail "lexicon-gone" "new lexicon $new_lex, ref lexicon $ref_lex, new model $new_mod, readers $readers"
fi

model_new=$(unzip -p $JAR stateful-authz-model.csv | shasum -a 256 | cut -c1-16)
model_ref=$(unzip -p $REFJAR stateful-authz-model.csv | shasum -a 256 | cut -c1-16)
if [ $model_new = $model_ref ]; then
  pass "model-same    stateful-authz-model.csv $model_new in both jars"
else
  fail "model-same" "$model_new vs $model_ref"
fi

added() { git -C $EM diff HEAD -- core/src/main/kotlin | grep -E '^\+' | grep -vE '^\+\+\+'; }
removed() { git -C $EM diff HEAD -- core/src/main/kotlin | grep -E '^-' | grep -vE '^---'; }

added_comments=$(added | grep -cE '^\+[[:space:]]*(//|/\*|\*|#)')
removed_comments=$(removed | grep -cE '^-[[:space:]]*(//|/\*|\*)')
if [ $added_comments = 0 ] && [ $removed_comments = 0 ]; then
  pass "no-comments   0 added, 0 removed"
else
  fail "no-comments" "added $added_comments, removed $removed_comments"
fi

prints=$(added | grep -cE 'println|printStackTrace|System\.out')
if [ $prints = 0 ]; then
  pass "no-prints     0 added"
else
  fail "no-prints" "$prints added"
fi

lam='\.(map|mapNotNull|flatMap|filter|filterNot|forEach|forEachIndexed|any|all|none|associate|fold|reduce|sumOf|maxBy|minBy|maxByOrNull|minByOrNull|firstOrNull|first|find|count)[[:space:]]*\{'
lam_new=$(added | grep -cE "$lam")
lam_rem=$(removed | grep -cE "$lam")
sort_new=$(added | grep -cE '\.sorted(By|ByDescending)[[:space:]]*\{')
sort_rem=$(removed | grep -cE '\.sorted(By|ByDescending)[[:space:]]*\{')
if [ $lam_new -le $lam_rem ] && [ $sort_new -le $sort_rem ]; then
  pass "no-new-lambda stream lambdas added $lam_new, removed $lam_rem; sort lambdas added $sort_new, removed $sort_rem"
else
  fail "no-new-lambda" "stream added $lam_new removed $lam_rem, sort added $sort_new removed $sort_rem"
fi

LOGSTAT=$(git -C $EM diff HEAD -- core/src/main/kotlin | grep -E '^[-+]' | grep -E 'log\.(debug|warn|info)|getInfoLogger' | grep -vE '^(\+\+\+|---)')
LOGREM=$(echo "$LOGSTAT" | grep -c '^-')
LOGADD=$(echo "$LOGSTAT" | grep -c '^+')
echo "INFO  log statements changed: removed $LOGREM, added $LOGADD"
echo "$LOGSTAT"

if [ "${STATICONLY:-0}" = 1 ]; then
  echo "static checks only"
  exit $FAILED
fi

JAR=$JAR REFJAR=$REFJAR LEXJAR=$REFJAR REFLABEL=SR STATIC=0 GAPMODES=$GAPS \
  zsh $SELF/refactor-simplify-20261027.sh $OUT/run || FAILED=1

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
REFLABEL=SR python3 $SELF/refactor_compare.py $SENS "" "$M" "" "" "" > $SENS/compare.txt 2>&1
sens_exit=$?
if [ $sens_exit = 1 ] && grep -qE "^FAIL  cand-$M-trace-identical" $SENS/compare.txt; then
  pass "compare-can-fail  AF2 logs swapped in as new make the trace check fail: $(grep -E "^FAIL  cand-$M-trace-identical" $SENS/compare.txt | cut -c1-140)"
else
  fail "compare-can-fail" "comparator exit $sens_exit on the older jar AF2; see $SENS/compare.txt"
fi

echo "output $OUT"
exit $FAILED
