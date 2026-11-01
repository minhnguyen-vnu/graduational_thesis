import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "dupcheck.py")).read().split("per_rep = []")[0])

models = {v: train(ops, fx) for v, fx in VARIANTS.items()}
for name, path, m, p in M.TARGETS[:3]:
    tops = [o for o in M.R.spec_ops(path) if o["method"] in ("POST", "PUT", "PATCH", "DELETE")]
    for i, o in enumerate(tops):
        o["row_id"] = "%s-%d" % (name, i)
    sc = {v: scorer(w, prior, VARIANTS[v]) for v, (w, prior) in models.items()}
    above = {v: {(o["method"], o["path"]) for o in tops if sc[v](o) > 0} for v in VARIANTS}
    print(name, "write ops", len(tops), "| >0:", {v: len(s) for v, s in above.items()})
    for v in ("B", "C"):
        print("  A>0 not %s:" % v, sorted(above["A"] - above[v]), "| %s>0 not A:" % v, sorted(above[v] - above["A"]))
    for o in sorted(tops, key=lambda o: -sc["A"](o)):
        if sc["A"](o) > 0 or sc["B"](o) > 0:
            print("   %-6s %-40s A %+.3f B %+.3f C %+.3f" % (o["method"], o["path"], sc["A"](o), sc["B"](o), sc["C"](o)))
