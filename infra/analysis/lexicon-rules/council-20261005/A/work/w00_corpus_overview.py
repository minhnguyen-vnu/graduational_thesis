"""Tong quan cac file mau trong corpus/: so spec, tang, nua, danh muc."""
import json, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(HERE, "..", "corpus")

for f in sorted(os.listdir(C)):
    if not f.endswith(".json"):
        continue
    d = json.load(open(os.path.join(C, f)))
    if isinstance(d, dict):
        print("==", f, "dict keys", list(d)[:5])
        d = [x for v in d.values() for x in v]
    else:
        print("==", f)
    print("  n =", len(d), "keys =", sorted(d[0].keys()))
    for k in ("pool", "split", "tier", "stratum"):
        if k in d[0]:
            print("  ", k, Counter(a.get(k) for a in d))
    cats = Counter(c for a in d for c in a.get("categories", []))
    print("  categories top:", cats.most_common(8))
