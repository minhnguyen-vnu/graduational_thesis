#!/bin/sh
set -e
cd "$(dirname "$0")"
T=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-TR2-3beccb00.jar
JAVA="$(/usr/libexec/java_home -v 17)/bin/java"
F='^SLF4J\|DEBUG\|^\s*at \|There are [0-9]* usable'
"$JAVA" -cp "$JAR" Members.java \
  "$T/docs/evomaster-study/probe-phan1/reports-api-openapi.json" \
  "$T/infra/em-config/reports-auth.yaml" \
  "$T/infra/vampi-seeded/openapi_specs/openapi3.yml" \
  "$T/infra/em-results/tr2-wave2-20261121/openapi-trimmed.json" \
  "$T/infra/pyload-cve/openapi-merged.json" 2>&1 | grep -v "$F" > members.out
shasum -a 256 "$JAR" | cut -c1-16
wc -l members.out
