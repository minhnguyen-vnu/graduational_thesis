import sys, math
sys.argv = ["x", "RF"]
exec(open("nbcheck_all.py").read().split("flt = sys.argv[1]")[0])
w, prior = nb_train(ops)
print("prior %.2f  tokens %d" % (prior, len(w)))
for name, path, m, p in M.TARGETS:
    if name != "pyLoad":
        continue
    tops = M.R.spec_ops(path)
    for i, o in enumerate(tops):
        o.setdefault("row_id", "%s-%d" % (name, i))
    for want in ("/api/set_user_permission", "/json/add_user", "/api/add_user"):
        o = next(x for x in tops if x["path"] == want and x["method"] == "POST")
        hits = sorted(((w[t], t) for t in fe(o) if t in w), reverse=True)
        s = prior + sum(x for x, _ in hits)
        print("%-28s score %.2f p=%.3f  %s  fields=%s" % (want, s, 1 / (1 + math.exp(-s)), " ".join("%s%+.2f" % (t, x) for x, t in hits), [f["raw_leaf"] for f in o["fields"]]))
