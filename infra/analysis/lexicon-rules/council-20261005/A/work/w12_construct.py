"""Khop giua nhan A/C va thu runtime can: truong A nam trong op co truong C (gan quyen cho mot chu the da ton tai)
hay khong; quyet dinh phan xu role-def / subject-key o vong 1 so voi luat vong 2."""
from collections import Counter
from load import *

F = load_all()
O = ops(F)
print("# 1. Truong A-role/admin duong: op co truong C hay khong; kieu chu the trong path")
for sp in ("train", "dev", "test"):
    rows = Counter()
    for op in O.values():
        if op[0]["split"] != sp:
            continue
        hasC = any(f["C"] for f in op)
        for f in op:
            if f["A"] in ("role", "perms", "admin"):
                rows[(f["A"], "op co C" if hasC else "op khong C")] += 1
    print(" ", sp, sorted(rows.items()))
    # API co it nhat mot op ma A (role/admin, khong tinh perms) va C cung op
    apis = {op[0]["spec"] for op in O.values() if op[0]["split"] == sp and any(f["C"] for f in op)
            and any(f["A"] in ("role", "admin") for f in op)}
    apis_any = {op[0]["spec"] for op in O.values() if op[0]["split"] == sp and any(f["A"] for f in op)}
    print("    API co op (A role/admin + C cung op)=%d; API co A bat ky=%d" % (len(apis), len(apis_any)))

print("\n# 2. Phan xu vong 1 theo luat: ket qua nhan cuoi")
for rnd in (1, 2):
    adj = [f for f in F if f["round"] == rnd and f["adj"]]
    c = Counter((f["adj_row"]["rule"], "A=" + (f["A"] or "-"), "C=" + (f["C"] or "-")) for f in adj)
    print(" vong", rnd)
    for k, v in sorted(c.items()):
        print("   ", k, v)

print("\n# 3. C cho chu the khong phai nguoi dung (client/key/token/app) theo tap")
pat = ("client", "key", "token", "app", "secret", "credential")
for sp in ("train", "dev", "test"):
    cc = [f for f in F if f["split"] == sp and f["C"]]
    nonuser = [f for f in cc if any(p in f["leaf"] for p in pat)]
    print("  %s: C=%d, ten la chua %s=%d; vi du %s" % (sp, len(cc), pat, len(nonuser),
                                                    Counter(f["leaf"] for f in nonuser).most_common(6)))
