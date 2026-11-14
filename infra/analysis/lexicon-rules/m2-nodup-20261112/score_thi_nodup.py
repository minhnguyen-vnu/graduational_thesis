import csv, hashlib, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LR = os.path.normpath(os.path.join(HERE, ".."))
NOP = os.path.join(LR, "relabel-20261101", "nop-hoi-dong")
sys.path.insert(0, os.path.join(LR, "p2-model-20261012"))
sys.path.insert(0, HERE)
import derive_model as D
import derive_nodup as N

M2 = os.path.join(LR, "m2-model-20261107", "stateful-authz-model.csv")
M2_SHA = "b2deef150bf8"
NEW = os.path.join(HERE, "stateful-authz-model.csv")
OUT = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else "ket-qua.txt")

fails = []
lines = []


def say(s):
    print(s)
    lines.append(s)


def check(ok, msg):
    say(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        fails.append(msg)


def binom_cdf(k, n, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))


def bisect(f):
    a, b = 0.0, 1.0
    for _ in range(100):
        m = (a + b) / 2
        if f(m):
            a = m
        else:
            b = m
    return a


def cp(k, n):
    lo = 0.0 if k == 0 else bisect(lambda p: 1 - binom_cdf(k - 1, n, p) < 0.025)
    hi = 1.0 if k == n else bisect(lambda p: binom_cdf(k, n, p) > 0.025)
    return lo, hi


def pct(k, n):
    lo, hi = cp(k, n)
    return "%d/%d = %.1f%%, CP 95%% %.1f–%.1f%%" % (k, n, 100.0 * k / n, 100 * lo, 100 * hi)


def mcnemar(b, c):
    if b + c == 0:
        return 1.0
    return min(1.0, 2 * binom_cdf(min(b, c), b + c, 0.5))


def to_op(r):
    fields = []
    for f in r["fields"]:
        if f["name"] == "(body)":
            continue
        fields.append({"loc": f["loc"], "name": f["name"], "key": "%s:%s" % (f["loc"], f["name"]),
                       "leaf": D.sim.leaf(f["name"]).lower(), "raw_leaf": D.sim.leaf(f["name"]), "type": f["type"],
                       "enum": [str(v) for v in f["enum"]], "kind": D.sim.gene_kind(f)})
    return {"row_id": r["row_id"], "method": r["method"], "path": r["path"], "fields": fields}


def read_model(path):
    m = {}
    for r in csv.DictReader(open(path)):
        m.setdefault(r["table"], {})[r["feature"]] = float(r["weight"])
    return m


def score(m, feats):
    t = m["op"]
    return t[D.PRIOR] + sum(t.get(f, 0.0) for f in feats)


def main():
    if os.path.exists(OUT):
        sys.exit("output exists: " + OUT)
    check(hashlib.sha256(open(M2, "rb").read()).hexdigest().startswith(M2_SHA), "M2 sha256 bat dau " + M2_SHA)
    new_sha = hashlib.sha256(open(NEW, "rb").read()).hexdigest()
    say("mo hinh bo lap: %s, sha256 %s" % (os.path.relpath(NEW, LR), new_sha[:16]))

    m2 = read_model(M2)
    mn = read_model(NEW)
    ops = {r["row_id"]: to_op(r) for r in (json.loads(l) for l in open(os.path.join(NOP, "op-thi.jsonl")) if l.strip())}
    lab = {r["row_id"]: r for r in csv.DictReader(open(os.path.join(NOP, "nhan-thi-cuoi.csv")))}
    check(len(ops) == 8674 and set(ops) == set(lab), "8674 op thi, trung nhan-thi-cuoi")
    s2 = {k: score(m2, D.op_feats(o)) for k, o in ops.items()}
    sn = {k: score(mn, N.op_feats_nodup(o)) for k, o in ops.items()}

    T = sorted(k for k, r in lab.items() if r["T"] == "1")
    Nn = sorted(k for k, r in lab.items() if r["T"] == "0")
    pos2 = [k for k in ops if s2[k] > 0]
    posn = [k for k in ops if sn[k] > 0]
    c2 = [k for k in T if s2[k] > 0]
    cn = [k for k in T if sn[k] > 0]
    f2 = [k for k in pos2 if lab[k]["T"] == "0"]
    fn = [k for k in posn if lab[k]["T"] == "0"]
    check(len(T) == 153 and len(c2) == 117 and len(pos2) == 880 and len(f2) == 763,
          "M2 cham lai bang script nay khop cham-thi/ket-qua-sau-soat-lai.txt: 117/153, 880 op diem > 0, 763 N")

    say("")
    say("Phan thi: %d op, %d op T, %d op N; diem op = prior + tong trong so bang op; chon khi diem > 0" % (len(ops), len(T), len(Nn)))
    say("%-44s %-36s %s" % ("", "M2", "bo lap"))
    say("%-44s %-36s %s" % ("Bat duoc: op T co diem > 0", pct(len(c2), len(T)), pct(len(cn), len(T))))
    say("%-44s %-36d %d" % ("So op diem > 0", len(pos2), len(posn)))
    say("%-44s %-36s %s" % ("Bao nham: op diem > 0 ma nhan cuoi N", pct(len(f2), len(pos2)), pct(len(fn), len(posn))))
    say("%-44s %-36d %d" % ("So spec co it nhat mot op diem > 0", len({lab[k]["spec_id"] for k in pos2}),
                            len({lab[k]["spec_id"] for k in posn})))

    say("")
    say("Ghep doi tren cung op, McNemar chinh xac hai phia")
    tb = [k for k in T if s2[k] > 0 and sn[k] <= 0]
    tc = [k for k in T if s2[k] <= 0 and sn[k] > 0]
    nb = [k for k in Nn if s2[k] > 0 and sn[k] <= 0]
    nc = [k for k in Nn if s2[k] <= 0 and sn[k] > 0]
    say("  op T: chi M2 bat %d, chi bo lap bat %d, p = %.4g" % (len(tb), len(tc), mcnemar(len(tb), len(tc))))
    say("  op N: chi M2 chon %d, chi bo lap chon %d, p = %.4g" % (len(nb), len(nc), mcnemar(len(nb), len(nc))))

    say("")
    say("Op T doi ket qua (id, method, path, diem M2 -> diem bo lap)")
    for k in tb + tc:
        o = ops[k]
        say("  %s %s %s %.3f -> %.3f" % (k, o["method"], o["path"], s2[k], sn[k]))

    say("")
    say("Op co tham so path bi tinh lap o M2 (it nhat mot dac trung f: chi den tu tham so path)")
    dup = [k for k, o in ops.items() if D.op_feats(o) - N.op_feats_nodup(o)]
    say("  %d/%d op thi; trong do op T: %d/%d" % (len(dup), len(ops), sum(lab[k]["T"] == "1" for k in dup), len(T)))

    if fails:
        sys.exit("%d FAIL, khong ghi file" % len(fails))
    with open(OUT, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
