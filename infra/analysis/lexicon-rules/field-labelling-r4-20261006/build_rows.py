import json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
R1 = os.path.join(HERE, "..", "field-labelling-20261004")
R3 = os.path.join(HERE, "..", "field-labelling-r3-20261006")
sys.path.insert(0, R1)
import extract_fields as ef
from extract_ops import deref

CHUNK = 75
SEED = 20261006


def ref_name(sch, depth=0):
    if not isinstance(sch, dict) or depth > 4:
        return ""
    if "$ref" in sch:
        return sch["$ref"].split("/")[-1]
    if sch.get("type") == "array" and isinstance(sch.get("items"), dict):
        return ref_name(sch["items"], depth + 1)
    for k in ("allOf", "oneOf", "anyOf"):
        for p in sch.get(k) or []:
            n = ref_name(p, depth + 1)
            if n:
                return n
    return ""


def body_ref(doc, op):
    rb = op.get("requestBody") or {}
    if "$ref" in rb:
        rb = deref(doc, rb)
    for ct in (rb.get("content") or {}).values():
        if isinstance(ct, dict) and ct.get("schema"):
            return ref_name(ct["schema"])
    for pm in op.get("parameters") or []:
        pm = deref(doc, pm)
        if pm.get("in") == "body" and pm.get("schema"):
            return ref_name(pm["schema"])
    return ""


def render(r):
    lines = ["## %s  %s %s" % (r["row_id"], r["method"], r["path"])]
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
    return lines


def main():
    old = [json.loads(l) for l in open(os.path.join(R3, "rows.jsonl"))]
    have = {(r["spec_id"], r["method"], r["path"]) for r in old}
    specs = sorted({r["spec_id"] for r in old})
    pos, new, bad = {}, [], []
    for sid in specs:
        try:
            doc = ef.load_cached(sid)
            ops = ef.ops_of(doc)
        except Exception as e:
            bad.append((sid, str(e)[:80]))
            continue
        for i, (m, p, item, op) in enumerate(ops, 1):
            pos[(sid, m, p)] = i
            if (sid, m, p) in have:
                continue
            flds, cut = ef.fields_of(doc, item, op)
            rec = ef.record("%s-N%04d" % (sid, i), sid, "r4", m, p, op, flds, cut)
            rec["round"] = "r4"
            rec["schema"] = body_ref(doc, op)
            rec["pos"] = i
            new.append(rec)
    for r in old:
        r["pos"] = pos.get((r["spec_id"], r["method"], r["path"]))
    with open(os.path.join(HERE, "rows-new.jsonl"), "w") as fh:
        for r in new:
            fh.write(json.dumps(r) + "\n")
    with open(os.path.join(HERE, "rows-all.jsonl"), "w") as fh:
        for r in old + new:
            fh.write(json.dumps(r) + "\n")
    order = sorted({r["spec_id"] for r in new})
    random.Random(SEED).shuffle(order)
    rank = {s: i for i, s in enumerate(order)}
    seq = sorted(new, key=lambda r: (rank[r["spec_id"]], r["pos"]))
    os.makedirs(os.path.join(HERE, "rows"), exist_ok=True)
    manifest = {}
    for i in range(0, len(seq), CHUNK):
        part = seq[i:i + CHUNK]
        name = "chunk-%03d" % (i // CHUNK + 1)
        manifest[name] = [r["row_id"] for r in part]
        lines = []
        for r in part:
            lines.extend(render(r))
        open(os.path.join(HERE, "rows", name + ".txt"), "w").write("\n".join(lines))
    json.dump(manifest, open(os.path.join(HERE, "manifest.json"), "w"), indent=0)
    print("old", len(old), "new", len(new), "old without pos", sum(1 for r in old if r["pos"] is None),
          "chunks", len(manifest), "specs with new ops", len(order), "bad", bad)


main()
