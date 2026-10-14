#!/usr/bin/env zsh
set -u
NAME=${1:-djva}
PORT=${2:-8096}
docker rm -f $NAME > /dev/null 2>&1
docker run -d --name $NAME -p $PORT:80 djva-target:849f9aaf > /dev/null || { echo "run FAIL"; exit 1 }
for i in $(seq 1 90); do
  [ "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$PORT/api/swagger/?format=openapi)" = "200" ] && break
  sleep 2
done
echo "spec $(curl -s -o /dev/null -w '%{http_code}' http://localhost:$PORT/api/swagger/?format=openapi)"
docker exec -i $NAME python manage.py shell <<'PY'
from apps.system.models import User
for name, pw, su in [("admin", "adminpass", True), ("victim", "victimpass", True), ("viewer", "viewerpass", False)]:
    u, _ = User.objects.get_or_create(username=name)
    u.set_password(pw)
    u.is_superuser = su
    u.is_staff = su
    u.is_active = True
    u.save()
    print("user", name, "id", u.id, "superuser", u.is_superuser, "roles", list(u.roles.values_list("name", flat=True)))
PY
for u in admin victim viewer; do
  echo "login $u $(curl -s -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' -d "{\"username\":\"$u\",\"password\":\"${u}pass\"}" http://localhost:$PORT/api/token/)"
done
