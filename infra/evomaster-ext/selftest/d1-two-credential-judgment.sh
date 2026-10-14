#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=$EM/core/target/evomaster.jar
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
OUT=${1:-$THESIS/infra/em-results/d1-selftest-$(date +%Y%m%d-%H%M%S)}
export JAVA_HOME=$(/usr/libexec/java_home -v 17)

NEW="freshly issued victim credential"
OLD="re-logging the victim in did not show the privilege removed"

mkdir -p $OUT
FAILED=0

pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1  --  $2"; FAILED=1; }

HELP=$OUT/help.txt
java -jar $JAR --help > $HELP 2>&1

if grep -q -- "--statefulAuthzTwoCredentialJudgment" $HELP; then
  pass "option-present        EMConfig.kt statefulAuthzTwoCredentialJudgment"
else
  fail "option-present" "not in --help; the jar does not carry the patch"
fi

optblock() {
  awk '/^--statefulAuthzTwoCredentialJudgment/{f=1} f&&/^--/&&!/^--statefulAuthzTwoCredentialJudgment/{exit} f' $HELP \
    | tr -s ' \n' ' '
}

if optblock | grep -q "(default: false)"; then
  pass "option-default-false  old behaviour is what an unflagged run gets"
else
  fail "option-default-false" "the option does not default to false"
fi

count970() {
  python3 -c "
import json,sys
try:
    n=0
    for f in json.load(open('$1/report.json'))['faults']['foundFaults']:
        if 970 in [x['code'] for x in f['faultCategories']]: n+=1
    print(n)
except Exception: print('ERR')"
}

probe_rule() {
  python3 - "$1" "$2" <<'PYEOF'
import re, sys
log, n970 = sys.argv[1], sys.argv[2]
text = open(log, errors="replace").read()
codes = re.findall(r"fresh-credential probe: .*=(\S+)\s*$", text, re.M)
if n970 == "ERR":
    print("report.json unreadable, cannot pair findings with probe lines"); sys.exit(1)
n = int(n970)
denials = [c for c in codes if c == "403"]
if n > 0 and not codes:
    print("%d finding(s) of 970 but no probe line at all" % n); sys.exit(1)
if len(denials) < n:
    print("%d finding(s) of 970 but only %d probe line(s) ending =403, codes seen %s"
          % (n, len(denials), sorted(set(codes)))); sys.exit(1)
if n == 0 and denials:
    print("no 970 although %d probe line(s) ended =403" % len(denials)); sys.exit(1)
print("%d finding(s) of 970, %d probe line(s) =403, codes seen %s" % (n, len(denials), sorted(set(codes))))
PYEOF
}

det970() {
  python3 -c "
import json,sys
try:
    c=[x['code'] for f in json.load(open('$1/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')"
}

run() {
  curl -s -X POST http://localhost:8080/reset > /dev/null
  java -jar $JAR \
    --blackBox true --bbSwaggerUrl http://localhost:8080/v3/api-docs --bbTargetUrl http://localhost:8080 \
    --configPath $THESIS/infra/em-config/reports-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment $2 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 1 \
    --outputFolder $OUT/$1 > $OUT/$1.log 2>&1
  echo $?
}

OFFEXIT=$(run flagoff false)
OFF970=$(det970 $OUT/flagoff)

if [ "$OFFEXIT" = 0 ] && [ "$OFF970" = 1 ]; then
  pass "flagoff-970           tier1 vuln seed 1 still raises 970, as tier1-clean-remeasure records"
else
  fail "flagoff-970" "exit=$OFFEXIT det970=$OFF970; expected exit 0 and 970 raised"
fi

if grep -q "$NEW" $OUT/flagoff.log; then
  fail "flagoff-branch" "the two-credential message appeared with the flag off"
else
  pass "flagoff-branch        no two-credential message with the flag off"
fi

ONEXIT=$(run flagon true)
ON970=$(det970 $OUT/flagon)

if [ "$ONEXIT" = 0 ] && ! grep -q "at org.evomaster" $OUT/flagon.log; then
  pass "flagon-survives       run exits 0 with no stack trace from org.evomaster"
else
  fail "flagon-survives" "exit=$ONEXIT or a stack trace is in $OUT/flagon.log"
fi

if grep -q "$OLD" $OUT/flagon.log; then
  fail "flagon-no-c4" "the re-login probe message appeared although the flag is on"
else
  pass "flagon-no-c4         the C4 re-login probe took no part in the judgment"
fi

if grep -q "fresh-credential probe:" $OUT/flagon.log; then
  pass "flagon-probe-ran      freshCredentialDeniesFollowUp sent the follow-up and printed its code"
else
  fail "flagon-probe-ran" "no probe line in the log: the new branch left no trace, so nothing below is evidence"
fi

if [ "$ON970" = 1 ]; then
  pass "flagon-970            tier1 vuln seed 1 raises 970 under two-credential judgment"
else
  fail "flagon-970" "det970=$ON970; a fresh alice token is denied by the app (403, checked by hand), so D1 must confirm"
fi

ONCOUNT=$(count970 $OUT/flagon)

if RULE=$(probe_rule $OUT/flagon.log $ONCOUNT); then
  pass "flagon-probe-403      every 970 pairs with a probe line ending =403: $RULE"
else
  fail "flagon-probe-403" "$RULE"
fi

FIX=$OUT/fixtures
mkdir -p $FIX
cat > $FIX/good.log <<'EOF'
Stateful-authorization fresh-credential probe: PUT:/reports/{id}[alice]=403
EOF
cat > $FIX/bad401.log <<'EOF'
Stateful-authorization fresh-credential probe: PUT:/reports/{id}[alice]=401
EOF
cat > $FIX/bad404.log <<'EOF'
Stateful-authorization fresh-credential probe: DELETE:/reports/{id}[alice]=404
EOF
cat > $FIX/bad200.log <<'EOF'
Stateful-authorization fresh-credential probe: PUT:/reports/{id}[alice]=200
EOF

if probe_rule $FIX/good.log 1 > /dev/null; then
  pass "rule-accepts-403      the check passes a log whose only probe line is =403"
else
  fail "rule-accepts-403" "the check rejected a log it must accept, so its verdicts mean nothing"
fi

RULEFAILS=1
for f in bad401 bad404 bad200; do
  if probe_rule $FIX/$f.log 1 > /dev/null; then
    fail "rule-rejects-$f" "a 970 paired with a non-403 probe line was accepted; the check cannot fail"
    RULEFAILS=0
  fi
done
[ $RULEFAILS = 1 ] && pass "rule-rejects-non-403  401, 404 and 200 each make the check print FAIL"

if unzip -p $JAR 'org/evomaster/core/problem/rest/service/RestSecurityBuilder*.class' | strings | grep -q "neither 403 nor 2xx"; then
  pass "jar-has-inconclusive  the built jar carries the branch that logs a non-403 non-2xx code as inconclusive"
else
  fail "jar-has-inconclusive" "the string is absent: the jar predates the denial-code fix"
fi

if optblock | grep -q "non-2xx for PUT"; then
  fail "help-denial-wording" "the option text still promises any non-2xx for PUT"
else
  pass "help-denial-wording   the option text no longer promises any non-2xx for PUT"
fi

if optblock | grep -q "inconclusive and reports nothing"; then
  pass "help-inconclusive     the option text names the inconclusive outcome"
else
  fail "help-inconclusive" "the option text does not mention the inconclusive outcome"
fi

echo "det970 flagoff=$OFF970 flagon=$ON970 count970=$ONCOUNT   output $OUT"
exit $FAILED
