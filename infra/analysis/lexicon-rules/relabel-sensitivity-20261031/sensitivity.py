import csv, glob, math, os, random, statistics, sys, tempfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
LR = os.path.normpath(os.path.join(HERE, ".."))
INFRA = os.path.normpath(os.path.join(LR, "..", ".."))
sys.path.insert(0, os.path.join(LR, "lexicon-r4-20261007"))
sys.path.insert(0, os.path.join(LR, "field-ranking-20261007"))
import measure as M

X, sim, R = M.X, M.sim, M.R
SEED = 20261031
MODEL = "/Users/minhnguyen/IdeaProjects/EvoMaster/core/src/main/resources/stateful-authz-model.csv"
VERBS = ("POST", "PUT", "PATCH", "DELETE")
TARGETS = list(M.TARGETS) + [
    ("raouf", os.path.join(INFRA, "em-results", "raouf-heldout-20261014", "openapi-nokill.json"),
     "PUT", "/v1/users/{id}/role"),
    ("magic", os.path.join(INFRA, "em-results", "magic-heldout-20261014", "openapi.json"),
     "DELETE", "/magic/system/magic/users_roles"),
]


def op_feats(op):
    fs = {"v:" + op["method"]}
    fs |= {"p:" + t for t in X.tokens(op["path"])}
    for f in op["fields"]:
        if f["loc"] in ("path", "query", "body"):
            fs |= {"f:" + t for t in X.tokens(f["raw_leaf"])}
    return fs


def field_feats(f):
    fs = {"k:" + f["kind"], "l:" + f["loc"], "w:" + f["leaf"]}
    fs |= {"n:" + t for t in X.tokens(f["raw_leaf"])}
    for p in [p.replace("[]", "") for p in f["name"].split(".")[:-1]]:
        fs |= {"a:" + t for t in X.tokens(p)}
    for v in f["enum"]:
        fs |= {"e:" + t for t in X.tokens(str(v))}
    return fs


def nb(docs):
    npos = sum(m for _, _, pos, m in docs if pos)
    nneg = sum(m for _, _, pos, m in docs if not pos)
    dp, dn, pv = defaultdict(int), defaultdict(int), defaultdict(set)
    for fs, prov, pos, m in docs:
        for t in fs:
            if pos:
                dp[t] += m
                pv[t].add(prov)
            else:
                dn[t] += m
    w = {t: math.log((dp[t] + 1) / (npos + 2)) - math.log((dn[t] + 1) / (nneg + 2))
         for t in dp if len(pv[t]) >= 2}
    return w, math.log(npos / nneg)


def train(ops, opf, ff, lab, mult=None):
    od, rd = [], []
    for o in ops:
        m = 1 if mult is None else mult.get(o["provider"], 0)
        if m == 0:
            continue
        L = lab[o["row_id"]]
        od.append((opf[o["row_id"]], o["provider"], L["T"], m))
        if L["T"]:
            for f in o["fields"]:
                rd.append((ff[(o["row_id"], f["key"])], o["provider"], f["key"] in L["role"], m))
    return nb(od), nb(rd)


def rank_target(tops, tm, op_model, role_model):
    (w, prior), (rw, rprior) = op_model, role_model
    method, path = tm
    usable, score_t = [], None
    for o in tops:
        s = prior + sum(w.get(t, 0.0) for t in o["_f"])
        if o["method"] == method and o["path"] == path:
            score_t = s
        if s <= 0:
            continue
        ok = any(rprior + sum(rw.get(t, 0.0) for t in fs) > 0
                 for f, fs in o["_ff"] if f["loc"] != "path")
        if ok:
            usable.append((s, o))
    usable.sort(key=lambda x: -x[0])
    pos = next((i + 1 for i, (_, o) in enumerate(usable) if o["method"] == method and o["path"] == path), None)
    return score_t, pos, len(usable)


def load_targets():
    out = []
    for name, path, m, p in TARGETS:
        tops = [o for o in R.spec_ops(path) if o["method"] in VERBS]
        for o in tops:
            o["_f"] = op_feats(o)
            o["_ff"] = [(f, field_feats(f)) for f in o["fields"][:80]]
        out.append((name, (m, p), tops))
    return out


def merged_labels(r3_dir, r4_dir):
    rows = []
    for d in (r3_dir, r4_dir):
        for fn in sorted(glob.glob(os.path.join(d, "chunk-*.csv"))):
            rows.extend(csv.DictReader(open(fn)))
    tmp = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="")
    w = csv.DictWriter(tmp, ["row_id", "T", "victim", "role", "order", "source"], extrasaction="ignore")
    w.writeheader()
    for r in rows:
        r["source"] = ""
        w.writerow(r)
    tmp.close()
    lab = sim.load_labels(tmp.name)
    os.unlink(tmp.name)
    return lab


