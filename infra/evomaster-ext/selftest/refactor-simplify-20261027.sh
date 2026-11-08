#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:-$EM/evomaster-SR-77465fe5.jar}
REFJAR=${REFJAR:-$EM/evomaster-P2f-64ee8ffc.jar}
P2OLD=${P2OLD:-$EM/evomaster-P1-80024675.jar}
CANDOLD=${CANDOLD:-$EM/evomaster-AF2-6b5606d4.jar}
SETOLD=${SETOLD:-$EM/evomaster-P2e-6ae8277b.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
SELF=$THESIS/infra/evomaster-ext/selftest
OUT=${1:-$THESIS/infra/em-results/refactor-simplify-selftest-$(date +%Y%m%d-%H%M%S)}
PORT=${PORT:-18160}
STOP=(${=STOP:---maxTime 30s})
P2MODES=(${=P2MODES-enum-role bool-restricted num-two path-id-username access-level anon-deny gate-low put-id-source})
CANDMODES=(${=CANDMODES-noop-decoy reject-decoy restore-budget protected-victim revoke proven-404 alpha cap20 bool-flag})
SETMODES=(${=SETMODES-setfield})
PATHMODES=(${=PATHMODES-cap5 cap20 unavailable budget})
GAPMODES=(${=GAPMODES-})
LEXJAR=${LEXJAR:-$JAR}
SETSTOP=(${=SETSTOP:---stoppingCriterion ACTION_EVALUATIONS --maxEvaluations 300})
STATIC=${STATIC:-1}
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
SRC=$EM/core/src/main/kotlin/org/evomaster/core
REMOVED="statefulAuthzTransition|statefulAuthzResetEndpoint|statefulAuthzTwoCredentialJudgment|parseDeclaredTransition|DeclaredTransition|resetSutState|freshCredentialDeniesFollowUp|privilegeRemovalConfirmed|unconfirmedReason|inconclusiveProbe|applyDeclaredBindings|distinctUsersOn|MAX_STATEFUL_TRIPLE_ATTEMPTS_DECLARED|maxStatefulAttempts"

mkdir -p $OUT/p2 $OUT/cand $OUT/setfield $OUT/paths $OUT/gaps
FAILED=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1  --  $2"; FAILED=1; }

echo "exercises RestSecurityBuilder.kt:91-349 (model, tokens, schema fields, scores as loops), :641-764 (addForStatefulAccessControl, stopSources flag), :766-836 (guardedSources, anyAuthenticatedSuccess, victimSlicesOn, operatorsFor), :838-990 (buildStatefulAuthzTriple, tryReducedRoles, restoreOperatorsAndRetry, RoleAttempt), :1018-1193 (executeStatefulAuthzTriple without declared/reset/D1, C4 probe), :1195-1811 (field, value, restore and victim-object helpers as loops); RestSecurityOracle.kt:575-603; EMConfig without the three options"
echo "jar-new $(shasum -a 256 $JAR | cut -c1-16)  jar-ref $(shasum -a 256 $REFJAR | cut -c1-16)  stop ${STOP[*]}  setfield-stop ${SETSTOP[*]}"

if [ $STATIC = 1 ]; then
  opts_new=$(unzip -p $JAR 'org/evomaster/core/EMConfig*.class' | strings | grep -o "statefulAuthz[A-Za-z]*" | sort -u | tr '\n' ' ')
  opts_ref=$(unzip -p $REFJAR 'org/evomaster/core/EMConfig*.class' | strings | grep -o "statefulAuthz[A-Za-z]*" | sort -u | wc -l | tr -d ' ')
  if [ -z "$opts_new" ] && [ $opts_ref = 3 ]; then
    pass "emconfig-options-gone      new jar compiles 0 statefulAuthz options, ref jar 3"
  else
    fail "emconfig-options-gone" "new [$opts_new] ref count $opts_ref"
  fi

  for flag in statefulAuthzTransition statefulAuthzResetEndpoint statefulAuthzTwoCredentialJudgment; do
    for tag in new ref; do
      j=$JAR
      [ $tag = ref ] && j=$REFJAR
      java -jar $j --$flag x --blackBox true --maxTime 1s > $OUT/flag-$flag-$tag.out 2>&1
    done
    if grep -q "$flag is not a recognized option" $OUT/flag-$flag-new.out \
      && ! grep -q "$flag is not a recognized option" $OUT/flag-$flag-ref.out; then
      pass "flag-rejected-$flag   new jar: not a recognized option; ref jar accepts it"
    else
      fail "flag-rejected-$flag" "see $OUT/flag-$flag-new.out"
    fi
  done

  refs=$(grep -rnE "$REMOVED" $SRC | wc -l | tr -d ' ')
  refs_head=$(git -C $EM grep -nE "$REMOVED" HEAD -- core/src/main/kotlin | wc -l | tr -d ' ')
  if [ $refs = 0 ] && [ $refs_head -gt 0 ]; then
    pass "no-removed-symbols         0 references in the working tree, $refs_head at HEAD f73010103b"
  else
    fail "no-removed-symbols" "$refs references left: $(grep -rnoE "$REMOVED" $SRC | head -3 | tr '\n' ' ')"
  fi

  added_comments=$(git -C $EM diff HEAD -- core/src/main | grep -E '^\+' | grep -vE '^\+\+\+' | grep -cE '^\+[[:space:]]*(//|/\*|\*|#)')
  removed_comments=$(git -C $EM diff HEAD -- core/src/main | grep -E '^-' | grep -vE '^---' | grep -cE '^-[[:space:]]*(//|/\*|\*)')
  if [ $added_comments = 0 ]; then
    pass "no-new-comments            0 added comment lines; $removed_comments comment lines removed (upstream comments kept)"
  else
    fail "no-new-comments" "$added_comments added comment lines"
  fi

  prints=$(git -C $EM diff HEAD -- core/src/main | grep -E '^\+' | grep -cE 'println|printStackTrace|System\.out')
  if [ $prints = 0 ]; then
    pass "no-debug-prints            0 added println/printStackTrace"
  else
    fail "no-debug-prints" "$prints added"
  fi
fi

auth_yaml() {
  local f=$1
  shift
  echo "auth:" > $f
  for u in $@; do
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

stub_start() {
  local fam=$1 mode=$2 dir=$3 tag=$4
  case $fam in
    p2) python3 $SELF/p2_stub.py $mode $PORT > $dir/$mode-$tag-stub.err 2>&1 & ;;
    cand) python3 $SELF/candidate_stub.py $mode $PORT > $dir/$mode-$tag-stub.err 2>&1 & ;;
    setfield) python3 $SELF/setfield_stub.py $PORT $dir/$tag-stub.jsonl > $dir/$mode-$tag-stub.err 2>&1 & ;;
    paths) python3 $SELF/refactor_paths_stub.py $mode $PORT > $dir/$mode-$tag-stub.err 2>&1 & ;;
    gaps) python3 $SELF/gaps_stub.py $mode $PORT > $dir/$mode-$tag-stub.err 2>&1 & ;;
  esac
  STUB_PID=$!
}

