#!/bin/zsh
set -u
H=${1:-http://localhost:8082}
AT=$(curl -s -X POST $H/auth/token -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"adminpass"}' | python3 -c "import json,sys;print(json.load(sys.stdin)['access_token'])")
curl -s -o /dev/null -X DELETE -H "Authorization: Bearer $AT" $H/auth/fab/v1/users/victim
curl -s -o /dev/null -X POST -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' $H/auth/fab/v1/users \
  -d '{"username":"victim","password":"victimpass","email":"v@x.com","first_name":"v","last_name":"v","roles":[{"name":"Op"}]}'
curl -s -H "Authorization: Bearer $AT" $H/auth/fab/v1/users/victim | python3 -c "import json,sys;d=json.load(sys.stdin);print('victim roles',[r['name'] for r in d.get('roles') or []],'active',d.get('active'))"
