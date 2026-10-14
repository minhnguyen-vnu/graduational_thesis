import csv, json, os, random, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
R4 = os.path.join(HERE, "..", "field-labelling-r4-20261006")
R1 = os.path.join(HERE, "..", "field-labelling-20261004")
sys.path.insert(0, R4)
sys.path.insert(0, R1)
import sim
import extract_fields as ef
from extract_ops import load as load_spec, deref

ROOT = os.path.join(HERE, "..", "..", "..", "..")
TARGETS = [
    ("bamf", os.path.join(ROOT, "infra/em-results/emailparam-selftest-20260930-112049/bamf-seed1-target/openapi.json"),
     "PATCH", "/api/v1/users/{email}"),
    ("artifact-keeper", os.path.join(ROOT, "infra/em-results/artifactkeeper-machine-20261001/openapi-trimmed.json"),
     "PATCH", "/api/v1/users/{id}"),
]
ARMS = ["V", "R4", "RK", "RK2", "RK0", "RKs"]
METRICS = ["M1", "M1any", "M1top", "M2", "M3", "M4", "M5"]


def score_items(items, cand):
    st = {}
    for w in cand:
        dp = dn = 0
        pp, ap = set(), set()
        for n, pos, p in items:
            if w in n:
                ap.add(p)
                if pos:
                    dp += 1
                    pp.add(p)
                else:
                    dn += 1
        if dp:
            st[w] = {"score": (dp + 1) / (dp + dn + 2) * len(pp) / (len(pp) + 1), "dp": dp, "dn": dn,
                     "ncc": len(pp), "anyp": len(ap)}
    return st


def build(items, cand, ncc_min):
    st = score_items(items, cand)
    ws = {w for w, s in st.items() if s["ncc"] >= ncc_min}
    ws = {w for w in ws if not any(o != w and len(o) < len(w) and o in w for o in ws)}
    return {w: st[w] for w in ws}


def gate(rank):
    return {w for w, s in rank.items() if s["ncc"] / s["anyp"] >= 0.5}


def field_items(docs):
    items, cand = [], set()
    for f, pos, p in docs:
        items.append((f["leaf"], pos, p))
        if pos:
            cand |= sim.tokens(f["raw_leaf"])
            cand.add(f["leaf"])
    return items, cand | sim.std_terms()


def role_docs(ops, lab):
    out = []
    for op in ops:
        l = lab.get(op["row_id"])
        if not l or not l["T"]:
            continue
        for f in op["fields"]:
            out.append((f, f["key"] in l["role"], op["provider"]))
    return out


def order_items(ops, lab, side):
    items, cand = [], set()
    for levels, p in sim.order_docs(ops, lab):
        tgt = levels[0] if side == "low" else levels[-1]
        for lv in levels:
            for v in lv:
                items.append((v, lv is tgt, p))
                if lv is tgt:
                    cand |= sim.tokens(v)
                    cand.add(v)
    return items, cand


def rank_model(ops, lab, admin_list, ncc_min=1, split=False, bonus=True):
    m = {"kind": "rank", "split": split, "admin": list(admin_list) if bonus else []}
    m["victim"] = build(*field_items(sim.docs(ops, lab, "victim")), ncc_min)
    if split:
        m["role"] = build(*field_items(sim.docs(ops, lab, "role")), ncc_min)
        m["bool"] = build(*field_items(sim.docs(ops, lab, "admin")), ncc_min)
        m["bool_gate"] = gate(m["bool"])
    else:
        m["role"] = build(*field_items(role_docs(ops, lab)), ncc_min)
    m["role_gate"] = gate(m["role"])
    m["low"] = build(*order_items(ops, lab, "low"), ncc_min)
    m["high"] = build(*order_items(ops, lab, "high"), ncc_min)
    return m


def models(ops, lab):
    r4, _ = sim.derive(ops, lab, "std")
    return {"V": sim.HARD, "R4": r4,
            "RK": rank_model(ops, lab, r4["admin"]),
            "RK2": rank_model(ops, lab, r4["admin"], ncc_min=2),
            "RK0": rank_model(ops, lab, r4["admin"], bonus=False),
            "RKs": rank_model(ops, lab, r4["admin"], split=True)}


def fscore(rank, name):
    return max([s["score"] for w, s in rank.items() if w in name] or [0.0])


def r_role_genes(op, M):
    out = []
    for i, (n, k, f) in enumerate(sim.genes(op)):
        if M["split"] and k == "bool":
            ok, s = any(w in n for w in M["bool_gate"]), fscore(M["bool"], n)
        else:
            ok, s = any(w in n for w in M["role_gate"]), fscore(M["role"], n)
        if ok:
            out.append((-s, i, n, k, f))
    return [(n, k, f) for _, _, n, k, f in sorted(out, key=lambda x: (x[0], x[1]))]


