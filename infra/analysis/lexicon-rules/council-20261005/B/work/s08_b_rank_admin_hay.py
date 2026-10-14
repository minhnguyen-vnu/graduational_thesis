"""(1) B: mo phong thu tu ung vien gia tri cua builder.
  - Ha quyen: harvestReducedRoleCandidates (RestSecurityBuilder.kt:970-983): enumVocab = moi gia tri enum cua MOI
    gene trong op (khong chi truong role); lowPrivEnum = isLowPrivRole (:709-712, chua tu thap VA khong chua tu cao)
    dung truoc. Hang cua B_low trong (lowPrivEnum + phan con lai cua enumVocab).
  - Nang quyen: harvestElevatedRoleCandidates (:986-1006): enum cua op + MOI op cua API, loc chua tu cao.
    Xap xi 'moi op cua API' bang moi op ghi da trich cua cung spec (rows chi co op ghi, toi da 36 op).
  So sanh danh sach viet tay va danh sach R4 cuoi.
(2) ADMIN_FLAG_FIELD_SIGNALS con dung o transitionScore (:104-112): hay = path + ten op + ten truong body cap 1.
  Neu thay bang 'admin' (danh sach rut), dem op co hay chua 'admin' (diem 0.6 > moi diem path trong lexicon)."""
from collections import defaultdict
from lib import *

f1, f2 = all_fields()
HL, HH = HARD["B-low"], HARD["B-high"]
DL = derive(docs(f1, "B-low"), "R4")[0]
DH = derive(docs(f1, "B-high"), "R4")[0]
print("hard low", HL, "\nhard high", HH, "\nR4 low", DL, "\nR4 high", DH)


def is_low(v, lo, hi):
    v = v.lower()
    return any(w in v for w in lo) and not any(w in v for w in hi)


def reduced_rank(op_fields, target, lo, hi):
    vocab = []
    for f in op_fields:
        for v in f["enum"]:
            if v not in vocab:
                vocab.append(v)
    low = [v for v in vocab if is_low(v, lo, hi)]
    order = low + [v for v in vocab if v not in low]
    return order.index(target) + 1 if target in order else None, len(order), low


def elevated_rank(op_fields, spec_fields, target, hi):
    vocab = []
    for f in op_fields + spec_fields:
        for v in f["enum"]:
            if v not in vocab:
                vocab.append(v)
    high = [v for v in vocab if any(w in v.lower() for w in hi)]
    return high.index(target) + 1 if target in high else None, len(high)


for label, ff in (("train+dev", f1), ("test r2", f2)):
    ops, spec = defaultdict(list), defaultdict(list)
    for f in ff:
        ops[f["row_id"]].append(f)
        spec[f["spec"]].append(f)
    tgt = [f for f in ff if f["A"] in ("role", "perms") and f["enum"] and f["B_low"] not in ("", "unordered")]
    print("\n== %s: %d truong co B" % (label, len(tgt)))
    for nm, lo, hi in (("hard", HL, HH), ("R4", DL, DH)):
        r1 = rk = 0
        e1 = 0
        details = []
        for f in tgt:
            rr, n, low = reduced_rank(ops[f["row_id"]], f["B_low"], lo, hi)
            er, nh = elevated_rank(ops[f["row_id"]], spec[f["spec"]], f["B_high"], hi)
            r1 += rr == 1
            e1 += er == 1
            details.append("%s:%s low#%s/%d high#%s/%d" % (f["provider"][:10], f["leaf"], rr, n, er, nh))
        print("  %-4s B_low dung o vi tri 1: %d/%d | B_high dung o vi tri 1: %d/%d" % (nm, r1, len(tgt), e1, len(tgt)))
        print("       ", "; ".join(details))

print("\n== (2) 'admin' trong hay cua transitionScore")
for label, ff in (("train+dev", f1), ("test r2", f2)):
    ops = defaultdict(list)
    for f in ff:
        ops[f["row_id"]].append(f)
    n = len(ops)
    tot = {"hard": [0, 0], "admin": [0, 0]}
    for rid, fs in ops.items():
        top_body = [f["name"] for f in fs if f["loc"] == "body" and "." not in f["name"] and "[]" not in f["name"]]
        hay = (fs[0]["path"] + " " + fs[0]["method"] + ":" + fs[0]["path"] + " " + " ".join(top_body)).lower()
        is_tr = any(f["A"] in ("role", "perms", "admin") for f in fs)
        for nm, sig in (("hard", HARD["A-admin"]), ("admin", ["admin"])):
            if any(s in hay for s in sig):
                tot[nm][0 if is_tr else 1] += 1
    n_tr = sum(1 for fs in ops.values() if any(f["A"] in ("role", "perms", "admin") for f in fs))
    print("  %s: %d op (%d op co truong A role/perms/admin)" % (label, n, n_tr))
    for nm, (a, b) in tot.items():
        print("    %-5s: hay khop o %d op co A, %d op khong co A" % (nm, a, b))
