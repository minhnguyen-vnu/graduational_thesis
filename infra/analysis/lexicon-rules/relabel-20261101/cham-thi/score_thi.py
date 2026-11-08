import csv, hashlib, json, math, os, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RL = os.path.normpath(os.path.join(HERE, ".."))
LR = os.path.normpath(os.path.join(RL, ".."))
NOP = os.path.join(RL, "nop-hoi-dong")
sys.path.insert(0, os.path.join(LR, "p2-model-20261012"))
import derive_model as D

M2 = os.path.join(LR, "m2-model-20261107", "stateful-authz-model.csv")
M2_SHA = "b2deef150bf8"
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


def score(m, op):
    t = m["op"]
    return t[D.PRIOR] + sum(t.get(f, 0.0) for f in D.op_feats(op))


def main():
    if os.path.exists(OUT):
        sys.exit("output exists: " + OUT)
    check(hashlib.sha256(open(M2, "rb").read()).hexdigest().startswith(M2_SHA), "M2 sha256 bat dau " + M2_SHA)

    hoc = [json.loads(l) for l in open(os.path.join(NOP, "op-hoc.jsonl")) if l.strip()]
    ref = {o["row_id"]: o for o in D.sim.load_ops({r["row_id"] for r in hoc})}
    check(len(ref) == 10381 and all(D.op_feats(to_op(r)) == D.op_feats(ref[r["row_id"]]) for r in hoc),
          "doc op-hoc.jsonl ra dung dac trung op nhu luc hoc M2 (10381 op)")

    m = read_model(M2)
    ops = {r["row_id"]: to_op(r) for r in (json.loads(l) for l in open(os.path.join(NOP, "op-thi.jsonl")) if l.strip())}
    lab = {r["row_id"]: r for r in csv.DictReader(open(os.path.join(NOP, "nhan-thi-cuoi.csv")))}
    check(len(ops) == 8674 and set(ops) == set(lab), "8674 op thi, trung nhan-thi-cuoi")
    sc = {k: score(m, o) for k, o in ops.items()}

    say("")
    say("So 1: trong 176 op it nhat mot AI goi T, nhan cuoi la T o bao nhieu op (xem het, khong co khoang tin cay)")
    g176 = [r for r in lab.values() if r["nhom"] == "it_nhat_mot_AI_T"]
    check(len(g176) == 176, "176 op nhom it_nhat_mot_AI_T")
    ai = {r["row_id"]: r for r in csv.DictReader(open(os.path.join(NOP, "nhan-ai-thi.csv")))}

    def sub(a):
        s = D_is_t(a, "sonnet_")
        o = D_is_t(a, "opus_")
        if s and o:
            return "hai_AI_cung_T" if all(norm(a["sonnet_" + c]) == norm(a["opus_" + c]) for c in ("victim", "role", "order")) else "cung_T_lech_truong"
        return "lech_T"

    by = Counter()
    byT = Counter()
    for r in g176:
        g = sub(ai[r["row_id"]])
        by[g] += 1
        byT[g] += r["T"] == "1"
    for g in ("hai_AI_cung_T", "cung_T_lech_truong", "lech_T"):
        say("  %-20s %d/%d = %.1f%%" % (g, byT[g], by[g], 100.0 * byT[g] / by[g]))
    say("  %-20s %d/%d = %.1f%%" % ("cong", sum(byT.values()), 176, 100.0 * sum(byT.values()) / 176))

    say("")
    say("So 2: trong 368 op ngau nhien hai AI cung N, nhan cuoi la T o bao nhieu op; suy ra cho 8014 op chua xem")
    samp = [r for r in lab.values() if r["nhom"] == "hai_AI_cung_N" and r["cho_boc"] == "1" and r["nguon"] != "AI_chua_xem"]
    unseen = [r for r in lab.values() if r["nhom"] == "hai_AI_cung_N" and r["cho_boc"] == "1" and r["nguon"] == "AI_chua_xem"]
    check(len(samp) == 368 and len(unseen) == 8014, "368 op mau va 8014 op chua xem")
    k2 = sum(r["T"] == "1" for r in samp)
    lo, hi = cp(k2, 368)
    say("  " + pct(k2, 368))
    say("  so op T bi sot trong 8014 op chua xem: %d–%d (CP 95%%)" % (round(lo * 8014), round(hi * 8014)))

    say("")
    say("So 3: M2 tren phan thi; diem op = prior + tong trong so bang op, ung vien khi diem > 0")
    T = [k for k, r in lab.items() if r["T"] == "1"]
    caught = [k for k in T if sc[k] > 0]
    check(all(lab[k]["nhom"] == "it_nhat_mot_AI_T" for k in T), "moi op T thuoc 176 op (mau ngau nhien 0 op T, trong so khong doi ket qua)")
    say("  Bat duoc: op T co diem > 0: " + pct(len(caught), len(T)))
    say("  Neu %d op T bi sot o So 2 deu co diem <= 0: %d/%d = %.1f%%" % (round(hi * 8014), len(caught), len(T) + round(hi * 8014),
                                                                      100.0 * len(caught) / (len(T) + round(hi * 8014))))
    pos = [k for k in ops if sc[k] > 0]
    fp = [k for k in pos if lab[k]["T"] == "0"]
    say("  Bao nham: op diem > 0 ma nhan cuoi la N: " + pct(len(fp), len(pos)))
    say("    theo nguon nhan: %s" % dict(Counter(lab[k]["nguon"] for k in fp)))
    say("    theo nhom: %s" % dict(Counter((lab[k]["nhom"], lab[k]["cho_boc"]) for k in fp)))
    say("  So op diem > 0: %d tren %d op thi; so spec co it nhat mot op diem > 0: %d tren %d spec" % (
        len(pos), len(ops), len({lab[k]["spec_id"] for k in pos}), len({r["spec_id"] for r in lab.values()})))

    if fails:
        sys.exit("%d FAIL, khong ghi file" % len(fails))
    with open(OUT, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(OUT)


CORE_B = {"role_set", "role_remove", "perm", "admin_flag", "member_role", "member_remove"}


def D_is_t(r, p):
    return r[p + "A"] in {"existing", "self"} and r[p + "B"] in CORE_B and r[p + "C"] in {"down", "unclear"}


def norm(v):
    return "|".join(sorted(x.strip() for x in v.split("|") if x.strip()))


main()
