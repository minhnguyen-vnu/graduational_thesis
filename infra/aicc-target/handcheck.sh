#!/usr/bin/env zsh
set -u
B=http://localhost:${1:-8097}/api/v1
J='Content-Type: application/json'
C='X-AICC-Csrf: 1'
D=$(mktemp -d)
login () { curl -s -o /dev/null -w '%{http_code}' -c $D/$1 -H "$J" -d "{\"username\":\"$2\",\"password\":\"$3\"}" $B/auth/login }
n=0
src () { n=$((n+1)); curl -s -o /dev/null -w '%{http_code}' -b $D/$1 -H "$J" -H "$C" -d "{\"username\":\"probe$n\",\"displayName\":\"probe$n\",\"role\":\"ADMIN\",\"password\":\"probepassw0rd\"}" $B/users }
echo "login admin $(login admin admin aiccseedpass) victim $(login v1 victim victimpassw0rd) viewer $(login w viewer viewerpassw0rd)"
VID=$(curl -s -b $D/admin $B/users | python3 -c 'import json,sys; print([u["userId"] for u in json.load(sys.stdin)["items"] if u["username"]=="victim"][0])')
echo "victim id $VID"
echo "nguon POST /users, cookie cu victim: $(src v1)"
echo "nguon POST /users, viewer: $(src w)"
echo "transition PUT /users/$VID role=AGENT: $(curl -s -o $D/t.json -w '%{http_code}' -X PUT -b $D/admin -H "$J" -H "$C" -d '{"username":"victim","displayName":"victim","role":"AGENT","status":"ACTIVE"}' $B/users/$VID) $(head -c 200 $D/t.json)"
echo "follow-up, cookie cu victim: $(src v1)"
echo "dang nhap lai victim $(login v2 victim victimpassw0rd)"
echo "follow-up, cookie moi victim: $(src v2)"
echo "me, cookie cu victim: $(curl -s -b $D/v1 $B/auth/me | head -c 200)"
rm -rf $D
