#!/bin/bash
JAR=/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/wagoe-target/src/target/wagoe-1.0.0-standalone.jar
JH=$(/usr/libexec/java_home -v 17)
export JAVA_HOME=$JH WAG_ENV=dev JWT_SECRET=thesis_local_dev_only_secret_min_32_chars
export POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=wagoe POSTGRES_USER=wagoe POSTGRES_PASSWORD=wagoe
PW='Devpass123'
docker exec wagoe-pg psql -U wagoe -d wagoe -c "TRUNCATE user_sessions, user_audit_log, users, auth_users CASCADE;" >/dev/null 2>&1
q () { java -jar "$JAR" cli user create --email "$1" --name "$2" --role "$3" --password "$PW" 2>/dev/null | grep -oE "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}" | tail -1; }
OID=$(q op@acme.test  Operator admin)
VID=$(q vic@acme.test Victim   admin)
TID=$(q tgt@acme.test Target   user)
echo "OID=$OID"; echo "VID=$VID"; echo "TID=$TID"
echo "--- verify logins ---"
for e in op@acme.test vic@acme.test tgt@acme.test; do
  r=$(curl -s -X POST http://localhost:3000/api/v1/auth/login -H 'Content-Type: application/json' -d "{\"email\":\"$e\",\"password\":\"$PW\"}" | python3 -c "import sys,json;d=json.load(sys.stdin);print('auth=%s jwt=%s'%(d.get('authenticated'),bool(d.get('jwtToken'))))")
  echo "$e -> $r"
done
