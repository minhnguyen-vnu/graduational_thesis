import csv, io, json, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "..", "..", "corpus")
sys.path.insert(0, CORPUS)
from extract_ops import load, deref, unwrap_envelope

WRITE = ("post", "put", "patch", "delete")
MAX_DEPTH = 3
MAX_FIELDS = 80
MAX_ENUM = 12
CAP = 36
SEED = 20261004


def merged(doc, sch, depth=0):
    s = deref(doc, sch)
    if depth > 6 or not isinstance(s, dict):
        return {}
    parts = [p for k in ("allOf", "oneOf", "anyOf") for p in (s.get(k) or [])]
    if not parts:
        return s
    props = dict(s.get("properties") or {})
    out = dict(s)
    for p in parts:
        m = merged(doc, p, depth + 1)
        for k, v in (m.get("properties") or {}).items():
            props.setdefault(k, v)
        for k in ("type", "enum", "items"):
            if k in m and k not in out:
                out[k] = m[k]
    out["properties"] = props
    return out


def type_of(s):
    t = s.get("type")
    if isinstance(t, list):
        t = next((x for x in t if x != "null"), t[0] if t else "")
    if not t and s.get("properties"):
        t = "object"
    if not t and s.get("enum"):
        t = "string"
    return t or "any"


def enum_of(s):
    e = s.get("enum")
    if isinstance(e, list):
        return [str(v) for v in e if v is not None][:MAX_ENUM]
    return []


def walk(doc, name, sch, depth, out):
    s = merged(doc, sch)
    t = type_of(s)
    if t == "array" and isinstance(s.get("items"), dict):
        it = merged(doc, s["items"])
        it_t = type_of(it)
        out.append(("body", name, "array<%s>" % it_t, enum_of(it) or enum_of(s)))
        if it.get("properties") and depth < MAX_DEPTH:
            for k, v in it["properties"].items():
                walk(doc, "%s[].%s" % (name, k), v, depth + 1, out)
        return
    out.append(("body", name, t, enum_of(s)))
    if s.get("properties") and depth < MAX_DEPTH:
        for k, v in s["properties"].items():
            walk(doc, "%s.%s" % (name, k), v, depth + 1, out)


def body_schema(doc, op):
    rb = deref(doc, op.get("requestBody") or {})
    for ct in (rb.get("content") or {}).values():
        if isinstance(ct, dict) and ct.get("schema"):
            return ct["schema"]
    for pm in op.get("parameters") or []:
        pm = deref(doc, pm)
        if pm.get("in") == "body" and pm.get("schema"):
            return pm["schema"]
    return None


def fields_of(doc, item, op):
    out = []
    params = [deref(doc, x) for x in ((item.get("parameters") or []) + (op.get("parameters") or []))]
    seen = set()
    for loc in ("path", "query", "formData"):
        for x in params:
            if x.get("in") != loc or not x.get("name") or (loc, x["name"]) in seen:
                continue
            seen.add((loc, x["name"]))
            s = merged(doc, x.get("schema") or x)
            t = type_of(s)
            e = enum_of(s)
            if t == "array" and isinstance(s.get("items"), dict):
                it = merged(doc, s["items"])
                t, e = "array<%s>" % type_of(it), enum_of(it) or e
            out.append(("body" if loc == "formData" else loc, x["name"], t, e))
    sch = body_schema(doc, op)
    if sch is not None:
        s = merged(doc, sch)
        if type_of(s) == "array" and isinstance(s.get("items"), dict):
            s = merged(doc, s["items"])
        s = unwrap_envelope(doc, s)
        props = s.get("properties") or {}
        if props:
            for k, v in props.items():
                walk(doc, k, v, 1, out)
        else:
            out.append(("body", "(body)", type_of(s), enum_of(s)))
    return out[:MAX_FIELDS], max(0, len(out) - MAX_FIELDS)


def ops_of(doc):
    res = []
    for p, item in (doc.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for m, op in item.items():
            if m.lower() in WRITE and isinstance(op, dict):
                res.append((m.upper(), p, item, op))
    res.sort(key=lambda r: (r[1], r[0]))
    return res


def spec_file(sid):
    for ext in ("json", "yaml", "yml"):
        f = os.path.join(CORPUS, "specs", "%s.%s" % (sid, ext))
        if os.path.exists(f):
            return f
    return None


def record(row_id, sid, split, m, p, op, flds, cut):
    return {"row_id": row_id, "spec_id": sid, "split": split, "method": m, "path": p,
            "summary": " ".join((op.get("summary") or "").split()),
            "description": " ".join((op.get("description") or "").split())[:400],
            "fields": [{"loc": l, "name": n, "type": t, "enum": e} for l, n, t, e in flds],
            "fields_cut": cut}


def old_rows():
    base = os.path.join(HERE, "..")
    lab = {}
    for r in csv.DictReader(io.open(os.path.join(base, "labelling-r2", "final.csv"), encoding="utf-8")):
        lab[r["row_id"]] = r["final_label"]
    for r in csv.DictReader(io.open(os.path.join(base, "labelling-r3", "final.v2.csv"), encoding="utf-8")):
        lab[r["row_id"]] = r["final_label"]
    files = []
    for d in ("labelling-r2", "labelling-r3"):
        for f in sorted(os.listdir(os.path.join(base, d))):
            if re.match(r"^S\d+\.csv$", f) or f == "S131.v2.csv":
                if d == "labelling-r2" and f == "S131.csv":
                    continue
                files.append(os.path.join(base, d, f))
    out, miss = [], []
    docs = {}
    for f in files:
        for r in csv.DictReader(io.open(f, encoding="utf-8")):
            if r["row_id"] not in lab:
                continue
            sid = r["spec_id"]
            if sid not in docs:
                docs[sid] = {(m, p): (item, op) for m, p, item, op in ops_of(load_cached(sid))}
            hit = docs[sid].get((r["method"], r["path"]))
            if not hit:
                miss.append(r["row_id"])
                continue
            flds, cut = fields_of(load_cached(sid), hit[0], hit[1])
            rec = record(r["row_id"], sid, "train", r["method"], r["path"], hit[1], flds, cut)
            rec["old_label"] = lab[r["row_id"]]
            out.append(rec)
    return out, miss


_cache = {}


def load_cached(sid):
    if sid not in _cache:
        _cache[sid] = load(spec_file(sid))
    return _cache[sid]


def new_rows(sample):
    out, bad = [], []
    for a in sample:
        sid = a["spec_id"]
        f = spec_file(sid)
        try:
            doc = load_cached(sid)
            ops = ops_of(doc)
        except Exception as e:
            bad.append((sid, "doc: %s" % str(e)[:80]))
            continue
        if not ops:
            bad.append((sid, "0 operation ghi"))
            continue
        if len(ops) > CAP:
            ops = sorted(random.Random(SEED + int(sid[1:])).sample(ops, CAP), key=lambda r: (r[1], r[0]))
        for i, (m, p, item, op) in enumerate(ops, 1):
            flds, cut = fields_of(doc, item, op)
            out.append(record("%s-%04d" % (sid, i), sid, a["split"], m, p, op, flds, cut))
    return out, bad
