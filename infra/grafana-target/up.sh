#!/bin/bash
N=${1:-grafana-heldout}; P=${2:-3001}; U=http://localhost:$P; A="-u admin:adminpass"
docker rm -f $N > /dev/null 2>&1
docker run -d --name $N -p $P:3000 -e GF_SECURITY_ADMIN_PASSWORD=adminpass \
  -e GF_ANALYTICS_REPORTING_ENABLED=false -e GF_ANALYTICS_CHECK_FOR_UPDATES=false \
  grafana/grafana-oss:12.1.1 > /dev/null
for i in $(seq 1 60); do [ "$(curl -s -o /dev/null -w '%{http_code}' $U/api/health)" = "200" ] && break; sleep 2; done
mk() {
  curl -s $A -X POST $U/api/admin/users -H 'content-type: application/json' \
    -d "{\"name\":\"$1\",\"login\":\"$1\",\"password\":\"$2\"}" > /dev/null
  local id=$(curl -s $A "$U/api/users/lookup?loginOrEmail=$1" | python3 -c 'import json,sys;print(json.load(sys.stdin)["id"])')
  curl -s $A -X PATCH $U/api/org/users/$id -H 'content-type: application/json' -d "{\"role\":\"$3\"}" > /dev/null
}
mk victim victimpass Admin
mk viewer viewerpass Viewer
curl -s $A "$U/api/org/users" | python3 -c '
import json,sys
for u in json.load(sys.stdin): print(u["login"], "id", u["userId"], "role", u["role"])'
for u in admin:adminpass victim:victimpass viewer:viewerpass; do
  printf "login ${u%%:*} "; curl -s -o /dev/null -w "%{http_code}\n" -X POST $U/login -H 'content-type: application/json' -d "{\"user\":\"${u%%:*}\",\"password\":\"${u##*:}\"}"
done
