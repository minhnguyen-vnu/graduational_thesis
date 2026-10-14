import csv, glob, json, os, random, re

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 20261006
COLS = ["T", "victim", "role", "order"]


def norm(s):
    return "|".join(sorted(x.strip() for x in (s or "").split("|") if x.strip()))


def load(who):
    out = {}
    for p in sorted(glob.glob(os.path.join(HERE, who, "chunk-*.csv"))):
        for r in csv.DictReader(open(p)):
            t = (r.get("T") or "0").strip()
            out[r["row_id"].strip()] = {"T": t, "victim": norm(r.get("victim")) if t == "1" else "",
                                        "role": norm(r.get("role")) if t == "1" else "",
                                        "order": (r.get("order") or "").strip() if t == "1" else ""}
    return out


def blocks():
    out = {}
    for p in sorted(glob.glob(os.path.join(HERE, "rows", "chunk-*.txt"))):
        for b in open(p).read().split("\n## ")[0:]:
            b = b if b.startswith("## ") else "## " + b
            rid = re.match(r"## (\S+)", b).group(1)
            out[rid] = b.strip()
    return out


def main(outdir):
    l1, l2 = load("L1"), load("L2")
    rng = random.Random(SEED)
    rows, items = [], []
    for rid in sorted(l1):
        a, b = l1[rid], l2[rid]
        if all(a[c] == b[c] for c in COLS):
            continue
        x_is_l1 = rng.random() < 0.5
        x, y = (a, b) if x_is_l1 else (b, a)
        rows.append({"row_id": rid, "X": "L1" if x_is_l1 else "L2", "Y": "L2" if x_is_l1 else "L1",
                     **{"L1_" + c: a[c] for c in COLS}, **{"L2_" + c: b[c] for c in COLS}})
        items.append((rid, x, y))
    with open(os.path.join(HERE, "disagreements.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    bl = blocks()
    with open(os.path.join(outdir, "items.md"), "w") as fh:
        for rid, x, y in items:
            fh.write(bl[rid] + "\n\n")
            for tag, l in (("X", x), ("Y", y)):
                fh.write("%s: T=%s victim=%s role=%s order=%s\n" % (tag, l["T"], l["victim"] or "-", l["role"] or "-", l["order"] or "-"))
            fh.write("\n---\n\n")
    print(len(rows), "disagreements;", sum(1 for r in rows if r["L1_T"] != r["L2_T"]), "on T")


if __name__ == "__main__":
    import sys
    main(sys.argv[1])
