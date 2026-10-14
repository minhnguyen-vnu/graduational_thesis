#!/usr/bin/env zsh
set -u
NAME=${1:-mattermost}
PORT=${2:-8065}
IMAGE=mattermost/mattermost-preview:11.11.1
U=http://localhost:$PORT/api/v4
docker rm -f $NAME > /dev/null 2>&1
docker run -d --platform linux/amd64 --name $NAME -p $PORT:8065 $IMAGE > /dev/null || { echo "docker run failed"; exit 1 }
for i in {1..90}; do
  [ "$(curl -s -o /dev/null -w '%{http_code}' $U/system/ping)" = 200 ] && break
  sleep 2
done
[ "$(curl -s -o /dev/null -w '%{http_code}' $U/system/ping)" = 200 ] || { echo "not healthy"; exit 1 }
mk () { curl -s -X POST $U/users -H 'Content-Type: application/json' $3 -d "{\"email\":\"$1@example.com\",\"username\":\"$1\",\"password\":\"$2\"}" > /dev/null }
mk admin adminpass ""
TOK=$(curl -s -D - -o /dev/null -X POST $U/users/login -H 'Content-Type: application/json' -d '{"login_id":"admin","password":"adminpass"}' | awk 'tolower($1)=="token:"{print $2}' | tr -d '\r')
[ -n "$TOK" ] || { echo "admin login failed"; exit 1 }
A=(-H "Authorization: Bearer $TOK" -H 'Content-Type: application/json')
curl -s -X POST $U/users "${A[@]}" -d '{"email":"victim@example.com","username":"victim","password":"victimpass"}' > /dev/null
curl -s -X POST $U/users "${A[@]}" -d '{"email":"viewer@example.com","username":"viewer","password":"viewerpass"}' > /dev/null
id () { curl -s $U/users/username/$1 "${A[@]}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))" }
VID=$(id victim); WID=$(id viewer); AID=$(id admin)
curl -s -o /dev/null -X PUT $U/users/$VID/roles "${A[@]}" -d '{"roles":"system_user system_admin"}'
TEAM=$(curl -s -X POST $U/teams "${A[@]}" -d '{"name":"thesis","display_name":"thesis","type":"O"}' | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))")
for u in $VID $WID; do
  curl -s -o /dev/null -X POST $U/teams/$TEAM/members "${A[@]}" -d "{\"team_id\":\"$TEAM\",\"user_id\":\"$u\"}"
done
for n in admin victim viewer; do
  r=$(curl -s $U/users/username/$n "${A[@]}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id',''), d.get('roles',''))")
  echo "$n id-roles $r"
done
echo "team $TEAM"
for n in admin:adminpass victim:victimpass viewer:viewerpass; do
  echo "login ${n%%:*} $(curl -s -o /dev/null -w '%{http_code}' -X POST $U/users/login -H 'Content-Type: application/json' -d "{\"login_id\":\"${n%%:*}\",\"password\":\"${n##*:}\"}")"
done
