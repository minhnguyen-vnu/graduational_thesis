import csv, json, os, subprocess, sys

WRITE = ("post", "put", "patch", "delete")
HEAD = ["row_id", "spec_id", "method", "path", "summary", "description",
        "param_names", "body_field_names", "enum_values",
        "annotator", "label", "rule_id", "doubt_token", "note", "final_label"]


def load(path):
    if path.endswith((".yaml", ".yml")):
        r = subprocess.run(["ruby", "-ryaml", "-rjson", "-e",
                            "print JSON.dump(YAML.safe_load(File.read(ARGV[0]), aliases: true))", path],
                           capture_output=True, text=True, timeout=180)
        if r.returncode:
            raise ValueError(r.stderr.strip()[:100])
        return json.loads(r.stdout)
    with open(path, encoding="utf-8", errors="replace") as f:
        return json.load(f)


def deref(doc, node, depth=0):
    while isinstance(node, dict) and "$ref" in node and depth < 12:
        ref = node["$ref"]
        if not ref.startswith("#/"):
            return {}
        cur = doc
        for seg in ref[2:].split("/"):
            seg = seg.replace("~1", "/").replace("~0", "~")
            if not isinstance(cur, dict) or seg not in cur:
                return {}
            cur = cur[seg]
        node, depth = cur, depth + 1
    return node if isinstance(node, dict) else {}


def enums_of(doc, name, sch, out, depth=0):
    sch = deref(doc, sch, depth)
    if not sch or depth > 6:
        return
    if isinstance(sch.get("enum"), list):
        vals = [str(v) for v in sch["enum"]][:12]
        out.append("%s=[%s]" % (name, "|".join(vals)))
    for k, v in (sch.get("properties") or {}).items():
        enums_of(doc, k, v, out, depth + 1)
    if isinstance(sch.get("items"), dict):
        enums_of(doc, name, sch["items"], out, depth + 1)


def body_fields(doc, op):
    sch = None
    rb = deref(doc, op.get("requestBody") or {})
    for ct in (rb.get("content") or {}).values():
        if isinstance(ct, dict) and ct.get("schema"):
            sch = ct["schema"]
            break
    if sch is None:
        for pm in op.get("parameters") or []:
            pm = deref(doc, pm)
            if pm.get("in") == "body" and pm.get("schema"):
                sch = pm["schema"]
                break
    if sch is None:
        return [], None
    s = deref(doc, sch)
    if s.get("type") == "array" and isinstance(s.get("items"), dict):
        s = deref(doc, s["items"])
    s = unwrap_envelope(doc, s)
    return sorted((s.get("properties") or {}).keys()), s


ENVELOPE_KEYS = ("data", "attributes")
ENVELOPE_SIBLINGS = {"attributes", "relationships", "type", "id", "links", "meta", "included"}


def _inner(doc, node):
    n = deref(doc, node)
    if n.get("type") == "array" and isinstance(n.get("items"), dict):
        n = deref(doc, n["items"])
    return n


def unwrap_envelope(doc, s, depth=0):
    if depth >= 4 or not isinstance(s, dict):
        return s
    props = s.get("properties") or {}
    if not props:
        return s
    if len(props) == 1 and list(props)[0] in ENVELOPE_KEYS:
        inner = _inner(doc, props[list(props)[0]])
        if inner.get("properties"):
            return unwrap_envelope(doc, inner, depth + 1)
        return s
    if "attributes" in props and set(props) <= ENVELOPE_SIBLINGS:
        merged = {}
        merged.update((_inner(doc, props["attributes"]).get("properties") or {}))
        if "relationships" in props:
            merged.update((_inner(doc, props["relationships"]).get("properties") or {}))
        if merged:
            return unwrap_envelope(doc, dict(s, properties=merged), depth + 1)
    return s


def rows_for(path, spec_id):
    doc = load(path)
    out = []
    for p, item in (doc.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        shared = item.get("parameters") or []
        for m, op in item.items():
            if m.lower() not in WRITE or not isinstance(op, dict):
                continue
            params = [deref(doc, x) for x in (shared + (op.get("parameters") or []))]
            pnames = sorted({x.get("name", "") for x in params if x.get("name")})
            bnames, bsch = body_fields(doc, op)
            en = []
            for x in params:
                if x.get("name"):
                    enums_of(doc, x["name"], x.get("schema") or x, en)
            if bsch:
                for k, v in (bsch.get("properties") or {}).items():
                    enums_of(doc, k, v, en)
            out.append([spec_id, m.upper(), p,
                        " ".join((op.get("summary") or "").split()),
                        " ".join((op.get("description") or "").split())[:400],
                        ";".join(pnames), ";".join(bnames), ";".join(sorted(set(en)))])
    out.sort(key=lambda r: (r[2], r[1]))
    return out


def write_sheet(rows, dest, spec_id):
    with open(dest, "w", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(HEAD)
        for i, r in enumerate(rows, 1):
            w.writerow(["%s-%04d" % (spec_id, i)] + r + ["", "", "", "", "", ""])


if __name__ == "__main__":
    rows = rows_for(sys.argv[1], sys.argv[2])
    write_sheet(rows, sys.argv[3], sys.argv[2])
    print("%s %d dòng" % (sys.argv[3], len(rows)))
