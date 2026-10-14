import csv, glob, sys
from gate_words import classes

rows = []
for f in sorted(glob.glob("ops-full/*.csv")):
    with open(f, newline="") as fh:
        r = list(csv.reader(fh))[1:]
    rows.extend(r)

done = set()
for f in sorted(glob.glob("../lexicon-rules/labelling/S*.csv")):
    if ".l1." in f or ".l2." in f or ".human." in f or ".final." in f:
        continue
    with open(f, newline="") as fh:
        for x in list(csv.reader(fh))[1:]:
            done.add(x[0])

per = {}
tot = {"both": 0, "one": 0, "none": 0}
for x in rows:
    s, p = classes(x)
    k = "both" if (s and p) else ("one" if (s or p) else "none")
    tot[k] += 1
    d = per.setdefault(x[1], {"both": 0, "one": 0, "none": 0, "new_both": 0, "new_one": 0, "n": 0})
    d[k] += 1
    d["n"] += 1
    if x[0] not in done:
        if k == "both":
            d["new_both"] += 1
        elif k == "one":
            d["new_one"] += 1

print("full rows", len(rows), "already sampled", len(done), tot)
print("%-6s %5s %5s %5s %5s %9s %8s" % ("spec", "ops", "both", "one", "none", "new_both", "new_one"))
for k in sorted(per):
    d = per[k]
    if d["n"]:
        print("%-6s %5d %5d %5d %5d %9d %8d" % (k, d["n"], d["both"], d["one"], d["none"], d["new_both"], d["new_one"]))

for cb in (8, 10, 12, 15):
    for co in (0, 3, 4, 6):
        t = sum(min(per[k]["new_both"], cb) + min(per[k]["new_one"], co) for k in per)
        print("cap both=%-3d one=%-3d -> new rows %d" % (cb, co, t))
