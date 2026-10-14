#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EM=/Users/minhnguyen/IdeaProjects/EvoMaster
F1=core/src/main/kotlin/org/evomaster/core/EMConfig.kt
F2=core/src/main/kotlin/org/evomaster/core/problem/rest/service/RestSecurityBuilder.kt
WIP=$THESIS/infra/evomaster-ext/wip
FIX=$WIP/gene-set-guard-20260925.patch
FULL=$WIP/d1-lexicon-field-harvest-rolefield-postfallback-geneguard-20260925.patch
BASE=$THESIS/infra/em-results/genesetguard-chain-20260925
GBASE=$THESIS/infra/em-results/regression-check
PREV=$THESIS/infra/em-results/postfallback-chain-20260925/progress.log
WANT_TREE=00f98d290947d998
PREV_JAR=evomaster-PF-0607485b.jar
PROG=$BASE/progress.log
mkdir -p $BASE/logs

say () { echo "$(date +%H:%M:%S) $*" >> $PROG }
die () { say "DUNG CHUOI: $*"; echo "CHAIN STOPPED $(date)" >> $PROG; exit 1 }

echo "chuoi gene-set-guard start $(date), doi chuoi post-fallback xong" > $PROG

while true; do
  grep -q "CHAIN DONE" $PREV 2>/dev/null && break
  grep -q "CHAIN STOPPED" $PREV 2>/dev/null && die "chuoi post-fallback dung giua chung, khong ap patch"
  sleep 60
done
say "chuoi post-fallback xong"
pgrep -f "evomaster.*\.jar" > /dev/null && die "con tien trinh EvoMaster dang chay"

TREE=$(git -C $EM diff | shasum -a 256 | cut -c1-16)
[ "$TREE" = "$WANT_TREE" ] || die "cay lam viec sha $TREE, cho $WANT_TREE"
[ -f $EM/$PREV_JAR ] || die "khong thay jar truoc khi doi: $PREV_JAR"
say "cay lam viec $TREE, jar truoc khi doi da giu: $PREV_JAR"

git -C $EM apply $FIX || die "git apply $FIX hong"
git -C $EM diff > $FULL
NEWTREE=$(shasum -a 256 < $FULL | cut -c1-16)
say "da ap patch, cay moi $NEWTREE"

git -C $EM checkout -- $F1 $F2
[ "$(git -C $EM diff HEAD | wc -l | tr -d ' ')" = "0" ] || die "rollback: git diff HEAD khong rong"
git -C $EM apply $FULL || die "rollback: git apply lai hong"
cmp -s <(git -C $EM diff) $FULL || die "rollback: diff sau khi ap lai khac patch da luu"
say "tap rollback dat: sha $(git -C $EM diff | shasum -a 256 | cut -c1-16) truoc va sau"

say "build"
JAVA_HOME=$(/usr/libexec/java_home -v 17) mvn -q -f $EM/pom.xml -pl core -am package -Dmaven.test.skip=true > $BASE/logs/build.log 2>&1 || die "build hong, xem logs/build.log"
JAR=$EM/core/target/evomaster.jar
JARSHA=$(shasum -a 256 $JAR | cut -c1-16)
KEEP=$EM/evomaster-GG-${JARSHA[1,8]}.jar
cp $JAR $KEEP
shasum -a 256 $KEEP > $KEEP.sha256
say "jar $JARSHA, giu o $KEEP"

say "self-test gene-set-guard"
JAR=$JAR zsh $THESIS/infra/evomaster-ext/selftest/gene-set-guard.sh $BASE/selftest-geneguard > $BASE/logs/selftest-geneguard.log 2>&1
E1=$?
grep -E '^(PASS|FAIL)' $BASE/logs/selftest-geneguard.log >> $PROG
[ $E1 -eq 0 ] || die "self-test gene-set-guard hong"

say "self-test post-fallback tren jar moi"
JAR=$JAR zsh $THESIS/infra/evomaster-ext/selftest/post-fallback.sh $BASE/selftest-postfallback > $BASE/logs/selftest-postfallback.log 2>&1
E2=$?
grep -E '^(PASS|FAIL)' $BASE/logs/selftest-postfallback.log >> $PROG
[ $E2 -eq 0 ] || die "self-test post-fallback hong"

say "cong hoi quy"
ARCH=$GBASE/archive-20260925-postfallback
mkdir -p $ARCH
for f in observed.csv progress.log logs; do
  [ -e $GBASE/$f ] && mv $GBASE/$f $ARCH/ 2>/dev/null
done
zsh $GBASE/regression_check.sh > $BASE/logs/gate.log 2>&1
GEXIT=$?
cp $GBASE/observed.csv $BASE/logs/gate-observed.csv 2>/dev/null
VERDICT=$(python3 - "$GBASE/observed.csv" <<'PY'
import csv, io, sys
rows = list(csv.DictReader(io.open(sys.argv[1], encoding='utf-8')))
bad_fixed = [r for r in rows if 'fixed' in r['arm'] and r['verdict'] != 'MATCH']
bad_vuln = [r for r in rows if 'fixed' not in r['arm'] and r['verdict'] != 'MATCH']
print('%d %d %d' % (len(rows), len(bad_fixed), len(bad_vuln)))
PY
)
set -- ${=VERDICT}
say "cong hoi quy: $1 dong, ban da va lech $2, ban loi lech $3 (exit $GEXIT)"

say "Vikunja seed 1, log debug"
zsh $THESIS/infra/em-results/vikunja-postfallback-20260925/run.sh $JAR gg-seed1 > $BASE/logs/vikunja.log 2>&1
tail -1 $THESIS/infra/em-results/vikunja-postfallback-20260925/progress.log >> $PROG

say "sao luu"
cd /Users/minhnguyen/IdeaProjects
TAR=~/thesis-backups/thesis-full-$(date +%Y%m%d-%H%M).tar.gz
tar --exclude 'graduational-thesis/infra/em-venv' -czf $TAR graduational-thesis
shasum -a 256 $TAR > $TAR.sha256
say "sao luu $TAR"
echo "CHAIN DONE $(date)" >> $PROG
