import json, os, random, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
LEX4 = os.path.normpath(os.path.join(HERE, "..", "lexicon-r4-20261007"))
sys.path.insert(0, LEX4)
import lexlib as X
import measure as M

sim = X.sim
F = M.F
ARMS = ["A-cur", "A-new", "A-new-0", "A-new-OR", "A-new-bool"]
PAIRS = [("A-new", "A-new-0"), ("A-new", "A-new-OR"), ("A-new", "A-new-bool"), ("A-new-0", "A-new-OR"),
         ("A-new-0", "A-new-bool"), ("A-cur", "A-new-OR"), ("A-cur", "A-new-bool")]


def memo(fn):
    store = {}

    def get(op):
        k = id(op)
        hit = store.get(k)
        if hit is None or hit[0] is not op:
            hit = (op, fn(op))
            store[k] = hit
        return hit[1]
    return get


def or_hits(pw, h):
    hits = [(w, s) for w, s in pw if w in h]
    ws = [w for w, _ in hits]
    return [(w, s) for w, s in hits if not any(o != w and w in o for o in ws)]


def or_score(pw, h):
    p = 1.0
    for _, s in or_hits(pw, h):
        p *= 1.0 - s
    return 1.0 - p


def user_param(qw):
    return memo(lambda o: any(w in n for n, _, _ in sim.genes(o) for w, _ in qw))


def scorer_or(pw, qw):
    return memo(lambda o: or_score(pw, sim.hay(o))), user_param(qw), (lambda o: False)


def has_flag(op, flag):
    return bool(flag) and any(k == "bool" and any(w in n for w in flag) for n, k, _ in sim.genes(op))


def flag_feature(train_ops, lab):
    flag = sim.derive(train_ops, lab, "std")[0]["admin"]
    dr = [op for op in train_ops if lab[op["row_id"]]["T"] and has_flag(op, flag)]
    dn = sum(1 for op in train_ops if not lab[op["row_id"]]["T"] and has_flag(op, flag))
    ncc = len({op["provider"] for op in dr})
    fs = round(X.score(len(dr), dn, ncc), 4) if dr else 0.0
    return flag, fs, {"flag": flag, "df_r": len(dr), "df_n": dn, "ncc": ncc, "score": fs}


def scorer_bool(pw, qw, flag, fs):
    word = memo(lambda o: max([s for w, s in pw if w in sim.hay(o)] or [0.0]))
    fires = memo(lambda o: fs > 0 and has_flag(o, flag))
    tscore = memo(lambda o: max(word(o), fs) if fires(o) else word(o))
    return tscore, user_param(qw), (lambda o: fires(o) and fs > word(o))


def arm_scorers(lx_cur, lx_new, flag, fs):
    (pc, qc), (pn, qn) = lx_cur, lx_new
    return {"A-cur": M.scorer(pc, qc, sim.HARD["admin"]),
            "A-new": M.scorer(pn, qn, sim.HARD["admin"]),
            "A-new-0": M.scorer(pn, qn, []),
            "A-new-OR": scorer_or(pn, qn),
            "A-new-bool": scorer_bool(pn, qn, flag, fs)}


def run_cv(lab, ops, rows, provider, old29):
    spec_ok = lambda s: s not in old29
    cur = X.read_lexicon(X.JAR_LEX)
    reps = []
    for fl in M.folds(ops):
        pooled = {a: defaultdict(dict) for a in ARMS}
        pooled_rf = {a: defaultdict(dict) for a in ARMS}
        info = []
        for held in fl:
            tr_rows = [x for x in rows if provider[x["spec_id"]] not in held]
            tr_ops = [op for op in ops if op["provider"] not in held]
            te_ops = [op for op in ops if op["provider"] in held]
            new = X.as_lex(*X.derive_new(tr_rows, provider, False))
            flag, fs, fst = flag_feature(tr_ops, lab)
            info.append({"train_test_providers": len({op["provider"] for op in tr_ops} & held),
                         "test_specs_in_old29": len({op["spec"] for op in te_ops if spec_ok(op["spec"])} & set(old29)),
                         "feature": fst})
            rf = F.models(tr_ops, lab)["RF"]
            for a, (ts, up, ao) in arm_scorers(cur, new, flag, fs).items():
                for m, d in M.rank_outcomes(te_ops, lab, spec_ok, ts, up).items():
                    pooled[a][m].update(d)
                for m, d in M.sim_outcomes(te_ops, lab, spec_ok, sim.HARD, ts, up, ao).items():
                    pooled[a][m].update(d)
                for m, d in M.sim_outcomes(te_ops, lab, spec_ok, rf, ts, up, ao).items():
                    pooled_rf[a][m].update(d)
        reps.append({"V": pooled, "RF": pooled_rf, "info": info})
    return reps


