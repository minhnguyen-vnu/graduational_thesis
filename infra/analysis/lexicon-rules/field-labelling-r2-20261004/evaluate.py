import csv, glob, json, os
from fractions import Fraction
from math import comb
from common import *

CORPUS = os.path.join(HERE, "..", "..", "corpus")
EVAL = ("A-role", "A-admin", "A-active", "C", "B-low", "B-high")

ANCHOR = [
    ("reports-api", ["role"], "role", ["username"], "VIEWER", "ADMIN"),
    ("vampi-seeded", ["role"], "role", ["username"], "user", "admin"),
    ("pyLoad", ["permission", "role"], "role", ["user"], None, None),
    ("artifact-keeper", ["is_admin"], "admin", ["id"], None, None),
    ("Airflow", ["roles"], "perms", ["username"], None, None),
    ("bamf", [], None, ["email"], None, None),
]


def providers():
    out = {}
    for f in ("sample-field-r2.json", "sample-field-r2-replacements.json"):
        for a in json.load(open(os.path.join(CORPUS, f))):
            out[a["spec_id"]] = a["provider"]
    return out


def labels():
    l1, l2 = {}, {}
    for who, d in (("L1", l1), ("L2", l2)):
        for p in glob.glob(os.path.join(HERE, who, "chunk-*.csv")):
            for r in csv.DictReader(open(p)):
                d[(r["row_id"], r["field"])] = "%s/%s/%s/%s" % (r["A"], r["B_low"], r["B_high"], r["C"])
    adj = {(r["row_id"], r["field"]): r["final"] for r in csv.DictReader(open(os.path.join(HERE, "adjudication.csv")))}
    out = {}
    for k in set(l1) | set(l2):
        v = adj.get(k)
        if v is None:
            assert l1.get(k) == l2.get(k), k
            v = l1[k]
        a, bl, bh, c = v.split("/")
        if a or c:
            out[k] = {"A": a, "B_low": bl, "B_high": bh, "C": c}
    return out


def r2_fields():
    prov = providers()
    lab = labels()
    fields = []
    for l in open(os.path.join(HERE, "rows.jsonl")):
        r = json.loads(l)
        for f in r["fields"]:
            key = (r["row_id"], "%s:%s" % (f["loc"], f["name"]))
            lb = lab.pop(key, {"A": "", "B_low": "", "B_high": "", "C": ""})
            fields.append({"row_id": r["row_id"], "spec": r["spec_id"], "provider": prov[r["spec_id"]],
                           "split": "test2", "field": key[1], "leaf": R1NS["leaf"](f["name"]), "type": f["type"],
                           "enum": f["enum"], "A": lb["A"], "B_low": lb["B_low"], "B_high": lb["B_high"],
                           "C": lb["C"]})
    assert not lab, sorted(lab)[:5]
    with open(os.path.join(HERE, "final.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, ["row_id", "spec", "field", "type", "enum", "A", "B_low", "B_high", "C"],
                           extrasaction="ignore")
        w.writeheader()
        for f in fields:
            if f["A"] or f["C"]:
                w.writerow(dict(f, enum="|".join(f["enum"])))
    return fields


def exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, float(2 * Fraction(sum(comb(n, i) for i in range(0, k + 1)), 2 ** n)))


def mcnemar(name, hard, words, dd):
    b = c = both = neither = 0
    for d in dd:
        hc = classify(name, hard, d[0]) == d[1]
        dc = classify(name, words, d[0]) == d[1]
        if hc and dc:
            both += 1
        elif hc:
            b += 1
        elif dc:
            c += 1
        else:
            neither += 1
    return {"docs": len(dd), "both_correct": both, "only_hard_correct": b, "only_final_correct": c,
            "both_wrong": neither, "p_exact": round(exact(b, c), 6)}


def counts(ff):
    return {"fields": len(ff), "ops": len({f["row_id"] for f in ff}), "specs": len({f["spec"] for f in ff}),
            "providers": len({f["provider"] for f in ff}),
            "A": {k: sum(1 for f in ff if f["A"] == k) for k in ("role", "perms", "admin", "active")},
            "C": {k: sum(1 for f in ff if f["C"] == k) for k in ("name", "id", "email")},
            "providers_with_A": len({f["provider"] for f in ff if f["A"]}),
            "providers_with_C": len({f["provider"] for f in ff if f["C"]})}