def report(title, results, targets):
    print("\n## %s, %d lần" % (title, len(next(iter(results.values())))))
    print("| Target | Điểm op > 0 | pos ≤ 4 | Trung vị pos |")
    print("|---|---|---|---|")
    for name, _, _ in targets:
        rs = results[name]
        g = sum(1 for s, _, _ in rs if s is not None and s > 0)
        k = sum(1 for _, p, _ in rs if p is not None and p <= 4)
        ps = [p for _, p, _ in rs if p is not None]
        med = statistics.median(ps) if ps else "-"
        print("| %s | %d/%d | %d/%d | %s |" % (name, g, len(rs), k, len(rs), med))


def main():
    lab, ops, _, provider = X.new_data()
    opf = {o["row_id"]: op_feats(o) for o in ops}
    ff = {(o["row_id"], f["key"]): field_feats(f) for o in ops for f in o["fields"]}
    targets = load_targets()

    base_op, base_role = train(ops, opf, ff, lab)
    model = {}
    for r in csv.DictReader(open(MODEL)):
        if r["table"] == "op" and r["feature"] != "__prior__":
            model[r["feature"]] = float(r["weight"])
    diff = max(abs(base_op[0].get(k, 99) - v) for k, v in model.items())
    print("kiem: dau hieu op mo phong %d, trong jar %d, lech lon nhat %.3g" % (len(base_op[0]), len(model), diff))
    print("\n## Gốc, nhãn đa số")
    for name, tm, tops in targets:
        s, pos, n = rank_target(tops, tm, base_op, base_role)
        print("%-16s %-7s %-38s diem %+.3f pos %s/%d" % (name, tm[0], tm[1], s if s is not None else float("nan"), pos, n))
        if name == "artifact-keeper" and (pos != 4 or n != 7):
            print("DUNG: artifact-keeper khong ra 4/7 nhu log P2f")
            return

    r3 = os.path.join(LR, "field-labelling-r3-20261006")
    r4 = os.path.join(LR, "field-labelling-r4-20261006")
    res = defaultdict(list)
    print("\n## E1, từng tổ hợp lượt gán, pos/số khả dụng")
    names = [n for n, _, _ in targets]
    print("| Vòng 3 + vòng 4 | Op T | " + " | ".join(names) + " |")
    print("|---|---|" + "---|" * len(names))
    for a in ("L1", "L2"):
        for b in ("LA", "LB", "LM"):
            L = merged_labels(os.path.join(r3, a), os.path.join(r4, b))
            missing = [o["row_id"] for o in ops if o["row_id"] not in L]
            if missing:
                print("HONG %s+%s: thieu %d dong" % (a, b, len(missing)))
                continue
            om, rm = train(ops, opf, ff, L)
            cells = []
            for name, tm, tops in targets:
                s, pos, n = rank_target(tops, tm, om, rm)
                res[name].append((s, pos, n))
                cells.append("%s/%d" % (pos if pos is not None else "-", n))
            print("| %s + %s | %d | %s |" % (a, b, sum(1 for o in ops if L[o["row_id"]]["T"]), " | ".join(cells)))
    report("E1", res, targets)

    rng = random.Random(SEED)
    provs = sorted({o["provider"] for o in ops})
    res = defaultdict(list)
    for _ in range(200):
        mult = defaultdict(int)
        for _ in provs:
            mult[rng.choice(provs)] += 1
        om, rm = train(ops, opf, ff, lab, mult)
        for name, tm, tops in targets:
            res[name].append(rank_target(tops, tm, om, rm))
    report("E2, bootstrap nhà cung cấp", res, targets)

    pos_ids = [o["row_id"] for o in ops if lab[o["row_id"]]["T"]]
    neg_ids = [o["row_id"] for o in ops if not lab[o["row_id"]]["T"]]
    for x in (0.1, 0.2, 0.3):
        k = round(x * len(pos_ids))
        res = defaultdict(list)
        for _ in range(100):
            L = dict(lab)
            for rid in rng.sample(pos_ids, k):
                L[rid] = dict(lab[rid], T=False)
            for rid in rng.sample(neg_ids, k):
                L[rid] = dict(lab[rid], T=True)
            om, rm = train(ops, opf, ff, L)
            for name, tm, tops in targets:
                res[name].append(rank_target(tops, tm, om, rm))
        report("E3, lật %d%% (%d op mỗi chiều)" % (round(x * 100), k), res, targets)


main()
