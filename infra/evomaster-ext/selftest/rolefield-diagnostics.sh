#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:-$EM/core/target/evomaster.jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
OUT=${1:-$THESIS/infra/em-results/rolefield-selftest-$(date +%Y%m%d-%H%M%S)}
export JAVA_HOME=$(/usr/libexec/java_home -v 17)

RES=stateful-authz-lexicon.csv
CHOSEN="Stateful-authorization transition chosen:"
CANDIDATE="Stateful-authorization transition candidate"
VALUES="Stateful-authorization reduced role values:"
SOURCES="Stateful-authorization guarded source candidates:"
VICTIMS="Stateful-authorization source "
OPERATORS="Stateful-authorization victim '"
EXHAUSTED="Stateful-authorization: sources exhausted after"
WANT_TIER1="PUT:/users/{username}/role"
NOROLE="POST:/auth/login"
VULN=8080
FIXED=8081

mkdir -p $OUT
FAILED=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1  --  $2"; FAILED=1; }

cat > $OUT/logback-debug.xml <<'XML'
<configuration>
    <turboFilter class="org.evomaster.core.logging.UniqueTurboFilter" />
    <appender name="REGULAR_STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder><pattern>%d{HH:mm:ss.SSS} %-5level %logger{36} - %msg%n</pattern></encoder>
    </appender>
    <appender name="INFO_STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder><pattern>* %msg%n</pattern></encoder>
    </appender>
    <logger name="io.swagger" level="OFF" />
    <logger name="org.evomaster.core.problem.rest.service.RestSecurityBuilder" level="DEBUG" />
    <root level="warn"><appender-ref ref="REGULAR_STDOUT" /></root>
    <logger name="info_logger" level="INFO" additivity="false"><appender-ref ref="INFO_STDOUT" /></logger>
</configuration>
XML

det970() {
  python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$1/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')"
}

run() {
  local name=$1 jar=$2 port=$3 logcfg=$4
  shift 4
  curl -s -X POST http://localhost:$port/reset > /dev/null
  java $logcfg -jar $jar \
    --blackBox true --bbSwaggerUrl http://localhost:$port/v3/api-docs --bbTargetUrl http://localhost:$port \
    --configPath $THESIS/infra/em-config/reports-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 1 \
    "$@" \
    --outputFolder $OUT/$name > $OUT/$name.log 2>&1
  echo $?
}

DEBUG="-Dlogback.configurationFile=$OUT/logback-debug.xml"

for p in $VULN $FIXED; do
  if ! curl -s --max-time 5 -o /dev/null http://localhost:$p/v3/api-docs; then
    echo "FAIL  target-up  --  cong $p khong tra loi, khong chay duoc self-test"
    exit 1
  fi
done

echo "jar $(shasum -a 256 $JAR | cut -c1-16)"

printf 'kind,word,score\npath,login,0.9900\npath,role,0.5000\nparam,username,0.5000\n' > $OUT/norole-lexicon.csv
cp $JAR $OUT/norole.jar
cp $OUT/norole-lexicon.csv $OUT/$RES
( cd $OUT && zip -q norole.jar $RES )
rm -f $OUT/$RES

NREXIT=$(run norole $OUT/norole.jar $VULN $DEBUG)
NRFIRST=$(grep "$CANDIDATE" $OUT/norole.log | head -1)
NRTOP=$(echo "$NRFIRST" | sed "s/.*$CANDIDATE *//" | awk '{print $1}')
NRHARVEST=$(echo "$NRFIRST" | sed 's/.*reducedRoleValues //')
NRGOT=$(grep "$CHOSEN" $OUT/norole.log | tail -1 | sed "s/.*$CHOSEN *//")
NR970=$(det970 $OUT/norole)
if [ "$NRTOP" = "$NOROLE" ] && [ "$NRHARVEST" = "0" ]; then
  pass "no-role-field-skipped   harvestReducedRoleCandidates returns [] for $NOROLE, which has a body and no role field"
else
  fail "no-role-field-skipped" "top='$NRTOP' reducedRoleValues='$NRHARVEST'; expected '$NOROLE' and 0"
fi
if [ "$NRGOT" = "$WANT_TIER1" ] && [ "$NR970" = 1 ]; then
  pass "loop-reaches-role       the loop passes $NOROLE, chooses $WANT_TIER1 and raises 970"
else
  fail "loop-reaches-role" "chose '$NRGOT' det970=$NR970 exit=$NREXIT"
fi

BASEEXIT=$(run base $JAR $VULN $DEBUG)
BASE970=$(det970 $OUT/base)
BASEGOT=$(grep "$CHOSEN" $OUT/base.log | tail -1 | sed "s/.*$CHOSEN *//")
BASEVALS=$(grep "$VALUES" $OUT/base.log | tail -1 | sed "s/.*$VALUES *//")
BASEN=$(grep "$CANDIDATE $WANT_TIER1" $OUT/base.log | tail -1 | sed 's/.*reducedRoleValues //')