def negative_control(lab, ops, rows, provider, old29):
    spec_ok = lambda s: s not in old29
    fl = next(M.folds(ops))
    rng = random.Random(sim.SEED)
    real = perm = n = 0
    for held in fl:
        tr_rows = [x for x in rows if provider[x["spec_id"]] not in held]
        te_ops = [op for op in ops if op["provider"] in held]
        labels = [x["final_label"] for x in tr_rows]
        rng.shuffle(labels)
        sh_rows = [dict(x, final_label=l) for x, l in zip(tr_rows, labels)]
        for rr, tag in ((tr_rows, "real"), (sh_rows, "perm")):
            pw, qw = X.as_lex(*X.derive_new(rr, provider, False))
            ts, up, _ = scorer_or(pw, qw)
            d = M.rank_outcomes(te_ops, lab, spec_ok, ts, up)["top1"]
            if tag == "real":
                real += sum(d.values())
                n += len(d)
            else:
                perm += sum(d.values())
    return {"specs": n, "top1_real": real, "top1_permuted": perm}


def target_rows(cur, new, flag, fs):
    out = []
    for name, path, m, p in M.TARGETS:
        tops = M.R.spec_ops(path)
        for a, (ts, up, ao) in arm_scorers(cur, new, flag, fs).items():
            is_t = lambda op: op["method"] == m and op["path"] == p
            best, worst, rseq = M.rank_of(tops, is_t, ts, up)
            op = next(o for o in tops if is_t(o))
            via = M.viable(tops, sim.HARD, ts, up)
            vpos = [i + 1 for i, o in enumerate(via) if is_t(o)]
            ranked = sorted(tops, key=M.runtime_key(ts, up))
            out.append({"target": name, "arm": a, "write_ops": len(tops), "score": round(ts(op), 4),
                        "top10": ["%s %s %.4f" % (o["method"], o["path"], ts(o)) for o in ranked[:10]],
                        "rank_best": best, "rank_worst": worst, "rank_spec_order": rseq,
                        "viable": ["%s %s" % (o["method"], o["path"]) for o in via], "viable_pos": vpos[0] if vpos else None,
                        "flag_fires": has_flag(op, flag), "or_hits": [[w, s] for w, s in or_hits(new[0], sim.hay(op))]})
    return out


def main(outdir):
    lab, ops, rows, provider = X.new_data()
    old29 = set(X.old_train_specs())
    unit_prov = {op["spec"]: op["provider"] for op in ops}
    unit_prov.update({op["row_id"]: op["provider"] for op in ops})
    reps = run_cv(lab, ops, rows, provider, old29)
    res = {"ops": len(ops), "old29": sorted(old29), "repeats": []}
    for r, rep in enumerate(reps):
        row = {"repeat": r + 1, "info": rep["info"],
               "rates_V": {a: {m: M.rate(rep["V"][a][m]) for m in M.RANK_METRICS + M.SIM_METRICS} for a in ARMS},
               "rates_RF": {a: {m: M.rate(rep["RF"][a][m]) for m in M.SIM_METRICS} for a in ARMS}, "tests_V": {}, "tests_RF": {}}
        if r == 0:
            for a, b in PAIRS:
                for m in M.RANK_METRICS[:3] + M.SIM_METRICS:
                    t = sim.mcnemar(rep["V"][a][m], rep["V"][b][m])
                    t["ci95_diff"] = sim.boot_diff(rep["V"][a][m], rep["V"][b][m], unit_prov)
                    row["tests_V"]["%s - %s %s" % (b, a, m)] = t
                for m in M.SIM_METRICS:
                    t = sim.mcnemar(rep["RF"][a][m], rep["RF"][b][m])
                    t["ci95_diff"] = sim.boot_diff(rep["RF"][a][m], rep["RF"][b][m], unit_prov)
                    row["tests_RF"]["%s - %s %s" % (b, a, m)] = t
        res["repeats"].append(row)
    res["negative_control"] = negative_control(lab, ops, rows, provider, old29)
    cur = X.read_lexicon(X.JAR_LEX)
    new = X.as_lex(*X.derive_new(rows, provider, False))
    flag, fs, fst = flag_feature(ops, lab)
    res["feature_full"] = fst
    tg = target_rows(cur, new, flag, fs)
    json.dump(res, open(os.path.join(outdir, "cv.json"), "w"), indent=1, sort_keys=True, default=list)
    json.dump(tg, open(os.path.join(outdir, "targets.json"), "w"), indent=1, sort_keys=True)
    for r in res["repeats"]:
        print("repeat", r["repeat"], {a: {m: r["rates_V"][a][m]["yes"] for m in ["top1", "top3", "top8", "M1", "M2", "M5"]} for a in ARMS})
    print("feature full", fst, "negative control", res["negative_control"])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else HERE)
