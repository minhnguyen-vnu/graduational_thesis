"""(1) Tai lap so cua tac gia bang bo nap chi doc; (2) tinh lai kappa + do dong y duong tinh (PA)
theo tung phan (old / new-train / new-test(dev) / r2)."""
import json, os
from collections import Counter, defaultdict
from lib import *

f1, f2 = all_fields()
tr = [f for f in f1 if f["split"] == "train"]
dev = [f for f in f1 if f["split"] == "test"]

print("== tai lap danh sach (phai khop results.json)")
for name in ("A-role", "A-admin", "A-active", "C", "B-low", "B-high"):
    w0, _, _ = derive(docs(tr, name), "R0")
    w4, _, _ = derive(docs(f1, name), "R4")
    print(" ", name, "R0(train r1)=", w0, "| R4(train+dev)=", w4, "| test:", prf(name, w4, docs(f2, name)))

print("\n== kappa tinh lai, theo phan")


def kappa(pairs):
    n = len(pairs)
    cats = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    po = sum(1 for a, b in pairs if a == b) / n
    pe = sum((sum(1 for a, _ in pairs if a == c) / n) * (sum(1 for _, b in pairs if b == c) / n) for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


for rnd, ff, d in ((1, f1, R1), (2, f2, R2)):
    _, l1, l2, adj = final_labels(d)
    groups = defaultdict(list)
    for f in ff:
        k = (f["row_id"], f["field"])
        groups[f["part"]].append(k)
        groups["ALL"].append(k)
    for part, keys in sorted(groups.items()):
        for col in ("A", "C"):
            p = [("1" if (l1.get(k) or {}).get(col) else "0", "1" if (l2.get(k) or {}).get(col) else "0") for k in keys]
            both = sum(1 for a, b in p if a == b == "1")
            only1 = sum(1 for a, b in p if a == "1" and b == "0")
            only2 = sum(1 for a, b in p if a == "0" and b == "1")
            pa = 2 * both / (2 * both + only1 + only2) if both + only1 + only2 else float("nan")
            print("  r%d %-9s %s fields=%5d L1+=%3d L2+=%3d both=%3d onlyL1=%3d onlyL2=%3d kappa=%.3f PA(dong y duong)=%.3f"
                  % (rnd, part, col, len(keys), both + only1, both + only2, both, only1, only2, kappa(p), pa))

print("\n== phan xu: ai thang, theo luat")
for rnd, d in ((1, R1), (2, R2)):
    import csv
    rows_ = list(csv.DictReader(open(os.path.join(d, "adjudication.csv"))))
    print("  r%d" % rnd, Counter(r["chosen"] for r in rows_), "| so dong", len(rows_))
    print("     theo luat:", dict(Counter((r["rule"], r["chosen"]) for r in rows_)))