def anchor(final):
    out = []
    for target, afields, kind, cfields, low, high in ANCHOR:
        row = {"target": target, "A": [], "C": [], "B": None}
        alist = "A-admin" if kind == "admin" else "A-role"
        for n in afields:
            row["A"].append({"field": n, "list": alist, "hard": classify(alist, HARD[alist], n),
                             "final": classify(alist, final[alist], n)})
        for n in cfields:
            row["C"].append({"field": n, "hard": classify("C", HARD["C"], n), "hard_noid": classify("C", HARD["C-noid"], n),
                             "final": classify("C", final["C"], n)})
        if low:
            lo, hi = low.lower(), high.lower()
            row["B"] = {"low": low, "high": high,
                        "hard_low_hit": classify("B-low", HARD["B-low"], lo),
                        "hard_high_hit": classify("B-high", HARD["B-high"], hi),
                        "hard_high_as_low": classify("B-low", HARD["B-low"], hi),
                        "final_low_hit": classify("B-low", final["B-low"], lo),
                        "final_high_hit": classify("B-high", final["B-high"], hi),
                        "final_high_as_low": classify("B-low", final["B-low"], hi)}
        out.append(row)
    return out


def main():
    dev_train = r1_fields()
    test = r2_fields()
    report = {"rule": "R4", "counts": {"train_dev": counts(dev_train), "test": counts(test)}, "lists": {}}
    final = {}
    os.makedirs(os.path.join(HERE, "lists"), exist_ok=True)
    for name in EVAL:
        dtd, dte = docs(dev_train, name), docs(test, name)
        words, stats, base = derive(dtd, "R4")
        r0, _, _ = derive(dtd, "R0")
        final[name] = words
        with open(os.path.join(HERE, "lists", "candidates-%s.csv" % name), "w", newline="") as fh:
            w = csv.DictWriter(fh, ["word", "df_pos", "df_neg", "providers", "precision", "score"])
            w.writeheader()
            w.writerows(sorted(stats, key=lambda s: (-s["score"], s["word"])))
        open(os.path.join(HERE, "lists", "list-%s.txt" % name), "w").write("\n".join(words) + ("\n" if words else ""))
        e = {"base_rate_train_dev": round(base, 4), "final": words, "r0": r0,
             "final_test": prf(name, words, dte), "r0_test": prf(name, r0, dte)}
        if name in HARD:
            e["hard_test"] = prf(name, HARD[name], dte)
            e["mcnemar_hard_vs_final"] = mcnemar(name, HARD[name], words, dte)
            e["hard_word_support_train_dev"] = R1NS["hard_word_support"](name, stats, dtd)
        if name == "C":
            e["hard_noid_test"] = prf(name, HARD["C-noid"], dte)
            e["mcnemar_hard_noid_vs_final"] = mcnemar(name, HARD["C-noid"], words, dte)
        report["lists"][name] = e
    final["C-noid"] = HARD["C-noid"]
    report["values_test"] = R1NS["value_coverage"](test, "test2")
    report["victim_test"] = R1NS["victim_coverage"](test, "test2")
    report["anchor"] = anchor(final)
    json.dump(report, open(os.path.join(HERE, "results.json"), "w"), indent=1)
    json.dump({n: report["lists"][n].get("mcnemar_hard_vs_final") for n in HARD if n in report["lists"]} |
              {"C-noid": report["lists"]["C"]["mcnemar_hard_noid_vs_final"]},
              open(os.path.join(HERE, "mcnemar.json"), "w"), indent=1)
    json.dump(report["anchor"], open(os.path.join(HERE, "anchor.json"), "w"), indent=1)
    print(json.dumps(report["counts"], indent=1))
    for n in EVAL:
        e = report["lists"][n]
        print(n, "final", e["final"], e["final_test"], "| hard", e.get("hard_test"), "| r0", len(e["r0"]), e["r0_test"]["f1"])
        if "mcnemar_hard_vs_final" in e:
            print("   mcnemar", e["mcnemar_hard_vs_final"])
    print("C-noid", report["lists"]["C"]["hard_noid_test"], report["lists"]["C"]["mcnemar_hard_noid_vs_final"])
    print(report["values_test"], report["victim_test"])
    print(json.dumps(report["anchor"]))


main()
