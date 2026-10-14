import sys
sys.argv = ["x", "RF"]
exec(open("nbcheck_all.py").read().split("flt = sys.argv[1]")[0])
ps, qs = X.derive_new(rows, provider, False)
pw, qw = X.as_lex(ps, qs)
up = lambda o: any(w in n for n, _, _ in sim.genes(o) for w, _ in qw)
LB = F.models(ops, lab)["RF"]; red = F.fns(LB)[0]
w, prior = nb_train(ops)
nb = nb_scorer(w, prior); mx = max_scorer(pw)
for name, path, m, p in M.TARGETS:
    tops = M.R.spec_ops(path)
    for i, o in enumerate(tops):
        o.setdefault("row_id", "%s-%d" % (name, i))
    line = name
    for a, sc, g in (("max", mx, lambda o: mx(o) > 0), ("NB", nb, lambda o: True)):
        FC.clear()
        ranked = [o for o in tops if o["method"] in sim.VERB_ORDER and g(o)]
        ranked.sort(key=lambda o: (-sc(o), not up(o), sim.VERB_ORDER.index(o["method"])))
        via = [o for o in ranked if red(o, LB)]
        pos = next((i + 1 for i, o in enumerate(via) if o["method"] == m and o["path"] == p), "-")
        line += " | %s #%s/%d %s" % (a, pos, len(via), [o["method"] + " " + o["path"] for o in via[:3]])
    print(line)
