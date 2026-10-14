import csv, hashlib, json, os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import measure2 as W

X, M, sim = W.X, W.M, W.sim
PREV = W.LEX4
RESULTS = []


def report(code, ok, msg):
    RESULTS.append(ok)
    print("%s %s %s" % (code, "PASS" if ok else "FAIL", msg))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def k2():
    lex = [(r["word"], float(r["score"])) for r in csv.DictReader(open(os.path.join(PREV, "lexicon-new.csv"))) if r["kind"] == "path"]
    lab, ops, rows, provider = X.new_data()
    pw, qw = X.as_lex(*X.derive_new(rows, provider, False))
    same_lex = sorted(pw) == sorted(lex)
    tops = {t[0]: M.R.spec_ops(t[1]) for t in M.TARGETS}
    picks = [next(o for o in tops["artifact-keeper"] if o["method"] == "PATCH" and o["path"] == "/api/v1/users/{id}"),
             next(o for o in tops["reports-api"] if o["method"] == "PUT" and o["path"] == "/users/{username}/role")]
    picks.append(next(o for o in ops if len(W.or_hits(pw, sim.hay(o))) >= 3))
    ok, msgs = same_lex, []
    ts, _, _ = W.scorer_or(pw, qw)
    for op in picks:
        h = sim.hay(op)
        matched = [w for w, _ in lex if w in h]
        keep = [w for w in matched if all(w == o or w not in o for o in matched)]
        prod = 1.0
        for w in keep:
            prod *= 1.0 - dict(lex)[w]
        hand = 1.0 - prod
        got = ts(op)
        good = abs(hand - got) < 1e-12
        ok = ok and good
        msgs.append("%s %s: words %s hand %.6f code %.6f" % (op["method"], op["path"], keep, hand, got))
    report("K2", ok, "lexicon equals lexicon-new.csv: %s; " % same_lex + "; ".join(msgs))


def k3():
    a = W.or_hits([("collaborator", 0.6588), ("collaborators", 0.6588)], "/orgs/{org}/collaborators")
    b = W.or_hits([("user", 0.15), ("collaborator", 0.66)], "/users/{id}/collaborator")
    ok = [w for w, _ in a] == ["collaborators"] and sorted(w for w, _ in b) == ["collaborator", "user"]
    report("K3", ok, "nested -> %s; disjoint -> %s" % ([w for w, _ in a], sorted(w for w, _ in b)))


def k4():
    lab, ops, rows, provider = X.new_data()
    flag, fs, st = W.flag_feature(ops, lab)
    dr = dn = 0
    pv = set()
    ex = []
    for op in ops:
        hit = any(f["kind"] == "bool" and any(w in f["leaf"] for w in flag) for f in op["fields"])
        if not hit:
            continue
        if lab[op["row_id"]]["T"]:
            dr += 1
            pv.add(op["provider"])
            if len(ex) < 3:
                ex.append("%s %s %s" % (op["provider"], op["method"], op["path"]))
        else:
            dn += 1
    ok = (dr, dn, len(pv)) == (st["df_r"], st["df_n"], st["ncc"]) and bool(flag)
    report("K4", ok, "flag %s; independent %d/%d/%d vs code %d/%d/%d; score %.4f; T=1 examples %s"
           % (flag, dr, dn, len(pv), st["df_r"], st["df_n"], st["ncc"], fs, ex))


def k1():
    a = json.load(open(os.path.join(HERE, "cv.json")))["repeats"][0]
    b = json.load(open(os.path.join(PREV, "cv.json")))["repeats"][0]
    diff = []
    for arm in ("A-cur", "A-new"):
        for m in M.RANK_METRICS + M.SIM_METRICS:
            if a["rates_V"][arm][m] != b["rates_V"][arm][m]:
                diff.append((arm, "V", m, a["rates_V"][arm][m], b["rates_V"][arm][m]))
        for m in M.SIM_METRICS:
            if a["rates_RF"][arm][m] != b["rates_RF"][arm][m]:
                diff.append((arm, "RF", m, a["rates_RF"][arm][m], b["rates_RF"][arm][m]))
    report("K1", not diff, "A-cur, A-new repeat 1 vs ../lexicon-r4-20261007/cv.json: %d differences %s" % (len(diff), diff[:3]))


def k5():
    res = json.load(open(os.path.join(HERE, "cv.json")))
    info = [i for r in res["repeats"] for i in r["info"]]
    rows, _ = X.old_train()
    trained = {r["spec_id"] for r in rows}
    ok = all(i["train_test_providers"] == 0 and i["test_specs_in_old29"] == 0 for i in info) and set(res["old29"]) == trained and len(trained) == 29
    report("K5", ok, "%d folds; excluded %d specs = old training specs" % (len(info), len(res["old29"])))


def k6():
    res = json.load(open(os.path.join(HERE, "cv.json")))
    nc = res["negative_control"]
    a = res["repeats"][0]["rates_V"]["A-new-OR"]["top1"]["yes"]
    report("K6", nc["top1_permuted"] < nc["top1_real"] and nc["top1_real"] == a,
           "A-new-OR top-1 real %d, permuted %d, of %d specs; equals arm repeat 1 (%d)" % (nc["top1_real"], nc["top1_permuted"], nc["specs"], a))


def k8():
    a = json.load(open(os.path.join(HERE, "targets.json")))
    b = json.load(open(os.path.join(PREV, "targets.json")))
    keys = ["target", "arm", "write_ops", "score", "rank_best", "rank_worst", "rank_spec_order", "viable", "viable_pos"]
    pick = lambda rows: sorted(tuple(json.dumps(r[k]) for k in keys) for r in rows if r["arm"] in ("A-cur", "A-new"))
    pa, pb = pick(a), pick(b)
    report("K8", pa == pb and len(pa) == 12, "A-cur, A-new target rows: %d here, %d before, identical %s" % (len(pa), len(pb), pa == pb))


def k7():
    tmp = tempfile.mkdtemp(dir=os.environ.get("TMPDIR", "/tmp"))
    W.main(tmp)
    diff = [n for n in ("cv.json", "targets.json") if sha(os.path.join(tmp, n)) != sha(os.path.join(HERE, n))]
    shutil.rmtree(tmp)
    report("K7", not diff, "second full run, differing files: %s" % (diff or "none"))


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"
    if stage in ("pre", "all"):
        k2()
        k3()
        k4()
    if stage in ("post", "all"):
        k1()
        k5()
        k6()
        k8()
        k7()
    print("ALL PASS" if all(RESULTS) else "SOME FAIL")
    sys.exit(0 if all(RESULTS) else 1)


if __name__ == "__main__":
    main()
