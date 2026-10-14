import sys
from collections import Counter, defaultdict
sys.argv = ["x", "RF"]
exec(open("nbcheck_all.py").read().split("flt = sys.argv[1]")[0])
RF = F.models(ops, lab)["RF"]; red = F.fns(RF)[0]
HARDred = sim.reduced_candidates
print("RF lists role", RF["role"], "admin", RF["admin"])
T = [o for o in ops if lab[o["row_id"]]["T"]]
cat = Counter(); ex = defaultdict(list); names = Counter()
for o in T:
    L = lab[o["row_id"]]
    has_role = bool(L["role"])
    p_rf = bool(red(o, RF)); p_h = bool(HARDred(o, sim.HARD))
    if has_role:
        for r in L["role"]:
            names[r.split(":", 1)[1].split(".")[-1].replace("[]", "").lower()] += 1
    k = ("role-labelled" if has_role else "no-role-field", "RF pass" if p_rf else "RF fail")
    cat[k] += 1
    ex[k].append("%s %s %s role=%s" % (o["spec"], o["method"], o["path"], "|".join(L["role"])))
for k, v in sorted(cat.items()):
    print(k, v)
    for e in ex[k][:6]:
        print("    ", e)
print("labelled role field leaf names (top 30):", names.most_common(30))
print("method of no-role T ops:", Counter(o["method"] for o in T if not lab[o["row_id"]]["role"]))
