#!/usr/bin/env zsh
set -u
D=${0:A:h}
tok () { python3 -c 'import json,sys;print(json.load(sys.stdin)["token"])'; }
run () {
  local port=$1 out=$2
  curl -s -o /dev/null -X POST http://localhost:$port/reset
  python3 $D/../capture_proxy.py 8280 localhost $port $out &
  local px=$!
  for i in $(seq 1 20); do nc -z localhost 8280 2>/dev/null && break; sleep 0.3; done
  local P=http://localhost:8280 J='Content-Type: application/json'
  local a=$(curl -s -H $J -d '{"username":"alice","password":"alicepass"}' $P/auth/login | tok)
  local s=$(curl -s -H $J -d '{"username":"superadmin","password":"superpass"}' $P/auth/login | tok)
  curl -s -o /dev/null -X DELETE -H "Authorization: Bearer $a" $P/reports/1
  curl -s -o /dev/null -X PUT -H $J -H "Authorization: Bearer $s" -d '{"role":"VIEWER"}' $P/users/alice/role
  curl -s -o /dev/null -X DELETE -H "Authorization: Bearer $a" $P/reports/2
  local a2=$(curl -s -H $J -d '{"username":"alice","password":"alicepass"}' $P/auth/login | tok)
  curl -s -o /dev/null -X DELETE -H "Authorization: Bearer $a2" $P/reports/3
  kill $px
  wait $px 2>/dev/null
  curl -s -o /dev/null -X POST http://localhost:$port/reset
}
run 8080 $D/vuln.jsonl
run 8081 $D/fixed.jsonl
python3 $D/../audit_traffic.py $D/vuln.jsonl $D/fixed.jsonl
