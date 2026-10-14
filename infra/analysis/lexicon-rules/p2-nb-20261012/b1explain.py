import sys, math
exec(open("b1check.py").read().split("for rep, fl in")[0])
w, prior = ftrain(ops)
pos_n = sum(1 for o in ops if lab[o["row_id"]]["T"] for f in o["fields"] if f["key"] in lab[o["row_id"]]["role"])
all_n = sum(len(o["fields"]) for o in ops if lab[o["row_id"]]["T"])
print("role fields %d of %d fields in T ops; prior log-odds %.2f; base %.1f%%" % (pos_n, all_n, prior, 100 * pos_n / all_n))
def show(spec, method, path, names):
    o = next(x for x in ops if x["spec"] == spec and x["method"] == method and x["path"] == path)
    for f in o["fields"]:
        if f["raw_leaf"] not in names:
            continue
        hits = [(t, w[t]) for t in sorted(ffeats(f)) if t in w]
        s = prior + sum(x for _, x in hits)
        print("%s %s %s | %-14s %-5s | %s | sum %.2f post %.0f%% | Lratio-only %.2f" % (spec, method, path, f["raw_leaf"], f["kind"],
              " ".join("%s%+.2f" % (t, x) for t, x in hits), s, 100 / (1 + math.exp(-s)), s - prior))
show("S109", "POST", "/v3/groups/{id}/members", ["access_level", "user_id", "expires_at"])
show("S213", "POST", "/admin.users.assign", ["is_restricted", "team_id", "user_id"])
for o in ops:
    if lab[o["row_id"]]["T"] and any(f["raw_leaf"] in ("enabled",) for f in o["fields"]):
        show(o["spec"], o["method"], o["path"], ["enabled"]); break