run() {
  local fam=$1 mode=$2 tag=$3 jar=$4
  local dir=$OUT/$fam
  local name=$mode-$tag
  local stop=($STOP)
  if [ $fam = setfield ]; then
    name=$tag
    stop=($SETSTOP)
  fi
  stub_start $fam $mode $dir $tag
  if ! stub_up; then
    kill $STUB_PID 2>/dev/null
    echo "stub-down" > $dir/$name.exit
    return
  fi
  local cmd=(java $DEBUG -jar $jar --blackBox true
    --bbSwaggerUrl http://localhost:$PORT/openapi.json --bbTargetUrl http://localhost:$PORT
    --configPath $dir/auth-$mode.yaml
    --useExperimentalOracles true --extraPhaseBudgetPercentage 1.0
    --outputFormat PYTHON_UNITTEST $stop --seed 1
    --outputFolder $dir/$name)
  echo "${cmd[*]}" > $dir/$name.cmd
  "${cmd[@]}" > $dir/$name.log 2>&1
  echo $? > $dir/$name.exit
  kill $STUB_PID 2>/dev/null
  wait $STUB_PID 2>/dev/null
}

fixture_scores() {
  local fam=$1 mode=$2 dir=$OUT/$1
  stub_start $fam $mode $dir scores
  if stub_up; then
    case $fam in
      p2) python3 $SELF/p2_scores.py http://localhost:$PORT/openapi.json $mode > $dir/$mode-scores.txt 2>$dir/$mode-scores.err ;;
      cand) python3 $SELF/candidate_scores.py $dir/lexicon.csv http://localhost:$PORT/openapi.json $mode > $dir/$mode-scores.txt 2>$dir/$mode-scores.err ;;
    esac
  fi
  kill $STUB_PID 2>/dev/null
  wait $STUB_PID 2>/dev/null
}

