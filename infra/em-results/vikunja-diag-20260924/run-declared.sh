#!/bin/zsh
set -u
T=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=$1
NAME=$2
JH=$(/usr/libexec/java_home -v 17)
B=$T/infra/em-results/vikunja-diag-20260924
mkdir -p $B/logs $B/tests
echo "$(date +%H:%M:%S) $NAME jar $(shasum -a 256 $JAR | cut -c1-16)" >> $B/progress.log
$T/infra/vikunja-target/reset.sh 3457 >> $B/progress.log
OUT=$B/tests/$NAME; rm -rf $OUT
JAVA_HOME=$JH java -Dlogback.configurationFile=$T/infra/em-config/logback-builder-debug.xml -jar $JAR --blackBox true \
  --bbSwaggerUrl file://$T/infra/vikunja-target/vikunja-2.2.2-docs.json \
  --bbTargetUrl http://localhost:3457 \
  --configPath $T/infra/em-config/vikunja-auth.yaml \
  --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
  --statefulAuthzTwoCredentialJudgment false \
  --statefulAuthzTransition "POST /api/v1/projects/{projectID}/users/{userID} permission=0 projectID=4" \
  --outputFormat PYTHON_UNITTEST --ratePerMinute 60 --maxTime 600s --seed 1 \
  --outputFolder $OUT > $B/logs/$NAME.log 2>&1
EX=$?
L=$B/logs/$NAME.log
echo "$(date +%H:%M:%S) $NAME exit=$EX chosen=[$(grep 'transition chosen' $L | tail -1 | sed 's/.*chosen: //')] candidates=$(grep -c 'transition candidate' $L) assembled=$(grep -c 'Assembled .* statuses' $L) void=$(grep -c 'Discarded a VOID' $L) loginfail=$(grep -c 'Failed to login' $L)" >> $B/progress.log
