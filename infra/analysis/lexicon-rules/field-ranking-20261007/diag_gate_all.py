import sys, os
sys.path.insert(0, os.getcwd())
import sim_rank as R
from collections import defaultdict
sim = R.sim
lab = sim.load_labels(os.path.join(R.R4, "final-all.csv"))
ops = sim.load_ops(set(lab))
M = R.models(ops, lab)["RK"]
anyp = defaultdict(set)
for op in ops:
    for f in op["fields"]:
        for w in M["role"]:
            if w in f["leaf"]:
                anyp[w].add(op["provider"])
old = sorted(M["role_gate"])
new = sorted(w for w, s in M["role"].items() if s["ncc"] / len(anyp[w]) >= 0.5)
print("gate T=1 only:", len(old))
print("gate all ops:", len(new), new)
for w in ["code", "create", "client", "post", "custom", "role", "permission", "admin", "level", "restrict", "task"]:
    s = M["role"].get(w)
    if s: print(w, "pos", s["ncc"], "any(T=1)", s["anyp"], "any(all ops)", len(anyp[w]))
