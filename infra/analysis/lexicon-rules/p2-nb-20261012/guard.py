import sys, math
sys.argv = ["x", "RF"]
exec(open("nbcheck_all.py").read().split("flt = sys.argv[1]")[0])
w, prior = nb_train(ops)
ps, qs = X.derive_new(rows, provider, False)
cur = X.read_lexicon(X.JAR_LEX)[0]
def lexhit(o):
    h = sim.hay(o)
    return any(x in h for x, s in cur)
nb = nb_scorer(w, prior)
for name, path, m, p in M.TARGETS:
    tops = [o for o in M.R.spec_ops(path) if o["method"] in sim.VERB_ORDER]
    for i, o in enumerate(tops):
        o.setdefault("row_id", "%s-%d" % (name, i))
    FC.clear()
    t = next(o for o in tops if o["method"] == m and o["path"] == p)
    print("%-16s write ops %3d | lexicon>0 (today) %3d | NB>0 %3d | transition NB %.2f" % (name, len(tops), sum(1 for o in tops if lexhit(o)), sum(1 for o in tops if nb(o) > 0), nb(t)))
    if name in ("reports-api", "pyLoad", "vampi-seeded"):
        for o in tops:
            if name != "pyLoad" or o["path"].startswith("/json/"):
                print("     %-7s %-32s lex %d  NB %+.2f" % (o["method"], o["path"], lexhit(o), nb(o)))