def r_reduced(op, M):
    rg = r_role_genes(op, M)
    if not rg:
        return []
    vocab = []
    for f in op["fields"]:
        if f["kind"] == "enum":
            for v in f["enum"]:
                if v not in vocab:
                    vocab.append(v)
    key = {v: fscore(M["low"], v.lower()) - fscore(M["high"], v.lower()) for v in vocab}
    low = sorted([v for v in vocab if key[v] > 0], key=lambda v: -key[v])
    rest = sorted([v for v in vocab if v not in low], key=lambda v: -key[v])
    adm = ["false"] if any(k == "bool" for _, k, _ in rg) else []
    empty = ["[]"] if any(f is not None and f["loc"] == "body" and k == "array" for _, k, f in rg) else []
    num = ["1", "0", "2"] if any(k == "num" for _, k, _ in rg) else []
    strs = ["user", "viewer", "guest", "member", "basic"] if any(k == "str" for _, k, _ in rg) else []
    res = []
    for v in adm + low + empty + num + rest + strs:
        if v not in res:
            res.append(v)
    return res


def r_role_keys(op, M):
    return {f["key"] for _, _, f in r_role_genes(op, M) if f is not None}


def r_top_role(op, M):
    for _, _, f in r_role_genes(op, M):
        if f is not None:
            return f["key"]
    return None


def l_top_role(op, L):
    for n, k, f in sim.genes(op):
        if f is not None and any(w in n for w in L["role"]):
            return f["key"]
    for n, k, f in sim.genes(op):
        if f is not None and k == "bool" and any(w in n for w in L["admin"]):
            return f["key"]
    return None


def r_pick_victim(op, M):
    def best(fs):
        sc = [(fscore(M["victim"], f["leaf"]), -i, f) for i, f in enumerate(fs)]
        sc = [x for x in sc if x[0] > 0]
        return max(sc, key=lambda x: (x[0], x[1]))[2] if sc else None
    for loc in ("path", "body"):
        f = best([f for f in op["fields"] if f["loc"] == loc and f["kind"] in ("str", "num")])
        if f:
            return f
    return best([f for f in op["fields"] if f["loc"] == "query" and "." not in f["name"] and f["kind"] in ("str", "num")])


def fns(L):
    if L.get("kind") == "rank":
        return r_reduced, r_role_keys, r_pick_victim, r_top_role
    return sim.reduced_candidates, sim.matched_role_keys, sim.pick_victim, l_top_role


def viable(oplist, L):
    red = fns(L)[0]
    ranked = [op for op in oplist if op["method"] in sim.VERB_ORDER and sim.transition_score(op, L) > 0]
    ranked.sort(key=lambda op: (-sim.transition_score(op, L), not sim.has_user_param(op), sim.VERB_ORDER.index(op["method"])))
    return [op for op in ranked[:sim.MAX_TRANSITION_CANDIDATES] if red(op, L)]


def outcomes(ops, lab, L):
    red, keys, victim, top = fns(L)
    by_spec = defaultdict(list)
    for op in ops:
        by_spec[op["spec"]].append(op)
    out = {m: {} for m in METRICS}
    for s, oplist in by_spec.items():
        tops = [op for op in oplist if lab[op["row_id"]]["T"]]
        tops_role = [op for op in tops if lab[op["row_id"]]["role"]]
        via = viable(oplist, L)
        def hit(op):
            l = lab[op["row_id"]]
            return l["T"] and bool(keys(op, L) & set(l["role"]))
        if tops_role:
            out["M1"][s] = bool(via) and hit(via[0])
            out["M1any"][s] = any(hit(op) for op in via)
            out["M1top"][s] = bool(via) and lab[via[0]["row_id"]]["T"] and top(via[0], L) in lab[via[0]["row_id"]]["role"]
        if not tops:
            out["M2"][s] = bool(via)
    for op in ops:
        l = lab[op["row_id"]]
        if l["T"] and l["victim"] and l["victim"] != ["self"]:
            v = victim(op, L)
            out["M3"][op["row_id"]] = v is not None and v["key"] in l["victim"]
        if l["T"] and "<" in l["order"]:
            low = [x.strip().lower() for x in l["order"].split("<")[0].split("=") if x.strip()]
            c = red(op, L)
            out["M4"][op["row_id"]] = bool(c) and c[0].lower() in low
        if not l["T"]:
            out["M5"][op["row_id"]] = sim.admin_hit(op, L) and sim.path_score(op) < sim.ADMIN_SCORE
    return out


def cv(ops, lab):
    provs = sorted({op["provider"] for op in ops})
    rng = random.Random(sim.SEED)
    reps = []
    for rep in range(4):
        order = provs[:]
        rng.shuffle(order)
        folds = [set(order[i::5]) for i in range(5)]
        pooled = {a: defaultdict(dict) for a in ARMS}
        for held in folds:
            train = [op for op in ops if op["provider"] not in held]
            test = [op for op in ops if op["provider"] in held]
            for a, L in models(train, lab).items():
                for m, d in outcomes(test, lab, L).items():
                    pooled[a][m].update(d)
        reps.append(pooled)
    return reps


