#!/bin/bash
cd /Users/minhnguyen/IdeaProjects/graduational-thesis/infra/artifact-keeper-target/src
C=artifact-keeper-dev-backend
FAIL='protoc failed|build failed|could not compile|error\[E[0-9]|cannot find|panicked|Exit status: [1-9]|linking with|error: '
echo "=== $(date '+%T') rebuild image (+protoc) + recreate backend ==="
docker compose -f docker-compose.local-dev.yml -f docker-compose.thesis.yml up -d --build backend 2>&1 | tail -15
echo "=== $(date '+%T') waiting: health | failure | container-exit ==="
for i in $(seq 1 540); do
  running=$(docker inspect --format '{{.State.Running}}' $C 2>/dev/null)
  if [ "$running" != "true" ]; then echo "[$((i*5))s] CONTAINER NOT RUNNING (state=$running):"; docker logs --tail 40 $C 2>&1 | tail -40; break; fi
  code=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/health 2>/dev/null)
  if [ "$code" != "000" ] && [ -n "$code" ]; then echo "[$((i*5))s] SERVER UP /health http=$code"; break; fi
  if docker logs $C 2>&1 | tail -60 | grep -qiE "$FAIL"; then
    echo "[$((i*5))s] BUILD FAILURE DETECTED:"; docker logs $C 2>&1 | grep -iE "$FAIL" | tail -8; echo "--- tail ---"; docker logs --tail 15 $C 2>&1 | tail -15; break
  fi
  if [ $((i % 12)) -eq 0 ]; then echo "[$((i*5))s] compiling... tail:"; docker logs --tail 2 $C 2>&1 | tail -2; fi
  sleep 5
done
echo "=== $(date '+%T') DONE ==="
