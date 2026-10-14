#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=$EM/core/target/evomaster.jar
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
OUT=${1:-$THESIS/infra/em-results/lexicon-selftest-$(date +%Y%m%d-%H%M%S)}
export JAVA_HOME=$(/usr/libexec/java_home -v 17)

RES=stateful-authz-lexicon.csv
CHOSEN="Stateful-authorization transition chosen:"
CANDIDATE="Stateful-authorization transition candidate"
EXHAUSTED="no reduced role value could be proposed for any of"
WARN="Stateful-authorization lexicon"
WANT_TIER1="PUT:/users/{username}/role"
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

ordered() {
  python3 - "$1" "$CANDIDATE" "$CHOSEN" "$EXHAUSTED" <<'PY'
import io, re, sys
log, cand, chosen, exhausted = sys.argv[1:5]
blocks, cur = [], []
for line in io.open(log, encoding='utf-8', errors='replace'):
    if cand in line:
        m = re.search(r' score ([0-9.]+) ', line)
        cur.append(float(m.group(1)) if m else -1.0)
    elif (chosen in line or exhausted in line) and cur:
        blocks.append(cur)
        cur = []
if cur:
    blocks.append(cur)
if not blocks:
    print('NOBLOCK')
elif any(-1.0 in b for b in blocks):
    print('NOSCORE')
elif all(b == sorted(b, reverse=True) for b in blocks):
    print('OK %d' % len(blocks))
else:
    print('UNSORTED ' + ';'.join(','.join(str(x) for x in b) for b in blocks))
PY
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

unzip -p $JAR $RES > $OUT/lexicon-from-jar.csv 2>/dev/null
if [ -s $OUT/lexicon-from-jar.csv ]; then
  pass "lexicon-in-jar        $RES ships inside the jar"
else
  fail "lexicon-in-jar" "$RES is not in the jar; the jar does not carry the patch"
fi

NPATH=$(awk -F, '$1=="path"' $OUT/lexicon-from-jar.csv 2>/dev/null | wc -l | tr -d ' ')
NPARAM=$(awk -F, '$1=="param"' $OUT/lexicon-from-jar.csv 2>/dev/null | wc -l | tr -d ' ')
if [ "$NPATH" -gt 0 ] && [ "$NPARAM" -gt 0 ]; then
  pass "lexicon-both-kinds    $NPATH path words, $NPARAM param words"
else
  fail "lexicon-both-kinds" "path=$NPATH param=$NPARAM; both must be non-empty"
fi

BASEEXIT=$(run base $JAR $VULN)
BASE970=$(det970 $OUT/base)
NCAND=$(grep -c "$CANDIDATE" $OUT/base.log)

if [ "$NCAND" -gt 0 ]; then
  pass "candidates-logged     the builder names each transition candidate it weighs ($NCAND lines)"
else
  fail "candidates-logged" "no '$CANDIDATE' line; the diagnostic the airflow run needed is missing"
fi

ORD=$(ordered $OUT/base.log)
case $ORD in
  OK*) pass "candidates-ordered    every candidate block is sorted by score, $ORD" ;;
  *)   fail "candidates-ordered" "$ORD" ;;
esac

if [ "$NCAND" -le 8 ]; then
  pass "candidate-cap         $NCAND candidate lines, cap is 8"
else
  fail "candidate-cap" "$NCAND candidate lines; MAX_TRANSITION_CANDIDATES=8 is not enforced"
fi

GOT=$(grep "$CHOSEN" $OUT/base.log | tail -1 | sed "s/.*$CHOSEN *//")
if [ "$GOT" = "$WANT_TIER1" ]; then
  pass "tier1-chosen          transition chosen is $WANT_TIER1"
else
  fail "tier1-chosen" "chose '$GOT', expected '$WANT_TIER1'"
fi

if [ "$BASEEXIT" = 0 ] && [ "$BASE970" = 1 ]; then
  pass "tier1-970             tier1 vuln seed 1 still raises 970"
