#!/usr/bin/env zsh
set -u
APP=/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/raouf-target/app
B=http://localhost:3000
PGUP="UPDATE user_role_assignments ura SET role_id=(CASE u.email WHEN 'superadmin@store.local' THEN 1 WHEN 'admin@store.local' THEN 2 WHEN 'customer@store.local' THEN 3 END), updated_at=now() FROM users u WHERE u.id=ura.user_id AND u.email IN ('superadmin@store.local','admin@store.local','customer@store.local');"

( cd $APP && npm run db:seed ) >/tmp/raouf-reseed-seed.out 2>&1 || { echo "RESEED_FAIL db:seed"; exit 1; }
docker exec postgres-db psql -U postgres -d my_database -c "$PGUP" >/tmp/raouf-reseed-roles.out 2>&1 || { echo "RESEED_FAIL roles"; exit 1; }

rotate() {
  local em=$1 pw=$2
  local t1=$(curl -s -X POST "$B/v1/authentication/login" -H 'Content-Type: application/json' -d "{\"email\":\"$em\",\"password\":\"$pw\"}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('accessToken',''))" 2>/dev/null)
  [ -n "$t1" ] || { echo "RESEED_FAIL login $em"; return 1; }
  local code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$B/v1/authentication/change-password" -H "Authorization: Bearer $t1" -H 'Content-Type: application/json' -d "{\"currentPassword\":\"$pw\",\"newPassword\":\"${pw}x\"}")
  [ "$code" = 200 ] || { echo "RESEED_FAIL chpw $em http=$code"; return 1; }
}
rotate superadmin@store.local 'SuperAdmin123!' || exit 1
rotate admin@store.local 'Admin123!' || exit 1
rotate customer@store.local 'Customer123!' || exit 1

VROLE=$(curl -s -X POST "$B/v1/authentication/login" -H 'Content-Type: application/json' -d '{"email":"admin@store.local","password":"Admin123!x"}' | python3 -c "import sys,base64,json;t=json.load(sys.stdin).get('accessToken','');p=t.split('.')[1];p+='='*(-len(p)%4);print(json.loads(base64.urlsafe_b64decode(p)).get('role'))" 2>/dev/null)
OROLE=$(curl -s -X POST "$B/v1/authentication/login" -H 'Content-Type: application/json' -d '{"email":"superadmin@store.local","password":"SuperAdmin123!x"}' | python3 -c "import sys,base64,json;t=json.load(sys.stdin).get('accessToken','');p=t.split('.')[1];p+='='*(-len(p)%4);print(json.loads(base64.urlsafe_b64decode(p)).get('role'))" 2>/dev/null)
[ "$VROLE" = ADMIN ] && [ "$OROLE" = SUPER_ADMIN ] || { echo "RESEED_FAIL roles-after victim=$VROLE operator=$OROLE"; exit 1; }
echo "RESEED_OK victim_role=$VROLE operator_role=$OROLE"
