#!/bin/zsh
set -u
H=$1
tok() { curl -s -o /tmp/tk.$$ -w "%{http_code}" -X POST $H/auth/token -H 'Content-Type: application/json' \
  -d "{\"username\":\"$1\",\"password\":\"$2\"}"; }
AT=$(curl -s -X POST $H/auth/token -H 'Content-Type: application/json' -d '{"username":"admin","password":"adminpass"}' \
  | python3 -c "import json,sys;print(json.load(sys.stdin)['access_token'])")
curl -s -o /dev/null -X DELETE -H "Authorization: Bearer $AT" $H/auth/fab/v1/users/victim
CR=$(curl -s -o /tmp/cr.$$ -w "%{http_code}" -X POST -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' \
  $H/auth/fab/v1/users -d '{"username":"victim","password":"victimpass","email":"v@x.com","first_name":"v","last_name":"v","roles":[{"name":"Op"}]}')
echo "create victim: $CR"
VC=$(tok victim victimpass); VT=$(python3 -c "import json;print(json.load(open('/tmp/tk.$$'))['access_token'])" 2>/dev/null)
echo "victim login before: $VC"
S=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Authorization: Bearer $VT" -H 'Content-Type: application/json' \
  $H/api/v2/variables -d '{"key":"probe_src","value":"1","description":""}')
echo "source  POST /api/v2/variables (stale token, before transition): $S"
TR=$(curl -s -o /tmp/tr.$$ -w "%{http_code}" -X PATCH -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' \
  "$H/auth/fab/v1/users/victim?update_mask=active" -d '{"active":false}')
echo "transition PATCH /auth/fab/v1/users/victim active=false: $TR"
echo "  active now: $(python3 -c "import json;print(json.load(open('/tmp/tr.$$')).get('active'))" 2>/dev/null)"
F=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Authorization: Bearer $VT" -H 'Content-Type: application/json' \
  $H/api/v2/variables -d '{"key":"probe_follow","value":"1","description":""}')
echo "follow-up POST /api/v2/variables (same stale token): $F"
FC=$(tok victim victimpass)
echo "D1 fresh login victim: $FC"
rm -f /tmp/tk.$$ /tmp/cr.$$ /tmp/tr.$$
