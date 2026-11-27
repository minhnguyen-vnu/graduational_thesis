#!/bin/sh
set -e
cd "$(dirname "$0")"
T=/Users/minhnguyen/IdeaProjects/graduational-thesis
JAR=/Users/minhnguyen/IdeaProjects/EvoMaster/evomaster-TR2-3beccb00.jar
JAVA="$(/usr/libexec/java_home -v 17)/bin/java"
F='^SLF4J\|DEBUG\|^\s*at \|There are [0-9]* usable'
"$JAVA" -cp "$JAR" Classes.java "$JAR" 2>&1 | grep -v "$F" > classes.out
"$JAVA" -cp "$JAR" Tree.java "$T/docs/evomaster-study/probe-phan1/reports-api-openapi.json" "PUT:/users/{username}/role" alice 2>&1 | grep -v "$F" > tree-reports.out
"$JAVA" -cp "$JAR" Tree.java "$T/infra/vampi-seeded/openapi_specs/openapi3.yml" "PUT:/users/v1/{username}/role" superadmin 2>&1 | grep -v "$F" > tree-vampi.out
"$JAVA" -cp "$JAR" Tree.java "$T/infra/pyload-cve/openapi-merged.json" "POST:/api/set_user_permission" 2>&1 | grep -v "$F" > tree-pyload.out
"$JAVA" -cp "$JAR" Tree.java "$T/infra/em-results/tr2-wave2-20261121/openapi-trimmed.json" "PATCH:/api/v1/users/{id}" 2>&1 | grep -v "$F" > tree-ak.out
shasum -a 256 "$JAR" | cut -c1-16
wc -l *.out
