#!/usr/bin/env bash
# Can the MR-A1 triple's PRECONDITION be rebuilt through the target's own API, with no /thesis/reset?
#
# Measured by hand 2026-08-24, before any code was written. Full record and reading:
# docs/measurement-self-provisioning-2026-08-24.md
#
# Part A -- the generic chain (restore the VICTIM), the Tier-1/Tier-2 failure mode.
# Part B -- restore the OPERATOR, which is pyLoad's ACTUAL failure mode: all 40 VOID attempts in
#           infra/em-results/tier2b-inference-trials are 200/401/200, ie the victim kept its
#           privilege and the operators lost theirs. Part B reproduces that exact signature first,
#           so the simulated state can be shown to be faithful, and only then applies the rescue.
# Part C -- add_user as an alternative provisioning route, and the ceiling when NO admin survives.
#
# Nothing here asserts an expected outcome: it prints what the SUT did.
set -u
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

role_of(){ docker exec "$1" python -c "
import sqlite3;c=sqlite3.connect('/data/data/pyload.db').cursor()
c.execute('SELECT role FROM users WHERE name=?',('$2',));r=c.fetchone();print(r[0] if r else 'NO_ROW')" 2>/dev/null; }
login(){ curl -s -o /dev/null -c "$3" -X POST -d "username=$1&password=$2" "http://localhost:$4/login"; }
# guarded, non-consuming write; /json/status is one of the 8 sources the tool itself selected
src(){ curl -s -o /dev/null -w "%{http_code}" -b "$1" -X POST -H "Content-Type: application/json" \
       -d '{}' "http://localhost:$2/json/status"; }
setperm(){ curl -s -o /dev/null -w "%{http_code}" -b "$1" -X POST \
       "http://localhost:$2/api/set_user_permission?user=$3&permission=0&role=$4"; }
seed(){ docker exec "$1" python /seed_users.py /data/data/pyload.db >/dev/null 2>&1
        docker exec "$1" python -c "
import sqlite3;d=sqlite3.connect('/data/data/pyload.db');d.execute(\"UPDATE users SET role=0 WHERE name='pyload'\");d.commit()" 2>/dev/null; }

partA(){
 local port=$1 c=$2 label=$3
 echo "──── A. restore the VICTIM — $label (:$port) ────"
 seed "$c"
 local SJ="$TMP/A-s-$port.jar"; login superadmin superpass "$SJ" "$port"
 echo "  [1] simulate a search that demoted the victim: -> HTTP $(setperm "$SJ" "$port" alice 1), alice role=$(role_of $c alice)"
 local A0="$TMP/A-a0-$port.jar"; login alice alicepass "$A0" "$port"
 echo "  [2] alice logs in fresh, tries the guarded source -> HTTP $(src "$A0" "$port")   (the dead end today)"
 echo "  [3] superadmin PROMOTES alice back -> HTTP $(setperm "$SJ" "$port" alice 0), alice role=$(role_of $c alice)"
 local AJ="$TMP/A-a-$port.jar"; login alice alicepass "$AJ" "$port"
 local s1 s2 s3; s1=$(src "$AJ" "$port"); s2=$(setperm "$SJ" "$port" alice 1); s3=$(src "$AJ" "$port")
 echo "  [4] triple with the SAME replayed cookie -> $s1 / $s2 / $s3"
 echo
}

partB(){
 local port=$1 c=$2 label=$3
 echo "──── B. restore the OPERATOR — $label (:$port) ────"
 seed "$c"
 local PJ="$TMP/B-p-$port.jar"; login pyload pyload "$PJ" "$port"
 setperm "$PJ" "$port" alice 1 >/dev/null; setperm "$PJ" "$port" superadmin 1 >/dev/null
 echo "  corrupted state: alice=$(role_of $c alice) superadmin=$(role_of $c superadmin) pyload=$(role_of $c pyload)"
 local P2="$TMP/B-p2-$port.jar"; login pyload pyload "$P2" "$port"
 local AJ="$TMP/B-a-$port.jar";  login alice alicepass "$AJ" "$port"
 local a b d; a=$(src "$P2" "$port"); b=$(setperm "$AJ" "$port" pyload 1); d=$(src "$P2" "$port")
 echo "  [reproduce] victim=pyload operator=alice -> $a/$b/$d   (real logs: 200/401/200, 40/40)"
 docker exec "$c" python -c "
import sqlite3;d=sqlite3.connect('/data/data/pyload.db');d.execute(\"UPDATE users SET role=0 WHERE name='pyload'\");d.commit()" 2>/dev/null
 local P3="$TMP/B-p3-$port.jar"; login pyload pyload "$P3" "$port"   # FRESH login: not a stale session
 echo "  [rescue] surviving admin 'pyload' PROMOTES operator alice -> HTTP $(setperm "$P3" "$port" alice 0), alice role=$(role_of $c alice)"
 local PV="$TMP/B-pv-$port.jar"; login pyload pyload "$PV" "$port"
 local AO="$TMP/B-ao-$port.jar"; login alice alicepass "$AO" "$port"
 local s1 s2 s3; s1=$(src "$PV" "$port"); s2=$(setperm "$AO" "$port" pyload 1); s3=$(src "$PV" "$port")
 echo "  [triple] -> $s1 / $s2 / $s3   (pyload role now $(role_of $c pyload))"
 seed "$c"; echo
}

partC(){
 echo "──── C. add_user, and the ceiling ────"
 seed pyload-vuln
 local SJ="$TMP/C-s.jar"; login superadmin superpass "$SJ" 8090
 local NEW="victim$RANDOM"
 echo "  add_user role=0 -> HTTP $(curl -s -o /dev/null -w '%{http_code}' -b "$SJ" -X POST \
    "http://localhost:8090/api/add_user?user=$NEW&newpw=pw123&role=0&perms=0")   db role=$(role_of pyload-vuln $NEW)"
 local NJ="$TMP/C-n.jar"; login "$NEW" pw123 "$NJ" 8090
 echo "  the new account's guarded source -> HTTP $(src "$NJ" 8090)"
 seed pyload-vuln
 local S2="$TMP/C-s2.jar"; login superadmin superpass "$S2" 8090
 for u in alice pyload superadmin; do setperm "$S2" 8090 $u 1 >/dev/null; done
 echo "  every admin demoted: alice=$(role_of pyload-vuln alice) pyload=$(role_of pyload-vuln pyload) superadmin=$(role_of pyload-vuln superadmin)"
 local S3="$TMP/C-s3.jar"; login superadmin superpass "$S3" 8090
 echo "  fresh login then try to promote -> HTTP $(setperm "$S3" 8090 alice 0)   <- the ceiling"
 seed pyload-vuln; echo "  (reseeded)"
}

partA 8090 pyload-vuln  "VULNERABLE"; partA 8091 pyload-fixed "FIXED"
partB 8090 pyload-vuln  "VULNERABLE"; partB 8091 pyload-fixed "FIXED"
partC
