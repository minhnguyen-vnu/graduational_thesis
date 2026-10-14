#!/usr/bin/env zsh
NAME=${1:-bamf}
T=/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/bamf-target
for f in $T/run-$NAME/api.pid $T/run-$NAME/shim.pid; do [ -f $f ] && kill $(cat $f) 2>/dev/null; done
docker rm -f $NAME-db $NAME-redis > /dev/null 2>&1
