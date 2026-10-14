#!/bin/bash
API=http://localhost:3000; PW='Thesis-Pass-1234!'
VID=d2e1485c-f15f-4ce3-8434-6581733a7011
jqpy(){ python3 -c "import sys,json;d=json.load(sys.stdin);print($1)"; }
login(){ curl -s -X POST $API/v1/auth/operator/login -H 'Content-Type: application/json' -d "{\"email\":\"$1\",\"password\":\"$PW\"}" | jqpy "d.get('accessToken','')"; }
stepup(){ curl -s -X POST $API/v1/auth/operator/me/password-confirm -H "Authorization: Bearer $1" -H 'Content-Type: application/json' -d "{\"password\":\"$PW\"}" | jqpy "d.get('accessToken','')"; }
SA=$(login op@orkestra.test); SAE=$(stepup "$SA")
code=$(curl -s -o /dev/null -w '%{http_code}' -X PUT $API/v1/users/$VID -H "Authorization: Bearer $SAE" -H 'Content-Type: application/json' -d '{"role":"administrator"}')
echo "reseed victim->administrator: HTTP $code"
echo "victim role: $(curl -s -X POST $API/v1/auth/operator/login -H 'Content-Type: application/json' -d "{\"email\":\"vic@orkestra.test\",\"password\":\"$PW\"}" | jqpy "d.get('user',{}).get('role')")"
