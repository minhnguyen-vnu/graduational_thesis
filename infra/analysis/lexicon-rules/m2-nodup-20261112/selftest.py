import csv, hashlib, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LR = os.path.normpath(os.path.join(HERE, ".."))
NOP = os.path.join(LR, "relabel-20261101", "nop-hoi-dong")
sys.path.insert(0, os.path.join(LR, "p2-model-20261012"))
sys.path.insert(0, HERE)
import derive_model as D
import derive_nodup as N
import score_thi_nodup as S

M2 = os.path.join(LR, "m2-model-20261107", "stateful-authz-model.csv")
NEW = os.path.join(HERE, "stateful-authz-model.csv")
KQ = os.path.join(HERE, "ket-qua.txt")
fails = []


def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        fails.append(msg)


def path_tokens(op):
    out = set()
    for f in op["fields"]:
        if f["loc"] == "path":
            out |= D.X.tokens(f["raw_leaf"])
    return out


def qb_tokens(op):
    out = set()
    for f in op["fields"]:
        if f["loc"] in ("query", "body"):
            out |= D.X.tokens(f["raw_leaf"])
    return out


def removed_ok(op):
    old = D.op_feats(op)
    new = N.op_feats_nodup(op)
    f_new = {x[2:] for x in new if x.startswith("f:")}
    return new <= old and f_new == qb_tokens(op) and old - new == {"f:" + t for t in path_tokens(op) - qb_tokens(op)}


def table_lines(path):
    return open(path).read().splitlines()


