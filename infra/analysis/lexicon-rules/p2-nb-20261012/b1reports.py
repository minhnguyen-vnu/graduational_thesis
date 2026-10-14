import sys, math
exec(open("b1check.py").read().split("for rep, fl in")[0])
w, prior = ftrain(ops)
for name, path, m, p in M.TARGETS:
    if name != "reports-api":
        continue
    for o in M.R.spec_ops(path):
        if o["method"] == m and o["path"] == p:
            for f in o["fields"]:
                hits = [(t, w[t]) for t in sorted(ffeats(f)) if t in w]
                s = prior + sum(x for _, x in hits)
                print(f["loc"], f["raw_leaf"], f["kind"], f["enum"], " ".join("%s%+.2f" % (t, x) for t, x in hits), "sum %.2f post %.0f%%" % (s, 100 / (1 + math.exp(-s))))
