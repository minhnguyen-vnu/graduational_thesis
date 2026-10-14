#!/usr/bin/env zsh
set -u
THESIS=/Users/minhnguyen/IdeaProjects/graduational-thesis
EM=/Users/minhnguyen/IdeaProjects/EvoMaster
BASE=$THESIS/infra/em-results/gate-mismatch-20260930
JH=$(/usr/libexec/java_home -v 17)
DEBUG="-Dlogback.configurationFile=$THESIS/infra/em-config/logback-builder-debug.xml"
for tag in NR-aeeb485c VI-d2325da7; do
  curl -s http://localhost:5003/createdb > /dev/null
  OUT=$BASE/out-$tag; rm -rf $OUT
  JAVA_HOME=$JH java $DEBUG -jar $EM/evomaster-$tag.jar \
    --blackBox true \
    --bbSwaggerUrl http://localhost:5003/openapi.json --bbTargetUrl http://localhost:5003 \
    --configPath $THESIS/infra/em-config/vampi-seeded-auth.yaml \
    --useExperimentalOracles true --extraPhaseBudgetPercentage 0.6 \
    --statefulAuthzResetEndpoint "GET http://localhost:5003/createdb" \
    --outputFormat PYTHON_UNITTEST --ratePerMinute 120 --maxTime 150s --seed 3 \
    --outputFolder $OUT > $BASE/$tag.log 2>&1
  echo "$(date +%H:%M:%S) $tag exit=$? $(grep -o 'statuses [0-9/]*' $BASE/$tag.log | tr '\n' ';')" >> $BASE/progress.log
done
