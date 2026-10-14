import sys, math
from collections import defaultdict
sys.argv = ["x", "RF"]
exec(open("nbcheck_all.py").read().split("flt = sys.argv[1]")[0])

def ffeats(f):
    fs = {"k:" + f["kind"], "l:" + f["loc"], "w:" + f["leaf"]}
    fs |= {"n:" + t for t in X.tokens(f["raw_leaf"])}
    parts = [p.replace("[]", "") for p in f["name"].split(".")[:-1]]
    for p in parts:
        fs |= {"a:" + t for t in X.tokens(p)}
    for v in f["enum"]:
        fs |= {"e:" + t for t in X.tokens(str(v))}
    return fs

def ftrain(tr_ops):
    pos, neg = [], []
    for o in tr_ops:
        L = lab[o["row_id"]]
        if not L["T"]:
            continue
        for f in o["fields"]:
            (pos if f["key"] in L["role"] else neg).append((ffeats(f), o["provider"]))
    dr, dn, pv = defaultdict(int), defaultdict(int), defaultdict(set)
    for fs, p in pos:
        for t in fs:
            dr[t] += 1; pv[t].add(p)
    for fs, p in neg:
        for t in fs:
            dn[t] += 1
    w = {t: math.log((dr[t] + 1) / (len(pos) + 2)) - math.log((dn[t] + 1) / (len(neg) + 2)) for t in dr if len(pv[t]) >= 2}
    return w, math.log(len(pos) / len(neg))

def nbf_pick(o, w, prior):
    best = None
    for f in o["fields"]:
        if f["loc"] == "path":
            continue
        s = prior + sum(w.get(t, 0.0) for t in ffeats(f))
        if s > 0 and (best is None or s > best[0]):
            best = (s, f["key"], f)
    return best

def inferable(o, key):
    L = lab[o["row_id"]]
    f = next((x for x in o["fields"] if x["key"] == key), None)
    if f is None:
        return False
    return f["kind"] in ("bool", "array") or (f["kind"] == "enum" and "<" in L["order"])

for rep, fl in enumerate(M.folds(ops)):
    res = {"RF": {}, "NBf": {}}; fv = {"RF": {}, "NBf": {}}; picked = defaultdict(lambda: defaultdict(int))
    for held in fl:
        tr = [o for o in ops if o["provider"] not in held]
        te = [o for o in ops if o["provider"] in held and o["spec"] not in old29]
        wA, pA = nb_train(tr); nbA = nb_scorer(wA, pA)
        LB = F.models(tr, lab)["RF"]; red, _, _, top = F.fns(LB)
        wF, pF = ftrain(tr)
        by = defaultdict(list)
        for o in te:
            if o["method"] in sim.VERB_ORDER:
                by[o["spec"]].append(o)
        for s, ol in by.items():
            ol.sort(key=lambda o: -nbA(o))
            hasT = any(lab[o["row_id"]]["T"] for o in ol)
            for arm in ("RF", "NBf"):
                via = []
                for o in ol:
                    if arm == "RF":
                        k = top(o, LB) if red(o, LB) else None
                    else:
                        b = nbf_pick(o, wF, pF); k = b[1] if b else None
                        if b and not lab[o["row_id"]]["T"]:
                            picked[arm][b[2]["leaf"]] += 1
                    if k is not None:
                        via.append((o, k))
                if hasT:
                    res[arm][s] = any(lab[o["row_id"]]["T"] and k in lab[o["row_id"]]["role"] and inferable(o, k) for o, k in via[:4])
                else:
                    fv[arm][s] = bool(via)
    a, b = res["RF"], res["NBf"]
    disc = (sum(1 for s in a if a[s] and not b[s]), sum(1 for s in a if b[s] and not a[s]))
    print("repeat %d  hit4K RF %d NBf %d of %d | discordant RF-only %d NBf-only %d | noT specs with viable op RF %d NBf %d of %d" % (
        rep + 1, sum(a.values()), sum(b.values()), len(a), disc[0], disc[1], sum(fv["RF"].values()), sum(fv["NBf"].values()), len(fv["RF"])))
    if rep == 0:
        print("   NBf picks on non-T ops (top):", sorted(picked["NBf"].items(), key=lambda x: -x[1])[:10])
