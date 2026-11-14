import csv, hashlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LR = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(LR, "..", "..", ".."))
sys.path.insert(0, os.path.join(LR, "p2-model-20261012"))
sys.path.insert(0, HERE)
import derive_model as D
import derive_nodup as N

SR = D.SR
OLD_OUT = os.path.join(LR, "m2-model-20261107", "compare_targets.out")
MODELS = [("M2", os.path.join(LR, "m2-model-20261107", "stateful-authz-model.csv"), D.op_feats),
          ("bo-lap", os.path.join(HERE, "stateful-authz-model.csv"), N.op_feats_nodup)]
TARGETS = [
    ("reports-api", "infra/analysis/demo-20261018/reports-api-docs-8081.json", "PUT", "/users/{username}/role"),
    ("vampi-seeded", "infra/vampi-seeded/openapi_specs/openapi3.yml", "PUT", "/users/v1/{username}/role"),
    ("pyload", "infra/pyload-cve/openapi-merged.json", "POST", "/api/set_user_permission"),
    ("artifact-keeper", "infra/em-results/artifactkeeper-machine-20261001/openapi-trimmed.json", "PATCH", "/api/v1/users/{id}"),
]
WRITE = ("PUT", "PATCH", "POST", "DELETE")
fails = []


def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        fails.append(msg)


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


def analyse(m, ops, feats):
    guard = sorted((o for o in ops if o["method"] in WRITE and score(m, "op", feats(o)) > 0),
                   key=lambda o: -score(m, "op", feats(o)))
    out = []
    for o in guard:
        rf, rs = role_field(m, o)
        vf, vs = victim_field(m, o, rf)
        red = reduced(m, rf)
        out.append({"op": "%s %s" % (o["method"], o["path"]), "score": score(m, "op", feats(o)),
                    "role": rf["key"] if rf else None, "role_kind": rf["kind"] if rf else None,
                    "victim": vf["key"] if vf else None, "reduced": red, "viable": bool(red)})
    return out


def block(n, rows, true):
    via = [r for r in rows if r["viable"]]
    pos = next((i + 1 for i, r in enumerate(via) if r["op"] == true), None)
    t = next((r for r in rows if r["op"] == true), None)
    out = ["  %s: qua guard %d, viable %d, transition that hang %s trong viable" % (n, len(rows), len(via), pos)]
    if t:
        out.append("      score %.2f role %s (%s) victim %s reduced %s" % (t["score"], t["role"], t["role_kind"], t["victim"], t["reduced"][:6]))
    for i, r in enumerate(via[:6], 1):
        out.append("      viable #%d %-45s %.2f role %s" % (i, r["op"], r["score"], r["role"]))
    return out, pos, t


def old_block(name):
    lines = open(OLD_OUT).read().splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith("== %s " % name))
    j = next(k for k in range(i, len(lines)) if lines[k].startswith("  M2:"))
    out = []
    for l in lines[j:]:
        if l.startswith("  guard chi") or l.startswith("=="):
            break
        out.append(l)
    return out


def main():
    models = {n: (read_model(p), f) for n, p, f in MODELS}
    for n, p, _ in MODELS:
        print("%s: %s sha256 %s" % (n, os.path.relpath(p, LR), hashlib.sha256(open(p, "rb").read()).hexdigest()[:12]))
    summary = []
    for name, rel, meth, path in TARGETS:
        ops = SR.spec_ops(os.path.join(ROOT, rel))
        true = "%s %s" % (meth, path)
        if not any("%s %s" % (o["method"], o["path"]) == true for o in ops):
            check(False, "%s: transition %s co trong spec" % (name, true))
            continue
        o_true = next(o for o in ops if "%s %s" % (o["method"], o["path"]) == true)
        print("")
        print("== %s (%d op ghi), transition that: %s" % (name, sum(o["method"] in WRITE for o in ops), true))
        print("   path params: %s; dac trung bo di: %s" % (
            [f["name"] for f in o_true["fields"] if f["loc"] == "path"], sorted(D.op_feats(o_true) - N.op_feats_nodup(o_true))))
        res = {}
        for n, (m, feats) in models.items():
            rows = analyse(m, ops, feats)
            lines, pos, t = block(n, rows, true)
            res[n] = (rows, pos, t)
            for l in lines:
                print(l)
            if n == "M2":
                check(lines == old_block(name), "%s: M2 tinh bang script nay trung compare_targets.out cua M2" % name)
        g2 = {r["op"] for r in res["M2"][0]}
        gn = {r["op"] for r in res["bo-lap"][0]}
        print("  guard chi M2: %s" % sorted(g2 - gn))
        print("  guard chi bo-lap: %s" % sorted(gn - g2))
        summary.append((name, res["M2"][2], res["M2"][1], res["bo-lap"][2], res["bo-lap"][1]))

    print("")
    print("Tom tat: diem op cua transition that, hang trong cac op dung duoc")
    for name, t2, p2, tn, pn in summary:
        print("  %-16s M2 %s hang %s | bo lap %s hang %s" % (
            name, "%.2f" % t2["score"] if t2 else "<= 0 (khong qua guard)", p2,
            "%.2f" % tn["score"] if tn else "<= 0 (khong qua guard)", pn))
    print("%d FAIL" % len(fails) if fails else "ALL PASS")
    sys.exit(1 if fails else 0)


main()
