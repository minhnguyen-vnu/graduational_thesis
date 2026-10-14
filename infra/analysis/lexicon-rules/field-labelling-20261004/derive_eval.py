import csv, glob, json, os, re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "..", "..", "corpus")
MIN_LEN = 4

HARD = {
    "A-role": ["role", "plan", "permission", "level", "tier"],
    "A-admin": ["is_admin", "isadmin", "is_superuser", "is_superadmin", "is_staff"],
    "C": ["username", "userid", "user_id", "user", "account", "member", "subject", "principal", "id", "email"],
    "C-noid": ["username", "userid", "user_id", "user", "account", "member", "subject", "principal", "email"],
    "B-low": ["view", "read", "guest", "basic", "free", "member", "user", "none", "restrict", "limited"],
    "B-high": ["admin", "owner", "super", "root", "manage", "write", "edit", "power", "full"],
}
STRING_LOW = ["user", "viewer", "guest", "member", "basic"]
STRING_HIGH = ["admin", "administrator", "owner", "superuser"]
NUMERIC = ["0", "1", "2"]
VICTIM_FIELDS = ["login", "username", "userName", "user_name", "name", "userId", "user_id", "id", "uid"]


def providers():
    out = {}
    for f in ("sample-picked.json", "sample-replacements.json", "sample-ext.json",
              "sample-field.json", "sample-field-replacements.json"):
        for a in json.load(open(os.path.join(CORPUS, f))):
            out[a["spec_id"]] = a["provider"]
    return out


def leaf(name):
    return name.split(".")[-1].replace("[]", "").lower()


def tokens(text):
    out = set()
    for piece in re.split(r"[^A-Za-z0-9]+", text):
        for t in re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+", piece):
            t = t.lower()
            if len(t) >= MIN_LEN and not t.isdigit():
                out.add(t)
    return out


def load_final():
    agreed = {}
    l1, l2 = {}, {}
    for who, d in (("L1", l1), ("L2", l2)):
        for p in glob.glob(os.path.join(HERE, who, "chunk-*.csv")):
            for r in csv.DictReader(open(p)):
                d[(r["row_id"], r["field"])] = "%s/%s/%s/%s" % (r["A"], r["B_low"], r["B_high"], r["C"])
    adj = {(r["row_id"], r["field"]): r["final"] for r in csv.DictReader(open(os.path.join(HERE, "adjudication.csv")))}
    for k in set(l1) | set(l2):
        v = adj.get(k)
        if v is None:
            assert l1.get(k) == l2.get(k), k
            v = l1[k]
        a, bl, bh, c = v.split("/")
        if a or c:
            agreed[k] = {"A": a, "B_low": bl, "B_high": bh, "C": c, "adjudicated": int(k in adj)}
    return agreed


def build():
    prov = providers()
    lab = load_final()
    fields = []
    for l in open(os.path.join(HERE, "rows.jsonl")):
        r = json.loads(l)
        for f in r["fields"]:
            key = (r["row_id"], "%s:%s" % (f["loc"], f["name"]))
            lb = lab.get(key, {"A": "", "B_low": "", "B_high": "", "C": ""})
            fields.append({"row_id": r["row_id"], "spec": r["spec_id"], "provider": prov[r["spec_id"]],
                           "split": r["split"], "field": key[1], "leaf": leaf(f["name"]), "type": f["type"],
                           "enum": f["enum"], "A": lb["A"], "B_low": lb["B_low"], "B_high": lb["B_high"],
                           "C": lb["C"]})
    with open(os.path.join(HERE, "final.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, ["row_id", "spec", "split", "field", "type", "enum", "A", "B_low", "B_high", "C"],
                           extrasaction="ignore")
        w.writeheader()
        for f in fields:
            if f["A"] or f["C"]:
                w.writerow(dict(f, enum="|".join(f["enum"])))
    return fields


def docs(fields, name):
    usable = [f for f in fields if f["leaf"] != "(body)"]
    if name == "A-role":
        return [(f["leaf"], f["A"] in ("role", "perms"), f["provider"]) for f in usable]
    if name == "A-admin":
        return [(f["leaf"], f["A"] == "admin", f["provider"]) for f in usable if f["type"] == "boolean" or f["A"] == "admin"]
    if name == "A-active":
        return [(f["leaf"], f["A"] == "active", f["provider"]) for f in usable]
    if name in ("C", "C-noid"):
        return [(f["leaf"], bool(f["C"]), f["provider"]) for f in usable]
    if name in ("B-low", "B-high"):
        col = "B_low" if name == "B-low" else "B_high"
        out = []
        for f in fields:
            if f["A"] in ("role", "perms") and f["enum"] and f["B_low"] not in ("", "unordered"):
                for v in f["enum"]:
                    if v:
                        out.append((v.lower(), v == f[col], f["provider"]))
        return out
    raise ValueError(name)


def derive(dd):
    pos = [d for d in dd if d[1]]
    neg = [d for d in dd if not d[1]]
    if not pos:
        return [], [], 0.0
    base = len(pos) / float(len(dd))
    cand = set()
    for d in pos:
        cand |= tokens(d[0])
    stats = []
    for w in sorted(cand):
        hp = [d for d in pos if w in d[0]]
        hn = [d for d in neg if w in d[0]]
        ncc = len({d[2] for d in hp})
        prec = len(hp) / float(len(hp) + len(hn))
        stats.append({"word": w, "df_pos": len(hp), "df_neg": len(hn), "providers": ncc,
                      "precision": round(prec, 4),
                      "score": round((len(hp) + 1) / float(len(hp) + len(hn) + 2) * ncc / float(ncc + 1), 4),
                      "p1": int(ncc >= 2), "p2": int(prec >= 2 * base)})
    kept = sorted(s["word"] for s in stats if s["p1"] and s["p2"])
    dropped = {b for a in kept for b in kept if a != b and a in b}
    final = [w for w in kept if w not in dropped]
    for s in stats:
        s["p3"] = int(s["word"] in final)
    return final, stats, base


def classify(name, words, value):
    if name == "B-low" and words is HARD["B-low"]:
        return any(w in value for w in HARD["B-low"]) and not any(w in value for w in HARD["B-high"])
    return any(value == w or w in value for w in words)


def prf(name, words, dd):
    tp = sum(1 for d in dd if d[1] and classify(name, words, d[0]))
    fp = sum(1 for d in dd if not d[1] and classify(name, words, d[0]))
    fn = sum(1 for d in dd if d[1] and not classify(name, words, d[0]))
    p = tp / float(tp + fp) if tp + fp else 0.0
    r = tp / float(tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 3), "recall": round(r, 3), "f1": round(f1, 3),
            "pos": tp + fn, "pos_providers": len({d[2] for d in dd if d[1]})}


