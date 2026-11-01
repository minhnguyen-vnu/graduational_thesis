import csv
import glob
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LR = os.path.normpath(os.path.join(HERE, "..", "lexicon-rules"))
R3 = os.path.join(LR, "field-labelling-r3-20261006")
R4 = os.path.join(LR, "field-labelling-r4-20261006")


def block(rows_dir, rid):
    for f in sorted(glob.glob(os.path.join(rows_dir, "chunk-*.txt"))):
        text = open(f, encoding="utf-8").read()
        m = re.search(r"^## " + re.escape(rid) + r"\b.*?(?=^## |\Z)", text, re.S | re.M)
        if m:
            return os.path.basename(f), m.group(0).rstrip()
    return None, None


def labels(folder, names, rid):
    out = {}
    for n in names:
        for f in sorted(glob.glob(os.path.join(folder, n, "chunk-*.csv"))):
            for r in csv.DictReader(open(f, encoding="utf-8")):
                if r["row_id"] == rid:
                    out[n] = ",".join(r[k] for k in ["row_id", "T", "victim", "role", "order", "sub"])
    return out


def final(folder, name, rid):
    for r in csv.DictReader(open(os.path.join(folder, name), encoding="utf-8")):
        if r["row_id"] == rid:
            return r
    return None


for title, folder, names, rid, fin in [
    ("round 3, both labellers agree", R3, ["L1", "L2"], "S101-0104", "final.csv"),
    ("round 4, two of three say T=1", R4, ["LA", "LB", "LM"], "S304-N0080", "final-all.csv"),
    ("round 4, no majority on columns, adjudicated", R4, ["LA", "LB", "LM"], "S330-N0048", "final-all.csv"),
]:
    print("=" * 8, title, rid)
    f, b = block(os.path.join(folder, "rows"), rid)
    print(f"-- what the labeller sees ({os.path.relpath(os.path.join(folder, 'rows', f), LR)})")
    print("\n".join(b.splitlines()[:12]))
    print("-- what each labeller wrote")
    for n, line in labels(folder, names, rid).items():
        print(f"{n}: {line}")
    print("-- final", final(folder, fin, rid))

print("=" * 8, "adjudication rows shown to the adjudicator, S330-N0048")
for r in csv.DictReader(open(os.path.join(R4, "disagreements.csv"), encoding="utf-8")):
    if r["row_id"] == "S330-N0048":
        print(r)
for r in csv.DictReader(open(os.path.join(R4, "adjudication.csv"), encoding="utf-8")):
    if r["row_id"] == "S330-N0048":
        print("adjudicator:", r)

sys.path.insert(0, os.path.join(LR, "p2-model-20261012"))
sys.argv = [sys.argv[0]]
import derive_model as D

lab, ops = D.load()
for name in ["op_docs", "role_docs", "victim_docs"]:
    docs = getattr(D, name)(ops, lab)
    p = sum(1 for _, _, x in docs if x)
    n = len(docs) - p
    print(f"{name}: positive {p}, negative {n}, prior ln({p}/{n}) = {math.log(p / n):.3f}")
