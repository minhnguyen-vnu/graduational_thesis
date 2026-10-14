import csv, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import derive_model as D

NB_DIR = os.path.join(D.LR, "p2-nb-20261012")
RK_CSV = os.path.join(D.LR, "field-ranking-20261007", "rankings", "RK.csv")
FAILED = []


def check(name, ok, detail):
    if not ok:
        FAILED.append(name)
    print("%s  %-26s %s" % ("PASS" if ok else "FAIL", name, detail))


def read_model(path):
    m = {}
    for r in csv.DictReader(open(path)):
        m.setdefault(r["table"], {})[r["feature"]] = float(r["weight"])
    return m


def analysis_namespace():
    cwd = os.getcwd()
    os.chdir(NB_DIR)
    try:
        ns = {"__name__": "nb"}
        exec(open("b3check.py").read().rsplit("for rep, fl in", 1)[0], ns)
        return ns
    finally:
        os.chdir(cwd)


def main():
    lab, ops = D.load()
    same = D.render(D.model(ops, lab)).encode() == open(D.OUT, "rb").read()
    check("regenerates-byte-identical", same, "derive_model.py output equals %s" % os.path.basename(D.OUT))

    m = read_model(D.OUT)
    ns = analysis_namespace()
    ops = ns["ops"]
    for table, fn in (("op", "nb_train"), ("role", "ftrain"), ("victim", "vtrain")):
        w, prior = ns[fn](ops)
        got = dict(m[table])
        gp = got.pop(D.PRIOR)
        ok = got == w and gp == prior
        check("%s-equals-%s" % (table, fn), ok, "%d features, prior %.4f; measured scripts: %d features, prior %.4f" % (
            len(got), gp, len(w), prior))

    rk = {}
    for r in csv.DictReader(open(RK_CSV)):
        rk.setdefault(r["ranking"], {})[r["word"]] = (float(r["score"]), int(r["ncc"]))
    for side in ("low", "high"):
        ok = set(m[side]) == set(rk[side]) and all(round(m[side][w], 4) == rk[side][w][0] for w in m[side])
        strs = sorted(w for w, (_, n) in rk[side].items() if n >= 2)
        ok2 = sorted(m[side + "str"]) == strs
        check("%s-equals-RK.csv" % side, ok and ok2, "%s; ncc>=2 %s" % (
            sorted(m[side], key=lambda w: -m[side][w]), sorted(m[side + "str"], key=lambda w: -m[side + "str"][w])))

    check("priors", round(m["op"][D.PRIOR], 2) == -3.94 and round(m["role"][D.PRIOR], 2) == -1.94,
          "op %.4f role %.4f victim %.4f (design doc: -3.94, -1.94)" % (
              m["op"][D.PRIOR], m["role"][D.PRIOR], m["victim"][D.PRIOR]))

    tops = D.SR.spec_ops(os.path.join(D.LR, "..", "..", "pyload-cve", "openapi-merged.json"))
    want = {"/api/set_user_permission": 5.61, "/json/add_user": 2.84, "/api/add_user": 1.69}
    got = {}
    for o in tops:
        if o["method"] == "POST" and o["path"] in want:
            got[o["path"]] = round(m["op"][D.PRIOR] + sum(m["op"].get(t, 0.0) for t in D.op_feats(o)), 2)
    check("pyload-op-scores", got == want, "model %s; pyload_nb.py %s" % (got, want))

    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
