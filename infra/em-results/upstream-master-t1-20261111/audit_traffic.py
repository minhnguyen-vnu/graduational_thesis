import base64
import json
import re
import sys
from urllib.parse import unquote

SEED_ROLES = {"alice": "ADMIN", "superadmin": "ADMIN", "bob": "VIEWER"}
ROLE_PATH = re.compile(r"^/users/([^/?]+)/role/?(\?.*)?$")
REPORTS_PATH = re.compile(r"^/reports(/[^?]*)?(\?.*)?$")
WRITE = {"POST", "PUT", "DELETE", "PATCH"}


def claims(token):
    try:
        p = token.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4)))
    except Exception:
        return {}


def body_json(s):
    try:
        return json.loads(s)
    except Exception:
        return None


def admin_only(rec):
    if rec["method"] not in WRITE:
        return False
    return bool(REPORTS_PATH.match(rec["path"]) or ROLE_PATH.match(rec["path"]))


def audit(path):
    recs = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    roles = dict(SEED_ROLES)
    tokens = {}
    logins = {u: 0 for u in SEED_ROLES}
    demotions = []
    writes_by_tail = {}
    stale = []
    proxy_errors = 0
    for i, r in enumerate(recs):
        if r["status"] == 502 and r["resp_body"].startswith("proxy error"):
            proxy_errors += 1
        tail = r["auth_tail"]
        if r["method"] == "POST" and r["path"].split("?")[0] == "/auth/login" and r["status"] == 200:
            req = body_json(r["req_body"]) or {}
            resp = body_json(r["resp_body"]) or {}
            u, tok = req.get("username"), resp.get("token")
            if u in logins and isinstance(tok, str):
                logins[u] += 1
                c = claims(tok)
                tokens[tok[-12:]] = {"user": u, "claim": c.get("role"), "issued": i}
            continue
        if r["method"] == "POST" and r["path"].split("?")[0] == "/reset" and 200 <= r["status"] < 300:
            roles = dict(SEED_ROLES)
            continue
        info = tokens.get(tail)
        ok = 200 <= r["status"] < 300
        if info and admin_only(r):
            u = info["user"]
            if info["claim"] == "ADMIN" and roles.get(u) == "VIEWER":
                d = max((x for x in demotions if x["user"] == u and x["idx"] < i and x["idx"] > info["issued"]),
                        key=lambda x: x["idx"], default=None)
                src = [k for k in writes_by_tail.get(tail, []) if d and k < d["idx"]]
                stale.append({"idx": i, "t": r["t"], "user": u, "method": r["method"], "path": r["path"],
                              "status": r["status"], "demotion_idx": d["idx"] if d else None,
                              "source_idx": src[-1] if src else None})
            if ok:
                writes_by_tail.setdefault(tail, []).append(i)
        m = ROLE_PATH.match(r["path"])
        if r["method"] == "PUT" and m and ok:
            target = unquote(m.group(1))
            new = (body_json(r["req_body"]) or {}).get("role")
            if target in roles and new in ("ADMIN", "VIEWER"):
                if roles[target] == "ADMIN" and new == "VIEWER":
                    by = info["user"] if info else None
                    demotions.append({"idx": i, "t": r["t"], "user": target, "by": by})
                roles[target] = new
    s2 = [x for x in stale if 200 <= x["status"] < 300]
    return {
        "file": path,
        "requests": len(recs),
        "proxy_errors": proxy_errors,
        "logins": logins,
        "demotions": len(demotions),
        "demoted_users": sorted({d["user"] for d in demotions}),
        "stale_2xx": len(s2),
        "stale_403": sum(1 for x in stale if x["status"] == 403),
        "stale_other": sum(1 for x in stale if not (200 <= x["status"] < 300) and x["status"] != 403),
        "full_triples_2xx": sum(1 for x in s2 if x["source_idx"] is not None),
        "stale": stale,
        "demotion_list": demotions,
    }


def main(paths):
    print("file\trequests\tproxy_errors\tlogin_alice\tlogin_superadmin\tlogin_bob\tdemotions\tdemoted\tstale_2xx\tstale_403\tstale_other\tfull_triples_2xx")
    details = []
    for p in paths:
        a = audit(p)
        print("\t".join(str(x) for x in [
            p.rsplit("/", 1)[-1], a["requests"], a["proxy_errors"], a["logins"]["alice"], a["logins"]["superadmin"],
            a["logins"]["bob"], a["demotions"], "|".join(a["demoted_users"]) or "-", a["stale_2xx"], a["stale_403"],
            a["stale_other"], a["full_triples_2xx"]]))
        for x in a["stale"]:
            details.append("%s\t%s" % (p.rsplit("/", 1)[-1], json.dumps(x)))
    if details:
        print("# stale-token admin-only calls")
        print("\n".join(details))


if __name__ == "__main__":
    main(sys.argv[1:])
