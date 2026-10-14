#!/usr/bin/env zsh
set -u
PORT=${1:-8065}
U=http://localhost:$PORT/api/v4
tok () { curl -s -D - -o /dev/null -X POST $U/users/login -H 'Content-Type: application/json' -d "{\"login_id\":\"$1\",\"password\":\"$2\"}" | awk 'tolower($1)=="token:"{print $2}' | tr -d '\r' }
code () { curl -s -o /dev/null -w '%{http_code}' -X $1 "$U$2" -H "Authorization: Bearer $3" -H 'Content-Type: application/json' ${4:+-d} ${4:-} }
ADMIN=$(tok admin adminpass); OLD=$(tok victim victimpass); VIEW=$(tok viewer viewerpass)
VID=$(curl -s $U/users/username/victim -H "Authorization: Bearer $ADMIN" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
TEAM=$(curl -s $U/teams/name/thesis -H "Authorization: Bearer $ADMIN" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "$(date +%H:%M:%S) team $TEAM victim $VID"
echo "victim-old  PUT teams/patch   $(code PUT /teams/$TEAM/patch $OLD '{"display_name":"a1"}')"
echo "viewer      PUT teams/patch   $(code PUT /teams/$TEAM/patch $VIEW '{"display_name":"a2"}')"
echo "victim-old  GET config        $(code GET /config $OLD)"
echo "viewer      GET config        $(code GET /config $VIEW)"
echo "admin       PUT users/roles   $(code PUT /users/$VID/roles $ADMIN '{"roles":"system_user"}')"
echo "roles now   $(curl -s $U/users/$VID -H "Authorization: Bearer $ADMIN" | python3 -c "import json,sys; print(json.load(sys.stdin)['roles'])")"
echo "victim-old  PUT teams/patch   $(code PUT /teams/$TEAM/patch $OLD '{"display_name":"a3"}')"
echo "victim-old  GET config        $(code GET /config $OLD)"
NEW=$(tok victim victimpass)
echo "victim-new  PUT teams/patch   $(code PUT /teams/$TEAM/patch $NEW '{"display_name":"a4"}')"
echo "victim-new  GET config        $(code GET /config $NEW)"
