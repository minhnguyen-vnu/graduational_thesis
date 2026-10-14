#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EM=/Users/minhnguyen/IdeaProjects/EvoMaster
D=$THESIS/infra/em-results/t1seed10-debug-20260930
JH=$(/usr/libexec/java_home -v 17)
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
for J in NR-3c087e58 VI-d2325da7; do tag=${J%%-*}
  JAR=$EM/evomaster-$J.jar
  curl -s -o /dev/null -X POST http://localhost:8080/reset
  echo "$(date +%H:%M:%S) start $tag $(basename $JAR)" >> $D/progress.log
  JAVA_HOME=$JH java $DEBUG -jar $JAR --blackBox true \
    --bbSwaggerUrl http://localhost:8080/v3/api-docs --bbTargetUrl http://localhost:8080 \
    --configPath $THESIS/infra/em-config/reports-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzTwoCredentialJudgment false \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 10 \
    --outputFolder $D/tests-$tag > $D/t1-vuln-seed10-$tag.log 2>&1
  echo "$(date +%H:%M:%S) $tag exit $? $(grep -c 'Assembled' $D/t1-vuln-seed10-$tag.log) assembled; $(grep -o 'statuses [0-9/]*' $D/t1-vuln-seed10-$tag.log | tr '\n' ';')" >> $D/progress.log
done
