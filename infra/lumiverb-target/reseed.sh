#!/bin/bash
set -e
cd "$(dirname "$0")/repo"
pkill -f "uvicorn src.server.api.main" 2>/dev/null || true
sleep 2
docker exec lumiverb-postgres psql -U app -d postgres \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='control_plane' AND pid<>pg_backend_pid();" \
  -c "DROP DATABASE IF EXISTS control_plane;" \
  -c "CREATE DATABASE control_plane OWNER app;" >/dev/null
bash scripts/migrate.sh >/dev/null 2>&1
set -a; . ./.env.local; set +a
nohup uv run uvicorn src.server.api.main:app --host 127.0.0.1 --port 8000 > ../logs/server-vuln.log 2>&1 &
disown
ok=0
for i in $(seq 1 25); do sleep 2; if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then ok=1; break; fi; done
[ "$ok" = 1 ] || { echo "server did not come up"; exit 1; }
ADMIN_KEY=$(python3 -I -c "print([l.split('=',1)[1].strip() for l in open('.env.local') if l.startswith('ADMIN_KEY=')][0])")
AK=$(curl -s -X POST -H "Authorization: Bearer $ADMIN_KEY" -H 'Content-Type: application/json' \
  -d '{"name":"default","plan":"free"}' http://127.0.0.1:8000/v1/admin/tenants \
  | python3 -I -c "import sys,json;print(json.load(sys.stdin)['api_key'])")
PW="Thesis-Pass-1234"
for u in "victim@thesis.test:admin" "operator@thesis.test:admin" "viewer@thesis.test:viewer"; do
  em=${u%:*}; rl=${u#*:}
  curl -s -o /dev/null -X POST -H "Authorization: Bearer $AK" -H 'Content-Type: application/json' \
    -d "{\"email\":\"$em\",\"password\":\"$PW\",\"role\":\"$rl\"}" http://127.0.0.1:8000/v1/users
done
role=$(curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"email":"victim@thesis.test","password":"Thesis-Pass-1234"}' http://127.0.0.1:8000/v1/auth/login \
  | python3 -I -c "import sys,json,base64;t=json.load(sys.stdin).get('access_token','');p=t.split('.')[1];p+='='*(-len(p)%4);print(json.loads(base64.urlsafe_b64decode(p)).get('role'))")
echo "reseed done; victim role=$role"
