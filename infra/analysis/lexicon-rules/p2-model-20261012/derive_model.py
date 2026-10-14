import io, math, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
LR = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(LR, "lexicon-r4-20261007"))
sys.path.insert(0, os.path.join(LR, "field-ranking-20261007"))
import lexlib as X
import sim_rank as SR

sim = X.sim
OUT = os.path.join(HERE, "stateful-authz-model.csv")
TABLES = ["op", "role", "victim", "low", "high", "lowstr", "highstr"]
PRIOR = "__prior__"
MIN_PROVIDERS = 2


def op_feats(op):
    fs = {"v:" + op["method"]}
    fs |= {"p:" + t for t in X.tokens(op["path"])}
    for f in op["fields"]:
        if f["loc"] in ("path", "query", "body"):
            fs |= {"f:" + t for t in X.tokens(f["raw_leaf"])}
    return fs


def field_feats(f):
    fs = {"k:" + f["kind"], "l:" + f["loc"], "w:" + f["leaf"]}
    fs |= {"n:" + t for t in X.tokens(f["raw_leaf"])}
    for p in [p.replace("[]", "") for p in f["name"].split(".")[:-1]]:
        fs |= {"a:" + t for t in X.tokens(p)}
    for v in f["enum"]:
        fs |= {"e:" + t for t in X.tokens(str(v))}
    return fs


def naive_bayes(docs):
    npos = sum(1 for _, _, pos in docs if pos)
    nneg = len(docs) - npos
    dp, dn, pv = defaultdict(int), defaultdict(int), defaultdict(set)
    for fs, prov, pos in docs:
        for t in fs:
            if pos:
                dp[t] += 1
                pv[t].add(prov)
            else:
                dn[t] += 1
    w = {t: math.log((dp[t] + 1) / (npos + 2)) - math.log((dn[t] + 1) / (nneg + 2))
         for t in dp if len(pv[t]) >= MIN_PROVIDERS}
    return w, math.log(npos / nneg)


def op_docs(ops, lab):
    return [(op_feats(o), o["provider"], lab[o["row_id"]]["T"]) for o in ops]


def role_docs(ops, lab):
    out = []
    for o in ops:
        L = lab[o["row_id"]]
        if not L["T"]:
            continue
        for f in o["fields"]:
            out.append((field_feats(f), o["provider"], f["key"] in L["role"]))
    return out


def victim_docs(ops, lab):
    out = []
    for o in ops:
        L = lab[o["row_id"]]
        if not L["T"] or not L["victim"] or L["victim"] == ["self"]:
            continue
        for f in o["fields"]:
            out.append((field_feats(f), o["provider"], f["key"] in L["victim"]))
    return out


def ranking(ops, lab, side):
    return SR.build(*SR.order_items(ops, lab, side), 1)


def model(ops, lab):
    m = {}
    for name, docs in (("op", op_docs), ("role", role_docs), ("victim", victim_docs)):
        w, prior = naive_bayes(docs(ops, lab))
        m[name] = dict(w)
        m[name][PRIOR] = prior
    for side in ("low", "high"):
        r = ranking(ops, lab, side)
        m[side] = {k: v["score"] for k, v in r.items()}
        m[side + "str"] = {k: v["score"] for k, v in r.items() if v["ncc"] >= 2}
    return m


def render(m):
    buf = io.StringIO()
    buf.write("table,feature,weight\n")
    for t in TABLES:
        rows = m[t]
        keys = ([PRIOR] if PRIOR in rows else []) + sorted(k for k in rows if k != PRIOR)
        for k in keys:
            if any(c in k for c in ',"\r\n'):
                raise ValueError("feature %r of table %s cannot be written as a plain CSV cell" % (k, t))
            buf.write("%s,%s,%r\n" % (t, k, rows[k]))
    return buf.getvalue()


def load():
    lab, ops, _, _ = X.new_data()
    return lab, ops


def main(out):
    lab, ops = load()
    text = render(model(ops, lab))
    with open(out, "w", newline="") as fh:
        fh.write(text)
    counts = defaultdict(int)
    for line in text.splitlines()[1:]:
        counts[line.split(",")[0]] += 1
    print("ops %d labelled T %d | rows per table %s | %s" % (
        len(ops), sum(1 for o in ops if lab[o["row_id"]]["T"]), dict(counts), out))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else OUT)
