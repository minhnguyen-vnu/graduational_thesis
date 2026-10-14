#!/usr/bin/env zsh
set -u
NAME=${1:-djva}
B=http://localhost:${2:-8096}/api
J='Content-Type: application/json'
tok () { curl -s -H "$J" -d "{\"username\":\"$1\",\"password\":\"$2\"}" $B/token/ | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["access"])' }
code () { curl -s -o /dev/null -w '%{http_code}' "$@" }
uid () { docker exec -i $NAME python manage.py shell -c "from apps.system.models import User; print(User.objects.get(username='$1').id)" | tail -1 }
n=0
src () { n=$((n+1)); code -X POST -H "$J" -H "Authorization: Bearer $1" -d "{\"name\":\"probe-$2-$n\"}" $B/system/role/ }

echo "== duong A: ha is_superuser, victim"
VID=$(uid victim)
AT=$(tok admin adminpass); VT=$(tok victim victimpass); WT=$(tok viewer viewerpass)
echo "nguon, token cu victim: $(src $VT a)"
echo "nguon, viewer: $(src $WT a)"
echo "transition PUT user/$VID is_superuser=false: $(code -X PUT -H "$J" -H "Authorization: Bearer $AT" -d '{"username":"victim","is_superuser":false,"roles":[]}' $B/system/user/$VID/)"
echo "follow-up, token cu victim: $(src $VT a)"
VT2=$(tok victim victimpass)
echo "follow-up, token moi victim: $(src $VT2 a)"

echo "== duong B: go role, rolevictim"
docker exec -i $NAME python manage.py shell <<'PY' | tail -1
from apps.system.models import User, Role, Permission
r, _ = Role.objects.get_or_create(name="full-handcheck")
r.perms.set(Permission.objects.all())
u, _ = User.objects.get_or_create(username="rolevictim")
u.set_password("rolevictimpass"); u.is_superuser = False; u.is_active = True; u.save()
u.roles.set([r])
print("rolevictim", u.id, "perms", r.perms.count())
PY
RID=$(uid rolevictim)
RT=$(tok rolevictim rolevictimpass)
echo "nguon, token cu rolevictim: $(src $RT b)"
echo "transition PUT user/$RID roles=[]: $(code -X PUT -H "$J" -H "Authorization: Bearer $AT" -d '{"username":"rolevictim","roles":[]}' $B/system/user/$RID/)"
echo "follow-up, token cu rolevictim: $(src $RT b)"
RT2=$(tok rolevictim rolevictimpass)
echo "follow-up, token moi rolevictim: $(src $RT2 b)"
