import json, sys
import sim

lab = sim.load_labels("final-all.csv")
ops = sim.load_ops(set(lab))
unit_prov = {op["spec"]: op["provider"] for op in ops}
unit_prov.update({op["row_id"]: op["provider"] for op in ops})
P = sim.cv(ops, lab)[0]["pooled"]
out = {}
for a, b in (("hard", "derived"), ("r3", "derived"), ("hard", "r3")):
    for m in ("M1", "M1any", "M2", "M3", "M4", "M5"):
        out["%s_vs_%s_%s" % (b, a, m)] = dict(sim.mcnemar(P[a][m], P[b][m]), ci95_diff=sim.boot_diff(P[a][m], P[b][m], unit_prov))
json.dump(out, open("extra-tests.json", "w"), indent=1)
for k, v in out.items():
    print(k, v)
