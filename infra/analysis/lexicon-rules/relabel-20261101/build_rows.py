import json, os, random, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
LR = os.path.normpath(os.path.join(HERE, ".."))
INFRA = os.path.normpath(os.path.join(LR, "..", ".."))
sys.path.insert(0, os.path.join(LR, "field-labelling-20261004"))
import extract_fields as ef
from extract_ops import deref, load

CHUNK = 75
SEED = 20261101
TARGETS = [
    ("reports-api", os.path.join(LR, "lexicon-r4-20261007", "targets", "reports-api.json"), "PUT", "/users/{username}/role"),
    ("vampi-seeded", os.path.join(LR, "lexicon-r4-20261007", "targets", "vampi-seeded.json"), "PUT", "/users/v1/{username}/role"),
    ("pyLoad", os.path.join(INFRA, "pyload-cve", "openapi-merged.json"), "POST", "/api/set_user_permission"),
    ("Airflow", os.path.join(INFRA, "airflow-target", "airflow-merged.json"), "PATCH", "/auth/fab/v1/users/{username}"),
    ("artifact-keeper", os.path.join(INFRA, "em-results", "artifactkeeper-machine-20261001", "openapi-trimmed.json"), "PATCH", "/api/v1/users/{id}"),
    ("bamf", os.path.join(INFRA, "bamf-target", "run-bamf", "openapi.json"), "PATCH", "/api/v1/users/{email}"),
    ("raouf", os.path.join(INFRA, "em-results", "raouf-heldout-20261014", "openapi-nokill.json"), "PUT", "/v1/users/{id}/role"),
    ("magic", os.path.join(INFRA, "em-results", "magic-heldout-20261014", "openapi.json"), "DELETE", "/magic/system/magic/users_roles"),
]


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


def to_row(doc, sid, i, m, p, item, op):
    flds, cut = ef.fields_of(doc, item, op)
    rec = ef.record("%s-N%04d" % (sid, i), sid, "relabel", m, p, op, flds, cut)
    rec["schema"] = body_ref(doc, op)
    rec["pos"] = i
    return rec


def write_blocks(stage, rows, order, manifest):
    rank = {s: i for i, s in enumerate(order)}
    seq = sorted(rows, key=lambda r: (rank[r["spec_id"]], r["pos"] or 0, r["row_id"]))
    d = os.path.join(HERE, "blocks", stage)
    os.makedirs(d, exist_ok=True)
    manifest[stage] = {}
    for i in range(0, len(seq), CHUNK):
        part = seq[i:i + CHUNK]
        name = "chunk-%03d" % (i // CHUNK + 1)
        manifest[stage][name] = [r["row_id"] for r in part]
        lines = []
        for r in part:
            lines.extend(render(r))
        with open(os.path.join(d, name + ".txt"), "w") as fh:
            fh.write("\n".join(lines))


def train(manifest):
    rows = [json.loads(l) for l in open(os.path.join(LR, "field-labelling-r4-20261006", "rows-all.jsonl"))]
    for r in rows:
        r.pop("old_label", None)
    order = sorted({r["spec_id"] for r in rows})
    random.Random(SEED).shuffle(order)
    write_blocks("train", rows, order, manifest)
    return len(rows), len(order)


def test(manifest):
    specs = json.load(open(os.path.join(HERE, "test-specs.json")))
    rows, bad, empty = [], [], []
    for a in specs:
        if a["status"] != "ok":
            continue
        sid = a["spec_id"]
        try:
            doc = load(os.path.join(HERE, "test-specs", sid + ".json"))
            got = [to_row(doc, sid, i, m, p, item, op) for i, (m, p, item, op) in enumerate(ef.ops_of(doc), 1)]
        except Exception as e:
            bad.append((sid, a["provider"], type(e).__name__))
            continue
        if got:
            rows.extend(got)
        else:
            empty.append(sid)
    with open(os.path.join(HERE, "rows-test.jsonl"), "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    order = sorted({r["spec_id"] for r in rows})
    random.Random(SEED + 1).shuffle(order)
    write_blocks("test", rows, order, manifest)
    return len(rows), len(order), empty, bad


def known(manifest):
    rng = random.Random(SEED + 2)
    rows = []
    for k, (name, path, method, op_path) in enumerate(TARGETS, 1):
        doc = load(path)
        sid = "K%02d" % k
        ops = list(enumerate(ef.ops_of(doc), 1))
        hit = [x for x in ops if x[1][0] == method and x[1][1] == op_path]
        if len(hit) != 1:
            raise SystemExit("HONG %s: tim thay %d transition" % (name, len(hit)))
        rest = [x for x in ops if x is not hit[0]]
        picks = [(hit[0], 1)] + ([(rng.choice(rest), 0)] if rest else [])
        for (i, (m, p, item, op)), positive in picks:
            r = to_row(doc, sid, i, m, p, item, op)
            r["target"] = name
            r["known_positive"] = positive
            rows.append(r)
    with open(os.path.join(HERE, "rows-known.jsonl"), "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    order = sorted({r["spec_id"] for r in rows})
    random.Random(SEED + 3).shuffle(order)
    write_blocks("known", rows, order, manifest)
    return len(rows)


def main():
    manifest = {}
    n_train, s_train = train(manifest)
    n_test, s_test, empty, bad = test(manifest)
    n_known = known(manifest)
    json.dump(manifest, open(os.path.join(HERE, "manifest.json"), "w"), indent=0)
    print("train", n_train, "op", s_train, "bo", len(manifest["train"]), "khoi")
    print("test", n_test, "op", s_test, "bo co op ghi", len(manifest["test"]), "khoi", "rong", len(empty), "hong", bad)
    print("known", n_known, "dong", len(manifest["known"]), "khoi")
    specs = Counter(r.split("-")[0] for c in manifest["test"].values() for r in c)
    print("10 bo test lon nhat (so op):", [n for _, n in specs.most_common(10)])


main()
