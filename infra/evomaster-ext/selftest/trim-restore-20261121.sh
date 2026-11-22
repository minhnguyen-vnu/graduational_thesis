#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:?JAR must name the jar under test}
REFJAR=${REFJAR:-$EM/evomaster-CS2-f3412dc8.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
SELF=$THESIS/infra/evomaster-ext/selftest
OUT=${1:-$THESIS/infra/em-results/trim-restore-selftest-$(date +%Y%m%d-%H%M%S)}
CS2RUN=${CS2RUN:-$THESIS/infra/em-results/c4-source-status-selftest-20261121-170956}
NEWMODES=(enum num bool novictim noplan num1)
NEWSEED=${NEWSEED:-2}
C4MODES=(${=C4MODES:-len1 chain prior-noncreate anon-prefix source-200 op-refused value-reject prior-harmless})
LFMODES=(post-source login-name enum-lower two-role-fields bool-victim first-404 query-username nested-role num-enum c4-intact no-path-id source-401)
PORT=${PORT:-18291}
STOP=(--stoppingCriterion ACTION_EVALUATIONS --maxEvaluations ${EVALS:-300})
DEBUG=-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml
B=core/src/main/kotlin/org/evomaster/core/problem/rest/service/RestSecurityBuilder.kt
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
START=$(date '+%Y-%m-%d %H:%M:%S')

mkdir -p $OUT
cd $OUT
FAILED=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1  --  $2"; FAILED=1; }

lines() { grep -nF -- "$1" $EM/$B | cut -d: -f1 | tr '\n' ',' | sed 's/,$//'; }
echo "exercises RestSecurityBuilder.kt" \
  "S2 :$(lines 'if (values.isNotEmpty() && victimField(candidate) != null) {')" \
  "R6 :$(lines 'private fun guardedSources(verbs: List<HttpVerb>): List<RestCallAction> {')" \
  "R11 :$(lines 'val plan = restorePlan(transitionDef)')" \
  "R1-R4,R12 :$(lines 'private fun restoreValue(field: SchemaField): String? {')" \
  "R2,R12 :$(lines 'private fun restorePlan(transition: RestCallAction): List<Pair<String, String>> {')"
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

for spec in "op.path == transitionOp.path|0" "val exclude = roleValues.firstOrNull()|0" \
  "privilegeReducedByProof.remove(|0" "lastSourceCode = null|0" "victimSnapshot|0" "anyPlan|0" \
  "\"str\" -> tableValues(\"highstr\")|0" "if (high.isNotEmpty()) high else ranked|0" \
  "elevatedNumericRoleCandidates|0" "minOf(j, values.size - 1)|0" "for (plan in plans)|0" \
  "victimField(candidate) != null|1" "privilegeReducedByProof.add(|1" "privilegeReducedInPhase.retainAll(|1"; do
  text=${spec%|*}
  want=${spec##*|}
  n=$(grep -cF -- "$text" $EM/$B)
  if [ $n = $want ]; then
    pass "source         [$text] $n in tree"
  else
    fail "source [$text]" "$n in tree, want $want"
  fi
done

cls() { unzip -p $1 'org/evomaster/core/problem/rest/service/RestSecurityBuilder.class' | strings | grep -c "$2"; }
n=$(cls $JAR victimSnapshot); r=$(cls $REFJAR victimSnapshot)
if [ $n = 0 ] && [ $r -gt 0 ]; then
  pass "jar-has-change victimSnapshot: new jar $n, ref jar $r"
else
  fail "jar-has-change victimSnapshot" "new jar $n, ref jar $r"
fi
n=$(cls $JAR 'restore unavailable'); r=$(cls $REFJAR 'restore unavailable')
if [ $n -gt 0 ] && [ $r -gt 0 ]; then
  pass "jar-keeps-log  'restore unavailable': new jar $n, ref jar $r"
else
  fail "jar-keeps-log 'restore unavailable'" "new jar $n, ref jar $r"
fi

if [ "${STATICONLY:-0}" = 1 ]; then
  echo "static checks only"
  exit $FAILED
fi

auth_yaml() {
  local f=$1
  shift
  echo "auth:" > $f
  for u in "$@"; do
    cat >> $f <<EOF
  - name: $u
    loginEndpointAuth:
      payloadUserPwd:
        username: $u
        password: "${u}pass"
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

run_em() {
  local stub=$1 mode=$2 tag=$3 jar=$4 auth=$5 port=$6 seed=${7:-1}
  rm -f $OUT/$mode-$tag-req.jsonl
  python3 -I $SELF/$stub $mode $port $OUT/$mode-$tag-req.jsonl > $OUT/$mode-$tag-stub.err 2>&1 &
  local sp=$!
  local up=0
  for i in {1..50}; do
    [ "$(curl -s -o /dev/null --max-time 1 -w '%{http_code}' http://localhost:$port/openapi.json)" = 200 ] && up=1 && break
    sleep 0.2
  done
  if [ $up = 0 ]; then
    echo "stub-down" > $OUT/$mode-$tag.exit
    kill $sp 2>/dev/null
    return
  fi
  local cmd=(java $DEBUG -jar $jar --blackBox true
    --bbSwaggerUrl http://localhost:$port/openapi.json --bbTargetUrl http://localhost:$port
    --configPath $auth
    --useExperimentalOracles true --extraPhaseBudgetPercentage 1.0
    --outputFormat PYTHON_UNITTEST $STOP --seed $seed
    --outputFolder $OUT/$mode-$tag)
  echo "${cmd[*]}" > $OUT/$mode-$tag.cmd
  "${cmd[@]}" > $OUT/$mode-$tag.log 2>&1
  echo $? > $OUT/$mode-$tag.exit
  kill $sp 2>/dev/null
  wait $sp 2>/dev/null
}

auth_yaml $OUT/auth-trim.yaml alice bob carol
for mode in $NEWMODES; do
  run_em trim_stub.py $mode ref $REFJAR $OUT/auth-trim.yaml $PORT $NEWSEED
  run_em trim_stub.py $mode new $JAR $OUT/auth-trim.yaml $PORT $NEWSEED
  e1=$(cat $OUT/$mode-ref.exit); e2=$(cat $OUT/$mode-new.exit)
  if [ $e1 = 0 ] && [ $e2 = 0 ]; then
    pass "$mode-ran        both jars exit 0"
  else
    fail "$mode-ran" "ref exit $e1, new exit $e2"
  fi
done

for mode in enum num bool novictim; do
  found=$(grep -c "Constructed a stateful-authorization (MR-A1) test" $OUT/$mode-new.log)
  if [ $found -gt 0 ]; then
    pass "$mode-970        new jar constructed $found MR-A1 test(s)"
  else
    fail "$mode-970" "new jar constructed none"
  fi
done

for mode in enum num bool; do
  case $mode in
    enum) want="'ADMIN'" ;;
    num) want="'0,0'" ;;
    bool) want="'true'" ;;
  esac
  acc=$(grep -c "Privilege-restore accepted for '[a-z]*' by '[a-z]*' with role $want" $OUT/$mode-new.log)
  other=$(grep "Privilege-restore" $OUT/$mode-new.log | grep -vc "with role $want")
  if [ $acc -gt 0 ] && [ $other = 0 ]; then
    pass "$mode-restore    new jar: $acc accepted restore(s) with $want, $other restore line(s) with another value"
  else
    fail "$mode-restore" "accepted with $want: $acc, restore lines with another value: $other"
  fi
  raised=$(python3 -I -c "
import json, re, sys
mode = sys.argv[3]
high = {'enum': 'ADMIN', 'num': 0, 'bool': True}[mode]
key = {'enum': 'role', 'num': 'role', 'bool': 'is_admin'}[mode]
pairs = re.findall(r\"Privilege-restore accepted for '(\\w+)' by '(\\w+)'\", open(sys.argv[1]).read())
reqs = [json.loads(line) for line in open(sys.argv[2])]
n = 0
for target, restorer in pairs:
    for r in reqs:
        b = r.get('body')
        if (r.get('applied') and r['caller'] == restorer and r['path'].startswith('/users/' + target)
                and isinstance(b, dict) and b.get(key) == high and type(b.get(key)) is type(high)):
            n += 1
            break
print('%d/%d' % (n, len(pairs)))" $OUT/$mode-new.log $OUT/$mode-new-req.jsonl $mode)
  if [ ${raised%/*} -gt 0 ] && [ ${raised%/*} = ${raised#*/} ]; then
    pass "$mode-sut-raise  $raised accepted restore lines match a raise the stub applied (restorer, target, high value)"
  else
    fail "$mode-sut-raise" "$raised accepted restore lines match an applied raise"
  fi
done
python3 -I $SELF/trim_compare.py $OUT -ref.log $OUT -new.log trim enum num bool novictim || FAILED=1

n_new=$(grep -c "restore unavailable on PUT:/users/{username}/role" $OUT/noplan-new.log)
r_new=$(grep -c "Privilege-restore" $OUT/noplan-new.log)
r_ref=$(grep "Privilege-restore" $OUT/noplan-ref.log | head -1 | grep -o "with role '[^']*'")
if [ $n_new -gt 0 ] && [ $r_new = 0 ] && [ -n "$r_ref" ]; then
  pass "noplan-R3       enum without a high value: new jar 'restore unavailable' $n_new, restores 0; ref jar restored $r_ref"
else
  fail "noplan-R3" "new unavailable $n_new, new restores $r_new, ref first restore '$r_ref'"
fi

f_ref=$(grep "Privilege-restore" $OUT/num1-ref.log | head -1 | grep -o "with role '[^']*'")
v_new=$(grep "Privilege-restore" $OUT/num1-new.log | grep -o "with role '[^']*'" | sort -u | tr '\n' ' ')
held=$(grep -o "current roles \\[1\\], reduced role values \\[0, 2\\]" $OUT/num1-new.log | head -1)
if [ -n "$held" ] && [ "$f_ref" = "with role '1,1'" ] && [ "$v_new" = "with role '0,0' " ]; then
  pass "num1-R1-R12     victim holds 1: ref first restore $f_ref (exclude 0); new sends only $v_new(one plan, num 0)"
else
  fail "num1-R1-R12" "held '$held', ref first '$f_ref', new values '$v_new'"
fi

for mode in $C4MODES; do
  run_em c4src_stub.py $mode new $JAR $CS2RUN/auth.yaml 18281
done
python3 -I $SELF/trim_compare.py $CS2RUN -cs.log $OUT -new.log c4src $C4MODES || FAILED=1

JAR=$JAR zsh $SELF/logic-fix-20261118.sh $OUT/logicfix > $OUT/logicfix.out 2>&1
lfexit=$?
grep -E '^(PASS|FAIL)' $OUT/logicfix.out | grep -vE 'no-sleep|no-comments|no-prints|jar-has-change|gone ' > $OUT/logicfix-checks.txt
nfail=$(grep -c '^FAIL' $OUT/logicfix-checks.txt)
npass=$(grep -c '^PASS' $OUT/logicfix-checks.txt)
if [ $nfail = 0 ] && [ $npass -gt 0 ]; then
  pass "logicfix-behaviour  logic-fix-20261118.sh behaviour checks on the new jar: $npass PASS, 0 FAIL (exit $lfexit)"
else
  fail "logicfix-behaviour" "$npass PASS, $nfail FAIL; see $OUT/logicfix-checks.txt"
fi
python3 -I $SELF/trim_compare.py $CS2RUN/logicfix -lf.log $OUT/logicfix -lf.log logicfix $LFMODES || FAILED=1

sleeps=$(pmset -g log | awk -v s="$START" 'substr($0, 1, 19) >= s && /Entering Sleep/' | wc -l | tr -d ' ')
if [ $sleeps = 0 ]; then
  pass "no-sleep       0 'Entering Sleep' in pmset log since $START"
else
  fail "no-sleep" "$sleeps sleep entries since $START"
fi

echo "output $OUT"
exit $FAILED
