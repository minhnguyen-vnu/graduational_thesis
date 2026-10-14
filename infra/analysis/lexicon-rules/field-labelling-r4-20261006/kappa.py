import csv, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = "/private/tmp/claude-501/-Users-minhnguyen-IdeaProjects-graduational-thesis/7a0212c0-800c-4a9e-aace-fc2a83778aae/scratchpad/r4"
WHO = {"LA": os.path.join(SCR, "A", "out"), "LB": os.path.join(SCR, "B", "out"), "LM": os.path.join(HERE, "LM")}


def load(who, names):
    out = {}
    for n in names:
        p = os.path.join(WHO[who], "chunk-%s.csv" % n)
        if not os.path.exists(p) or os.path.getsize(p) == 0:
            continue
        for r in csv.DictReader(io.open(p, encoding="utf-8")):
            rid = (r.get("row_id") or "").strip()
            t = (r.get("T") or "").strip()
            if rid and t in ("0", "1"):
                out[rid] = r
    return out


def cohen(a, b, ids):
    ids = [i for i in ids if i in a and i in b]
    if not ids:
        return None, 0
    n = len(ids)
    po = sum(1 for i in ids if a[i]["T"] == b[i]["T"]) / n
    pa = sum(1 for i in ids if a[i]["T"] == "1") / n
    pb = sum(1 for i in ids if b[i]["T"] == "1") / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0, n


def fleiss(labs, ids):
    ids = [i for i in ids if all(i in l for l in labs)]
    if not ids:
        return None, 0
    k = len(labs)
    n = len(ids)
    p1 = 0.0
    pi_sum = 0.0
    for i in ids:
        c1 = sum(1 for l in labs if l[i]["T"] == "1")
        c0 = k - c1
        p1 += c1
        pi_sum += (c1 * (c1 - 1) + c0 * (c0 - 1)) / (k * (k - 1))
    p1 /= n * k
    pbar = pi_sum / n
    pe = p1 ** 2 + (1 - p1) ** 2
    return (pbar - pe) / (1 - pe) if pe < 1 else 1.0, n


def main():
    names = sys.argv[1].split(",") if len(sys.argv) > 1 else ["%03d" % i for i in range(1, 87)]
    manifest = json.load(open(os.path.join(HERE, "manifest.json")))
    ids = [rid for n in names for rid in manifest["chunk-" + n]]
    labs = {w: load(w, names) for w in WHO}
    res = {"chunks": len(names), "ops": len(ids)}
    for w in WHO:
        res["coverage_" + w] = sum(1 for i in ids if i in labs[w])
        res["T1_" + w] = sum(1 for i in ids if i in labs[w] and labs[w][i]["T"] == "1")
    for a, b in (("LA", "LB"), ("LA", "LM"), ("LB", "LM")):
        k, n = cohen(labs[a], labs[b], ids)
        res["cohen_%s_%s" % (a, b)] = [round(k, 3) if k is not None else None, n]
    k, n = fleiss([labs["LA"], labs["LB"], labs["LM"]], ids)
    res["fleiss_T"] = [round(k, 3) if k is not None else None, n]
    print(json.dumps(res))
    if len(sys.argv) > 2:
        json.dump(res, open(sys.argv[2], "w"), indent=1)


main()
