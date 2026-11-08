import csv, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LR = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(LR, "..", "..", ".."))
sys.path.insert(0, os.path.join(LR, "p2-model-20261012"))
import derive_model as D

SR = D.SR
MODELS = [("M1", os.path.join(LR, "p2-model-20261012", "stateful-authz-model.csv")),
          ("M2", os.path.join(HERE, "stateful-authz-model.csv"))]
TARGETS = [
    ("reports-api", "infra/analysis/demo-20261018/reports-api-docs-8081.json", "PUT", "/users/{username}/role"),
    ("vampi-seeded", "infra/vampi-seeded/openapi_specs/openapi3.yml", "PUT", "/users/v1/{username}/role"),
    ("pyload", "infra/pyload-cve/openapi-merged.json", "POST", "/api/set_user_permission"),
    ("artifact-keeper", "infra/em-results/artifactkeeper-machine-20261001/openapi-trimmed.json", "PATCH", "/api/v1/users/{id}"),
    ("bamf", "infra/bamf-target/run-bamf/openapi.json", "PATCH", "/api/v1/users/{email}"),
]
WRITE = ("PUT", "PATCH", "POST", "DELETE")


def read_model(path):
    m = {}
    for r in csv.DictReader(open(path)):
        m.setdefault(r["table"], {})[r["feature"]] = float(r["weight"])
    return m


def score(m, table, feats):
    t = m[table]
    return t[D.PRIOR] + sum(t.get(f, 0.0) for f in feats)


def value_score(m, table, v):
    v = v.lower()
    hits = [w for k, w in m[table].items() if k in v]
    return max(hits) if hits else 0.0


def role_field(m, op):
    best, bs = None, 0.0
    for f in op["fields"]:
        if f["loc"] == "path":
            continue
        s = score(m, "role", D.field_feats(f))
        if s > bs:
            best, bs = f, s
    return best, bs


def victim_field(m, op, role):
    best, bs = None, 0.0
    for f in op["fields"]:
        if f["kind"] not in ("str", "num") or (role and f["key"] == role["key"]):
            continue
        s = score(m, "victim", D.field_feats(f))
        if best is None or s > bs:
            best, bs = f, s
    return best, bs


def reduced(m, f):
    if f is None:
        return []
    k = f["kind"]
    if k == "enum":
        return sorted(f["enum"], key=lambda v: -(value_score(m, "low", v) - value_score(m, "high", v)))
    if k == "bool":
        return ["false"]
    if k == "array":
        return ["[]"]
    if k == "num":
        return ["1", "0", "2"]
    if k == "str":
        return [w for w, _ in sorted(m["lowstr"].items(), key=lambda x: -x[1])]
    return []


def analyse(m, ops):
    guard = sorted((o for o in ops if o["method"] in WRITE and score(m, "op", D.op_feats(o)) > 0),
                   key=lambda o: -score(m, "op", D.op_feats(o)))
    out = []
    for o in guard:
        rf, rs = role_field(m, o)
        vf, vs = victim_field(m, o, rf)
        red = reduced(m, rf)
        out.append({"op": "%s %s" % (o["method"], o["path"]), "score": score(m, "op", D.op_feats(o)),
                    "role": rf["key"] if rf else None, "role_kind": rf["kind"] if rf else None,
                    "victim": vf["key"] if vf else None, "reduced": red, "viable": bool(red)})
    return out


def main():
    models = {n: read_model(p) for n, p in MODELS}
    for name, rel, meth, path in TARGETS:
        ops = SR.spec_ops(os.path.join(ROOT, rel))
        true = "%s %s" % (meth, path)
        if not any("%s %s" % (o["method"], o["path"]) == true for o in ops):
            print("== %s: transition %s NOT IN SPEC" % (name, true))
            continue
        nwrite = sum(o["method"] in WRITE for o in ops)
        print("== %s (%d op ghi), transition that: %s" % (name, nwrite, true))
        res = {n: analyse(models[n], ops) for n in models}
        for n, rows in res.items():
            via = [r for r in rows if r["viable"]]
            pos = next((i + 1 for i, r in enumerate(via) if r["op"] == true), None)
            t = next((r for r in rows if r["op"] == true), None)
            print("  %s: qua guard %d, viable %d, transition that hang %s trong viable" % (n, len(rows), len(via), pos))
            if t:
                print("      score %.2f role %s (%s) victim %s reduced %s" % (t["score"], t["role"], t["role_kind"], t["victim"], t["reduced"][:6]))
            for i, r in enumerate(via[:6], 1):
                print("      viable #%d %-45s %.2f role %s" % (i, r["op"], r["score"], r["role"]))
        g1 = {r["op"] for r in res["M1"]}
        g2 = {r["op"] for r in res["M2"]}
        print("  guard chi M1: %s" % sorted(g1 - g2))
        print("  guard chi M2: %s" % sorted(g2 - g1))


main()