unzip -p $LEXJAR stateful-authz-lexicon.csv > $OUT/cand/lexicon.csv

for mode in $P2MODES; do
  auth_yaml $OUT/p2/auth-$mode.yaml alice:alicepass boss:bosspass bob:bobpass
  fixture_scores p2 $mode
  run p2 $mode new $JAR
  run p2 $mode refA $REFJAR
  run p2 $mode refB $REFJAR
  [ $mode = enum-role ] && run p2 $mode old $P2OLD
  echo "ran p2 $mode new=$(cat $OUT/p2/$mode-new.exit) refA=$(cat $OUT/p2/$mode-refA.exit) refB=$(cat $OUT/p2/$mode-refB.exit)"
done

for mode in $CANDMODES; do
  users=(alice:alicepass boss:bosspass bob:bobpass)
  [ $mode = proven-404 ] && users+=(carol:carolpass)
  auth_yaml $OUT/cand/auth-$mode.yaml $users
  fixture_scores cand $mode
  run cand $mode new $JAR
  run cand $mode refA $REFJAR
  run cand $mode refB $REFJAR
  run cand $mode old $CANDOLD
  echo "ran cand $mode new=$(cat $OUT/cand/$mode-new.exit) refA=$(cat $OUT/cand/$mode-refA.exit) refB=$(cat $OUT/cand/$mode-refB.exit) old=$(cat $OUT/cand/$mode-old.exit)"
done

for mode in $SETMODES; do
  auth_yaml $OUT/setfield/auth-$mode.yaml alice:alicepass boss:bosspass bob:bobpass
  run setfield $mode new $JAR
  run setfield $mode refA $REFJAR
  run setfield $mode refB $REFJAR
  run setfield $mode old $SETOLD
  echo "ran setfield new=$(cat $OUT/setfield/new.exit) refA=$(cat $OUT/setfield/refA.exit) refB=$(cat $OUT/setfield/refB.exit) old=$(cat $OUT/setfield/old.exit)"
done

for mode in $PATHMODES; do
  users=(alice:alicepass boss:bosspass bob:bobpass eve:evepass)
  [ $mode = unavailable ] || [ $mode = budget ] && users=(alice:alicepass boss:bosspass bob:bobpass)
  if [ $mode = cap20 ]; then
    users=(eve:evepass)
    for i in {1..22}; do users+=(u$(printf %02d $i):u$(printf %02d $i)pass); done
  fi
  auth_yaml $OUT/paths/auth-$mode.yaml $users
  run paths $mode new $JAR
  run paths $mode refA $REFJAR
  run paths $mode refB $REFJAR
  echo "ran paths $mode new=$(cat $OUT/paths/$mode-new.exit) refA=$(cat $OUT/paths/$mode-refA.exit) refB=$(cat $OUT/paths/$mode-refB.exit)"
done

for mode in $GAPMODES; do
  auth_yaml $OUT/gaps/auth-$mode.yaml alice:alicepass boss:bosspass bob:bobpass eve:evepass
  run gaps $mode new $JAR
  run gaps $mode refA $REFJAR
  run gaps $mode refB $REFJAR
  echo "ran gaps $mode new=$(cat $OUT/gaps/$mode-new.exit) refA=$(cat $OUT/gaps/$mode-refA.exit) refB=$(cat $OUT/gaps/$mode-refB.exit)"
done

python3 $SELF/refactor_compare.py $OUT "$P2MODES" "$CANDMODES" "$SETMODES" "$PATHMODES" "$GAPMODES" || FAILED=1

echo "--- legacy p2_checks.py on the new jar"
python3 $SELF/p2_checks.py $OUT/p2 $P2MODES > $OUT/p2-checks.txt
cat $OUT/p2-checks.txt
echo "--- legacy candidate_checks.py on the new jar"
python3 $SELF/candidate_checks.py $OUT/cand $CANDMODES > $OUT/cand-checks.txt
cat $OUT/cand-checks.txt
echo "--- legacy setfield_checks.py on the new jar"
python3 $SELF/setfield_checks.py $OUT/setfield > $OUT/setfield-checks.txt
cat $OUT/setfield-checks.txt

echo "output $OUT"
exit $FAILED