def hard_word_support(name, stats, dd_train):
    pos = [d for d in dd_train if d[1]]
    neg = [d for d in dd_train if not d[1]]
    out = []
    for w in HARD[name]:
        hp = [d for d in pos if w in d[0]]
        hn = [d for d in neg if w in d[0]]
        out.append({"word": w, "df_pos": len(hp), "df_neg": len(hn), "providers": len({d[2] for d in hp})})
    return out


def value_coverage(fields, split):
    rows = [f for f in fields if f["split"] == split and f["A"] in ("role", "perms") and f["enum"]
            and f["B_low"] not in ("", "unordered")]
    low_hit = sum(1 for f in rows if f["B_low"].lower() in STRING_LOW)
    high_hit = sum(1 for f in rows if f["B_high"].lower() in STRING_HIGH)
    any_low = sum(1 for f in rows if any(v.lower() in STRING_LOW for v in f["enum"]))
    numeric = sum(1 for f in rows if all(re.fullmatch(r"-?\d+", v or "x") for v in f["enum"] if v))
    return {"enum_role_fields": len(rows), "string_low_equals_B_low": low_hit,
            "string_high_equals_B_high": high_hit, "string_low_in_enum": any_low, "numeric_enums": numeric,
            "role_fields_without_enum": sum(1 for f in fields if f["split"] == split and f["A"] in ("role", "perms")
                                             and not f["enum"])}


def victim_coverage(fields, split):
    c = [f for f in fields if f["split"] == split and f["C"] and f["field"].startswith("body:")]
    names = {v.lower() for v in VICTIM_FIELDS}
    return {"C_body_fields": len(c), "leaf_in_victim_fields": sum(1 for f in c if f["leaf"] in names)}


def main():
    fields = build()
    train = [f for f in fields if f["split"] == "train"]
    test = [f for f in fields if f["split"] == "test"]
    report = {"counts": {}, "lists": {}, "values": {}, "victim": {}}
    for sp, ff in (("train", train), ("test", test)):
        report["counts"][sp] = {
            "fields": len(ff), "ops": len({f["row_id"] for f in ff}), "specs": len({f["spec"] for f in ff}),
            "providers": len({f["provider"] for f in ff}),
            "A": {k: sum(1 for f in ff if f["A"] == k) for k in ("role", "perms", "admin", "active")},
            "C": {k: sum(1 for f in ff if f["C"] == k) for k in ("name", "id", "email")},
            "providers_with_A": len({f["provider"] for f in ff if f["A"]}),
            "providers_with_C": len({f["provider"] for f in ff if f["C"]})}
    os.makedirs(os.path.join(HERE, "lists"), exist_ok=True)
    for name in ("A-role", "A-admin", "A-active", "C", "B-low", "B-high"):
        dtr, dte = docs(train, name), docs(test, name)
        words, stats, base = derive(dtr)
        with open(os.path.join(HERE, "lists", "candidates-%s.csv" % name), "w", newline="") as fh:
            w = csv.DictWriter(fh, ["word", "df_pos", "df_neg", "providers", "precision", "score", "p1", "p2", "p3"])
            w.writeheader()
            w.writerows(sorted(stats, key=lambda s: (-s["p3"], -s["score"], s["word"])))
        open(os.path.join(HERE, "lists", "list-%s.txt" % name), "w").write("\n".join(words) + ("\n" if words else ""))
        entry = {"base_rate_train": round(base, 4), "derived": words,
                 "derived_test": prf(name, words, dte), "derived_train": prf(name, words, dtr)}
        hk = name if name in HARD else None
        if hk:
            entry["hard_test"] = prf(name, HARD[hk], dte)
            entry["hard_train"] = prf(name, HARD[hk], dtr)
            entry["hard_word_support_train"] = hard_word_support(hk, stats, dtr)
        if name == "C":
            entry["hard_noid_test"] = prf(name, HARD["C-noid"], dte)
        report["lists"][name] = entry
    for sp in ("train", "test"):
        report["values"][sp] = value_coverage(fields, sp)
        report["victim"][sp] = victim_coverage(fields, sp)
    json.dump(report, open(os.path.join(HERE, "results.json"), "w"), indent=1)
    print(json.dumps(report, indent=1))


main()
