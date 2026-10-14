import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "..", "..", "corpus")
sys.path.insert(0, CORPUS)
from extract_ops import load, deref

R1 = os.path.join(HERE, "..", "field-labelling-20261004")
R2 = os.path.join(HERE, "..", "field-labelling-r2-20261004")
CHUNK = 75


def spec_path(sid):
    for name in ("%s.v2.json" % sid, "%s.json" % sid):
        p = os.path.join(CORPUS, "specs", name)
        if os.path.exists(p):
            return p
    return None


def ref_name(doc, sch, depth=0):
    if not isinstance(sch, dict) or depth > 4:
        return ""
    if "$ref" in sch:
        return sch["$ref"].split("/")[-1]
    if sch.get("type") == "array" and isinstance(sch.get("items"), dict):
        return ref_name(doc, sch["items"], depth + 1)
    for k in ("allOf", "oneOf", "anyOf"):
        for p in sch.get(k) or []:
            n = ref_name(doc, p, depth + 1)
            if n:
                return n
    return ""


def body_ref(doc, op):
    rb = op.get("requestBody") or {}
    if "$ref" in rb:
        rb = deref(doc, rb)
    for ct in (rb.get("content") or {}).values():
        if isinstance(ct, dict) and ct.get("schema"):
            return ref_name(doc, ct["schema"])
    for pm in op.get("parameters") or []:
        pm = deref(doc, pm)
        if pm.get("in") == "body" and pm.get("schema"):
            return ref_name(doc, pm["schema"])
    return ""


def main():
    rows = []
    for src, rnd in ((R1, "r1"), (R2, "r2")):
        for l in open(os.path.join(src, "rows.jsonl")):
            r = json.loads(l)
            r["round"] = rnd
            rows.append(r)
    docs, miss = {}, 0
    for r in rows:
        sid = r["spec_id"]
        if sid not in docs:
            p = spec_path(sid)
            docs[sid] = load(p) if p else None
        doc = docs[sid]
        r["schema"] = ""
        if doc is None:
            miss += 1
            continue
        item = (doc.get("paths") or {}).get(r["path"]) or {}
        op = item.get(r["method"].lower()) if isinstance(item, dict) else None
        if isinstance(op, dict):
            r["schema"] = body_ref(doc, op)
        else:
            miss += 1
    with open(os.path.join(HERE, "rows.jsonl"), "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    os.makedirs(os.path.join(HERE, "rows"), exist_ok=True)
    order = sorted(rows, key=lambda r: r["row_id"])
    for i in range(0, len(order), CHUNK):
        part = order[i:i + CHUNK]
        lines = []
        for r in part:
            lines.append("## %s  %s %s" % (r["row_id"], r["method"], r["path"]))
            d = (r.get("summary") or "") + (" | " if r.get("summary") and r.get("description") else "") + (r.get("description") or "")
            if d:
                lines.append("desc: " + d[:400].replace("\n", " "))
            if r["schema"]:
                lines.append("schema: " + r["schema"])
            for f in r["fields"]:
                e = " enum[%s]" % "|".join(f["enum"]) if f["enum"] else ""
                lines.append("- %s:%s %s%s" % (f["loc"], f["name"], f["type"], e))
            if r.get("fields_cut"):
                lines.append("(+%d fields cut)" % r["fields_cut"])
            lines.append("")
        open(os.path.join(HERE, "rows", "chunk-%03d.txt" % (i // CHUNK + 1)), "w").write("\n".join(lines))
    print(len(rows), "ops;", sum(1 for r in rows if r["schema"]), "with schema;", miss, "unmatched;",
          (len(order) + CHUNK - 1) // CHUNK, "chunks")


main()
