import hashlib, json, os, random, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lexlib as X

sim = X.sim
sys.path.insert(0, os.path.join(X.LR, "field-ranking-v2-20261007"))
import sim_rf as F

R = F.R
KS = [1, 3, 8]
ARMS = ["A-cur", "A-new", "A-newV1", "A-newV1-0"]
PAIRS = [("A-cur", "A-new"), ("A-new", "A-newV1"), ("A-newV1", "A-newV1-0"), ("A-cur", "A-newV1-0")]
RANK_METRICS = ["top1", "top3", "top8", "top1_best", "top3_best", "top8_best", "top1_worst", "top3_worst", "top8_worst"]
SIM_METRICS = ["M1", "M1any", "M2", "M5"]
TARGETS = [
    ("reports-api", os.path.join(HERE, "targets", "reports-api.json"), "PUT", "/users/{username}/role"),
    ("vampi-seeded", os.path.join(HERE, "targets", "vampi-seeded.json"), "PUT", "/users/v1/{username}/role"),
    ("pyLoad", os.path.join(X.LR, "..", "..", "pyload-cve", "openapi-merged.json"), "POST", "/api/set_user_permission"),
    ("Airflow", os.path.join(X.LR, "..", "..", "airflow-target", "airflow-merged.json"), "PATCH", "/auth/fab/v1/users/{username}"),
    ("artifact-keeper", os.path.join(X.LR, "..", "..", "em-results", "artifactkeeper-machine-20261001", "openapi-trimmed.json"), "PATCH", "/api/v1/users/{id}"),
    ("bamf", os.path.join(X.LR, "..", "..", "bamf-target", "run-bamf", "openapi.json"), "PATCH", "/api/v1/users/{email}"),
]


def scorer(pw, qw, bonus_list):
    cache, pcache, ucache = {}, {}, {}

    def memo(store, op, fn):
        k = id(op)
        hit = store.get(k)
        if hit is None or hit[0] is not op:
            hit = (op, fn(op))
            store[k] = hit
        return hit[1]

    def pscore(op):
        return memo(pcache, op, lambda o: max([s for w, s in pw if w in sim.hay(o)] or [0.0]))

    def tscore(op):
        def f(o):
            s = pscore(o)
            if bonus_list and any(a in sim.hay(o) for a in bonus_list):
                s = max(s, sim.ADMIN_SCORE)
            return s
        return memo(cache, op, f)

    def up(op):
        return memo(ucache, op, lambda o: any(w in n for n, _, _ in sim.genes(o) for w, _ in qw))

    def admin_only(op):
        return bool(bonus_list) and any(a in sim.hay(op) for a in bonus_list) and pscore(op) < sim.ADMIN_SCORE

    return tscore, up, admin_only


def runtime_key(tscore, up):
    return lambda op: (-tscore(op), not up(op), X.VERBS.index(op["method"].upper()))


def rank_of(oplist, is_target, tscore, up):
    key = runtime_key(tscore, up)
    oseq = sorted(oplist, key=key)
    rseq = min(i + 1 for i, op in enumerate(oseq) if is_target(op))
    groups = {}
    for op in oplist:
        groups.setdefault(key(op), []).append(op)
    before = 0
    for k in sorted(groups):
        g = groups[k]
        n = sum(1 for op in g if is_target(op))
        if n:
            return before + 1, before + (len(g) - n) + 1, rseq
        before += len(g)
    return None


def rank_outcomes(ops, lab, spec_ok, tscore, up):
    by = defaultdict(list)
    for op in ops:
        by[op["spec"]].append(op)
    out = {m: {} for m in RANK_METRICS}
    for s, ol in by.items():
        if not spec_ok(s) or not any(lab[op["row_id"]]["T"] for op in ol):
            continue
        best, worst, rseq = rank_of(ol, lambda op: lab[op["row_id"]]["T"], tscore, up)
        for k in KS:
            out["top%d" % k][s] = rseq <= k
            out["top%d_best" % k][s] = best <= k
            out["top%d_worst" % k][s] = worst <= k
    return out


def viable(oplist, LB, tscore, up):
    red = R.fns(LB)[0]
    ranked = [op for op in oplist if op["method"] in sim.VERB_ORDER and tscore(op) > 0]
    ranked.sort(key=lambda op: (-tscore(op), not up(op), sim.VERB_ORDER.index(op["method"])))
    return [op for op in ranked[:sim.MAX_TRANSITION_CANDIDATES] if red(op, LB)]