else
  fail "tier1-970" "exit=$BASEEXIT det970=$BASE970; expected exit 0 and 970 raised"
fi

FIXEXIT=$(run fixed $JAR $FIXED)
FIX970=$(det970 $OUT/fixed)
if [ "$FIXEXIT" = 0 ] && [ "$FIX970" = 0 ]; then
  pass "fixed-no-970          the patched app stays silent under 8 candidates"
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

printf 'kind,word,score\npath,login,0.9900\npath,role,0.5000\nparam,username,0.5000\n' \
  > $OUT/fallthrough-lexicon.csv
decoy_jar fallthrough
FTEXIT=$(run fallthrough $OUT/fallthrough.jar $VULN)
FTGOT=$(grep "$CHOSEN" $OUT/fallthrough.log | tail -1 | sed "s/.*$CHOSEN *//")
FTFIRST=$(grep "$CANDIDATE" $OUT/fallthrough.log | head -1)
FTTOP=$(echo "$FTFIRST" | sed "s/.*$CANDIDATE *//" | awk '{print $1}')
if [ "$FTGOT" = "$FTTOP" ] && [ "$FTGOT" = "POST:/auth/login" ]; then
  pass "top-scored-chosen     raising one endpoint's score to 0.99 moves the choice onto it"
else
  fail "top-scored-chosen" "top='$FTTOP' chosen='$FTGOT' exit=$FTEXIT"
fi

FTHARVEST=$(echo "$FTFIRST" | sed 's/.*reducedRoleValues //')
if [ "$FTHARVEST" != "0" ]; then
  pass "harvest-is-global     $FTHARVEST role values harvested on an endpoint with no role field of its own"
else
  fail "harvest-is-global" "expected a non-zero harvest on /auth/login, got '$FTHARVEST'"
fi

{
  printf 'kind,word,score\n'
  printf 'path,reports,0.9000\n'
  printf 'param,id,0.9000\n'
  printf 'a line with no comma at all\n'
  printf 'path,onlytwofields\n'
  printf 'path,badscore,notanumber\n'
  printf 'unknownkind,foo,0.5000\n'
  printf '\n'
  printf 'path,reports,0.9000\n'
} > $OUT/decoy-lexicon.csv
decoy_jar decoy
DECOYEXIT=$(run decoy $OUT/decoy.jar $VULN)
DGOT=$(grep "$CHOSEN" $OUT/decoy.log | tail -1 | sed "s/.*$CHOSEN *//")
if [ "$DECOYEXIT" = 0 ] && [ "$DGOT" != "$WANT_TIER1" ]; then
  pass "score-drives-choice   without 'role' in the file the role endpoint is never chosen (got '$DGOT')"
else
  fail "score-drives-choice" "chose '$DGOT' exit=$DECOYEXIT; the word list still comes from the code"
fi

if [ "$DECOYEXIT" = 0 ] && ! grep -q 'Caused by:\|	at org\.evomaster\.' $OUT/decoy.log; then
  pass "malformed-tolerated   6 malformed lines in the lexicon raise no exception"
else
  fail "malformed-tolerated" "exit=$DECOYEXIT; malformed lexicon lines broke the run"
fi

cp $JAR $OUT/nolexicon.jar
zip -q -d $OUT/nolexicon.jar $RES > /dev/null
MISSEXIT=$(run nolexicon $OUT/nolexicon.jar $VULN)
MISS970=$(det970 $OUT/nolexicon)
if [ "$MISSEXIT" = 0 ] && [ "$MISS970" = 0 ] && grep -q "$WARN" $OUT/nolexicon.log; then
  pass "missing-lexicon-warns a jar without the file warns instead of going quiet"
else
  fail "missing-lexicon-warns" "exit=$MISSEXIT det970=$MISS970 warn=$(grep -c "$WARN" $OUT/nolexicon.log)"
fi

echo ""
if [ $FAILED = 0 ]; then echo "tat ca kiem tra dat, ket qua o $OUT"; else echo "co kiem tra hong, ket qua o $OUT"; fi
exit $FAILED
