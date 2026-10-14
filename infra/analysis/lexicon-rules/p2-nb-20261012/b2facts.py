import sys
from collections import Counter, defaultdict
exec(open("b1check.py").read().split("for rep, fl in")[0])
T = [o for o in ops if lab[o["row_id"]]["T"]]
kinds = Counter(); orders = defaultdict(list); specs = defaultdict(set)
for o in T:
    L = lab[o["row_id"]]
    for r in L["role"]:
        f = next((x for x in o["fields"] if x["key"] == r), None)
        k = f["kind"] if f else "missing"
        if f and f["loc"] == "path":
            k += "@path"
        kinds[k] += 1; specs[k].add(o["spec"])
        orders[k].append((o["spec"], f["raw_leaf"] if f else r, L["order"], f["enum"][:6] if f else []))
for k, v in kinds.most_common():
    with_order = sum(1 for x in orders[k] if x[2])
    print("%-12s fields %3d specs %2d  with order label %d" % (k, v, len(specs[k]), with_order))
for k in ("bool", "enum", "num", "str", "array"):
    print("==", k)
    seen = set()
    for s, n, od, en in orders[k]:
        if (s, n) in seen: continue
        seen.add((s, n))
        if len(seen) > 9: break
        print("   ", s, n, "| order:", od or "-", "| enum:", en)
