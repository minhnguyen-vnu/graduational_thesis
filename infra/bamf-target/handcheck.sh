#!/usr/bin/env zsh
set -u
PORT=${1:-8110}
SHIM=${2:-8211}
B=http://localhost:$PORT/api/v1
J='Content-Type: application/json'
tok () { curl -s -X POST -H "$J" -d "{\"email\":\"$1\",\"password\":\"$2\"}" http://localhost:$SHIM/login | python3 -c "import json,sys;print(json.load(sys.stdin).get('token',''))" }
code () { curl -s -o /dev/null -w '%{http_code}' "$@" }
ADM=$(tok admin 'Adm1n-Bamf-Thesis-2026')
VIC=$(tok victim@example.com 'V1ctim-Bamf-Thesis-2026')
VIE=$(tok viewer@example.com 'V1ewer-Bamf-Thesis-2026')
echo "setup POST /roles handcheck-role admin $(code -X POST -H "Authorization: Bearer $ADM" -H "$J" -d '{"name":"handcheck-role","description":"hc"}' $B/roles)"
src () { code -X PATCH -H "Authorization: Bearer $1" -H "$J" -d "{\"description\":\"$2\"}" $B/roles/handcheck-role }
echo "source PATCH /roles/handcheck-role victim $(src $VIC s1)"
echo "source PATCH /roles/handcheck-role viewer $(src $VIE s2)"
echo "transition PATCH /users/victim@example.com roles=[] admin $(code -X PATCH -H "Authorization: Bearer $ADM" -H "$J" -d '{"roles":[]}' $B/users/victim@example.com)"
echo "roles now $(curl -s -H "Authorization: Bearer $ADM" $B/users/victim@example.com | python3 -c "import json,sys;print([r['name'] for r in json.load(sys.stdin).get('roles',[])])")"
echo "follow-up old token $(src $VIC s3)"
NEW=$(tok victim@example.com 'V1ctim-Bamf-Thesis-2026')
echo "relogin victim $([ -n "$NEW" ] && echo ok || echo failed)"
echo "follow-up new token $(src $NEW s4)"
echo "restore PATCH /users/victim@example.com roles=[admin] admin $(code -X PATCH -H "Authorization: Bearer $ADM" -H "$J" -d '{"roles":["admin"]}' $B/users/victim@example.com)"