def sim_outcomes(ops, lab, spec_ok, LB, tscore, up, admin_only):
    keys = R.fns(LB)[1]
    by = defaultdict(list)
    for op in ops:
        if spec_ok(op["spec"]):
            by[op["spec"]].append(op)
    out = {m: {} for m in SIM_METRICS}
    for s, ol in by.items():
        tops = [op for op in ol if lab[op["row_id"]]["T"]]
        tops_role = [op for op in tops if lab[op["row_id"]]["role"]]
        via = viable(ol, LB, tscore, up)

        def hit(op):
            l = lab[op["row_id"]]
            return l["T"] and bool(keys(op, LB) & set(l["role"]))
        if tops_role:
            out["M1"][s] = bool(via) and hit(via[0])
            out["M1any"][s] = any(hit(op) for op in via)
        if not tops:
            out["M2"][s] = bool(via)
        for op in ol:
            if not lab[op["row_id"]]["T"]:
                out["M5"][op["row_id"]] = admin_only(op)
    return out


def folds(ops):
    provs = sorted({op["provider"] for op in ops})
    rng = random.Random(sim.SEED)
    for _ in range(4):
        order = provs[:]
        rng.shuffle(order)
        yield [set(order[i::5]) for i in range(5)]


def lexicons(rows, provider):
    cur = X.read_lexicon(X.JAR_LEX)
    new = X.as_lex(*X.derive_new(rows, provider, False))
    newv1 = X.as_lex(*X.derive_new(rows, provider, True))
    return {"A-cur": (cur, True), "A-new": (new, True), "A-newV1": (newv1, True), "A-newV1-0": (newv1, False)}


def arm_scorers(lx):
    return {a: scorer(pw, qw, sim.HARD["admin"] if bonus else []) for a, ((pw, qw), bonus) in lx.items()}


def run_cv(lab, ops, rows, provider, old29, with_rf=True):
    spec_ok = lambda s: s not in old29
    reps = []
    for r, fl in enumerate(folds(ops)):
        pooled = {a: defaultdict(dict) for a in ARMS}
        pooled_rf = {a: defaultdict(dict) for a in ARMS}
        leak = []
        for held in fl:
            tr_rows = [x for x in rows if provider[x["spec_id"]] not in held]
            tr_ops = [op for op in ops if op["provider"] not in held]
            te_ops = [op for op in ops if op["provider"] in held]
            leak.append({"train_test_providers": len({provider[x["spec_id"]] for x in tr_rows} & held),
                         "test_specs_in_old29": len({op["spec"] for op in te_ops if spec_ok(op["spec"])} & set(old29))})
            sc = arm_scorers(lexicons(tr_rows, provider))
            rf = F.models(tr_ops, lab)["RF"] if with_rf else None
            for a, (ts, up, ao) in sc.items():
                for m, d in rank_outcomes(te_ops, lab, spec_ok, ts, up).items():
                    pooled[a][m].update(d)
                for m, d in sim_outcomes(te_ops, lab, spec_ok, sim.HARD, ts, up, ao).items():
                    pooled[a][m].update(d)
                if rf is not None:
                    for m, d in sim_outcomes(te_ops, lab, spec_ok, rf, ts, up, ao).items():
                        pooled_rf[a][m].update(d)
        reps.append({"V": pooled, "RF": pooled_rf, "leak": leak})
    return reps


def negative_control(lab, ops, rows, provider, old29):
    spec_ok = lambda s: s not in old29
    fl = next(folds(ops))
    real, perm, expect, n = 0, 0, 0.0, 0
    rng = random.Random(sim.SEED)
    for held in fl:
        tr_rows = [x for x in rows if provider[x["spec_id"]] not in held]
        te_ops = [op for op in ops if op["provider"] in held]
        labels = [x["final_label"] for x in tr_rows]
        rng.shuffle(labels)
        sh_rows = [dict(x, final_label=l) for x, l in zip(tr_rows, labels)]
        for rr, key in ((tr_rows, "real"), (sh_rows, "perm")):
            pw, qw = X.as_lex(*X.derive_new(rr, provider, True))
            ts, up, _ = scorer(pw, qw, [])
            d = rank_outcomes(te_ops, lab, spec_ok, ts, up)["top1"]
            if key == "real":
                real += sum(d.values())
                n += len(d)
            else:
                perm += sum(d.values())
        by = defaultdict(list)
        for op in te_ops:
            by[op["spec"]].append(op)
        for s, ol in by.items():
            t = sum(1 for op in ol if lab[op["row_id"]]["T"])
            if spec_ok(s) and t:
                expect += t / float(len(ol))
    return {"specs": n, "top1_real": real, "top1_permuted": perm, "top1_random_expected": round(expect, 2)}