def main():
    e035 = None
    e330 = None
    thi = {}
    for l in open(os.path.join(NOP, "op-thi.jsonl")):
        if l.strip():
            r = json.loads(l)
            thi[r["row_id"]] = S.to_op(r)
    e035 = thi["E035-N0065"]
    e330 = thi["E330-N0047"]

    want035 = {"v:PUT", "p:group", "p:memberships", "p:membership", "f:fields", "f:configurable", "f:permissions", "f:role"}
    check(N.op_feats_nodup(e035) == want035 and D.op_feats(e035) == want035 | {"f:group", "f:membership"},
          "1 op_feats_nodup (derive_nodup.py:14-20) tren E035-N0065 PUT /group_memberships/{group_membership_id}: "
          "bo f:group, f:membership (chi tu tham so path), giu f:fields, f:configurable, f:permissions, f:role")

    check(N.op_feats_nodup(e330) == {"v:DELETE", "p:groups", "p:group"} and D.op_feats(e330) - N.op_feats_nodup(e330) == {"f:group"},
          "2 op_feats_nodup (derive_nodup.py:14-20) tren E330-N0047 DELETE /me/groups/{group_id}: con v:DELETE, p:groups, p:group")

    synth = {"method": "PUT", "path": "/users/{userId}/role", "fields": [
        {"loc": "path", "raw_leaf": "userId"}, {"loc": "body", "raw_leaf": "role"}, {"loc": "query", "raw_leaf": "userName"}]}
    want_s = {"v:PUT", "p:users", "p:user", "p:role", "f:role", "f:user", "f:name"}
    check(N.op_feats_nodup(synth) == want_s and D.op_feats(synth) == want_s,
          "3 op_feats_nodup (derive_nodup.py:18) giu f:user khi tu nay co ca o tham so query userName, du tham so path userId cung co")

    lab, ops = N.load()
    bad_hoc = [o["row_id"] for o in ops if not removed_ok(o)]
    bad_thi = [k for k, o in thi.items() if not removed_ok(o)]
    check(not bad_hoc and not bad_thi,
          "4 op_feats_nodup (derive_nodup.py:14-20) tren 10381 op hoc va %d op thi: f: dung bang tu cua query+body, "
          "phan bo di dung bang tu chi co o tham so path (loi: hoc %d, thi %d)" % (len(thi), len(bad_hoc), len(bad_thi)))

    dup_hoc = sum(1 for o in ops if D.op_feats(o) != N.op_feats_nodup(o))
    dup_thi = sum(1 for o in thi.values() if D.op_feats(o) != N.op_feats_nodup(o))
    check(dup_hoc > 0 and dup_thi > 0,
          "5 bo do lap bat duoc lap tren dac trung M2 (derive_model.op_feats): %d op hoc, %d op thi co f: chi tu tham so path" % (dup_hoc, dup_thi))

    m2_text = D.render(D.model(ops, lab))
    check(m2_text == open(M2).read(),
          "6 du lieu hoc va ham hoc dung chung (N.load derive_nodup.py:27-32, D.model) sinh lai M2 trung tung byte, sha256 %s"
          % hashlib.sha256(m2_text.encode()).hexdigest()[:12])

    new_text = D.render(N.model_nodup(ops, lab))
    check(new_text == open(NEW).read(),
          "7 model_nodup (derive_nodup.py:35-40) chay lai ra dung file stateful-authz-model.csv, sha256 %s"
          % hashlib.sha256(new_text.encode()).hexdigest()[:12])

    old_rest = [l for l in table_lines(M2) if not l.startswith("op,")]
    new_rest = [l for l in table_lines(NEW) if not l.startswith("op,")]
    old_prior = [l for l in table_lines(M2) if l.startswith("op,__prior__,")]
    new_prior = [l for l in table_lines(NEW) if l.startswith("op,__prior__,")]
    check(old_rest == new_rest and len(new_rest) == 100 and old_prior == new_prior and len(new_prior) == 1,
          "8 model_nodup (derive_nodup.py:36-39) chi doi bang op: role, victim, low, high, lowstr, highstr va prior op trung M2")

    npos = sum(1 for o in ops if lab[o["row_id"]]["T"])
    nneg = len(ops) - npos
    dp, dn, prov = {}, {}, {}
    for o in ops:
        t = lab[o["row_id"]]["T"]
        for f in N.op_feats_nodup(o):
            if t:
                dp[f] = dp.get(f, 0) + 1
                prov.setdefault(f, set()).add(o["provider"])
            else:
                dn[f] = dn.get(f, 0) + 1
    want = {f: math.log((dp[f] + 1) / (npos + 2)) - math.log((dn.get(f, 0) + 1) / (nneg + 2)) for f in dp if len(prov[f]) >= 2}
    got = {}
    for r in csv.DictReader(open(NEW)):
        if r["table"] == "op" and r["feature"] != D.PRIOR:
            got[r["feature"]] = float(r["weight"])
    dropped = sum(1 for f in dp if len(prov[f]) < 2)
    check(set(want) == set(got) and all(abs(want[f] - got[f]) < 1e-12 for f in want) and dropped > 0,
          "9 dem lai doc lap tren nhan hoc: %d trong so bang op khop file; %d dac trung bi loai vi chi co o 1 cong ty" % (len(want), dropped))

    m = S.read_model(NEW)
    hand = m["op"]["__prior__"] + m["op"]["p:group"] + m["op"]["p:groups"] + m["op"]["v:DELETE"]
    kq = open(KQ).read()
    check(abs(S.score(m, N.op_feats_nodup(e330)) - hand) < 1e-12 and ("E330-N0047 DELETE /me/groups/{group_id} 0.322 -> %.3f" % hand) in kq,
          "10 score (score_thi_nodup.py:81-83) E330-N0047 = prior + p:group + p:groups + v:DELETE = %.3f, khop dong trong ket-qua.txt" % hand)

    labt = {r["row_id"]: r for r in csv.DictReader(open(os.path.join(NOP, "nhan-thi-cuoi.csv")))}
    sc = {}
    for k, o in thi.items():
        s = m["op"]["__prior__"]
        for f in N.op_feats_nodup(o):
            s += m["op"].get(f, 0.0)
        sc[k] = s
    T = [k for k in labt if labt[k]["T"] == "1"]
    caught = sum(1 for k in T if sc[k] > 0)
    pos = [k for k in sc if sc[k] > 0]
    fp = sum(1 for k in pos if labt[k]["T"] == "0")
    line_b = next(l for l in kq.splitlines() if l.startswith("Bat duoc"))
    line_p = next(l for l in kq.splitlines() if l.startswith("So op diem > 0"))
    line_n = next(l for l in kq.splitlines() if l.startswith("Bao nham"))
    ok = (re.findall(r"(\d+)/(\d+) =", line_b)[1] == (str(caught), str(len(T)))
          and line_p.split()[-1] == str(len(pos))
          and re.findall(r"(\d+)/(\d+) =", line_n)[1] == (str(fp), str(len(pos))))
    check(ok, "11 dem lai doc lap tren phan thi khop ket-qua.txt (score_thi_nodup.py:86-145): bat %d/%d, chon %d, bao nham %d"
          % (caught, len(T), len(pos), fp))

    print("%d FAIL" % len(fails) if fails else "ALL PASS")
    sys.exit(1 if fails else 0)


main()
