"""Pham vi nhan A so voi nhu cau runtime: truong A nam trong op co chu the bi tac dong (C) hay khong.
Builder chi can truong vai tro cua mot user da ton tai trong op ha quyen (victim + role).
Truong A trong op khong co C = dinh nghia role/nhom quyen, cai dat mac dinh, moi, tao moi...
Xem tu nao trong danh sach R0/R4 den chu yeu tu nhom 'khong C'."""
from collections import Counter, defaultdict
from lib import *

f1, f2 = all_fields()


def split_A(ff):
    ops = defaultdict(list)
    for f in ff:
        ops[f["row_id"]].append(f)
    withC, noC = [], []
    for rid, fs in ops.items():
        hasC = any(f["C"] for f in fs)
        for f in fs:
            if f["A"] in ("role", "perms") and f["leaf"] != "(body)":
                (withC if hasC else noC).append(f)
    return withC, noC


for label, ff in (("train+dev", f1), ("test", f2)):
    w, n = split_A(ff)
    print("== %s: A-role duong %d; trong op co C %d (nha_cc %d); trong op khong co C %d (nha_cc %d)"
          % (label, len(w) + len(n), len(w), len({f['provider'] for f in w}), len(n), len({f['provider'] for f in n})))
    print("   op khong C, top nha_cc:", Counter(f["provider"] for f in n).most_common(5))
    print("   op khong C, vi du:", [(f["provider"], f["leaf"], f["method"] + " " + f["path"][:45]) for f in n[:6]])

wtr, ntr = split_A(f1)
words = set(derive(docs(f1, "A-role"), "R0")[0]) | set(derive(docs(f1, "A-role"), "R4")[0])
print("\n== nguon cua tu R0/R4 A-role (train+dev): so truong duong chua tu, trong op co C / khong C")
for wd in sorted(words):
    a = sum(1 for f in wtr if wd in f["leaf"])
    b = sum(1 for f in ntr if wd in f["leaf"])
    print("   %-11s co C %3d | khong C %3d" % (wd, a, b))

print("\n== neu chi lay A trong op co C lam duong (A-role), R0/R4 rut tren train+dev:")
f1b = [dict(f, A=(f["A"] if f in wtr or f["A"] not in ("role", "perms") else "")) for f in f1]
for r in ("R0", "R1", "R4"):
    print("  ", r, derive(docs(f1b, "A-role"), r)[0])
