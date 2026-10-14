#!/bin/bash
cd /Users/minhnguyen/IdeaProjects/graduational-thesis/infra/artifact-keeper-target/src
C=artifact-keeper-dev-backend
echo "=== $(date '+%T') up backend (ports fixed: only 8080) ==="
docker compose -f docker-compose.local-dev.yml -f docker-compose.thesis.yml up -d backend 2>&1 | tail -15
echo "=== $(date '+%T') waiting: container running + :8080 health ==="
for i in $(seq 1 480); do
  running=$(docker inspect --format '{{.State.Running}}' $C 2>/dev/null)
  if [ "$running" != "true" ]; then
    echo "[$((i*5))s] CONTAINER NOT RUNNING (state=$running). Last logs:"; docker logs --tail 40 $C 2>&1 | tail -40; break
  fi
  code=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/health 2>/dev/null)
  if [ "$code" != "000" ] && [ -n "$code" ]; then echo "[$((i*5))s] SERVER UP /health http=$code"; break; fi
  if docker logs $C 2>&1 | grep -qiE 'error\[E[0-9]|error: could not compile|error: linking|panicked'; then
    echo "[$((i*5))s] COMPILE ERROR:"; docker logs --tail 40 $C 2>&1 | tail -40; break
  fi
  if [ $((i % 12)) -eq 0 ]; then echo "[$((i*5))s] compiling... tail:"; docker logs --tail 3 $C 2>&1 | tail -3; fi
  sleep 5
done
echo "=== $(date '+%T') DONE ==="
