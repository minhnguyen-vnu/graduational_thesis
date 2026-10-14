import json, os, random, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "field-ranking-20261007"))
import sim_rank as R

sim = R.sim
ARMS = ["V", "R4", "RFv", "RFe", "RF"]
METRICS = R.METRICS
ORIG_FNS = R.fns


def models(ops, lab):
    r4, _ = sim.derive(ops, lab, "std")
    rk = R.rank_model(ops, lab, r4["admin"])
    def rf(v, e, o):
        m = dict(r4)
        m.update({"kind": "rf", "rk": rk, "use_victim": v, "use_enum": e, "use_order": o})
        return m
    return {"V": sim.HARD, "R4": r4, "RFv": rf(True, False, False), "RFe": rf(False, True, False), "RF": rf(True, True, True)}


def rf_reduced(op, L):
    if not L["use_enum"]:
        return sim.reduced_candidates(op, L)
    rg, ag = sim.role_genes(op, L), sim.admin_genes(op, L)
    if not rg and not ag:
        return []
    vocab = []
    for f in op["fields"]:
        if f["kind"] == "enum":
            for v in f["enum"]:
                if v not in vocab:
                    vocab.append(v)
    M = L["rk"]
    key = {v: R.fscore(M["low"], v.lower()) - R.fscore(M["high"], v.lower()) for v in vocab}
    low = sorted([v for v in vocab if key[v] > 0], key=lambda v: -key[v])
    rest = sorted([v for v in vocab if v not in low], key=lambda v: -key[v])
    adm = ["false"] if ag else []
    empty = ["[]"] if any(f is not None and f["loc"] == "body" and k == "array" for _, k, f in rg) else []
    num = ["1", "0", "2"] if any(k == "num" for _, k, _ in rg) else []
    strs = ["user", "viewer", "guest", "member", "basic"] if any(k == "str" for _, k, _ in rg) else []
    res = []
    for v in adm + low + empty + num + rest + strs:
        if v not in res:
            res.append(v)
    return res


def rf_victim(op, L):
    return R.r_pick_victim(op, L["rk"]) if L["use_victim"] else sim.pick_victim(op, L)


def rf_top(op, L):
    if not L["use_order"]:
        return R.l_top_role(op, L)
    cands = []
    for i, (n, k, f) in enumerate(sim.genes(op)):
        if f is None:
            continue
        if any(w in n for w in L["role"]) or (k == "bool" and any(w in n for w in L["admin"])):
            cands.append((-R.fscore(L["rk"]["role"], n), i, f["key"]))
    return min(cands)[2] if cands else None


def fns(L):
    if L.get("kind") == "rf":
        return rf_reduced, sim.matched_role_keys, rf_victim, rf_top
    return ORIG_FNS(L)


R.fns = fns


def anchors(L):
    if L.get("kind") != "rf":
        return R.anchors(L)
    out = []
    for row in R.anchors(L):
        if L["use_victim"]:
            row["C"] = {f: R.fscore(L["rk"]["victim"], f) > 0 for f in row["C"]}
        row["pass"] = all(row["A"].values()) and all(row["C"].values())
        out.append(row)
    return out


def cv(ops, lab):
    provs = sorted({op["provider"] for op in ops})
    rng = random.Random(sim.SEED)
    reps = []
    for rep in range(4):
        order = provs[:]
        rng.shuffle(order)
        folds = [set(order[i::5]) for i in range(5)]
        pooled = {a: defaultdict(dict) for a in ARMS}
        for held in folds:
            train = [op for op in ops if op["provider"] not in held]
            test = [op for op in ops if op["provider"] in held]
            for a, L in models(train, lab).items():
                for m, d in R.outcomes(test, lab, L).items():
                    pooled[a][m].update(d)
        reps.append(pooled)
    return reps


def main(outdir):
    lab = sim.load_labels(os.path.join(R.R4, "final-all.csv"))
    ops = sim.load_ops(set(lab))
    unit_prov = {op["spec"]: op["provider"] for op in ops}
    unit_prov.update({op["row_id"]: op["provider"] for op in ops})
    reps = cv(ops, lab)
    res = {"ops": len(ops), "repeats": []}
    pairs = [("V", "RF"), ("R4", "RF"), ("R4", "RFv"), ("R4", "RFe"), ("V", "R4")]
    for r, P in enumerate(reps):
        row = {"repeat": r + 1, "rates": {a: {m: R.rate(P[a][m]) for m in METRICS} for a in ARMS}, "tests": {}}
        for a, b in pairs:
            for m in METRICS:
                t = sim.mcnemar(P[a][m], P[b][m])
                if r == 0:
                    t["ci95_diff"] = sim.boot_diff(P[a][m], P[b][m], unit_prov)
                row["tests"]["%s_vs_%s_%s" % (b, a, m)] = t
        res["repeats"].append(row)
    full = models(ops, lab)
    res["full_data"] = {a: {m: R.rate(d) for m, d in R.outcomes(ops, lab, L).items()} for a, L in full.items()}
    res["anchors"] = {a: anchors(L) for a, L in full.items()}
    res["targets"] = {a: R.target_check(L) for a, L in full.items()}
    json.dump(res, open(os.path.join(outdir, "cv.json"), "w"), indent=1, default=list)
    for r in res["repeats"]:
        print("repeat", r["repeat"], {a: {m: r["rates"][a][m]["yes"] for m in METRICS} for a in ARMS})


if __name__ == "__main__":
    main(sys.argv[1])
