#!/usr/bin/env zsh
set -u
B=http://localhost:4444
COMPOSE=/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/magic-target/magic/docker-compose.yml

THROTTLE=/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/em-results/magic-heldout-20261014/throttles-highlimit.hl
docker compose -f $COMPOSE down -v >/dev/null 2>&1
docker compose -f $COMPOSE up -d backend >/dev/null 2>&1 || { echo "RESEED_FAIL up"; exit 1; }
for i in $(seq 1 60); do docker cp "$THROTTLE" magic_backend:/magic/files/system/magic.startup/throttles.hl >/dev/null 2>&1 && break; sleep 1; done
docker compose -f $COMPOSE restart backend >/dev/null 2>&1 || { echo "RESEED_FAIL restart"; exit 1; }

auth() { curl -s -G "$B/magic/system/auth/authenticate" --data-urlencode "username=$1" --data-urlencode "password=$2" | python3 -c "import sys,json;print(json.load(sys.stdin).get('ticket',''))" 2>/dev/null; }
post() { curl -s -o /dev/null -w '%{http_code}' -X POST "$B$1" -H "Authorization: Bearer $2" -H 'Content-Type: application/json' -d "$3"; }

T0=""
for i in $(seq 1 120); do T0=$(auth root root); [ -n "$T0" ] && break; sleep 1; done
[ -n "$T0" ] || { echo "RESEED_FAIL preauth"; exit 1; }
curl -s -o /dev/null -X POST "$B/magic/system/config/setup" -H "Authorization: Bearer $T0" -H 'Content-Type: application/json' -d '{"username":"root","password":"RootSetup123","is_hashed":false,"name":"Root","email":"root@local.test","subscribe":false}'
sleep 2
TA=$(auth root RootSetup123)
[ -n "$TA" ] || { echo "RESEED_FAIL adminauth"; exit 1; }
post /magic/system/magic/users "$TA" '{"username":"victim","password":"VictimPass123"}' >/dev/null
post /magic/system/magic/users "$TA" '{"username":"plain","password":"PlainPass123"}' >/dev/null
post /magic/system/magic/users_roles "$TA" '{"role":"root","user":"victim"}' >/dev/null
post /magic/system/magic/roles "$TA" '{"name":"src_role","description":"init"}' >/dev/null

TV=$(auth victim VictimPass123)
VROLE=$(echo "$TV" | cut -d. -f2 | python3 -c "import sys,base64,json;s=sys.stdin.read().strip();s+='='*(-len(s)%4);print(json.loads(base64.urlsafe_b64decode(s)).get('role'))" 2>/dev/null)
echo "$VROLE" | grep -q root || { echo "RESEED_FAIL victim-role=$VROLE"; exit 1; }
echo "RESEED_OK victim_role=$VROLE"
