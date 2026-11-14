import csv, os, sys, tempfile, urllib.request

LR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "analysis", "lexicon-rules"))
sys.path.insert(0, os.path.join(LR, "p2-model-20261012"))
sys.path.insert(0, os.path.join(LR, "m2-nodup-20261112"))
import derive_model as D
import derive_nodup as N

MODELS = {"nodup": (os.path.join(LR, "m2-nodup-20261112", "stateful-authz-model.csv"), N.op_feats_nodup),
          "m2": (os.path.join(LR, "m2-model-20261107", "stateful-authz-model.csv"), D.op_feats),
          "nodup-pathf": (os.path.join(LR, "m2-nodup-20261112", "stateful-authz-model.csv"), D.op_feats)}
VERBS = ("PUT", "PATCH", "POST", "DELETE")

spec_url, which = sys.argv[1], sys.argv[2]
path, feats = MODELS[which]
table = {}
for r in csv.DictReader(open(path)):
    if r["table"] == "op":
        table[r["feature"]] = float(r["weight"])

with tempfile.NamedTemporaryFile("wb", suffix=".json", delete=False) as fh:
    fh.write(urllib.request.urlopen(spec_url).read())
    spec = fh.name

for op in D.SR.spec_ops(spec):
    if op["method"] not in VERBS:
        continue
    s = table[D.PRIOR] + sum(table.get(t, 0.0) for t in feats(op))
    print("SCORE %s:%s %r" % (op["method"], op["path"], s))
