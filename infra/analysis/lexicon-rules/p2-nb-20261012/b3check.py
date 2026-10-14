import sys, math
from collections import defaultdict
exec(open("b1check.py").read().split("for rep, fl in")[0])

def vtrain(tr_ops):
    pos, neg = [], []
    for o in tr_ops:
        L = lab[o["row_id"]]
        if not L["T"] or not L["victim"] or L["victim"] == ["self"]:
            continue
        for f in o["fields"]:
            (pos if f["key"] in L["victim"] else neg).append((ffeats(f), o["provider"]))
    dr, dn, pv = defaultdict(int), defaultdict(int), defaultdict(set)
    for fs, p in pos:
        for t in fs:
            dr[t] += 1; pv[t].add(p)
    for fs, p in neg:
        for t in fs:
            dn[t] += 1
    w = {t: math.log((dr[t] + 1) / (len(pos) + 2)) - math.log((dn[t] + 1) / (len(neg) + 2)) for t in dr if len(pv[t]) >= 2}
    return w, math.log(len(pos) / len(neg))

def vpick(o, w, prior, exclude, path_first=False):
    cands = [f for f in o["fields"] if f["kind"] in ("str", "num") and f["key"] != exclude]
    sc = [(prior + sum(w.get(t, 0.0) for t in ffeats(f)), -i, f) for i, f in enumerate(cands)]
    if path_first:
        p = [x for x in sc if x[2]["loc"] == "path" and x[0] > 0]
        if p:
            return max(p, key=lambda x: (x[0], x[1]))[2]
    return max(sc, key=lambda x: (x[0], x[1]))[2] if sc else None

for rep, fl in enumerate(M.folds(ops)):
    m3 = defaultdict(dict)
    for held in fl:
        tr = [o for o in ops if o["provider"] not in held]
        te = [o for o in ops if o["provider"] in held]
        wv, pvr = vtrain(tr); wf, pf = ftrain(tr)
        LB = F.models(tr, lab)["RF"]; rfv = F.fns(LB)[2]
        for o in te:
            L = lab[o["row_id"]]
            if not (L["T"] and L["victim"] and L["victim"] != ["self"]):
                continue
            b1 = nbf_pick(o, wf, pf); ex = b1[1] if b1 else None
            for arm, v in (("hand", sim.pick_victim(o, sim.HARD)), ("RF", rfv(o, LB)), ("NBv", vpick(o, wv, pvr, ex)), ("NBv-pathfirst", vpick(o, wv, pvr, ex, True))):
                m3[arm][o["row_id"]] = v is not None and v["key"] in L["victim"]
    print("repeat", rep + 1, {a: sum(d.values()) for a, d in m3.items()}, "of", len(m3["hand"]))
