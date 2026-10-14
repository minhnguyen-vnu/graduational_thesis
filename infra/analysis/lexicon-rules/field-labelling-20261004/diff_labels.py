import csv, glob, json, os

HERE = os.path.dirname(os.path.abspath(__file__))


def load(who):
    out = {}
    for p in sorted(glob.glob(os.path.join(HERE, who, "chunk-*.csv"))):
        for r in csv.DictReader(open(p)):
            out[(r["row_id"], r["field"])] = {k: (r.get(k) or "").strip() for k in ("A", "B_low", "B_high", "C")}
    return out


def main():
    rows = {}
    for l in open(os.path.join(HERE, "rows.jsonl")):
        r = json.loads(l)
        rows[r["row_id"]] = r
    l1, l2 = load("L1"), load("L2")
    empty = {"A": "", "B_low": "", "B_high": "", "C": ""}
    out = []
    for k in sorted(set(l1) | set(l2)):
        a, b = l1.get(k, empty), l2.get(k, empty)
        if a != b:
            r = rows[k[0]]
            f = next((x for x in r["fields"] if "%s:%s" % (x["loc"], x["name"]) == k[1]), {})
            out.append({"row_id": k[0], "field": k[1], "op": "%s %s" % (r["method"], r["path"]),
                        "summary": (r["summary"] or r["description"])[:120], "type": f.get("type", ""),
                        "enum": "|".join(f.get("enum", [])),
                        "L1": "%s/%s/%s/%s" % (a["A"], a["B_low"], a["B_high"], a["C"]),
                        "L2": "%s/%s/%s/%s" % (b["A"], b["B_low"], b["B_high"], b["C"])})
    w = csv.DictWriter(open(os.path.join(HERE, "disagreements.csv"), "w", newline=""), list(out[0].keys()))
    w.writeheader()
    w.writerows(out)
    print(len(out))


main()
