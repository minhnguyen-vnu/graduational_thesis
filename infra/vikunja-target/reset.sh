#!/bin/zsh
set -u
P=${1:-3457}
H=http://localhost:$P/api/v1
docker rm -f vikunja-em >/dev/null 2>&1
docker run -d --name vikunja-em --user 0 -p $P:3456 --tmpfs /db -e VIKUNJA_DATABASE_PATH=/db/vikunja.db \
  -e VIKUNJA_SERVICE_PUBLICURL=http://localhost:$P/ -e VIKUNJA_RATELIMIT_NOAUTHLIMIT=100000 -e VIKUNJA_RATELIMIT_LIMIT=100000 vikunja/vikunja:2.2.2 >/dev/null
python3 - $H <<'PY'
import json,sys,time,urllib.request
H=sys.argv[1]
def call(m,p,body=None,tok=None):
    req=urllib.request.Request(H+p,method=m,data=None if body is None else json.dumps(body).encode(),headers={"Content-Type":"application/json",**({"Authorization":"Bearer "+tok} if tok else {})})
    try:
        r=urllib.request.urlopen(req,timeout=5);return r.status,json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code,e.read()[:200]
for i in range(60):
    try:
        urllib.request.urlopen(H+"/info",timeout=2);break
    except Exception:
        time.sleep(1)
else:
    print("vikunja not up");sys.exit(1)
tok={}
for u in ["alice","bob","carol"]:
    print("register",u,call("POST","/register",{"username":u,"email":u+"@x.com","password":u+"pass1234"})[0])
    c,b=call("POST","/login",{"username":u,"password":u+"pass1234"});tok[u]=b["token"] if c==200 else None;print("login",u,c)
c,p=call("PUT","/projects",{"title":"shared"},tok["alice"]);pid=p["id"];print("project",c,pid)
print("share bob 2",call("PUT",f"/projects/{pid}/users",{"username":"bob","permission":2},tok["alice"])[0])
print("share carol 0",call("PUT",f"/projects/{pid}/users",{"username":"carol","permission":0},tok["alice"])[0])
print("task by alice",call("PUT",f"/projects/{pid}/tasks",{"title":"t1"},tok["alice"])[0])
print("bob writes task",call("PUT",f"/projects/{pid}/tasks",{"title":"t2"},tok["bob"])[0])
print("carol writes task",call("PUT",f"/projects/{pid}/tasks",{"title":"t3"},tok["carol"])[0])
PY
