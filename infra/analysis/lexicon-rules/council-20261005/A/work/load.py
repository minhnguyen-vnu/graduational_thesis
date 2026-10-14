"""Nap du lieu hai vong, khong ghi file nao ngoai work/.

Tap: train = nua train vong 1 (90 nha cung cap), dev = nua test vong 1 (46), test = vong 2 (92).
Nhan cuoi tinh dung nhu derive_eval.load_final / evaluate.labels: adjudication neu co, khong thi L1 (== L2).
"""
import csv, glob, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
R1 = os.path.join(ROOT, "lexicon-rules", "field-labelling-20261004")
R2 = os.path.join(ROOT, "lexicon-rules", "field-labelling-r2-20261004")
CORPUS = os.path.join(ROOT, "corpus")
R1_META = ("sample-picked.json", "sample-replacements.json", "sample-ext.json", "sample-field.json",
           "sample-field-replacements.json")
R2_META = ("sample-field-r2.json", "sample-field-r2-replacements.json")
EMPTY = ("", "", "", "")
MIN_LEN = 4

# danh sach viet tay, dung nhu RestSecurityBuilder.kt:104, :414, :415, :417, :418, :419
HARD = {
    "A-role": ["role", "plan", "permission", "level", "tier"],
    "A-admin": ["is_admin", "isadmin", "is_superuser", "is_superadmin", "is_staff"],
    "C-specific": ["username", "userid", "user_id", "user", "account", "member", "subject", "principal"],
    "C-email": ["email"],
    "C": ["username", "userid", "user_id", "user", "account", "member", "subject", "principal", "id", "email"],
    "B-low": ["view", "read", "guest", "basic", "free", "member", "user", "none", "restrict", "limited"],
    "B-high": ["admin", "owner", "super", "root", "manage", "write", "edit", "power", "full"],
}


def meta(files):
    out = {}
    for f in files:
        for a in json.load(open(os.path.join(CORPUS, f))):
            out[a["spec_id"]] = a
    return out


def read_labels(d, who):
    lab, chunk = {}, {}
    for p in sorted(glob.glob(os.path.join(d, who, "chunk-*.csv"))):
        c = os.path.basename(p)[6:9]
        for r in csv.DictReader(open(p)):
            k = (r["row_id"], r["field"])
            lab[k] = (r["A"], r["B_low"], r["B_high"], r["C"])
            chunk[k] = c
    return lab, chunk


def read_adj(d):
    return {(r["row_id"], r["field"]): r for r in csv.DictReader(open(os.path.join(d, "adjudication.csv")))}


def row_chunks(d):
    out = {}
    for p in sorted(glob.glob(os.path.join(d, "rows", "chunk-*.txt"))):
        c = os.path.basename(p)[6:9]
        for line in open(p):
            if line.startswith("## "):
                out[line.split()[1]] = c
    return out


def leaf(name):
    return name.split(".")[-1].replace("[]", "").lower()


def raw_leaf(name):
    return name.split(".")[-1].replace("[]", "")


def norm(t):
    return t if t is not None else EMPTY


def load_round(rnd):
    d = R1 if rnd == 1 else R2
    m = meta(R1_META if rnd == 1 else R2_META)
    l1, _ = read_labels(d, "L1")
    l2, _ = read_labels(d, "L2")
    adj = read_adj(d)
    rc = row_chunks(d)
    fields = []
    for line in open(os.path.join(d, "rows.jsonl")):
        r = json.loads(line)
        sp = r["split"] if rnd == 1 else "test"
        if rnd == 1 and sp == "test":
            sp = "dev"
        a = m[r["spec_id"]]
        for i, f in enumerate(r["fields"]):
            k = (r["row_id"], "%s:%s" % (f["loc"], f["name"]))
            v1, v2 = norm(l1.get(k)), norm(l2.get(k))
            if k in adj:
                fin = tuple(adj[k]["final"].split("/"))
            else:
                assert v1 == v2, k
                fin = v1
            fields.append({
                "round": rnd, "split": sp, "row_id": r["row_id"], "spec": r["spec_id"], "provider": a["provider"],
                "pool": a.get("pool", ""), "method": r["method"], "path": r["path"], "summary": r.get("summary", ""),
                "chunk": rc.get(r["row_id"], ""), "idx": i, "loc": f["loc"], "name": f["name"],
                "leaf": leaf(f["name"]), "raw_leaf": raw_leaf(f["name"]), "type": f["type"], "enum": f["enum"],
                "L1": v1, "L2": v2, "adj": k in adj, "adj_row": adj.get(k),
                "A": fin[0], "B_low": fin[1], "B_high": fin[2], "C": fin[3],
                "fields_cut": r.get("fields_cut", 0),
            })
    return fields


