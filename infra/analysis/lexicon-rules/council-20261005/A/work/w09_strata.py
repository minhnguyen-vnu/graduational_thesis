"""Mat do truong duong theo nguon (44 spec cu / spec moi) va theo tang (giau / ngau nhien); xep hang ung vien A-role."""
from collections import Counter, defaultdict
from load import *

F = load_all()


def src(f):
    n = int(f["spec"][1:])
    if f["round"] == 1 and n < 300:
        return "cu(S100-S214)"
    return "moi"


groups = defaultdict(list)
for f in F:
    groups[(f["split"], src(f), f["pool"])].append(f)
print("# 1. Mat do duong theo tap / nguon / tang")
for k in sorted(groups):
    ff = groups[k]
    nspec = len({f["spec"] for f in ff})
    a = sum(1 for f in ff if f["A"])
    c = sum(1 for f in ff if f["C"])
    sa = len({f["spec"] for f in ff if f["A"]})
    print(" %-5s %-14s %-9s spec=%3d op=%4d truong=%5d A+=%3d (spec co A=%2d) C+=%3d" % (
        k + (nspec, len({f["row_id"] for f in ff}), len(ff), a, sa, c)))

print("\n# 2. Xep hang ung vien A-role tren train+dev theo diem (R4 lay 5 dau, co P1)")
TD = [f for f in F if f["split"] in ("train", "dev")]
stats, base = candidates(docs(TD, "A-role"))
ok = sorted([s for s in stats if s["providers"] >= 2], key=lambda s: (-s["score"], s["word"]))
for s in ok[:12]:
    print("  ", s)
print("  'role':", [s for s in stats if s["word"] == "role"])

print("\n# 3. Ty le perms trong A-role duong va 10 ten la perms pho bien nhat (moi tap)")
for sp in ("train", "dev", "test"):
    ff = [f for f in F if f["split"] == sp and f["A"] in ("role", "perms")]
    c = Counter(f["A"] for f in ff)
    print(" ", sp, dict(c), Counter(f["leaf"] for f in ff if f["A"] == "perms").most_common(10))

print("\n# 4. Truong A-role theo kieu du lieu (runtime chi dat duoc gia tri vao string/integer/enum/array rong)")
for sp in ("train", "dev", "test"):
    ff = [f for f in F if f["split"] == sp and f["A"] in ("role", "perms")]
    print(" ", sp, Counter((f["A"], f["type"], bool(f["enum"])) for f in ff).most_common(10))
