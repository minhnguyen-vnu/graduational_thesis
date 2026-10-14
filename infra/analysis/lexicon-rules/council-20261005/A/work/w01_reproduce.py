"""Kiem loader: tai lap so cua select.json, results.json, merged-lists.json bang ma rieng trong work/."""
import json
from load import *

F = load_all()
tr = [f for f in F if f["split"] == "train"]
dv = [f for f in F if f["split"] == "dev"]
te = [f for f in F if f["split"] == "test"]
print("fields train/dev/test", len(tr), len(dv), len(te))
LISTS = ("A-role", "A-admin", "C", "B-low", "B-high")

print("\n# select (train -> dev)")
for rule in ("R0", "R1", "R2", "R3", "R4"):
    f1s = []
    for n in LISTS:
        w, _, _ = derive(docs(tr, n), rule)
        f1s.append(prf(n, w, docs(dv, n))["f1"])
    print(rule, round(sum(f1s) / len(f1s), 4), f1s)

print("\n# evaluate (train+dev -> test), R4")
for n in LISTS + ("A-active",):
    w, _, _ = derive(docs(tr + dv, n), "R4")
    print(n, w, prf(n, w, docs(te, n)), "hard", prf(n, HARD[n], docs(te, n)) if n in HARD else "")

print("\n# merged (train+dev+test), R4")
for n in LISTS + ("A-active",):
    w, _, _ = derive(docs(tr + dv + te, n), "R4")
    print(n, w)
