import math, os, re, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
NB_DIR = os.path.join(HERE, "..", "p2-nb-20261012")
sys.argv = ["x", "RF"]
exec(open(os.path.join(NB_DIR, "nbcheck_all.py")).read().split("flt = sys.argv[1]")[0])

ALPHA = 0.05 / 4
WANT_A = {"top1": [16, 16, 17, 18], "top4": [22, 21, 22, 25]}


def fA(o):
    fs = {"v:" + o["method"]}
    fs |= {"p:" + t for t in X.tokens(o["path"])}
    for f in o["fields"]:
        if f["loc"] in ("path", "query", "body"):
            fs |= {"f:" + t for t in X.tokens(f["raw_leaf"])}
    return fs


def fB(o):
    fs = {"v:" + o["method"]}
    fs |= {"p:" + t for t in X.tokens(o["path"])}
    for f in o["fields"]:
        if f["loc"] in ("query", "body"):
            fs |= {"f:" + t for t in X.tokens(f["raw_leaf"])}
    return fs


def fC(o):
    fs = {"v:" + o["method"]}
    fs |= {"p:" + t for t in X.tokens(re.sub(r"\{[^}]*\}", " ", o["path"]))}
    for f in o["fields"]:
        if f["loc"] in ("path", "query", "body"):
            fs |= {"f:" + t for t in X.tokens(f["raw_leaf"])}
    return fs


VARIANTS = {"A": fA, "B": fB, "C": fC}


def train(tr_ops, fx):
    pos = [o for o in tr_ops if lab[o["row_id"]]["T"]]
    neg = [o for o in tr_ops if not lab[o["row_id"]]["T"]]
    dr, dn, pv = defaultdict(int), defaultdict(int), defaultdict(set)
    for o in pos:
        for t in fx(o):
            dr[t] += 1
            pv[t].add(o["provider"])
    for o in neg:
        for t in fx(o):
            dn[t] += 1
    w = {t: math.log((dr[t] + 1) / (len(pos) + 2)) - math.log((dn[t] + 1) / (len(neg) + 2))
         for t in dr if len(pv[t]) >= 2}
    return w, math.log(len(pos) / len(neg))


def scorer(w, prior, fx):
    cache = {}

    def sc(o):
        k = o["row_id"]
        if k not in cache:
            cache[k] = prior + sum(w.get(t, 0.0) for t in fx(o))
        return cache[k]
    return sc


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def outcomes(rank, gate):
    out = {"top1": {}, "top4": {}, "T>0": {}, "N<=0": {}}
    for s, (pos, _, _) in rank.items():
        out["top1"][s] = pos == 0
        out["top4"][s] = pos is not None and pos < 4
    for k, (t, sc) in gate.items():
        if t:
            out["T>0"][k] = sc > 0
        else:
            out["N<=0"][k] = sc <= 0
    return out


per_rep = []
for rep, fl in enumerate(M.folds(ops)):
    rank = {v: {} for v in VARIANTS}
    gate = {v: {} for v in VARIANTS}
    for held in fl:
        tr_rows = [x for x in rows if provider[x["spec_id"]] not in held]
        tr_ops = [o for o in ops if o["provider"] not in held]
        te_ops = [o for o in ops if o["provider"] in held]
        pw, qw = X.as_lex(*X.derive_new(tr_rows, provider, False))
        up = lambda o, qw=qw: any(wd in n for n, _, _ in sim.genes(o) for wd, _ in qw)
        LB = F.models(tr_ops, lab)["RF"]
        red = F.fns(LB)[0]
        for v, fx in VARIANTS.items():
            w, prior = train(tr_ops, fx)
            sc = scorer(w, prior, fx)
            rank[v].update(evaluate(te_ops, sc, lambda o: True, up, red, LB))
            for o in te_ops:
                if o["spec"] not in old29:
                    gate[v][o["row_id"]] = (lab[o["row_id"]]["T"], sc(o))
    per_rep.append({v: outcomes(rank[v], gate[v]) for v in VARIANTS})

got_a = {m: [sum(r["A"][m].values()) for r in per_rep] for m in WANT_A}
if got_a != WANT_A:
    print("SELF-CHECK FAIL A", got_a, "want", WANT_A)
    sys.exit(1)
print("SELF-CHECK PASS A", got_a)

METRICS = ["top1", "top4", "T>0", "N<=0"]
print("%-6s %-5s %s" % ("metric", "var", "  |  ".join("rep%d: succ/units  b c  p" % (i + 1) for i in range(4))))
verdict = {}
for v in ("B", "C"):
    verdict[v] = {}
    for m in METRICS:
        cells, dirs, ps = [], [], []
        for r in per_rep:
            a, x = r["A"][m], r[v][m]
            b = sum(1 for k in a if x[k] and not a[k])
            c = sum(1 for k in a if a[k] and not x[k])
            p = mcnemar(b, c)
            cells.append("%d/%d vs A %d  %d %d  %.4f" % (sum(x.values()), len(x), sum(a.values()), b, c, p))
            dirs.append(1 if b > c else -1 if c > b else 0)
            ps.append(p)
        if all(d == 1 for d in dirs) and all(p < ALPHA for p in ps):
            verdict[v][m] = "better"
        elif all(d == -1 for d in dirs) and all(p < ALPHA for p in ps):
            verdict[v][m] = "worse"
        else:
            verdict[v][m] = "no-difference"
        print("%-6s %-5s %s  => %s" % (m, v, "  |  ".join(cells), verdict[v][m]))

passed = [v for v in ("B", "C") if "better" in verdict[v].values() and "worse" not in verdict[v].values()]
if not passed:
    print("DECISION keep A")
elif len(passed) == 1:
    print("DECISION adopt", passed[0])
else:
    t = {v: sum(sum(r[v]["top1"].values()) for r in per_rep) for v in passed}
    print("DECISION both pass, top1 totals", t, "adopt" if t["B"] != t["C"] else "tie, ask user",
          max(t, key=t.get) if t["B"] != t["C"] else "")

print("SANITY full-data models")
ps_all, qs_all = X.derive_new(rows, provider, False)
pw_all, qw_all = X.as_lex(ps_all, qs_all)
up_all = lambda o: any(wd in n for n, _, _ in sim.genes(o) for wd, _ in qw_all)
LB_all = F.models(ops, lab)["RF"]
red_all = F.fns(LB_all)[0]
for v, fx in VARIANTS.items():
    w, prior = train(ops, fx)
    line = "%s features %d prior %.3f" % (v, len(w), prior)
    for name, path, m, p in M.TARGETS[:3]:
        tops = M.R.spec_ops(path)
        for i, o in enumerate(tops):
            o["row_id"] = "%s-%d" % (name, i)
        sc = scorer(w, prior, fx)
        ranked = [o for o in tops if o["method"] in sim.VERB_ORDER]
        ranked.sort(key=lambda o: (-sc(o), not up_all(o), sim.VERB_ORDER.index(o["method"])))
        via = [o for o in ranked if red_all(o, LB_all)]
        pos = next((i + 1 for i, o in enumerate(via) if o["method"] == m and o["path"] == p), "-")
        t_op = next(o for o in tops if o["method"] == m and o["path"] == p)
        line += " | %s #%s/%d score %.3f" % (name, pos, len(via), sc(t_op))
        if name == "pyLoad":
            ep = next(o for o in tops if o["method"] == "POST" and o["path"] == "/json/edit_package")
            line += " edit_package %.3f" % sc(ep)
    print(line)
