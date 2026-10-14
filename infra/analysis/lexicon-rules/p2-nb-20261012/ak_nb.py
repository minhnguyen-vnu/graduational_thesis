import sys, math
sys.argv = ["x", "RF"]
exec(open("nbcheck_all.py").read().split("flt = sys.argv[1]")[0])
w, prior = nb_train(ops)
LB = F.models(ops, lab)["RF"]; red = F.fns(LB)[0]
name, path, m, p = next(t for t in M.TARGETS if t[0] == "artifact-keeper")
tops = M.R.spec_ops(path)
for i, o in enumerate(tops):
    o.setdefault("row_id", "ak-%d" % i)
nb = nb_scorer(w, prior)
wr = [o for o in tops if o["method"] in sim.VERB_ORDER]
wr.sort(key=lambda o: -nb(o))
print("write ops", len(wr))
for i, o in enumerate(wr[:12]):
    hits = sorted(((w[t], t) for t in fe(o) if t in w), reverse=True)
    v = red(o, LB)
    print("#%-3d %6.2f %-7s %-45s %s %s" % (i + 1, nb(o), o["method"], o["path"], "VIABLE" if v else "      ",
          " ".join("%s%+.2f" % (t, x) for x, t in hits[:7])), "<== TRUE" if (o["method"], o["path"]) == (m, p) else "")
for o in wr:
    if red(o, LB):
        print("viable:", o["method"], o["path"], "%.2f" % nb(o), "reduced:", red(o, LB)[:5], "fields:", [f["raw_leaf"] for f in o["fields"]][:10])
