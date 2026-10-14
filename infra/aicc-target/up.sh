#!/usr/bin/env zsh
set -u
NAME=${1:-aicc}
PORT=${2:-8097}
NET=$NAME-net
B=http://localhost:$PORT/api/v1
docker rm -f $NAME $NAME-db > /dev/null 2>&1
docker network rm $NET > /dev/null 2>&1
docker network create $NET > /dev/null
docker run -d --name $NAME-db --network $NET -e POSTGRES_USER=aicc -e POSTGRES_PASSWORD=aiccdbpass -e POSTGRES_DB=aicc postgres:18 > /dev/null || { echo "db FAIL"; exit 1 }
for i in $(seq 1 60); do docker exec $NAME-db pg_isready -U aicc -d aicc > /dev/null 2>&1 && break; sleep 1; done
docker run -d --name $NAME --network $NET -p $PORT:8080 \
  -e AICC_ENV=prod \
  -e AICC_DATABASE_URL="host=$NAME-db port=5432 dbname=aicc user=aicc password=aiccdbpass sslmode=disable" \
  -e AICC_PROVIDER=openai -e OPENAI_API_KEY=not-a-key \
  -e AICC_SEED=demo -e AICC_SEED_PASSWORD=aiccseedpass \
  aicc-target:47116cf6 > /dev/null || { echo "app FAIL"; exit 1 }
for i in $(seq 1 60); do
  [ "$(curl -s -o /dev/null -w '%{http_code}' $B/auth/me)" != "000" ] && break
  sleep 1
done
echo "me-unauth $(curl -s -o /dev/null -w '%{http_code}' $B/auth/me)"
J='Content-Type: application/json'
C='X-AICC-Csrf: 1'
CJ=$(mktemp)
echo "login admin $(curl -s -o /dev/null -w '%{http_code}' -c $CJ -H "$J" -d '{"username":"admin","password":"aiccseedpass"}' $B/auth/login)"
for u in victim:ADMIN viewer:AGENT; do
  n=${u%%:*}; r=${u##*:}
  echo "create $n $r $(curl -s -o /dev/null -w '%{http_code}' -b $CJ -H "$J" -H "$C" -d "{\"username\":\"$n\",\"displayName\":\"$n\",\"role\":\"$r\",\"password\":\"${n}passw0rd\"}" $B/users)"
done
curl -s -b $CJ $B/users | python3 -c '
import json,sys
d=json.load(sys.stdin)
items=d if isinstance(d,list) else d.get("items") or d.get("data") or []
for u in items:
    if u.get("username") in ("admin","victim","viewer"): print("user", u.get("username"), u.get("userId"), u.get("role"), u.get("status"))
'
for u in victim viewer; do
  echo "login $u $(curl -s -o /dev/null -w '%{http_code}' -H "$J" -d "{\"username\":\"$u\",\"password\":\"${u}passw0rd\"}" $B/auth/login)"
done
rm -f $CJ
