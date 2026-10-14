"""Phan tich nhan: dong thuan duong tinh, dong thuan B, huong phan xu, tap trung nha cung cap, khoi bi lo/doc thieu."""
from collections import Counter, defaultdict
from load import *

F = load_all()


def pa(pairs):
    a = sum(1 for x, y in pairs if x and y)
    b = sum(1 for x, y in pairs if x and not y)
    c = sum(1 for x, y in pairs if not x and y)
    return a, b, c, round(2 * a / float(2 * a + b + c), 3) if a + b + c else None


print("# 1. Dong thuan duong tinh (positive agreement = 2a/(2a+b+c)), theo vong")
for rnd in (1, 2):
    ff = [f for f in F if f["round"] == rnd]
    for col, i in (("A", 0), ("C", 3)):
        print(" vong %d %s: both=%d onlyL1=%d onlyL2=%d PA=%s" % ((rnd, col) + pa([(f["L1"][i], f["L2"][i]) for f in ff])))
    # theo loai A
    for kind in ("role", "perms", "admin", "active"):
        prs = [(f["L1"][0] == kind, f["L2"][0] == kind) for f in ff]
        print("   A=%s: both=%d onlyL1=%d onlyL2=%d PA=%s" % ((kind,) + pa(prs)))

print("\n# 2. Dong thuan B tren truong ca hai luot gan A role/perms va co enum")
for rnd in (1, 2):
    ff = [f for f in F if f["round"] == rnd and f["enum"]]
    both = [f for f in ff if f["L1"][0] in ("role", "perms") and f["L2"][0] in ("role", "perms")]
    any_ = [f for f in ff if f["L1"][0] in ("role", "perms") or f["L2"][0] in ("role", "perms")]
    same_low = sum(1 for f in both if f["L1"][1] == f["L2"][1])
    same_high = sum(1 for f in both if f["L1"][2] == f["L2"][2])
    ordered_l1 = sum(1 for f in both if f["L1"][1] not in ("", "unordered"))
    ordered_l2 = sum(1 for f in both if f["L2"][1] not in ("", "unordered"))
    print(" vong %d: truong co enum mot luot gan role/perms=%d, ca hai=%d, B_low trung=%d, B_high trung=%d,"
          " L1 xep duoc=%d, L2 xep duoc=%d" % (rnd, len(any_), len(both), same_low, same_high, ordered_l1, ordered_l2))
    for f in both:
        if f["L1"][1:3] != f["L2"][1:3]:
            print("   lech:", f["row_id"], f["name"], "|".join(f["enum"]), "L1", f["L1"][1:3], "L2", f["L2"][1:3],
                  "final", (f["B_low"], f["B_high"]))

print("\n# 3. Huong phan xu")
for rnd in (1, 2):
    adj = [f for f in F if f["round"] == rnd and f["adj"]]
    print(" vong %d: %d truong phan xu; chosen=%s" % (rnd, len(adj), Counter(f["adj_row"]["chosen"] for f in adj)))
    print("   rule=%s" % Counter(f["adj_row"]["rule"] for f in adj).most_common())
    print("   theo split:", Counter(f["split"] for f in adj))
    # phan xu lam doi nhan duong tinh trong tap nao
    flips = Counter()
    for f in adj:
        for col, i in (("A", 0), ("C", 3)):
            l1, l2, fin = bool(f["L1"][i]), bool(f["L2"][i]), bool(f[col])
            if l1 != l2:
                flips[(f["split"], col, "fin=L1" if fin == l1 else "fin=L2")] += 1
    print("   lech nhi phan A/C, ket qua:", sorted(flips.items()))

print("\n# 4. Tap trung nha cung cap cua truong duong (nhan cuoi)")
for sp in ("train", "dev", "test"):
    ff = [f for f in F if f["split"] == sp]
    for name, pred in (("A-role", lambda f: f["A"] in ("role", "perms")), ("A-admin", lambda f: f["A"] == "admin"),
                       ("A-active", lambda f: f["A"] == "active"), ("C", lambda f: bool(f["C"])),
                       ("B", lambda f: f["A"] in ("role", "perms") and f["enum"] and f["B_low"] not in ("", "unordered"))):
        pos = [f for f in ff if pred(f)]
        c = Counter(f["provider"] for f in pos)
        top = c.most_common(3)
        share = sum(n for _, n in top) / float(len(pos)) if pos else 0
        leaves = len({f["leaf"] for f in pos})
        print(" %-5s %-8s pos=%4d providers=%3d distinct_leaf=%3d top3=%s share_top3=%.2f" %
              (sp, name, len(pos), len(c), leaves, top, share))

print("\n# 5. Khoi doc thieu vong 1 (028, 031) va khoi da lo vong 2 (020-022)")
for rnd, chunks in ((1, ("028", "031")), (2, ("020", "021", "022"))):
    ff = [f for f in F if f["round"] == rnd and f["chunk"] in chunks]
    print(" vong %d khoi %s: specs=%s, split=%s, fields=%d, A+=%d, C+=%d" % (
        rnd, chunks, sorted({f["spec"] for f in ff}), Counter(f["split"] for f in ff), len(ff),
        sum(1 for f in ff if f["A"]), sum(1 for f in ff if f["C"])))
    if rnd == 2:
        tot_a = sum(1 for f in F if f["round"] == 2 and f["A"])
        tot_c = sum(1 for f in F if f["round"] == 2 and f["C"])
        print("   ty le duong cua test nam trong khoi da lo: A %d/%d, C %d/%d" % (
            sum(1 for f in ff if f["A"]), tot_a, sum(1 for f in ff if f["C"]), tot_c))

print("\n# 6. Operation bi cat sau 80 truong")
for rnd in (1, 2):
    ops_ = {f["row_id"]: f["fields_cut"] for f in F if f["round"] == rnd}
    cut = {k: v for k, v in ops_.items() if v}
    print(" vong %d: %d op bi cat, %d truong bi cat" % (rnd, len(cut), sum(cut.values())))
