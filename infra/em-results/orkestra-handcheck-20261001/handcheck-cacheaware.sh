#!/bin/bash
API=http://localhost:3000; PW='Thesis-Pass-1234!'
VID=d2e1485c-f15f-4ce3-8434-6581733a7011
jqpy(){ python3 -c "import sys,json;d=json.load(sys.stdin);print($1)"; }
login(){ curl -s -X POST $API/v1/auth/operator/login -H 'Content-Type: application/json' -d "{\"email\":\"$1\",\"password\":\"$PW\"}" | jqpy "d.get('accessToken','')"; }
srole(){ python3 -c "import sys,base64,json;t='$1'.split('.')[1];t+='='*(-len(t)%4);print(json.loads(base64.urlsafe_b64decode(t)).get('srole'))"; }
stepup(){ curl -s -X POST $API/v1/auth/operator/me/password-confirm -H "Authorization: Bearer $1" -H 'Content-Type: application/json' -d "{\"password\":\"$PW\"}" | jqpy "d.get('accessToken','')"; }
writecode(){ local n="c-$RANDOM$RANDOM"; curl -s -o /dev/null -w '%{http_code}' -X POST $API/v1/users -H "Authorization: Bearer $1" -H 'Content-Type: application/json' -d "{\"email\":\"$n@probe.test\",\"fullName\":\"P\",\"phone\":\"+1$RANDOM$RANDOM\",\"pin\":\"1234\",\"role\":\"guest\",\"username\":\"$n\"}"; }

echo "[PRE] promote victim->administrator"
SA=$(login op@orkestra.test); SAE=$(stepup "$SA")
echo "  promote -> $(curl -s -o /dev/null -w '%{http_code}' -X PUT $API/v1/users/$VID -H "Authorization: Bearer $SAE" -H 'Content-Type: application/json' -d '{"role":"administrator"}')"
echo "[A] victim login -> V_OLD"
VOLD=$(login vic@orkestra.test); echo "  V_OLD srole=$(srole "$VOLD")"
echo "[B] source write V_OLD (expect 200) -> $(writecode "$VOLD")"
echo "[D] demote victim->guest (step-up)"
SA=$(login op@orkestra.test); SAE=$(stepup "$SA")
echo "  demote -> $(curl -s -o /dev/null -w '%{http_code}' -X PUT $API/v1/users/$VID -H "Authorization: Bearer $SAE" -H 'Content-Type: application/json' -d '{"role":"guest"}')"
T0=$(date +%s)
echo "[poll] fresh(guest) vs V_OLD write, until fresh flips to 403 (cache expiry)"
for i in $(seq 1 30); do
  el=$(( $(date +%s) - T0 ))
  VNEW=$(login vic@orkestra.test); sr=$(srole "$VNEW")
  cf=$(writecode "$VNEW"); co=$(writecode "$VOLD")
  echo "  t=${el}s fresh(srole=$sr)=$cf  old(srole=administrator)=$co"
  if [ "$cf" = "403" ]; then echo "[FLIP] fresh->403 at t=${el}s ; old=$co"; break; fi
  sleep 5
done
echo "[DONE]"
