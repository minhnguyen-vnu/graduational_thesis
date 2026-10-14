import sys
from collections import Counter, defaultdict
exec(open("b1check.py").read().split("for rep, fl in")[0])
T = [o for o in ops if lab[o["row_id"]]["T"]]
loc = Counter(); kind = Counter(); names = Counter(); special = Counter(); nolab = 0
for o in T:
    v = lab[o["row_id"]]["victim"]
    if not v:
        nolab += 1; continue
    if v == ["self"]:
        special["self"] += 1; continue
    for k in v:
        f = next((x for x in o["fields"] if x["key"] == k), None)
        loc[k.split(":")[0]] += 1
        kind[f["kind"] if f else "missing"] += 1
        names[f["raw_leaf"] if f else k] += 1
print("T ops", len(T), "no victim label", nolab, dict(special))
print("victim loc", dict(loc)); print("victim kind", dict(kind))
print("victim names", names.most_common(25))
RFall = F.models(ops, lab)
for arm in ("V", "RF"):
    LB = RFall[arm]; pick = F.fns(LB)[2]
    ok = sum(1 for o in T if lab[o["row_id"]]["victim"] and lab[o["row_id"]]["victim"] != ["self"] and (lambda v: v is not None and v["key"] in lab[o["row_id"]]["victim"])(pick(o, LB)))
    print(arm, "M3 in-sample", ok)