def anchors(L):
    rows = [("reports-api", ["role"], ["username"]), ("vampi-seeded", ["role"], ["username"]),
            ("pyLoad", ["permission", "role"], ["user"]), ("artifact-keeper", ["is_admin"], ["id"]),
            ("Airflow", ["roles"], ["username"]), ("bamf", [], ["email"])]
    out = []
    for t, afields, cfields in rows:
        if L.get("kind") == "rank":
            def role_ok(f):
                if L["split"] and f == "is_admin":
                    return any(w in f for w in L["bool_gate"])
                return any(w in f for w in L["role_gate"])
            a = {f: role_ok(f) for f in afields}
            c = {f: fscore(L["victim"], f) > 0 for f in cfields}
        else:
            a = {f: (any(w in f for w in L["admin"]) if f == "is_admin" else any(w in f for w in L["role"])) for f in afields}
            c = {f: any(w in f for w in L["spec"] + L["email"] + L["id"]) for f in cfields}
        out.append({"target": t, "A": a, "C": c, "pass": all(a.values()) and all(c.values())})
    return out


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
    return ""


def spec_ops(path):
    doc = load_spec(path)
    ops = []
    for i, (m, p, item, op) in enumerate(ef.ops_of(doc), 1):
        flds, _ = ef.fields_of(doc, item, op)
        fields = []
        for loc, name, t, e in flds:
            if name == "(body)":
                continue
            f = {"loc": loc, "name": name, "key": "%s:%s" % (loc, name), "leaf": sim.leaf(name).lower(),
                 "raw_leaf": sim.leaf(name), "type": t, "enum": [str(v) for v in e]}
            f["kind"] = sim.gene_kind(f)
            fields.append(f)
        ops.append({"row_id": "%s %s" % (m, p), "spec": "t", "provider": "t", "method": m, "path": p,
                    "schema": body_ref(doc, op), "fields": fields, "pos": i})
    return ops


def target_check(L):
    red, keys, victim, top = fns(L)
    out = []
    for name, path, m, p in TARGETS:
        ops = spec_ops(path)
        via = viable(ops, L)
        ids = [op["row_id"] for op in via]
        op = next(o for o in ops if o["method"] == m and o["path"] == p)
        v = victim(op, L)
        c = red(op, L)
        out.append({"target": name, "op": op["row_id"], "rank_in_viable": ids.index(op["row_id"]) + 1 if op["row_id"] in ids else None,
                    "viable": ids, "transition_score": round(sim.transition_score(op, L), 4),
                    "victim": v["key"] if v else None, "role_keys": sorted(keys(op, L)), "first_reduced": c[0] if c else None})
    return out


def rate(d):
    return {"n": len(d), "yes": sum(d.values())}


def dump_rank(M, path):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ranking", "word", "score", "dp", "dn", "ncc", "any_providers", "gate"])
        for nm in ("victim", "role", "bool", "low", "high"):
            if nm not in M:
                continue
            g = M.get("bool_gate" if nm == "bool" else "role_gate", set()) if nm in ("role", "bool") else None
            for word, s in sorted(M[nm].items(), key=lambda kv: (-kv[1]["score"], kv[0])):
                w.writerow([nm, word, round(s["score"], 4), s["dp"], s["dn"], s["ncc"], s["anyp"],
                            "" if g is None else word in g])


def main(outdir):
    lab = sim.load_labels(os.path.join(R4, "final-all.csv"))
    ops = sim.load_ops(set(lab))
    unit_prov = {op["spec"]: op["provider"] for op in ops}
    unit_prov.update({op["row_id"]: op["provider"] for op in ops})
    reps = cv(ops, lab)
    res = {"ops": len(ops), "repeats": []}
    pairs = [("V", "RK"), ("R4", "RK"), ("RK", "RK2"), ("RK", "RK0"), ("RK", "RKs"), ("V", "R4"), ("V", "RK2"), ("V", "RKs")]
    for r, P in enumerate(reps):
        row = {"repeat": r + 1, "rates": {a: {m: rate(P[a][m]) for m in METRICS} for a in ARMS}, "tests": {}}
        for a, b in pairs:
            for m in METRICS:
                t = sim.mcnemar(P[a][m], P[b][m])
                if r == 0:
                    t["ci95_diff"] = sim.boot_diff(P[a][m], P[b][m], unit_prov)
                row["tests"]["%s_vs_%s_%s" % (b, a, m)] = t
        res["repeats"].append(row)
    full = models(ops, lab)
    res["full_data"] = {a: {m: rate(d) for m, d in outcomes(ops, lab, L).items()} for a, L in full.items()}
    res["anchors"] = {a: anchors(L) for a, L in full.items()}
    res["targets"] = {a: target_check(L) for a, L in full.items()}
    os.makedirs(os.path.join(outdir, "rankings"), exist_ok=True)
    for a in ("RK", "RK2", "RKs"):
        dump_rank(full[a], os.path.join(outdir, "rankings", "%s.csv" % a))
    json.dump(res, open(os.path.join(outdir, "cv.json"), "w"), indent=1, default=list)
    for r in res["repeats"]:
        print("repeat", r["repeat"], {a: {m: r["rates"][a][m]["yes"] for m in METRICS} for a in ARMS})


if __name__ == "__main__":
    main(sys.argv[1])
