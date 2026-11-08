import os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
LR = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(LR, "p2-model-20261012"))
import derive_model as D

LABELS = os.path.join(LR, "relabel-20261101", "nop-hoi-dong", "nhan-hoc-cuoi.csv")
OUT = os.path.join(HERE, "stateful-authz-model.csv")


def main():
    if os.path.exists(OUT):
        sys.exit("output exists: " + OUT)
    lab = D.sim.load_labels(LABELS)
    ops = D.sim.load_ops(set(lab))
    if len(lab) != 10381 or len(ops) != 10381:
        sys.exit("expected 10381 labels and ops, got %d and %d" % (len(lab), len(ops)))
    text = D.render(D.model(ops, lab))
    with open(OUT, "w", newline="") as fh:
        fh.write(text)
    counts = defaultdict(int)
    for line in text.splitlines()[1:]:
        counts[line.split(",")[0]] += 1
    orders = D.sim.order_docs(ops, lab)
    print("ops %d T %d with role %d with victim %d orderings %d providers-with-ordering %d" % (
        len(ops), sum(lab[o["row_id"]]["T"] for o in ops),
        sum(1 for o in ops if lab[o["row_id"]]["T"] and lab[o["row_id"]]["role"]),
        sum(1 for o in ops if lab[o["row_id"]]["T"] and lab[o["row_id"]]["victim"] and lab[o["row_id"]]["victim"] != ["self"]),
        len(orders), len({p for _, p in orders})))
    print("rows per table", dict(counts))
    print(OUT)


main()
