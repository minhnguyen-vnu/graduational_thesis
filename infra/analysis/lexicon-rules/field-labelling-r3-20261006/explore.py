import json, os, random
from collections import defaultdict
import sim

ops = sim.load_ops()
lab = sim.load_labels(os.path.join(sim.HERE, "final.csv"))
unit_prov = {op["spec"]: op["provider"] for op in ops}
unit_prov.update({op["row_id"]: op["provider"] for op in ops})
provs = sorted({op["provider"] for op in ops})
rng = random.Random(sim.SEED)
order = provs[:]
rng.shuffle(order)
folds = [set(order[i::5]) for i in range(5)]
variants = {"hard": defaultdict(dict), "derived_minus_type": defaultdict(dict), "hard_minus_plan_level_tier": defaultdict(dict),
            "derived_plus_hard_admin_email": defaultdict(dict)}
for held in folds:
    train = [op for op in ops if op["provider"] not in held]
    test = [op for op in ops if op["provider"] in held]
    Ld, _ = sim.derive(train, lab, True)
    Lmt = dict(Ld, role=[w for w in Ld["role"] if w != "type"])
    Lh = dict(sim.HARD, role=["role", "permission"])
    Lp = dict(Ld, admin=sim.HARD["admin"], email=["email"])
    for tag, L in (("hard", sim.HARD), ("derived_minus_type", Lmt), ("hard_minus_plan_level_tier", Lh),
                   ("derived_plus_hard_admin_email", Lp)):
        for m, d in sim.outcomes(test, lab, L).items():
            variants[tag][m].update(d)
out = {"note": "exploratory, post hoc, repeat 1 folds", "rates": {}, "tests": {}}
for tag, P in variants.items():
    out["rates"][tag] = {m: sim.rate(P[m]) for m in P}
    if tag != "hard":
        for m in ("M1", "M1any", "M2", "M3", "M4"):
            out["tests"]["%s_vs_hard_%s" % (tag, m)] = dict(sim.mcnemar(variants["hard"][m], P[m]),
                                                           ci95_diff=sim.boot_diff(variants["hard"][m], P[m], unit_prov))
json.dump(out, open(os.path.join(sim.HERE, "exploratory.json"), "w"), indent=1)
for tag, r in out["rates"].items():
    print(tag, {m: (v["yes"], v["n"]) for m, v in r.items()})
for k, v in out["tests"].items():
    print(k, v)
