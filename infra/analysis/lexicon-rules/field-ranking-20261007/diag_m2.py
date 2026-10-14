import sys, os
sys.path.insert(0, os.getcwd())
import sim_rank as R
from collections import Counter, defaultdict
lab = R.sim.load_labels(os.path.join(R.R4, "final-all.csv"))
ops = R.sim.load_ops(set(lab))
M = R.models(ops, lab)
by = defaultdict(list)
for op in ops: by[op["spec"]].append(op)
for arm in ("RK", "RK2", "RKs"):
    L = M[arm]
    words = Counter(); ex = {}
    for s, ol in by.items():
        if any(lab[o["row_id"]]["T"] for o in ol): continue
        via = R.viable(ol, L)
        if not via: continue
        op = via[0]
        hit = sorted({w for n, k, f in R.r_role_genes(op, L) for w in L["role_gate"] | L.get("bool_gate", set()) if w in n})
        for w in hit:
            words[w] += 1
            ex.setdefault(w, "%s %s %s" % (op["provider"], op["method"], op["path"]))
    print(arm, words.most_common(12))
    for w, _ in words.most_common(5): print("   ", w, ex[w])
