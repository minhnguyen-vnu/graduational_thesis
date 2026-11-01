import os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
LR = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(LR, "p2-model-20261012"))
sys.path.insert(0, os.path.join(LR, "field-labelling-20261004"))
import derive_model as D
from extract_fields import spec_file
from extract_ops import load, deref

MAX_DEPTH = 6
ID_TOKENS = ("name", "user", "login", "mail")


def norm(s):
    return "".join(c for c in s.lower() if c.isalnum())


def is_string(doc, sch):
    s = deref(doc, sch)
    if s.get("type") == "string":
        return True
    return any(deref(doc, p).get("type") == "string" for k in ("anyOf", "oneOf") for p in (s.get(k) or []))


def props_of(doc, sch, depth, refs):
    s = deref(doc, sch) if isinstance(sch, dict) else {}
    props = dict(s.get("properties") or {})
    if depth < MAX_DEPTH:
        for k in ("allOf", "oneOf", "anyOf"):
            for p in s.get(k) or []:
                for n, v in props_of(doc, p, depth + 1, refs).items():
                    props.setdefault(n, v)
    return props


def walk(doc, sch, depth, refs, out):
    if depth > MAX_DEPTH or not isinstance(sch, dict):
        return
    ref = sch.get("$ref")
    if ref:
        if ref in refs:
            return
        refs = refs | {ref}
    s = deref(doc, sch)
    props = props_of(doc, s, depth, refs)
    if props:
        out.append(({norm(n) for n in props},
                    any(is_string(doc, v) and any(t in n.lower() for t in ID_TOKENS) for n, v in props.items())))
    children = list(props.values())
    for k in ("allOf", "oneOf", "anyOf"):
        children += [p for p in (s.get(k) or []) if not (deref(doc, p).get("properties"))]
    if isinstance(s.get("items"), dict):
        children.append(s["items"])
    if isinstance(s.get("additionalProperties"), dict):
        children.append(s["additionalProperties"])
    for c in children:
        walk(doc, c, depth + 1, refs, out)


def get_objects(doc):
    out = defaultdict(list)
    for p, item in (doc.get("paths") or {}).items():
        if not isinstance(item, dict) or not isinstance(item.get("get"), dict):
            continue
        for code, resp in (item["get"].get("responses") or {}).items():
            if not (str(code).startswith("2") or str(code) == "default"):
                continue
            r = deref(doc, resp) if isinstance(resp, dict) else {}
            schemas = [r["schema"]] if isinstance(r.get("schema"), dict) else []
            for ct in (r.get("content") or {}).values():
                if isinstance(ct, dict) and isinstance(ct.get("schema"), dict):
                    schemas.append(ct["schema"])
            for sch in schemas:
                walk(doc, sch, 0, frozenset(), out[p])
    return out


def main():
    lab, ops = D.load()
    fields = []
    for o in ops:
        L = lab[o["row_id"]]
        if not L["T"]:
            continue
        for f in o["fields"]:
            if f["key"] in L["role"]:
                fields.append((o, f))
    cache, broken = {}, []
    rows = []
    for o, f in fields:
        sid = o["spec"]
        if sid not in cache:
            try:
                cache[sid] = get_objects(load(spec_file(sid)))
            except Exception as e:
                cache[sid] = None
                broken.append((sid, str(e)[:80]))
        objs = cache[sid]
        if objs is None:
            rows.append((o, f, None, None, ""))
            continue
        leaf = norm(f["raw_leaf"])
        m1 = [p for p, lst in objs.items() if any(leaf in names for names, _ in lst)]
        m2 = [p for p, lst in objs.items() if any(leaf in names and idok for names, idok in lst)]
        rows.append((o, f, bool(m1), bool(m2), (m2 or m1 or [""])[0]))

    print("BROKEN specs:", broken)
    print("NUMERIC role fields")
    for o, f, m1, m2, ex in rows:
        if f["kind"] == "num":
            print("  %-14s %-6s %-60s %-18s M1 %-5s M2 %-5s %s" % (
                o["provider"], o["method"], o["path"][:60], f["raw_leaf"], m1, m2, ex))
    for label, sel in (("num", lambda f: f["kind"] == "num"), ("all", lambda f: True)):
        sub = [r for r in rows if sel(r[1])]
        ok = [r for r in sub if r[2] is not None]
        prov = defaultdict(lambda: [False, False])
        for o, f, m1, m2, _ in ok:
            prov[o["provider"]][0] |= m1
            prov[o["provider"]][1] |= m2
        print("%s: fields %d (broken %d) | M1 %d | M2 %d | providers %d | M1 %d | M2 %d" % (
            label, len(sub), len(sub) - len(ok), sum(1 for r in ok if r[2]), sum(1 for r in ok if r[3]),
            len(prov), sum(1 for v in prov.values() if v[0]), sum(1 for v in prov.values() if v[1])))
    by_kind = defaultdict(lambda: [0, 0, 0])
    for o, f, m1, m2, _ in rows:
        if m1 is None:
            continue
        by_kind[f["kind"]][0] += 1
        by_kind[f["kind"]][1] += m1
        by_kind[f["kind"]][2] += m2
    print("by kind (fields, M1, M2):", dict(by_kind))


if __name__ == "__main__":
    main()