if [ -n "$BASEVALS" ] && ! echo "$BASEVALS" | grep -qi "application/"; then
  pass "no-content-type-value   values for $WANT_TIER1 are $BASEVALS, no content type among them"
else
  fail "no-content-type-value" "values line '$BASEVALS'"
fi
if echo "$BASEVALS" | grep -q "VIEWER"; then
  pass "role-enum-kept          VIEWER, the enum value of the role field, is still proposed ($BASEN values)"
else
  fail "role-enum-kept" "values line '$BASEVALS' lacks VIEWER"
fi
if [ "$BASEEXIT" = 0 ] && [ "$BASE970" = 1 ] && [ "$BASEGOT" = "$WANT_TIER1" ]; then
  pass "tier1-970               the shipped lexicon still chooses $WANT_TIER1 and raises 970"
else
  fail "tier1-970" "chose '$BASEGOT' det970=$BASE970 exit=$BASEEXIT"
fi

SRCLINE=$(grep "$SOURCES" $OUT/base.log | tail -1 | sed "s/.*$SOURCES *//")
SRCN=$(echo "$SRCLINE" | awk '{print $1}')
if [ -n "$SRCN" ] && [ "$SRCN" -ge 1 ] 2>/dev/null; then
  pass "sources-logged          $SOURCES $SRCLINE"
else
  fail "sources-logged" "line '$SRCLINE'; the guarded-source list is not logged or is empty on a run that raised 970"
fi

VICLINE=$(grep "$VICTIMS" $OUT/base.log | grep " victims \[" | grep -v "victims \[\]" | head -1 | sed "s/.*$VICTIMS//")
if [ -n "$VICLINE" ]; then
  pass "victims-logged          $VICLINE"
else
  fail "victims-logged" "no source line with a non-empty victim list"
fi

OPLINE=$(grep "$OPERATORS" $OUT/base.log | grep "operators" | head -1 | sed "s/.*$OPERATORS/'/")
OPVICTIM=$(echo "$OPLINE" | sed "s/^'\([^']*\)'.*/\1/")
OPLIST=$(echo "$OPLINE" | sed 's/.*operators //')
if [ -n "$OPLINE" ] && [ "$OPLIST" != "[]" ] && ! echo "$OPLIST" | grep -qw "$OPVICTIM"; then
  pass "operators-logged        victim '$OPVICTIM' operators $OPLIST, the victim is not its own operator"
else
  fail "operators-logged" "line '$OPLINE'"
fi

ATT=$(grep "$EXHAUSTED" $OUT/base.log | tail -1 | sed "s/.*$EXHAUSTED *//" | awk '{print $1}')
ASM=$(grep -c "Assembled .* statuses" $OUT/base.log)
if [ -n "$ATT" ] && [ "$ATT" -ge 1 ] 2>/dev/null && [ "$ATT" -ge "$ASM" ]; then
  pass "exhausted-logged        $ATT triple attempts logged at the end, $ASM assembled"
else
  fail "exhausted-logged" "attempts='$ATT' assembled=$ASM"
fi

FIXEXIT=$(run fixed $JAR $FIXED "")
FIX970=$(det970 $OUT/fixed)
FIXNEW=$(grep -cE "reduced role values:|guarded source candidates:| victims \[|' operators \[|sources exhausted after|phase timed out (before|on) source|attempt cap .* reached|already reduced in this phase" $OUT/fixed.log)
if [ "$FIXEXIT" = 0 ] && [ "$FIX970" = 0 ]; then
  pass "fixed-no-970            the patched app stays silent"
else
  fail "fixed-no-970" "exit=$FIXEXIT det970=$FIX970; a fixed target must raise nothing"
fi
if [ "$FIXNEW" = 0 ]; then
  pass "debug-only              at the default log level the new lines print nothing"
else
  fail "debug-only" "$FIXNEW new diagnostic lines printed at the default log level"
fi

DECL="PUT /users/{username}/role username=<victim> role=VIEWER"
DECLEXIT=$(run declared $JAR $VULN $DEBUG --statefulAuthzTransition "$DECL")
DECL970=$(det970 $OUT/declared)
DECLCAND=$(grep -c "$CANDIDATE" $OUT/declared.log)
DECLSRC=$(grep -c "$SOURCES" $OUT/declared.log)
if [ "$DECLCAND" = 0 ] && [ "$DECL970" = 1 ] && [ "$DECLEXIT" = 0 ] && [ "$DECLSRC" -ge 1 ]; then
  pass "declared-untouched      a declared transition skips ranking, logs its sources and still raises 970"
else
  fail "declared-untouched" "candidates=$DECLCAND sourceLines=$DECLSRC det970=$DECL970 exit=$DECLEXIT"
fi

echo ""
if [ $FAILED = 0 ]; then echo "tat ca kiem tra dat, ket qua o $OUT"; else echo "co kiem tra hong, ket qua o $OUT"; fi
exit $FAILED
