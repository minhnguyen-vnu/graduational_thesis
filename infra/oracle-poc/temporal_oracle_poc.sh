#!/usr/bin/env bash
# Temporal authorization oracle — proof-of-concept (thesis Step 3, first thin slice).
#
# Metamorphic relation under test:
#   "Removing a permission must never increase access."
#   If an action was ALLOWED before a permission-reducing transition, the SAME
#   token replayed AFTER the transition must now be DENIED (403).
#
# The move EvoMaster's baseline never makes: we replay the PRE-demotion token,
# we do NOT log in again (a fresh login would return a VIEWER token and hide the bug).
#
# Usage: temporal_oracle_poc.sh <base-url>
set -euo pipefail
BASE="${1:?usage: $0 <base-url>}"

json='-H Content-Type:application/json'

login() { # $1=user $2=pass  -> prints token
  curl -s -X POST "$BASE/auth/login" $json \
    -d "{\"username\":\"$1\",\"password\":\"$2\"}" \
    | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])"
}
code() { # runs a request, prints only the HTTP status code
  curl -s -o /dev/null -w "%{http_code}" "$@"
}

echo "=================================================================="
echo "TARGET: $BASE"
echo "=================================================================="

# Step 1 — clean state
curl -s -X POST "$BASE/reset" >/dev/null
echo "[1] reset                                          -> ok"

# Step 2 — alice logs in as ADMIN; keep this token for the whole run
TOKEN_OLD="$(login alice alicepass)"
echo "[2] login alice (ADMIN), capture TOKEN_OLD         -> ${TOKEN_OLD:0:16}..."

# Step 3 — OBSERVE ALLOWED: alice deletes report 1 while still ADMIN
c_before="$(code -X DELETE "$BASE/reports/1" -H "Authorization: Bearer $TOKEN_OLD")"
echo "[3] DELETE /reports/1  (alice, pre-demotion)       -> $c_before   (expect 204 = admin power works)"

# Step 4 — TRANSITION: superadmin demotes alice ADMIN -> VIEWER
TOKEN_ADMIN="$(login superadmin superpass)"
c_demote="$(code -X PUT "$BASE/users/alice/role" $json \
  -H "Authorization: Bearer $TOKEN_ADMIN" -d '{"role":"VIEWER"}')"
echo "[4] PUT /users/alice/role {VIEWER} (by superadmin) -> $c_demote   (permission-reducing transition)"

# Step 5 — RE-ATTEMPT with the SAME OLD TOKEN (no re-login!)
c_after="$(code -X DELETE "$BASE/reports/2" -H "Authorization: Bearer $TOKEN_OLD")"
echo "[5] DELETE /reports/2  (SAME TOKEN_OLD, post-demotion) -> $c_after"

echo "------------------------------------------------------------------"
# ---- THE ORACLE VERDICT --------------------------------------------
if [ "$c_before" = "204" ] && [ "$c_after" = "403" ]; then
  echo "ORACLE VERDICT: 🟢 PASS  — access correctly revoked after demotion"
elif [ "$c_before" = "204" ] && [[ "$c_after" =~ ^2 ]]; then
  echo "ORACLE VERDICT: 🔴 BUG DETECTED — demoted user still has access (stale-token privilege persistence, A1)"
else
  echo "ORACLE VERDICT: ⚠️  INCONCLUSIVE (before=$c_before after=$c_after — precondition not met)"
fi
echo
