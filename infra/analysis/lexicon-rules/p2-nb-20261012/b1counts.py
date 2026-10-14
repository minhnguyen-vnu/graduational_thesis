import sys, math
exec(open("b1check.py").read().split("for rep, fl in")[0])
specs = {o["spec"] for o in ops}
tspecs = {o["spec"] for o in ops if lab[o["row_id"]]["T"]}
print("APIs", len(specs), "with T", len(tspecs), "without T", len(specs - tspecs))
print("old29 total", len(old29 & specs), "old29 with T", len(old29 & tspecs), "old29 without T", len((specs - tspecs) & old29))
print("test with T", len(tspecs - old29), "test without T", len((specs - tspecs) - old29))
pos = [(f, o) for o in ops if lab[o["row_id"]]["T"] for f in o["fields"] if f["key"] in lab[o["row_id"]]["role"]]
neg = [(f, o) for o in ops if lab[o["row_id"]]["T"] for f in o["fields"] if f["key"] not in lab[o["row_id"]]["role"]]
for t in ("k:num", "l:body", "k:str", "l:path"):
    a = sum(1 for f, o in pos if t in ffeats(f)); b = sum(1 for f, o in neg if t in ffeats(f))
    pa, pb = (a + 1) / (len(pos) + 2), (b + 1) / (len(neg) + 2)
    print("%s: in %d/%d role fields (%.1f%%), in %d/%d other fields (%.2f%%), ratio %.1f, w %.2f" % (t, a, len(pos), 100 * pa, b, len(neg), 100 * pb, pa / pb, math.log(pa / pb)))
