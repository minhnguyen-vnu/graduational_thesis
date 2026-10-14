import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim_rf as F
R, sim = F.R, F.sim
lab = sim.load_labels(os.path.join(R.R4, "final-all.csv"))
ops = sim.load_ops(set(lab))
byid = {op["row_id"]: op for op in ops}
provs = sorted({op["provider"] for op in ops})
rng = random.Random(sim.SEED)
order = provs[:]
rng.shuffle(order)
folds = [set(order[i::5]) for i in range(5)]
for held in folds:
    train = [op for op in ops if op["provider"] not in held]
    test = [op for op in ops if op["provider"] in held]
    M = F.models(train, lab)
    for op in test:
        l = lab[op["row_id"]]
        if not (l["T"] and "<" in l["order"]):
            continue
        low = [x.strip().lower() for x in l["order"].split("<")[0].split("=") if x.strip()]
        cv_ = sim.reduced_candidates(op, M["V"])
        cr = F.rf_reduced(op, M["RF"])
        okv, okr = bool(cv_) and cv_[0].lower() in low, bool(cr) and cr[0].lower() in low
        if okv != okr:
            print(op["provider"], op["row_id"], op["method"], op["path"], "order", l["order"], "| V first", cv_[:1], okv, "| RF first", cr[:3], okr)
