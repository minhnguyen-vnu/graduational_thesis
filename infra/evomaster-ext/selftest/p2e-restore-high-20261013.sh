#!/bin/zsh
set -u

EM=/Users/minhnguyen/IdeaProjects/EvoMaster
JAR=${JAR:?set JAR to the P2e jar}
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
MODEL=$EM/core/src/main/resources/stateful-authz-model.csv
REC=$THESIS/infra/em-results/p2d-night-20261012/remeasure/logs
OLDV=${OLDV:-$REC/t2-ours-vuln-seed11-r0.log}
OLDF=${OLDF:-$REC/t2-ours-fixed-seed11-r0.log}
OUT=${1:-$THESIS/infra/em-results/p2e-selftest-$(date +%Y%m%d-%H%M%S)}
SEED=11
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
mkdir -p $OUT
FAILED=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1  --  $2"; FAILED=1; }

echo "exercises RestSecurityBuilder.kt:1265-1269 (enum restore values limited to those the model scores high > low)"
echo "jar-new $(shasum -a 256 $JAR | cut -c1-16)  model $(shasum -a 256 $MODEL | cut -c1-16)"
echo "old = recorded P2d 2e0dbd4d logs, same flags without the debug logback: $OLDV $OLDF"

for p in 5002 5003; do
  if [ "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:$p/createdb)" != 200 ]; then
    fail "target-up" "vampi :$p did not answer GET /createdb with 200"
    echo "output $OUT"; exit 1
  fi
done

runit() {
  local name=$1 port=$2
  curl -s -o /dev/null http://localhost:$port/createdb
  java -Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:$port/openapi.json --bbTargetUrl http://localhost:$port \
    --configPath $THESIS/infra/em-config/vampi-seeded-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed $SEED \
    --outputFolder $OUT/$name > $OUT/$name.log 2>&1
}
det970() {
  python3 -c "
import json
try:
    c=[x['code'] for f in json.load(open('$1/report.json'))['faults']['foundFaults'] for x in f['faultCategories']]
    print(1 if 970 in c else 0)
except Exception: print('ERR')"
}
restores() {
  grep -hoE "Privilege-restore (accepted|refused) for '[^']*' by '[^']*' with role '[^']*' on PUT:/users/v1/\{username\}/role" "$@"
}
roles() {
  restores "$@" | sed -E "s/.* with role '([^']*)'.*/\1/"
}
nothigh() {
  python3 -c "
import csv, sys
t = {}
for r in csv.DictReader(open('$MODEL')):
    t.setdefault(r['table'], {})[r['feature']] = float(r['weight'])
def score(name, v):
    v = v.lower()
    return max([w for k, w in t.get(name, {}).items() if k in v], default=0.0)
bad = sorted({v for v in sys.stdin.read().split() if score('high', v) <= score('low', v)})
print(' '.join(bad))"
}

runit vuln 5002
runit fixed 5003
NV=$OUT/vuln.log; NF=$OUT/fixed.log
DV=$(det970 $OUT/vuln); DF=$(det970 $OUT/fixed)

N=$(restores $NV $NF | wc -l | tr -d ' ')
[ "$N" -gt 0 ] \
  && pass "C-exercised     $N restore calls on the enum role field: $(roles $NV $NF | sort | uniq -c | tr -s ' ' | tr '\n' ';')" \
  || fail "C-exercised" "no restore call on PUT:/users/v1/{username}/role; :1265-1269 not reached on this run"

BAD=$(roles $NV $NF | nothigh)
[ "$N" -gt 0 ] && [ -z "$BAD" ] \
  && pass "C-high-only     every restore value scores high > low in the model" \
  || fail "C-high-only" "restore values scored high <= low: '$BAD' (or no restore call)"

grep -qF "with role 'EVOMASTER'" $NV $NF \
  && fail "C-no-evomaster" "a restore call used the EvoMaster invalid-data value EVOMASTER" \
  || pass "C-no-evomaster  no restore call uses EVOMASTER"

A=$(grep -oE "Privilege-restore accepted for '[^']*' by '[^']*'" $NV | head -1)
[ -n "$A" ] \
  && pass "C-accepted      vuln seed $SEED: $A" \
  || fail "C-accepted" "vuln seed $SEED: no restore accepted"

[ "$DV" = 1 ] \
  && pass "C-det970        vuln seed $SEED report.json has fault 970" \
  || fail "C-det970" "vuln seed $SEED did not detect 970 (det970=$DV)"

T=$(grep -oE "Assembled .* statuses [0-9]+/[0-9]+/403" $NF | head -1)
[ -n "$T" ] && [ "$DF" = 0 ] \
  && pass "C-fixed-triple  fixed seed $SEED assembled a triple with follow-up 403 and det970=0" \
  || fail "C-fixed-triple" "fixed seed $SEED: $(grep -c 'Assembled .* statuses [0-9]*/[0-9]*/403' $NF) triples with follow-up 403, det970=$DF"

OBAD=$(roles $OLDV $OLDF | nothigh)
if [ -n "$OBAD" ] && grep -qF "with role 'EVOMASTER'" $OLDV && ! grep -qF "Privilege-restore accepted" $OLDV \
   && ! grep -qE "Assembled .* statuses [0-9]+/[0-9]+/403" $OLDF; then
  pass "checks-can-fail P2d logs: restore values '$OBAD', no restore accepted, no fixed triple -> C-high-only, C-no-evomaster, C-accepted, C-fixed-triple FAIL on P2d"
else
  fail "checks-can-fail" "recorded P2d logs pass the same checks; they do not discriminate the change"
fi

echo "output $OUT"
exit $FAILED
