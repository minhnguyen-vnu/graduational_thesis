#!/usr/bin/env zsh
set -u
NAME=${1:-bamf}
PORT=${2:-8110}
SHIM=${3:-8211}
PGP=${4:-15433}
RDP=${5:-16380}
T=/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/bamf-target
LOGD=${6:-$T/run-$NAME}
mkdir -p $LOGD $T/run-$NAME

$T/down.sh $NAME > /dev/null 2>&1
docker run -d --name $NAME-db -e POSTGRES_USER=bamf -e POSTGRES_PASSWORD=bamf -e POSTGRES_DB=bamf -p $PGP:5432 postgres:16-alpine > /dev/null
docker run -d --name $NAME-redis -p $RDP:6379 redis:7-alpine > /dev/null
for i in $(seq 1 60); do docker exec $NAME-db pg_isready -U bamf > /dev/null 2>&1 && break; sleep 1; done

export DATABASE_URL="postgresql+asyncpg://bamf:bamf@localhost:$PGP/bamf"
export BAMF_DATABASE_URL=$DATABASE_URL
export BAMF_REDIS_URL="redis://localhost:$RDP"
export BAMF_CA_DATA_DIR=$LOGD/ca
export BAMF_RATE_LIMIT__ENABLED=false
export BAMF_JSON_LOGS=false
export BAMF_BOOTSTRAP_ADMIN_EMAIL=admin
export BAMF_BOOTSTRAP_ADMIN_PASSWORD='Adm1n-Bamf-Thesis-2026'
mkdir -p $BAMF_CA_DATA_DIR
PY=$T/.venv/bin/python
export PYTHONPATH=$T/src/services

(cd $T/src/alembic && $PY -m alembic -c alembic.ini upgrade head) > $LOGD/migrate.log 2>&1 || { echo "migrate-failed"; exit 1; }
(cd $T/src/services && $PY -m bamf.cli.bootstrap) > $LOGD/bootstrap.log 2>&1 || { echo "bootstrap-failed"; exit 1; }

(cd $T/src/services && nohup $PY -m uvicorn bamf.api.app:app --host 127.0.0.1 --port $PORT > $LOGD/api.log 2>&1 & echo $! | tee $LOGD/api.pid > $T/run-$NAME/api.pid)
nohup $PY $T/login_shim.py $SHIM http://localhost:$PORT > $LOGD/shim.log 2>&1 &
echo $! | tee $LOGD/shim.pid > $T/run-$NAME/shim.pid

for i in $(seq 1 90); do
  [ "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$PORT/api/openapi.json)" = 200 ] && break
  sleep 1
done
curl -s http://localhost:$PORT/api/openapi.json -o $LOGD/openapi.json
echo "spec $(shasum -a 256 $LOGD/openapi.json | cut -c1-16) ops $(python3 -c "import json;print(sum(1 for p in json.load(open('$LOGD/openapi.json'))['paths'].values() for m in p if m in ('get','post','put','patch','delete')))")"

tok () { curl -s -X POST -H 'Content-Type: application/json' -d "{\"email\":\"$1\",\"password\":\"$2\"}" http://localhost:$SHIM/login | python3 -c "import json,sys;print(json.load(sys.stdin).get('token',''))" 2>/dev/null }
ADM=$(tok admin 'Adm1n-Bamf-Thesis-2026')
[ -n "$ADM" ] || { echo "admin-login-failed"; exit 1; }
mk () {
  local code=$(curl -s -o $LOGD/create-$1.json -w '%{http_code}' -X POST -H "Authorization: Bearer $ADM" -H 'Content-Type: application/json' \
    -d "{\"email\":\"$1@example.com\",\"password\":\"$2\",\"roles\":$3}" http://localhost:$PORT/api/v1/users)
  echo "user $1@example.com create $code roles $(python3 -c "import json;print(json.load(open('$LOGD/create-$1.json')).get('roles'))" 2>/dev/null)"
}
if [ "${7:-email}" = dotless ]; then
  for a in "victim V1ctim-Bamf-Thesis-2026" "viewer V1ewer-Bamf-Thesis-2026"; do
    set -- ${=a}
    (cd $T/src/services && BAMF_BOOTSTRAP_ADMIN_EMAIL=$1 BAMF_BOOTSTRAP_ADMIN_PASSWORD=$2 $PY -m bamf.cli.bootstrap) >> $LOGD/bootstrap.log 2>&1 || { echo "bootstrap-$1-failed"; exit 1; }
  done
  echo "user viewer drop-admin $(curl -s -o $LOGD/create-viewer.json -w '%{http_code}' -X PATCH -H "Authorization: Bearer $ADM" -H 'Content-Type: application/json' -d '{"roles":[]}' http://localhost:$PORT/api/v1/users/viewer)"
  for u in victim viewer; do
    echo "user $u roles $(curl -s -H "Authorization: Bearer $ADM" http://localhost:$PORT/api/v1/users/$u | python3 -c "import json,sys;print([r['name'] for r in json.load(sys.stdin).get('roles',[])])")"
  done
  ACCTS=("admin Adm1n-Bamf-Thesis-2026" "victim V1ctim-Bamf-Thesis-2026" "viewer V1ewer-Bamf-Thesis-2026")
else
  mk victim 'V1ctim-Bamf-Thesis-2026' '["admin"]'
  mk viewer 'V1ewer-Bamf-Thesis-2026' '[]'
  ACCTS=("admin Adm1n-Bamf-Thesis-2026" "victim@example.com V1ctim-Bamf-Thesis-2026" "viewer@example.com V1ewer-Bamf-Thesis-2026")
fi
for a in "${ACCTS[@]}"; do
  set -- ${=a}
  echo "login $1 $(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d "{\"email\":\"$1\",\"password\":\"$2\"}" http://localhost:$SHIM/login)"
done
