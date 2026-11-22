import collections
import csv
import math
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(BASE)
W2 = os.path.join(RES, "tr2-wave2-20261121")

ARMS = [
    ("reports-api", "vuln", "t1-vuln", 20), ("reports-api", "fixed", "t1-fixed", 20),
    ("vampi-seeded", "vuln", "t2-ours-vuln", 20), ("vampi-seeded", "fixed", "t2-ours-fixed", 20),
    ("pyLoad", "vuln", "t2b-vuln", 5), ("pyLoad", "fixed", "t2b-fixed", 5),
    ("artifact-keeper", "vuln", "ak-vuln", 5), ("artifact-keeper", "fixed", "ak-fixed", 5),
]
TRIPLE = re.compile(r"triple on (\S+) \(victim '([^']*)', operator '([^']*)', transition (\S+), statuses ([0-9/]+)")
CODES = re.compile(r"codes ([0-9/-]+)\)")


def builder_lines(path):
    with open(path, errors="replace") as fh:
        return [line.rstrip("\n") for line in fh if line.startswith("* ")]


def mine(lines):
    c = collections.Counter()
    triples = []
    for line in lines:
        if line.startswith("* Assembled a stateful"):
            triples.append(TRIPLE.search(line).groups())
        elif "Discarded an UNCONFIRMED" in line:
            c["UNCONFIRMED"] += 1
        elif "Discarded a VOID" in line:
            c["VOID " + CODES.search(line).group(1)] += 1
        elif "Privilege-restore accepted" in line:
            c["restore accepted"] += 1
        elif "Privilege-restore refused" in line:
            c["restore refused"] += 1
        elif "re-login probe INCONCLUSIVE" in line:
            c["C4 INCONCLUSIVE: " + line.split("INCONCLUSIVE: ")[1]] += 1
        elif "victim is skipped" in line:
            c["victim skipped"] += 1
    return c, triples


for target, arm, tag, n in ARMS:
    logs = os.path.join(W2 if target == "artifact-keeper" else BASE, "logs")
    total = collections.Counter()
    print("== %s %s" % (target, arm))
    for seed in range(1, n + 1):
        c, triples = mine(builder_lines(os.path.join(logs, "%s-seed%d.log" % (tag, seed))))
        total += c
        void = sum(v for k, v in c.items() if k.startswith("VOID"))
        print("  seed %-2d triples %d UNCONFIRMED %d VOID %d | %s" % (
            seed, len(triples), c["UNCONFIRMED"], void,
            "; ".join("%s victim %s operator %s %s" % (t[0], t[1], t[2], t[4]) for t in triples)))
    for k in sorted(total):
        print("  total %s: %d" % (k, total[k]))


def det_rows(w1, w2_files):
    d = {}
    for r in csv.DictReader(open(w1)):
        d[(r["tier"], r["arm"], int(r["seed"]))] = r["det970"]
    for arm, path in w2_files:
        if os.path.exists(path):
            for r in csv.DictReader(open(path)):
                d[("ak", arm, int(r["seed"]))] = r["det970"]
    return d


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


LF = det_rows(os.path.join(RES, "lf-wave1-20261118", "runs.csv"),
              [("vuln", os.path.join(RES, "lf-wave2-20261118", "runs-ak-vuln.csv")),
               ("fixed", os.path.join(RES, "lf-wave2-20261118", "runs-ak-fixed.csv"))])
CS2 = det_rows(os.path.join(RES, "cs2-wave1-20261121", "runs.csv"),
               [("vuln", os.path.join(RES, "cs2-wave2-20261121", "runs-ak-vuln.csv"))])
TR2 = det_rows(os.path.join(BASE, "runs.csv"),
               [("vuln", os.path.join(W2, "runs-ak-vuln.csv")), ("fixed", os.path.join(W2, "runs-ak-fixed.csv"))])

print("== det970 paired by (target, arm, seed), McNemar exact two-sided")
for name_a, a, name_b, b in (("LF", LF, "CS2", CS2), ("CS2", CS2, "TR2", TR2), ("LF", LF, "TR2", TR2)):
    keys = sorted(set(a) & set(b))
    bad = [k for k in keys if a[k] not in ("0", "1") or b[k] not in ("0", "1")]
    lost = [k for k in keys if a[k] == "1" and b[k] == "0"]
    gained = [k for k in keys if a[k] == "0" and b[k] == "1"]
    print("  %s vs %s: %d rows paired, %d bad, lost %d %s, gained %d %s, p = %.4f" % (
        name_a, name_b, len(keys), len(bad), len(lost), lost, len(gained), gained, mcnemar(len(lost), len(gained))))
