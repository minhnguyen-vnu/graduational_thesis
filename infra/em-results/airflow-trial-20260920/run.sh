#!/bin/zsh
set -u
T=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/core/target/evomaster.jar
JH=$(/usr/libexec/java_home -v 17)
B=$T/infra/em-results/airflow-trial-20260920
for d1 in false true; do
  $T/infra/airflow-target/reset.sh http://localhost:8082 >> $B/progress.log
  OUT=$B/tests/long-d1$d1; rm -rf $OUT
  echo "$(date +%H:%M:%S) start d1=$d1" >> $B/progress.log
  JAVA_HOME=$JH java -jar $JAR --blackBox true \
    --bbSwaggerUrl file://$T/infra/airflow-target/airflow-merged-nodelete.json \
    --bbTargetUrl http://localhost:8082 \
    --configPath $T/infra/em-config/airflow-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment $d1 \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 600s --seed 1 \
    --outputFolder $OUT > $B/logs/long-d1$d1.log 2>&1
  echo "$(date +%H:%M:%S) done d1=$d1 assembled=$(grep -c 'Assembled .* statuses' $B/logs/long-d1$d1.log) void=$(grep -c 'Discarded a VOID' $B/logs/long-d1$d1.log) probe=$(grep -c 'fresh-credential probe:' $B/logs/long-d1$d1.log)" >> $B/progress.log
done
echo "AIRFLOW TRIAL DONE $(date)" >> $B/progress.log
