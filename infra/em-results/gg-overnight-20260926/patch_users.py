import json
import sys

who = {}
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
for r in rows:
    if r["method"] == "POST" and r["path"].startswith("/auth/token") and r["status"] < 300:
        try:
            user = json.loads(r["req_body"]).get("username")
            tok = json.loads(r["resp_body"])["access_token"]
            who[tok[-12:]] = user
        except Exception:
            pass

for i, r in enumerate(rows):
    if r["method"] == "PATCH" and r["path"].startswith("/auth/fab/v1/users/"):
        caller = who.get(r["auth_tail"], "?" if r["auth_tail"] else "-")
        print("%5d %s %s caller=%s status=%d" % (i, r["t"], r["path"], caller, r["status"]))
        print("      req  %s" % r["req_body"][:600])
        print("      resp %s" % r["resp_body"][:300].replace("\n", " "))
