import csv, io, json, os, random, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
R3 = os.path.join(HERE, "..", "field-labelling-r3-20261006")
SCR = "/private/tmp/claude-501/-Users-minhnguyen-IdeaProjects-graduational-thesis/7a0212c0-800c-4a9e-aace-fc2a83778aae/scratchpad/r4"
WHO = {"LA": os.path.join(SCR, "A", "out"), "LB": os.path.join(SCR, "B", "out"), "LM": os.path.join(HERE, "LM")}
SEED = 20261006


def norm_list(s):
    return "|".join(sorted(x.strip() for x in (s or "").split("|") if x.strip()))


def load(who, ids):
    out = {}
    d = WHO[who]
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".csv"):
            continue
        for r in csv.DictReader(io.open(os.path.join(d, fn), encoding="utf-8")):
            rid = (r.get("row_id") or "").strip()
            t = (r.get("T") or "").strip()
            if rid in ids and t in ("0", "1"):
                if t == "0":
                    out[rid] = ("0", "", "", "")
                else:
                    out[rid] = ("1", norm_list(r.get("victim")), norm_list(r.get("role")), (r.get("order") or "").strip())
    return out


def main(mode):
    manifest = json.load(open(os.path.join(HERE, "manifest.json")))
    ids = {rid for v in manifest.values() for rid in v}
    labs = {w: load(w, ids) for w in WHO}
    final, need = {}, []
    for rid in sorted(ids):
        got = [(w, labs[w][rid]) for w in WHO if rid in labs[w]]
        if len(got) < 2:
            continue
        tc = Counter(l[0] for _, l in got)
        t, n = tc.most_common(1)[0]
        if n >= 2 and (len(got) == 3 or n == len(got)):
            if t == "0":
                final[rid] = (("0", "", "", ""), "majority")
                continue
            ones = [l for _, l in got if l[0] == "1"]
            cols = []
            for i in (1, 2, 3):
                c = Counter(l[i] for l in ones).most_common(1)[0]
                cols.append(c[0] if c[1] >= 2 else None)
            if None not in cols:
                final[rid] = (("1", cols[0], cols[1], cols[2]), "majority")
                continue
            need.append((rid, sorted(set(ones)), [w for w, l in got if l[0] == "1"]))
            continue
        opts = sorted({l for _, l in got})
        need.append((rid, opts, [w for w, _ in got]))
    if mode == "items":
        rng = random.Random(SEED)
        rows = {}
        for n in manifest:
            text = open(os.path.join(HERE, "rows", n + ".txt")).read().split("\n## ")
            for block in text:
                block = block if block.startswith("## ") else "## " + block
                rid = block.split()[1] if len(block.split()) > 1 else ""
                rows[rid] = block.strip()
        mapping = []
        with open(os.path.join(SCR, "adj", "items.md"), "w") as fh:
            fh.write("# Các operation cần phân xử\n\n")
            for rid, opts, _ in need:
                o = opts[:]
                rng.shuffle(o)
                letters = "XYZ"[:len(o)]
                fh.write(rows.get(rid, "## " + rid) + "\n\nPhương án:\n")
                for L, l in zip(letters, o):
                    fh.write("- %s: T=%s; victim=%s; role=%s; order=%s\n" % (L, l[0], l[1] or "-", l[2] or "-", l[3] or "-"))
                    mapping.append({"row_id": rid, "letter": L, "T": l[0], "victim": l[1], "role": l[2], "order": l[3]})
                fh.write("\n")
        with open(os.path.join(HERE, "disagreements.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["row_id", "letter", "T", "victim", "role", "order"])
            w.writeheader()
            w.writerows(mapping)
        print("final by majority", len(final), "need adjudication", len(need),
              "coverage", {w: len(labs[w]) for w in WHO})
        return
    adj = {}
    mp = {}
    for r in csv.DictReader(open(os.path.join(HERE, "disagreements.csv"))):
        mp[(r["row_id"], r["letter"])] = ("1" if r["T"] == "1" else "0", r["victim"], r["role"], r["order"])
    araw = os.path.join(HERE, "adjudication-raw.csv")
    if os.path.exists(araw):
        for r in csv.DictReader(open(araw)):
            k = (r["row_id"].strip(), (r.get("choice") or "").strip().upper())
            if k in mp:
                adj[k[0]] = (mp[k], (r.get("reason") or "").strip())
    with open(os.path.join(HERE, "adjudication.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["row_id", "T", "victim", "role", "order", "reason"])
        for rid, (l, why) in sorted(adj.items()):
            w.writerow([rid, l[0], l[1], l[2], l[3], why])
    for rid, opts, who in need:
        if rid in adj:
            final[rid] = (adj[rid][0], "adjudicated")
    specs_new = {}
    for rid in ids:
        specs_new.setdefault(rid.split("-")[0], []).append(rid)
    reverted = sorted(s for s, rs in specs_new.items() if any(r not in final for r in rs))
    with open(os.path.join(HERE, "final-r4.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["row_id", "T", "victim", "role", "order", "source"])
        for rid in sorted(final):
            l, src = final[rid]
            w.writerow([rid, l[0], l[1], l[2], l[3], src])
    keep_new = {rid for rid in final if rid.split("-")[0] not in reverted}
    with open(os.path.join(HERE, "final-all.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["row_id", "T", "victim", "role", "order", "source"])
        for r in csv.DictReader(open(os.path.join(R3, "final.csv"))):
            w.writerow([r["row_id"], r["T"], r["victim"], r["role"], r["order"], "r3:" + r.get("source", "")])
        for rid in sorted(keep_new):
            l, src = final[rid]
            w.writerow([rid, l[0], l[1], l[2], l[3], "r4:" + src])
    json.dump({"reverted_specs": reverted, "new_ops_kept": len(keep_new), "new_ops_final": len(final),
               "new_ops_total": len(ids), "adjudicated": len(adj), "needed_adjudication": len(need),
               "T1_new": sum(1 for rid in keep_new if final[rid][0][0] == "1")},
              open(os.path.join(HERE, "aggregate.json"), "w"), indent=1)
    print(open(os.path.join(HERE, "aggregate.json")).read())


main(sys.argv[1])
