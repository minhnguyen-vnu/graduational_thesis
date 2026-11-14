#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:?JAR must name the jar under test}
REFJAR=${REFJAR:-$EM/evomaster-SLM2-b8b5cf1a.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
SELF=$THESIS/infra/evomaster-ext/selftest
LR=$THESIS/infra/analysis/lexicon-rules
PRE=$THESIS/infra/evomaster-ext/wip/thesis-comments-pre-nodup-20261113.patch
OUT=${1:-$THESIS/infra/em-results/nodup-tokens-selftest-$(date +%Y%m%d-%H%M%S)}
PORT=${PORT:-18190}
STOP=(${=STOP:---stoppingCriterion ACTION_EVALUATIONS --maxEvaluations 300})
P2MODES=(${=P2MODES-enum-role bool-restricted num-two path-id-username access-level anon-deny gate-low put-id-source})
CANDMODES=(${=CANDMODES-noop-decoy reject-decoy restore-budget protected-victim revoke proven-404 alpha cap20 bool-flag})
B=core/src/main/kotlin/org/evomaster/core/problem/rest/service/RestSecurityBuilder.kt
MODEL=core/src/main/resources/stateful-authz-model.csv
NODUP_SHA=dcc77b59ed0f
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
JAVA=$JAVA_HOME/bin/java
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
START=$(date '+%Y-%m-%d %H:%M:%S')

mkdir -p $OUT/runs $OUT/tokens
cd $OUT
FAILED=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1  --  $2"; FAILED=1; }

lines() { grep -nF -- "$2" $EM/$1 | cut -d: -f1 | tr '\n' ',' | sed 's/,$//'; }
op_start=$(lines $B 'fun opFeatures(a: RestCallAction)')
te_start=$(lines $B 'private fun tokenEnd(text: String, start: Int): Int {')
te_end=$(awk -v s=$te_start 'NR > s && /^        }$/ {print NR; exit}' $EM/$B)
op_skip=$(awk -v s=$op_start 'NR > s && /if \(f.loc == "path"\) \{/ {print NR; exit}' $EM/$B)
echo "exercises RestSecurityBuilder.kt tokens :$(lines $B 'while (start < text.length) {')-$(lines $B 'start = end')" \
  "tokenEnd :$te_start-$te_end" \
  "opFeatures path skip :$op_skip (opFeatures starts :$op_start)"
echo "jar-new $(shasum -a 256 $JAR | cut -c1-16)  jar-ref $(shasum -a 256 $REFJAR | cut -c1-16)  HEAD $(git -C $EM rev-parse --short=10 HEAD)"

head_count() { git -C $EM show HEAD:$1 | grep -cF -- "$2"; }
tree_count() { grep -cF -- "$2" $EM/$1; }

for pat in 'Regex(' 'TOKEN_PART' '.findAll('; do
  before=$(head_count $B "$pat")
  after=$(tree_count $B "$pat")
  if [ $before -gt 0 ] && [ $after = 0 ]; then
    pass "gone           [$pat]  HEAD $before, tree 0"
  else
    fail "gone           [$pat]" "HEAD $before, tree $after"
  fi
done

for spec in \
  "1|private fun tokenEnd(text: String, start: Int): Int {" \
  "1|val end = tokenEnd(text, start)" \
  "1|val nextIsLower = end < text.length && text[end] in 'a'..'z'"; do
  n=${spec%%|*}
  pat=${spec#*|}
  before=$(head_count $B "$pat")
  after=$(tree_count $B "$pat")
  if [ $before = 0 ] && [ $after = $n ]; then
    pass "new            [$pat]  HEAD 0, tree $after"
  else
    fail "new            [$pat]" "HEAD $before, tree $after, want $n"
  fi
done

path_head=$(head_count $B 'if (f.loc == "path") {')
path_tree=$(tree_count $B 'if (f.loc == "path") {')
if [ -n "$op_skip" ] && [ $path_tree = $((path_head + 1)) ]; then
  next=$(sed -n "$((op_skip + 1))p" $EM/$B | tr -d ' ')
  prev=$(sed -n "$((op_skip - 1))p" $EM/$B | tr -d ' ')
  if [ "$next" = "continue" ] && [ "$prev" = "for(finschemaFields(a)){" ]; then
    pass "opfeatures-skip  line $op_skip: first statement of the field loop in opFeatures skips path fields; [if (f.loc == \"path\")] HEAD $path_head, tree $path_tree"
  else
    fail "opfeatures-skip" "line $op_skip prev [$prev] next [$next]"
  fi
else
  fail "opfeatures-skip" "skip line [$op_skip], HEAD $path_head, tree $path_tree"
fi

added() { git -C $EM diff HEAD -- core/src/main/kotlin | grep -E '^\+' | grep -vE '^\+\+\+' | grep -vF 'THESIS'; }
removed() { git -C $EM diff HEAD -- core/src/main/kotlin | grep -E '^-' | grep -vE '^---' | grep -vF 'THESIS'; }

added_comments=$(added | grep -cE '^\+[[:space:]]*(//|/\*|\*|#)')
if [ $added_comments = 0 ]; then
  pass "no-comments    0 non-THESIS comment lines added"
else
  fail "no-comments" "$added_comments added"
fi

prints=$(added | grep -cE 'println|printStackTrace|System\.out')
if [ $prints = 0 ]; then
  pass "no-prints      0 added"
else
  fail "no-prints" "$prints added"
fi

lam='\.(map|mapNotNull|flatMap|filter|filterNot|forEach|forEachIndexed|any|all|none|associate|fold|reduce|sumOf|maxBy|minBy|maxByOrNull|minByOrNull|firstOrNull|first|find|count|joinToString)[[:space:]]*[\{\(]'
lam_new=$(added | grep -cE "$lam")
if [ $lam_new = 0 ]; then
  pass "no-new-stream  0 stream calls added"
else
  fail "no-new-stream" "$lam_new added: $(added | grep -E "$lam" | head -2 | tr '\n' ' ')"
fi

unicode_checks=$(added | grep -cE '(\.|Character\.)(isUpperCase|isLowerCase|isLetter|isLetterOrDigit|isDigit)\(')
if [ $unicode_checks = 0 ]; then
  pass "ascii-only     0 Char.isUpperCase/isLowerCase/isLetter/isDigit added; ranges 'A'..'Z', 'a'..'z', '0'..'9' only"
else
  fail "ascii-only" "$unicode_checks Unicode-aware char checks added"
fi

log_changed=$( { added; removed; } | grep -cE 'log\.(debug|warn|info)|getInfoLogger')
if [ $log_changed = 0 ]; then
  pass "logs-untouched 0 log statements added or removed"
else
  fail "logs-untouched" "$log_changed log lines in the diff"
fi

intended_gone=("// THESIS: Tách camelCase, snake_case, path thành từ." \
  "// THESIS: Đặc trưng của op cho bảng op: v:verb, p:từ của path, f:từ của tên lá mọi trường." \
  "// THESIS: Vd PUT /users/{username}/role body {role} -> {v:PUT, p:users, p:username, p:role, f:username, f:role}.")
intended_new=("// THESIS: Đặc trưng của op cho bảng op: v:verb, p:từ của path, f:từ của tên lá các trường query và body." \
  "// THESIS: Vd PUT /users/{username}/role body {role} -> {v:PUT, p:users, p:username, p:role, f:role}.")
pre_lines=$(grep -E '^\+' $PRE | grep -vE '^\+\+\+' | grep -F 'THESIS' | sed -E 's/^\+[[:space:]]*//')
pre_n=$(echo "$pre_lines" | grep -c .)
missing=()
while IFS= read -r l; do
  [ -z "$l" ] && continue
  if ! grep -rqF -- "$l" $EM/core/src/main/kotlin; then
    missing+=("$l")
  fi
done <<< "$pre_lines"
gone_ok=1
for l in $intended_gone; do
  found=0
  for m in $missing; do
    [[ "$m" == "$l"* ]] && found=1
  done
  [ $found = 0 ] && gone_ok=0
done
new_ok=1
for l in $intended_new; do
  grep -qF -- "$l" $EM/$B || new_ok=0
done
if [ $pre_n -gt 0 ] && [ ${#missing} = 3 ] && [ $gone_ok = 1 ] && [ $new_ok = 1 ]; then
  pass "thesis-comments  $pre_n THESIS lines before the change; exactly the 3 approved lines are gone and the 2 approved replacements are present"
else
  fail "thesis-comments" "missing ${#missing} (want 3), approved gone $gone_ok, approved new $new_ok; first missing [${missing[1]:-}]"
fi

model_tree=$(shasum -a 256 $EM/$MODEL | cut -c1-12)
model_jar=$(unzip -p $JAR stateful-authz-model.csv | shasum -a 256 | cut -c1-12)
model_lr=$(shasum -a 256 $LR/m2-nodup-20261112/stateful-authz-model.csv | cut -c1-12)
model_ref=$(unzip -p $REFJAR stateful-authz-model.csv | shasum -a 256 | cut -c1-12)
if [ $model_jar = $NODUP_SHA ] && [ $model_tree = $NODUP_SHA ] && [ $model_lr = $NODUP_SHA ] && [ $model_ref != $NODUP_SHA ]; then
  pass "model          jar, tree and m2-nodup-20261112 all $NODUP_SHA; ref jar $model_ref"
else
  fail "model" "jar $model_jar tree $model_tree analysis $model_lr ref $model_ref, want $NODUP_SHA"
fi

opts=$(unzip -p $JAR 'org/evomaster/core/EMConfig*.class' | strings | grep -o "statefulAuthz[A-Za-z]*" | sort -u | tr '\n' ' ')
if [ -z "$opts" ]; then
  pass "emconfig       0 statefulAuthz options compiled in"
else
  fail "emconfig" "[$opts]"
fi

cls() { unzip -p $1 'org/evomaster/core/problem/rest/service/RestSecurityBuilder*.class' | strings | grep -c "$2"; }
n_end=$(cls $JAR tokenEnd); n_part=$(cls $JAR TOKEN_PART); r_end=$(cls $REFJAR tokenEnd); r_part=$(cls $REFJAR TOKEN_PART)
if [ $n_end -gt 0 ] && [ $n_part = 0 ] && [ $r_end = 0 ] && [ $r_part -gt 0 ]; then
  pass "jar-has-change new jar: tokenEnd $n_end, TOKEN_PART 0; ref jar: tokenEnd 0, TOKEN_PART $r_part"
else
  fail "jar-has-change" "new tokenEnd $n_end TOKEN_PART $n_part; ref tokenEnd $r_end TOKEN_PART $r_part"
fi

python3 $SELF/nodup_corpus.py $OUT/tokens/corpus.txt
cp $SELF/TokensNoRegex.java $OUT/tokens/
$JAVA_HOME/bin/javac -cp $JAR -d $OUT/tokens $OUT/tokens/TokensNoRegex.java 2> $OUT/tokens/javac.err
for ref in regex wrong; do
  $JAVA -cp $JAR:$OUT/tokens TokensNoRegex $OUT/tokens/corpus.txt $ref > $OUT/tokens/$ref.out 2> $OUT/tokens/$ref.err
done
cat $OUT/tokens/regex.out
total=$(grep -E '^TOTAL' $OUT/tokens/regex.out)
groups=$(grep -cE '^GROUP .* mismatches=0$' $OUT/tokens/regex.out)
if [ $groups = 3 ] && [[ "$total" == *" mismatches=0" ]] && [[ "$total" == "TOTAL compared="* ]]; then
  pass "tokens-equal   jar tokens() equals the old regex on corpus, edge and random strings, minLength 1 and 4: $total"
else
  fail "tokens-equal" "$total; see $OUT/tokens/regex.out $OUT/tokens/regex.err"
fi
wrong=$(grep -E '^TOTAL' $OUT/tokens/wrong.out | sed -E 's/.*mismatches=//')
if [ -n "$wrong" ] && [ "$wrong" -gt 0 ]; then
  pass "tokens-can-fail  against a wrong reference regex [A-Z]+|[a-z0-9]+ the same harness reports $wrong mismatches"
else
  fail "tokens-can-fail" "wrong-reference mismatches [$wrong]; see $OUT/tokens/wrong.out"
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
  local fam=$1 mode=$2 tag=$3
  case $fam in
    p2) python3 $SELF/p2_stub.py $mode $PORT > $OUT/runs/$mode-$tag-stub.err 2>&1 & ;;
    cand) python3 $SELF/candidate_stub.py $mode $PORT > $OUT/runs/$mode-$tag-stub.err 2>&1 & ;;
  esac
  STUB_PID=$!
}

stub_stop() {
  kill $STUB_PID 2>/dev/null
  wait $STUB_PID 2>/dev/null
}

scores() {
  local fam=$1 mode=$2
  stub_start $fam $mode scores
  if stub_up; then
    for which in nodup m2 nodup-pathf; do
      python3 $SELF/nodup_scores.py http://localhost:$PORT/openapi.json $which > $OUT/runs/$mode-scores-$which.txt 2> $OUT/runs/$mode-scores-$which.err
    done
  fi
  stub_stop
}

run() {
  local fam=$1 mode=$2 tag=$3 jar=$4
  local name=$mode-$tag
  stub_start $fam $mode $tag
  if ! stub_up; then
    stub_stop
    echo "stub-down" > $OUT/runs/$name.exit
    return
  fi
  local cmd=($JAVA $DEBUG -jar $jar --blackBox true
    --bbSwaggerUrl http://localhost:$PORT/openapi.json --bbTargetUrl http://localhost:$PORT
    --configPath $OUT/runs/auth-$mode.yaml
    --useExperimentalOracles true --extraPhaseBudgetPercentage 1.0
    --outputFormat PYTHON_UNITTEST $STOP --seed 1
    --outputFolder $OUT/runs/$name)
  echo "${cmd[*]}" > $OUT/runs/$name.cmd
  "${cmd[@]}" > $OUT/runs/$name.log 2>&1
  echo $? > $OUT/runs/$name.exit
  stub_stop
}

MODES=()
for fam in p2 cand; do
  if [ $fam = p2 ]; then list=($P2MODES); else list=($CANDMODES); fi
  for mode in $list; do
    users=(alice:alicepass boss:bosspass bob:bobpass)
    [ $mode = proven-404 ] && users+=(carol:carolpass)
    auth_yaml $OUT/runs/auth-$mode.yaml $users
    scores $fam $mode
    run $fam $mode nd $JAR
    run $fam $mode ref $REFJAR
    echo "ran $fam $mode nd=$(cat $OUT/runs/$mode-nd.exit) ref=$(cat $OUT/runs/$mode-ref.exit)"
    MODES+=($mode)
  done
done

exits_bad=0
for mode in $MODES; do
  for tag in nd ref; do
    [ "$(cat $OUT/runs/$mode-$tag.exit)" = 0 ] || exits_bad=$((exits_bad + 1))
  done
done
if [ $exits_bad = 0 ]; then
  pass "runs-exit-0    ${#MODES} modes x 2 jars exited 0"
else
  fail "runs-exit-0" "$exits_bad runs exited non-zero"
fi

python3 $SELF/nodup_compare.py $OUT/runs "$MODES" > $OUT/compare.txt 2>&1 || FAILED=1
cat $OUT/compare.txt

sleeps=$(pmset -g log | awk -v s="$START" 'substr($0, 1, 19) >= s && /Entering Sleep/' | wc -l | tr -d ' ')
if [ $sleeps = 0 ]; then
  pass "no-sleep       0 'Entering Sleep' in pmset log since $START"
else
  fail "no-sleep" "$sleeps sleep entries since $START"
fi

echo "output $OUT"
exit $FAILED
