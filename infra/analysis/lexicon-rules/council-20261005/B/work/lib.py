"""Bo nap du lieu chi doc (khong ghi final.csv nhu build()/r2_fields()).

Tai dung ham tokens/leaf/docs/classify/prf/candidates/select cua tac gia qua common.py (vong 2),
de so lieu tu tinh khop dung code goc.
"""
import csv, glob, json, os, sys

W = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(W, "..")
LR = os.path.join(ROOT, "lexicon-rules")
R1 = os.path.join(LR, "field-labelling-20261004")
R2 = os.path.join(LR, "field-labelling-r2-20261004")
CORPUS = os.path.join(ROOT, "corpus")

sys.path.insert(0, R2)
import common as C  # noqa: E402  (chi dinh nghia ham, khong ghi file)

tokens, leaf, docs, classify, prf = C.tokens, C.R1NS["leaf"], C.docs, C.classify, C.prf
candidates, select, derive, HARD = C.candidates, C.select, C.derive, C.HARD


def providers_r1():
    out = {}
    for f in ("sample-picked.json", "sample-replacements.json", "sample-ext.json",
              "sample-field.json", "sample-field-replacements.json"):
        for a in json.load(open(os.path.join(CORPUS, f))):
            out[a["spec_id"]] = a["provider"]
    return out


def providers_r2():
    out = {}
    for f in ("sample-field-r2.json", "sample-field-r2-replacements.json"):
        for a in json.load(open(os.path.join(CORPUS, f))):
            out[a["spec_id"]] = a["provider"]
    return out


def raw_labels(d, who):
    out = {}
    for p in sorted(glob.glob(os.path.join(d, who, "chunk-*.csv"))):
        ch = os.path.basename(p)[6:9]
        for r in csv.DictReader(open(p)):
            out[(r["row_id"], r["field"])] = dict(
                {k: (r.get(k) or "").strip() for k in ("A", "B_low", "B_high", "C")}, chunk=ch)
    return out


def final_labels(d):
    l1, l2 = raw_labels(d, "L1"), raw_labels(d, "L2")
    s = lambda x: "%s/%s/%s/%s" % (x["A"], x["B_low"], x["B_high"], x["C"])
    adj = {(r["row_id"], r["field"]): r for r in csv.DictReader(open(os.path.join(d, "adjudication.csv")))}
    out = {}
    for k in set(l1) | set(l2):
        if k in adj:
            v = adj[k]["final"]
        else:
            # khong lech: L1 == L2 (cung cach so cua tac gia, khong strip)
            v = s(l1[k])
        a, bl, bh, c = v.split("/")
        out[k] = {"A": a, "B_low": bl, "B_high": bh, "C": c, "adj": k in adj}
    return out, l1, l2, adj


def rows(d):
    return [json.loads(l) for l in open(os.path.join(d, "rows.jsonl"))]


def fields(rnd):
    d = R1 if rnd == 1 else R2
    prov = providers_r1() if rnd == 1 else providers_r2()
    lab, _, _, _ = final_labels(d)
    out = []
    for r in rows(d):
        for f in r["fields"]:
            key = (r["row_id"], "%s:%s" % (f["loc"], f["name"]))
            lb = lab.get(key, {"A": "", "B_low": "", "B_high": "", "C": "", "adj": False})
            split = r["split"] if rnd == 1 else "test2"
            if rnd == 1 and "old_label" in r:
                part = "old"
            elif rnd == 1:
                part = "new-" + r["split"]
            else:
                part = "r2"
            out.append({"row_id": r["row_id"], "spec": r["spec_id"], "provider": prov[r["spec_id"]],
                        "split": split, "part": part, "field": key[1], "loc": f["loc"], "name": f["name"],
                        "leaf": leaf(f["name"]), "type": f["type"], "enum": f["enum"],
                        "A": lb["A"] if lb["A"] or lb["C"] else "", "B_low": lb["B_low"] if lb["A"] or lb["C"] else "",
                        "B_high": lb["B_high"] if lb["A"] or lb["C"] else "", "C": lb["C"] if lb["A"] or lb["C"] else "",
                        "method": r["method"], "path": r["path"], "summary": r["summary"],
                        "old_label": r.get("old_label", "")})
    return out


def all_fields():
    f1 = fields(1)
    f2 = fields(2)
    return f1, f2
