import sys
from collections import Counter, defaultdict
sys.argv = ["x", "RF"]
exec(open("nbcheck_all.py").read().split("flt = sys.argv[1]")[0])
RF = F.models(ops, lab)["RF"]; red = F.fns(RF)[0]
T = [o for o in ops if lab[o["row_id"]]["T"]]
why = Counter(); ex = defaultdict(list)
for o in T:
    L = lab[o["row_id"]]
    if not L["role"] or red(o, RF):
        continue
    fmap = {f["key"]: f for f in o["fields"]}
    for r in L["role"]:
        f = fmap.get(r)
        if f is None:
            k = "label key not in fields"
        else:
            n = f["leaf"]
            nm = any(w in n for w in RF["role"]); am = f["kind"] == "bool" and any(w in n for w in RF["admin"])
            k = "name-matches(%s)" % f["kind"] if nm or am else "name-miss %s" % f["kind"]
        why[k] += 1
        ex[k].append("%s %s %s %s" % (o["spec"], o["method"], o["path"], r))
for k, v in why.most_common():
    print(v, k)
    for e in ex[k][:8]:
        print("     ", e)
spec_T = defaultdict(list)
for o in T:
    spec_T[o["spec"]].append(o)
c = Counter()
for s, ol in spec_T.items():
    if any(red(o, RF) for o in ol):
        c["some T passes RF"] += 1
    elif all(not lab[o["row_id"]]["role"] for o in ol):
        c["all T ops have no role field"] += 1
    else:
        c["has role-labelled T but name/kind missed"] += 1
print("specs with T:", len(spec_T), dict(c))
