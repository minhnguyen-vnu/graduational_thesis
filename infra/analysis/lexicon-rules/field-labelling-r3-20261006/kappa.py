import csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def norm(s):
    return "|".join(sorted(x.strip() for x in (s or "").split("|") if x.strip()))


def load(who, n):
    p = os.path.join(HERE, who, "chunk-%s.csv" % n)
    out = {}
    for r in csv.DictReader(open(p)):
        out[r["row_id"].strip()] = {"T": (r.get("T") or "0").strip(), "victim": norm(r.get("victim")),
                                     "role": norm(r.get("role")), "order": (r.get("order") or "").strip(),
                                     "sub": (r.get("sub") or "").strip()}
    return out


def ids(n):
    return re.findall(r"^## (\S+)", open(os.path.join(HERE, "rows", "chunk-%s.txt" % n)).read(), re.M)


def kappa(a, b):
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    cats = set(a) | set(b)
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def main(chunks):
    a, b, full_a, full_b, missing = [], [], [], [], {"L1": 0, "L2": 0}
    for n in chunks:
        l1, l2 = load("L1", n), load("L2", n)
        for rid in ids(n):
            x, y = l1.get(rid), l2.get(rid)
            if x is None:
                missing["L1"] += 1
                x = {"T": "0", "victim": "", "role": "", "order": "", "sub": ""}
            if y is None:
                missing["L2"] += 1
                y = {"T": "0", "victim": "", "role": "", "order": "", "sub": ""}
            a.append(x["T"]); b.append(y["T"])
            full_a.append((x["T"], x["victim"], x["role"]) if x["T"] == "1" else ("0",))
            full_b.append((y["T"], y["victim"], y["role"]) if y["T"] == "1" else ("0",))
    res = {"chunks": chunks, "ops": len(a), "T1_L1": a.count("1"), "T1_L2": b.count("1"),
           "kappa_T": round(kappa(a, b), 3),
           "exact_T_victim_role_agree_on_T1_either": sum(1 for x, y in zip(full_a, full_b) if x == y and (x[0] == "1")),
           "T1_either": sum(1 for x, y in zip(a, b) if "1" in (x, y)), "missing_rows": missing}
    return res


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1].split(",")), indent=1))
