#!/bin/bash
cd /Users/minhnguyen/IdeaProjects/graduational-thesis/infra/artifact-keeper-target/src
echo "=== $(date '+%T') docker compose up --build backend ==="
docker compose -f docker-compose.local-dev.yml -f docker-compose.thesis.yml up -d --build backend 2>&1 | tail -25
echo "=== $(date '+%T') image built + container started; waiting for app compile + :8080 ==="
for i in $(seq 1 540); do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/health 2>/dev/null)
  if [ "$code" != "000" ] && [ -n "$code" ]; then echo "[$((i*5))s] SERVER UP /health http=$code"; break; fi
  if docker logs artifact-keeper-dev-backend 2>&1 | grep -qiE 'error\[E[0-9]|error: could not compile|error: linking|thread .main. panicked|Error: '; then
    echo "[$((i*5))s] BUILD/RUN ERROR:"; docker logs --tail 40 artifact-keeper-dev-backend 2>&1 | tail -40; break
  fi
  if [ $((i % 12)) -eq 0 ]; then echo "[$((i*5))s] still compiling... last log:"; docker logs --tail 2 artifact-keeper-dev-backend 2>&1 | tail -2; fi
  sleep 5
done
echo "=== $(date '+%T') DONE ==="
