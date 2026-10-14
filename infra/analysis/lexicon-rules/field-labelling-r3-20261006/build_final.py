import csv, glob, os

HERE = os.path.dirname(os.path.abspath(__file__))
COLS = ["T", "victim", "role", "order"]


def load(who):
    out = {}
    for p in sorted(glob.glob(os.path.join(HERE, who, "chunk-*.csv"))):
        for r in csv.DictReader(open(p)):
            out[r["row_id"].strip()] = r
    return out


l1, l2 = load("L1"), load("L2")
dis = {r["row_id"]: r for r in csv.DictReader(open(os.path.join(HERE, "disagreements.csv")))}
adj = {r["row_id"].strip(): r for r in csv.DictReader(open(os.path.join(HERE, "adjudication-raw.csv")))}
assert set(adj) == set(dis), (set(dis) - set(adj), set(adj) - set(dis))
won = {"L1": 0, "L2": 0}
with open(os.path.join(HERE, "adjudication.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["row_id", "choice", "winner", "reason"])
    for rid in sorted(dis):
        ch = adj[rid]["choice"].strip()
        assert ch in ("X", "Y"), (rid, ch)
        who = dis[rid][ch]
        won[who] += 1
        w.writerow([rid, ch, who, adj[rid]["reason"]])
with open(os.path.join(HERE, "final.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["row_id", "T", "victim", "role", "order", "source"])
    for rid in sorted(l1):
        if rid in dis:
            who = dis[rid][adj[rid]["choice"].strip()]
            src = l1 if who == "L1" else l2
            w.writerow([rid] + [src[rid].get(c, "") if src[rid].get("T", "0").strip() == "1" or c == "T" else "" for c in COLS] + ["adj-" + who])
        else:
            r = l1[rid]
            w.writerow([rid] + [r.get(c, "") if r.get("T", "0").strip() == "1" or c == "T" else "" for c in COLS] + ["agree"])
print(won)
