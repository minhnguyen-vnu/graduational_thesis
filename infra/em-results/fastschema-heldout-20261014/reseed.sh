#!/usr/bin/env zsh
set -u
B=http://localhost:8008
IMG=ghcr.io/fastschema/fastschema@sha256:e1ce4c3f45e9c0602124fcc2d5aedba3287bd7a23929c116fb18144640cc2bba

docker rm -f fastschema >/dev/null 2>&1
docker volume rm fastschema_data >/dev/null 2>&1
docker run -d --name fastschema -p 8008:8000 -v fastschema_data:/fastschema/data "$IMG" >/dev/null 2>&1 || { echo "RESEED_FAIL run"; exit 1; }

code=000
for i in $(seq 1 90); do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "$B/" 2>/dev/null)
  [ "$code" != "000" ] && [ -n "$code" ] && break
  sleep 1
done
[ "$code" != "000" ] || { echo "RESEED_FAIL notlistening"; exit 1; }
TOKEN=$(docker logs fastschema 2>&1 | grep -oE "token=[A-Za-z0-9]+" | tail -1 | cut -d= -f2)
[ -n "$TOKEN" ] || { echo "RESEED_FAIL token"; exit 1; }
curl -s -X POST "$B/api/setup" -H 'Content-Type: application/json' -d "{\"token\":\"$TOKEN\",\"username\":\"admin\",\"email\":\"admin@local.test\",\"password\":\"AdminPass123\"}" | grep -q '"data":true' || { echo "RESEED_FAIL setup"; exit 1; }

login() { curl -s -X POST "$B/api/auth/local/login" -H 'Content-Type: application/json' -d "{\"login\":\"$1\",\"password\":\"$2\"}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('data',{}).get('token',''))" 2>/dev/null; }
TA=$(login admin AdminPass123)
[ -n "$TA" ] || { echo "RESEED_FAIL adminlogin"; exit 1; }
R=$(curl -s -G "$B/api/role" -H "Authorization: Bearer $TA" | python3 -c "import sys,json;d=json.load(sys.stdin);print(json.dumps({r['name']:r['id'] for r in d['data']}))" 2>/dev/null)
ADMINID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['Admin'])" 2>/dev/null)
USERID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['User'])" 2>/dev/null)
[ -n "$ADMINID" ] && [ -n "$USERID" ] || { echo "RESEED_FAIL roleids"; exit 1; }

curl -s -o /dev/null -X POST "$B/api/content/user" -H "Authorization: Bearer $TA" -H 'Content-Type: application/json' -d "{\"username\":\"victim\",\"password\":\"VictimPass123\",\"email\":\"victim@local.test\",\"provider\":\"local\",\"active\":true,\"roles\":[{\"id\":\"$ADMINID\"}]}"
curl -s -o /dev/null -X POST "$B/api/content/user" -H "Authorization: Bearer $TA" -H 'Content-Type: application/json' -d "{\"username\":\"plain\",\"password\":\"PlainPass123\",\"email\":\"plain@local.test\",\"provider\":\"local\",\"active\":true,\"roles\":[{\"id\":\"$USERID\"}]}"

VR=$(login victim VictimPass123 | cut -d. -f2 | python3 -c "import sys,base64,json;s=sys.stdin.read().strip();s+='='*(-len(s)%4);u=json.loads(base64.urlsafe_b64decode(s))['user'];print(json.dumps(u.get('role_ids')))" 2>/dev/null)
echo "$VR" | grep -q "$ADMINID" || { echo "RESEED_FAIL victim-not-admin $VR"; exit 1; }
echo "RESEED_OK victim_role_ids=$VR admin_role=$ADMINID user_role=$USERID"
