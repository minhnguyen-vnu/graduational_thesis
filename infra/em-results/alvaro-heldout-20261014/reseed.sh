#!/usr/bin/env zsh
set -u
B=http://localhost:3000
PW='Passw0rd1'

reg() { curl -s -o /dev/null -X POST "$B/user" -H 'Content-Type: application/json' -d "{\"email\":\"$1\",\"password\":\"$PW\"}"; }
reg admin@test.com
reg victim@test.com
reg plain@test.com

docker exec alvaro-pg psql -U alvaro -d ecommerce -c "UPDATE \"User\" SET role='ADMIN' WHERE email IN ('admin@test.com','victim@test.com'); UPDATE \"User\" SET role='USER' WHERE email='plain@test.com';" >/tmp/alvaro-reseed-sql.out 2>&1 || { echo "RESEED_FAIL sql"; exit 1; }

VR=$(curl -s -X POST "$B/login" -H 'Content-Type: application/json' -d '{"email":"victim@test.com","password":"Passw0rd1"}' | python3 -c "import sys,base64,json;t=json.load(sys.stdin).get('accessToken','');p=t.split('.')[1] if t else '';p+='='*(-len(p)%4);print(json.loads(base64.urlsafe_b64decode(p)).get('userRole') if p else '')" 2>/dev/null)
OR=$(curl -s -X POST "$B/login" -H 'Content-Type: application/json' -d '{"email":"admin@test.com","password":"Passw0rd1"}' | python3 -c "import sys,base64,json;t=json.load(sys.stdin).get('accessToken','');p=t.split('.')[1] if t else '';p+='='*(-len(p)%4);print(json.loads(base64.urlsafe_b64decode(p)).get('userRole') if p else '')" 2>/dev/null)
[ "$VR" = ADMIN ] && [ "$OR" = ADMIN ] || { echo "RESEED_FAIL roles victim=$VR operator=$OR"; exit 1; }
echo "RESEED_OK victim_role=$VR operator_role=$OR"