def target_rows(lx_full):
    out = []
    for name, path, m, p in TARGETS:
        tops = R.spec_ops(path)
        for a, (ts, up, ao) in arm_scorers(lx_full).items():
            is_t = lambda op: op["method"] == m and op["path"] == p
            best, worst, rseq = rank_of(tops, is_t, ts, up)
            op = next(o for o in tops if is_t(o))
            h = sim.hay(op)
            pw = lx_full[a][0][0]
            words = sorted([(s, w) for w, s in pw if w in h], reverse=True)[:3]
            via = viable(tops, sim.HARD, ts, up)
            vpos = [i + 1 for i, o in enumerate(via) if is_t(o)]
            out.append({"target": name, "arm": a, "write_ops": len(tops), "score": round(ts(op), 4),
                        "top_words": [[w, s] for s, w in words], "rank_best": best, "rank_worst": worst,
                        "rank_spec_order": rseq, "viable": ["%s %s" % (o["method"], o["path"]) for o in via],
                        "viable_pos": vpos[0] if vpos else None})
    return out


def rate(d):
    return {"n": len(d), "yes": sum(d.values())}


def main(outdir):
    lab, ops, rows, provider = X.new_data()
    old29 = set(X.old_train_specs())
    unit_prov = {op["spec"]: op["provider"] for op in ops}
    unit_prov.update({op["row_id"]: op["provider"] for op in ops})
    full_p_new, full_q_new = X.derive_new(rows, provider, False)
    full_p_v1, full_q_v1 = X.derive_new(rows, provider, True)
    X.write_lexicon(os.path.join(outdir, "lexicon-new.csv"), X.lexicon_rows(full_p_new, full_q_new))
    X.write_lexicon(os.path.join(outdir, "lexicon-newV1.csv"), X.lexicon_rows(full_p_v1, full_q_v1))
    X.write_candidates(os.path.join(outdir, "candidates-new-path.csv"), full_p_new)
    X.write_candidates(os.path.join(outdir, "candidates-newV1-path.csv"), full_p_v1)
    X.write_candidates(os.path.join(outdir, "candidates-new-param.csv"), full_q_new)
    reps = run_cv(lab, ops, rows, provider, old29)
    res = {"ops": len(ops), "old29": sorted(old29), "repeats": []}
    for r, rep in enumerate(reps):
        row = {"repeat": r + 1, "leak": rep["leak"],
               "rates_V": {a: {m: rate(rep["V"][a][m]) for m in RANK_METRICS + SIM_METRICS} for a in ARMS},
               "rates_RF": {a: {m: rate(rep["RF"][a][m]) for m in SIM_METRICS} for a in ARMS}, "tests_V": {}, "tests_RF": {}}
        if r == 0:
            for a, b in PAIRS:
                for m in RANK_METRICS[:3] + SIM_METRICS:
                    t = sim.mcnemar(rep["V"][a][m], rep["V"][b][m])
                    t["ci95_diff"] = sim.boot_diff(rep["V"][a][m], rep["V"][b][m], unit_prov)
                    row["tests_V"]["%s - %s %s" % (b, a, m)] = t
                for m in SIM_METRICS:
                    t = sim.mcnemar(rep["RF"][a][m], rep["RF"][b][m])
                    t["ci95_diff"] = sim.boot_diff(rep["RF"][a][m], rep["RF"][b][m], unit_prov)
                    row["tests_RF"]["%s - %s %s" % (b, a, m)] = t
        res["repeats"].append(row)
    res["negative_control"] = negative_control(lab, ops, rows, provider, old29)
    lx_full = {"A-cur": (X.read_lexicon(X.JAR_LEX), True),
               "A-new": (X.as_lex(full_p_new, full_q_new), True),
               "A-newV1": (X.as_lex(full_p_v1, full_q_v1), True),
               "A-newV1-0": (X.as_lex(full_p_v1, full_q_v1), False)}
    tg = target_rows(lx_full)
    json.dump(res, open(os.path.join(outdir, "cv.json"), "w"), indent=1, sort_keys=True, default=list)
    json.dump(tg, open(os.path.join(outdir, "targets.json"), "w"), indent=1, sort_keys=True)
    for r in res["repeats"]:
        print("repeat", r["repeat"], {a: {m: r["rates_V"][a][m]["yes"] for m in ["top1", "top3", "top8", "M1", "M2", "M5"]} for a in ARMS})
    print("negative control", res["negative_control"])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else HERE)
