#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=$EM/core/target/evomaster.jar
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
OUT=${1:-$THESIS/infra/em-results/local-harvest-selftest-$(date +%Y%m%d-%H%M%S)}
export JAVA_HOME=$(/usr/libexec/java_home -v 17)

RES=stateful-authz-lexicon.csv
CHOSEN="Stateful-authorization transition chosen:"
CANDIDATE="Stateful-authorization transition candidate"
WANT_TIER1="PUT:/users/{username}/role"
BARREN="POST:/reset"
WITHBODY="POST:/auth/login"
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

printf 'kind,word,score\npath,reset,0.9900\npath,role,0.5000\nparam,username,0.5000\n' \
  > $OUT/fallthrough-lexicon.csv
decoy_jar fallthrough
FTEXIT=$(run fallthrough $OUT/fallthrough.jar $VULN)
FTFIRST=$(grep "$CANDIDATE" $OUT/fallthrough.log | head -1)
FTTOP=$(echo "$FTFIRST" | sed "s/.*$CANDIDATE *//" | awk '{print $1}')
FTHARVEST=$(echo "$FTFIRST" | sed 's/.*reducedRoleValues //')
FTGOT=$(grep "$CHOSEN" $OUT/fallthrough.log | tail -1 | sed "s/.*$CHOSEN *//")
FTCAND=$(grep -c "$CANDIDATE" $OUT/fallthrough.log)

if [ "$FTTOP" = "$BARREN" ] && [ "$FTHARVEST" = "0" ]; then
  pass "harvest-is-local      $BARREN carries no request body and now harvests 0 values"
else
  fail "harvest-is-local" "top='$FTTOP' reducedRoleValues='$FTHARVEST'; expected '$BARREN' and 0"
fi

if [ "$FTCAND" -ge 2 ] && [ "$FTGOT" = "$WANT_TIER1" ]; then
  pass "loop-advances         $FTCAND candidates weighed, the top-scored barren one is skipped for $WANT_TIER1"
else
  fail "loop-advances" "candidates=$FTCAND chosen='$FTGOT' exit=$FTEXIT; the 8-candidate loop never advanced"
fi

if [ "$FTCAND" -le 8 ]; then
  pass "candidate-cap         $FTCAND candidate lines, cap is 8"
else
  fail "candidate-cap" "$FTCAND candidate lines; MAX_TRANSITION_CANDIDATES=8 is not enforced"
fi

printf 'kind,word,score\npath,login,0.9900\npath,role,0.5000\nparam,username,0.5000\n' \
  > $OUT/bodytype-lexicon.csv
decoy_jar bodytype
BTEXIT=$(run bodytype $OUT/bodytype.jar $VULN)
BTFIRST=$(grep "$CANDIDATE" $OUT/bodytype.log | head -1)
BTTOP=$(echo "$BTFIRST" | sed "s/.*$CANDIDATE *//" | awk '{print $1}')
BTHARVEST=$(echo "$BTFIRST" | sed 's/.*reducedRoleValues //')
if [ "$BTTOP" = "$WITHBODY" ] && [ "$BTHARVEST" = "1" ]; then
  pass "content-type-is-a-value $WITHBODY has no role field yet still harvests 1 value, its BodyParam content type"
else
  fail "content-type-is-a-value" "top='$BTTOP' reducedRoleValues='$BTHARVEST' exit=$BTEXIT; expected '$WITHBODY' and 1"
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
  pass "fixed-no-970          the patched app stays silent"
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
