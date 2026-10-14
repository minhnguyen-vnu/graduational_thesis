import csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def universe(chunks):
    rows = [json.loads(l) for l in open(os.path.join(HERE, "rows.jsonl"))]
    ids = set()
    for c in chunks:
        for line in open(os.path.join(HERE, "rows", "chunk-%s.txt" % c)):
            if line.startswith("## "):
                ids.add(line.split()[1])
    out = []
    for r in rows:
        if r["row_id"] in ids:
            for f in r["fields"]:
                out.append((r["row_id"], "%s:%s" % (f["loc"], f["name"])))
    return out


def labels(who, chunks):
    lab = {}
    for c in chunks:
        p = os.path.join(HERE, who, "chunk-%s.csv" % c)
        for r in csv.DictReader(open(p)):
            lab[(r["row_id"], r["field"])] = r
    return lab


def kappa(pairs):
    n = len(pairs)
    if n == 0:
        return float("nan"), 0, 0
    cats = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    po = sum(1 for a, b in pairs if a == b) / n
    pe = sum((sum(1 for a, _ in pairs if a == c) / n) * (sum(1 for _, b in pairs if b == c) / n) for c in cats)
    k = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    return k, po, pe


def report(chunks):
    u = universe(chunks)
    l1, l2 = labels("L1", chunks), labels("L2", chunks)
    unknown = [k for k in set(l1) | set(l2) if k not in set(u)]
    def g(lab, k, col):
        r = lab.get(k)
        return (r[col] if r else "") or ""
    res = {}
    res["fields"] = len(u)
    res["unmatched_label_keys"] = len(unknown)
    for name, f in (("A_bin", lambda lab, k: "1" if g(lab, k, "A") else "0"),
                    ("A_kind", lambda lab, k: g(lab, k, "A") or "-"),
                    ("C_bin", lambda lab, k: "1" if g(lab, k, "C") else "0"),
                    ("C_kind", lambda lab, k: g(lab, k, "C") or "-")):
        pairs = [(f(l1, k), f(l2, k)) for k in u]
        k, po, pe = kappa(pairs)
        res[name] = {"kappa": round(k, 3), "po": round(po, 4), "pe": round(pe, 4),
                     "pos_L1": sum(1 for a, _ in pairs if a not in ("0", "-")),
                     "pos_L2": sum(1 for _, b in pairs if b not in ("0", "-"))}
    return res


if __name__ == "__main__":
    print(json.dumps(report(sys.argv[1].split(",")), indent=1))
