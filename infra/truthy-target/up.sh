#!/usr/bin/env zsh
set -u
NAME=${1:-truthy}
PORT=${2:-8100}
NET=$NAME-net
B=http://localhost:$PORT
IMG=truthy-target:9b9a61be
docker rm -f $NAME $NAME-db $NAME-redis > /dev/null 2>&1
docker network rm $NET > /dev/null 2>&1
docker network create $NET > /dev/null
docker run -d --name $NAME-db --network $NET -e POSTGRES_USER=truthy -e POSTGRES_PASSWORD=truthydbpass -e POSTGRES_DB=truthy  postgres:16-alpine > /dev/null || { echo "db FAIL"; exit 1 }
docker run -d --name $NAME-redis --network $NET redis:7-alpine > /dev/null || { echo "redis FAIL"; exit 1 }
for i in $(seq 1 60); do docker exec $NAME-db pg_isready -U truthy -d truthy > /dev/null 2>&1 && break; sleep 1; done
docker run -d --name $NAME --network $NET -p $PORT:7777 \
  -e NODE_ENV=development -e PORT=7777 \
  -e DB_HOST=$NAME-db -e DB_PORT=5432 -e DB_USERNAME=truthy -e DB_PASSWORD=truthydbpass -e DB_DATABASE_NAME=truthy \
  -e REDIS_HOST=$NAME-redis -e REDIS_PORT=6379 \
  -e THROTTLE_LIMIT=1000000 -e NODE_CONFIG='{"throttle":{"login":{"limit":1000000}}}' \
  $IMG sh -c "yarn migrate && yarn seed && node dist/main" > /dev/null || { echo "app FAIL"; exit 1 }
for i in $(seq 1 180); do
  [ "$(curl -s -o /dev/null -w '%{http_code}' $B/api-docs-json)" = "200" ] && break
  sleep 1
done
echo "spec $(curl -s -o /dev/null -w '%{http_code}' $B/api-docs-json)"
J='Content-Type: application/json'
CJ=$(mktemp)
echo "login admin $(curl -s -o /dev/null -w '%{http_code}' -c $CJ -H "$J" -d '{"username":"admin","password":"Truthy@123","remember":true}' $B/auth/login)"
for u in victim:1 viewer:2; do
  n=${u%%:*}; r=${u##*:}
  P="${(C)n}@123"
  echo "register $n $(curl -s -o /dev/null -w '%{http_code}' -H "$J" -d "{\"username\":\"$n\",\"email\":\"$n@truthy.test\",\"password\":\"$P\",\"name\":\"$n\"}" $B/auth/register)"
  tok=$(docker exec $NAME-db psql -U truthy -d truthy -tAc "select token from \"user\" where username='$n'")
  echo "activate $n $(curl -s -o /dev/null -w '%{http_code}' "$B/auth/activate-account?token=$tok")"
  id=$(docker exec $NAME-db psql -U truthy -d truthy -tAc "select id from \"user\" where username='$n'")
  echo "setrole $n $r $(curl -s -o /dev/null -w '%{http_code}' -X PUT -b $CJ -H "$J" -d "{\"roleId\":$r}" $B/users/$id)"
done
docker exec $NAME-db psql -U truthy -d truthy -tAF' ' -c "select 'user', u.username, u.id, r.name, u.status from \"user\" u join role r on r.id = u.\"roleId\" where u.username in ('admin','victim','viewer') order by u.id"
for u in admin:Truthy@123 victim:Victim@123 viewer:Viewer@123; do
  echo "login ${u%%:*} $(curl -s -o /dev/null -w '%{http_code}' -H "$J" -d "{\"username\":\"${u%%:*}\",\"password\":\"${u##*:}\",\"remember\":true}" $B/auth/login)"
done
rm -f $CJ
