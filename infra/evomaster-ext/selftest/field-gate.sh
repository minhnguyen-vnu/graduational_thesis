#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=$EM/core/target/evomaster.jar
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
OUT=${1:-$THESIS/infra/em-results/field-gate-selftest-$(date +%Y%m%d-%H%M%S)}
export JAVA_HOME=$(/usr/libexec/java_home -v 17)

RES=stateful-authz-lexicon.csv
CHOSEN="Stateful-authorization transition chosen:"
CANDIDATE="Stateful-authorization transition candidate"
NOTRANS="no permission-reducing transition endpoint found"
WANT_TIER1="PUT:/users/{username}/role"
BODYONLY="PUT:/reports/{id}"
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
  local name=$1 jar=$2 port=$3
  shift 3
  curl -s -X POST http://localhost:$port/reset > /dev/null
  java -Dlogback.configurationFile=$OUT/logback-debug.xml -jar $jar \
    --blackBox true --bbSwaggerUrl http://localhost:$port/v3/api-docs --bbTargetUrl http://localhost:$port \
    --configPath $THESIS/infra/em-config/reports-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 1 \
    "$@" \
    --outputFolder $OUT/$name > $OUT/$name.log 2>&1
  echo $?
}

decoy_jar() {
  local name=$1
  cp $JAR $OUT/$name.jar
  cp $OUT/$name-lexicon.csv $OUT/$RES
  ( cd $OUT && zip -q $name.jar $RES )
  rm -f $OUT/$RES
}

for p in $VULN $FIXED; do
  if ! curl -s --max-time 5 -o /dev/null http://localhost:$p/v3/api-docs; then
    echo "FAIL  target-up  --  cong $p khong tra loi, khong chay duoc self-test"
    exit 1
  fi
done

if unzip -p $JAR $RES 2>/dev/null | grep -q '^path,'; then
  pass "lexicon-in-jar        $RES ships inside the jar"
else
  fail "lexicon-in-jar" "$RES is not in the jar; the jar does not carry the lexicon patch"
fi

printf 'kind,word,score\npath,classification,0.9900\nparam,username,0.5000\n' > $OUT/bodyword-lexicon.csv
decoy_jar bodyword
BWEXIT=$(run bodyword $OUT/bodyword.jar $VULN)
BWGOT=$(grep "$CANDIDATE" $OUT/bodyword.log | head -1 | sed "s/.*$CANDIDATE *//" | awk '{print $1}')
BWINPATH=$(echo "$BWGOT" | grep -c classification)
if [ "$BWEXIT" = 0 ] && [ "$BWGOT" = "$BODYONLY" ] && [ "$BWINPATH" = 0 ]; then
  pass "body-word-passes-gate a word present only in a request body ranks $BODYONLY first"
else
  fail "body-word-passes-gate" "top candidate '$BWGOT' exit=$BWEXIT inpath=$BWINPATH; ReportRequest is the body of both PUT /reports/{id} and POST /reports, and PUT wins the declared verb order"
fi

printf 'kind,word,score\npath,zzzunused,0.9900\nparam,username,0.5000\n' > $OUT/absent-lexicon.csv
decoy_jar absent
ABEXIT=$(run absent $OUT/absent.jar $VULN)
ABCAND=$(grep -c "$CANDIDATE" $OUT/absent.log)
AB970=$(det970 $OUT/absent)
if [ "$ABEXIT" = 0 ] && [ "$ABCAND" = 0 ] && [ "$AB970" = 0 ] && grep -q "$NOTRANS" $OUT/absent.log; then
  pass "absent-word-no-gate   a word in no path and no body leaves 0 candidates and raises nothing"
else
  fail "absent-word-no-gate" "candidates=$ABCAND det970=$AB970 exit=$ABEXIT; the previous check may be a fallback, not a body hit"
fi

printf 'kind,word,score\npath,role,0.9900\nparam,username,0.5000\n' > $OUT/pathonly-lexicon.csv
decoy_jar pathonly
POEXIT=$(run pathonly $OUT/pathonly.jar $VULN)
POGOT=$(grep "$CHOSEN" $OUT/pathonly.log | tail -1 | sed "s/.*$CHOSEN *//")
if [ "$POEXIT" = 0 ] && [ "$POGOT" = "$WANT_TIER1" ]; then
  pass "path-word-unchanged   a path word still chooses $WANT_TIER1"
else
  fail "path-word-unchanged" "chose '$POGOT' exit=$POEXIT; widening the hay broke the path half"
fi

BASEEXIT=$(run base $JAR $VULN)
BASE970=$(det970 $OUT/base)
BASEGOT=$(grep "$CHOSEN" $OUT/base.log | tail -1 | sed "s/.*$CHOSEN *//")
if [ "$BASEEXIT" = 0 ] && [ "$BASE970" = 1 ] && [ "$BASEGOT" = "$WANT_TIER1" ]; then
  pass "tier1-970             the shipped lexicon still chooses $WANT_TIER1 and raises 970"
else
  fail "tier1-970" "chose '$BASEGOT' det970=$BASE970 exit=$BASEEXIT"
fi

FIXEXIT=$(run fixed $JAR $FIXED)
FIX970=$(det970 $OUT/fixed)
if [ "$FIXEXIT" = 0 ] && [ "$FIX970" = 0 ]; then
  pass "fixed-no-970          the wider gate raises nothing on the patched app"
else
  fail "fixed-no-970" "exit=$FIXEXIT det970=$FIX970; a fixed target must raise nothing"
fi

DECL="PUT /users/{username}/role username=<victim> role=VIEWER"
DECLEXIT=$(run declared $JAR $VULN --statefulAuthzTransition "$DECL")
DECL970=$(det970 $OUT/declared)
DECLCAND=$(grep -c "$CANDIDATE" $OUT/declared.log)
if [ "$DECLCAND" = 0 ] && [ "$DECL970" = 1 ] && [ "$DECLEXIT" = 0 ]; then
  pass "declared-untouched    a declared transition skips ranking and still raises 970"
else
  fail "declared-untouched" "candidates=$DECLCAND det970=$DECL970 exit=$DECLEXIT; expected 0, 1, 0"
fi

echo ""
if [ $FAILED = 0 ]; then echo "tat ca kiem tra dat, ket qua o $OUT"; else echo "co kiem tra hong, ket qua o $OUT"; fi
exit $FAILED
