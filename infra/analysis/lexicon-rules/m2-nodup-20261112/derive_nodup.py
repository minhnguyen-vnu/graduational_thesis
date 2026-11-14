import os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
LR = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(LR, "p2-model-20261012"))
import derive_model as D

LABELS = os.path.join(LR, "relabel-20261101", "nop-hoi-dong", "nhan-hoc-cuoi.csv")
OUT = os.path.join(HERE, "stateful-authz-model.csv")
F_LOCS = ("query", "body")


def op_feats_nodup(op):
    fs = {"v:" + op["method"]}
    fs |= {"p:" + t for t in D.X.tokens(op["path"])}
    for f in op["fields"]:
        if f["loc"] in F_LOCS:
            fs |= {"f:" + t for t in D.X.tokens(f["raw_leaf"])}
    return fs


def op_docs_nodup(ops, lab):
    return [(op_feats_nodup(o), o["provider"], lab[o["row_id"]]["T"]) for o in ops]


def load():
    lab = D.sim.load_labels(LABELS)
    ops = D.sim.load_ops(set(lab))
    if len(lab) != 10381 or len(ops) != 10381:
        sys.exit("expected 10381 labels and ops, got %d and %d" % (len(lab), len(ops)))
    return lab, ops


def model_nodup(ops, lab):
    m = D.model(ops, lab)
    w, prior = D.naive_bayes(op_docs_nodup(ops, lab))
    m["op"] = dict(w)
    m["op"][D.PRIOR] = prior
    return m


def main():
    if os.path.exists(OUT):
        sys.exit("output exists: " + OUT)
    lab, ops = load()
    text = D.render(model_nodup(ops, lab))
    with open(OUT, "w", newline="") as fh:
        fh.write(text)
    counts = defaultdict(int)
    for line in text.splitlines()[1:]:
        counts[line.split(",")[0]] += 1
    print("ops %d T %d rows per table %s" % (len(ops), sum(lab[o["row_id"]]["T"] for o in ops), dict(counts)))
    print(OUT)


if __name__ == "__main__":
    main()
