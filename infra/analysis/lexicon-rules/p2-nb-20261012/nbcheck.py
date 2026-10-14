import math, re, sys
from collections import defaultdict
D = "/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/analysis/lexicon-rules/lexicon-r4-20261007"
sys.path.insert(0, D)
import measure as M
X, sim, F = M.X, M.sim, M.F
lab, ops, rows, provider = X.new_data()
old29 = set(X.old_train_specs())

def feats(op):
    fs = {"v:" + op["method"]}
    fs |= {"p:" + t for t in X.tokens(op["path"])}
    for f in op["fields"]:
        if f["loc"] in ("path", "query", "body"):
            fs |= {"f:" + t for t in X.tokens(f["raw_leaf"])}
    return fs

FC = {}
def fe(op):
    k = op["row_id"]
    if k not in FC:
        FC[k] = feats(op)
    return FC[k]

def nb_train(tr_ops, minprov=2, a=1.0):
    pos = [o for o in tr_ops if lab[o["row_id"]]["T"]]
    neg = [o for o in tr_ops if not lab[o["row_id"]]["T"]]
    dr, dn, pv = defaultdict(int), defaultdict(int), defaultdict(set)
    for o in pos:
        for t in fe(o):
            dr[t] += 1; pv[t].add(o["provider"])
    for o in neg:
        for t in fe(o):
            dn[t] += 1
    w = {t: math.log((dr[t] + a) / (len(pos) + 2 * a)) - math.log((dn[t] + a) / (len(neg) + 2 * a))
         for t in dr if len(pv[t]) >= minprov}
    prior = math.log(len(pos) / len(neg))
    return w, prior

def nb_scorer(w, prior):
    return lambda op: prior + sum(w.get(t, 0.0) for t in fe(op))

def max_scorer(pw):
    return lambda op: max([s for x, s in pw if x in sim.hay(op)] or [0.0])

def or_scorer(pw):
    import importlib
    sys.path.insert(0, D.replace("lexicon-r4-20261007", "lexicon-combine-20261007"))
    import measure2 as W
    return lambda op: W.or_score(pw, sim.hay(op))

def evaluate(te_ops, score, gate, up, red, LB):
    by = defaultdict(list)
    for o in te_ops:
        if o["spec"] not in old29:
            by[o["spec"]].append(o)
    res = {}
    for s, ol in by.items():
        if not any(lab[o["row_id"]]["T"] for o in ol):
            continue
        ranked = [o for o in ol if o["method"] in sim.VERB_ORDER and gate(o)]
        ranked.sort(key=lambda o: (-score(o), not up(o), sim.VERB_ORDER.index(o["method"])))
        via = [o for o in ranked if red(o, LB)]
        pos = next((i for i, o in enumerate(via) if lab[o["row_id"]]["T"]), None)
        tin = any(lab[o["row_id"]]["T"] and red(o, LB) for o in ol)
        res[s] = (pos, tin, len(via))
    return res

def summarize(name, res):
    reach = {s: v for s, v in res.items() if v[0] is not None}
    passf = sum(1 for v in res.values() if v[1])
    w = [v[0] for v in reach.values()]
    print("%-14s specs %d | T passes filter %d | T reachable %d | first %d | top2 %d | top4 %d | wasted sum %d max %s" % (
        name, len(res), passf, len(reach), sum(1 for x in w if x == 0), sum(1 for x in w if x < 2),
        sum(1 for x in w if x < 4), sum(w), max(w) if w else "-"))
    return reach

flt = sys.argv[1] if len(sys.argv) > 1 else "HARD"
for rep, fl in enumerate(M.folds(ops)):
    if rep > 0:
        break
    pooled = defaultdict(dict)
    for held in fl:
        tr_rows = [x for x in rows if provider[x["spec_id"]] not in held]
        tr_ops = [o for o in ops if o["provider"] not in held]
        te_ops = [o for o in ops if o["provider"] in held]
        pw, qw = X.as_lex(*X.derive_new(tr_rows, provider, False))
        up = lambda o, qw=qw: any(w in n for n, _, _ in sim.genes(o) for w, _ in qw)
        if flt == "HARD":
            LB, red = sim.HARD, sim.reduced_candidates
        else:
            LB = F.models(tr_ops, lab)["RF"]; red = F.fns(LB)[0]
        mx = max_scorer(pw)
        orr = or_scorer(pw)
        w, prior = nb_train(tr_ops)
        nb = nb_scorer(w, prior)
        arms = {"max>0": (mx, lambda o: mx(o) > 0), "OR>0": (orr, lambda o: orr(o) > 0),
                "NB all": (nb, lambda o: True), "NB>prior": (nb, lambda o: nb(o) > prior)}
        for a, (sc, g) in arms.items():
            pooled[a].update(evaluate(te_ops, sc, g, up, red, LB))
    print("filter", flt, "repeat 1")
    out = {a: summarize(a, pooled[a]) for a in pooled}
    bad = sorted(((v[0], s) for s, v in pooled["max>0"].items() if v[0] is not None and v[0] >= 3), reverse=True)
    print("max>0 specs with >=3 wasted:", bad, "NB all same specs:", [(pooled["NB all"][s][0], s) for _, s in bad])
