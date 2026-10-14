import csv, os, sys, tempfile, urllib.request

MODEL_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "analysis", "lexicon-rules", "p2-model-20261012"))
sys.path.insert(0, MODEL_DIR)
import derive_model as D

spec_url, mode = sys.argv[1], sys.argv[2]

m = {}
for r in csv.DictReader(open(os.path.join(MODEL_DIR, "stateful-authz-model.csv"))):
    m.setdefault(r["table"], {})[r["feature"]] = float(r["weight"])


def table(name):
    return m.get(name, {})


def op_score(op):
    return table("op")[D.PRIOR] + sum(table("op").get(t, 0.0) for t in D.op_feats(op))


def field_score(name, f):
    return table(name)[D.PRIOR] + sum(table(name).get(t, 0.0) for t in D.field_feats(f))


def role_field(op):
    best = None
    for f in op["fields"]:
        if f["loc"] == "path":
            continue
        s = field_score("role", f)
        if s > 0 and (best is None or s > best[0]):
            best = (s, f)
    return best[1] if best else None


def victim_field(op, role):
    best = None
    for i, f in enumerate(op["fields"]):
        if f["kind"] not in ("str", "num"):
            continue
        if role is not None and f["key"] == role["key"]:
            continue
        s = field_score("victim", f)
        if best is None or s > best[0]:
            best = (s, f)
    return best[1] if best else None


with tempfile.NamedTemporaryFile("wb", suffix=".json", delete=False) as fh:
    fh.write(urllib.request.urlopen(spec_url).read())
    path = fh.name

ops = D.SR.spec_ops(path)
VERBS = ("PUT", "PATCH", "POST", "DELETE")
for op in ops:
    if op["method"] not in VERBS:
        continue
    for f in op["fields"]:
        f.setdefault("key", "%s:%s" % (f["loc"], f["name"]))
    s = op_score(op)
    rf = role_field(op)
    vf = victim_field(op, rf)
    print("SCORE %s %s %.4f gate=%s role=%s victim=%s" % (
        op["method"], op["path"], s, s > 0,
        rf["name"] if rf else "-", vf["name"] if vf else "-"))