def load_all():
    return load_round(1) + load_round(2)


def ops(fields):
    out = {}
    for f in fields:
        out.setdefault(f["row_id"], []).append(f)
    return out


# --- rut tu, chep dung derive_eval.py / common.py ---

def tokens(text):
    out = set()
    for piece in re.split(r"[^A-Za-z0-9]+", text):
        for t in re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+", piece):
            t = t.lower()
            if len(t) >= MIN_LEN and not t.isdigit():
                out.add(t)
    return out


def docs(fields, name, key="leaf"):
    usable = [f for f in fields if f["leaf"] != "(body)"]
    if name == "A-role":
        return [(f[key], f["A"] in ("role", "perms"), f["provider"]) for f in usable]
    if name == "A-admin":
        return [(f[key], f["A"] == "admin", f["provider"]) for f in usable if f["type"] == "boolean" or f["A"] == "admin"]
    if name == "A-active":
        return [(f[key], f["A"] == "active", f["provider"]) for f in usable]
    if name == "C":
        return [(f[key], bool(f["C"]), f["provider"]) for f in usable]
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


def candidates(dd, tok=tokens, lower_doc=True):
    pos = [d for d in dd if d[1]]
    neg = [d for d in dd if not d[1]]
    if not pos:
        return [], 0.0
    base = len(pos) / float(len(dd))
    cand = set()
    for d in pos:
        cand |= tok(d[0])
    stats = []
    for w in sorted(cand):
        hp = [d for d in pos if w in d[0].lower()]
        hn = [d for d in neg if w in d[0].lower()]
        ncc = len({d[2] for d in hp})
        prec = len(hp) / float(len(hp) + len(hn))
        score = (len(hp) + 1) / float(len(hp) + len(hn) + 2) * ncc / float(ncc + 1)
        stats.append({"word": w, "df_pos": len(hp), "df_neg": len(hn), "providers": ncc,
                      "precision": round(prec, 4), "score": round(score, 4)})
    return stats, base


def select(stats, base, rule):
    ok = [s for s in stats if s["providers"] >= 2]
    if rule == "R0":
        kept = [s["word"] for s in ok if s["precision"] >= 2 * base]
    elif rule == "R1":
        kept = [s["word"] for s in ok if s["precision"] >= 0.3]
    elif rule == "R2":
        kept = [s["word"] for s in ok if s["precision"] >= 0.5]
    elif rule == "R3":
        kept = [s["word"] for s in ok if s["score"] >= 0.3]
    elif rule == "R4":
        kept = [s["word"] for s in sorted(ok, key=lambda s: (-s["score"], s["word"]))[:5]]
    else:
        raise ValueError(rule)
    kept = sorted(kept)
    dropped = {b for a in kept for b in kept if a != b and a in b}
    return [w for w in kept if w not in dropped]


def derive(dd, rule="R4", **kw):
    stats, base = candidates(dd, **kw)
    if not stats:
        return [], stats, base
    return select(stats, base, rule), stats, base


def classify(name, words, value, hard_high=None):
    if name == "B-low" and hard_high is not None:
        return any(w in value for w in words) and not any(w in value for w in hard_high)
    if name == "B-low" and words is HARD["B-low"]:
        return any(w in value for w in HARD["B-low"]) and not any(w in value for w in HARD["B-high"])
    return any(value == w or w in value for w in words)


def prf_counts(tp, fp, fn):
    p = tp / float(tp + fp) if tp + fp else 0.0
    r = tp / float(tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f1


def prf(name, words, dd, **kw):
    tp = sum(1 for d in dd if d[1] and classify(name, words, d[0], **kw))
    fp = sum(1 for d in dd if not d[1] and classify(name, words, d[0], **kw))
    fn = sum(1 for d in dd if d[1] and not classify(name, words, d[0], **kw))
    p, r, f1 = prf_counts(tp, fp, fn)
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 3), "recall": round(r, 3), "f1": round(f1, 3)}
