"""Kiem lai mot so so cua chuyen gia B (peer-round1.md).
1. B xep hang (s08): tach anh huong cua danh sach B voi thu tu enum; ca train+dev.
2. C 'tren path chu the phi-nguoi' 18%/22% (s09 §2): liet ke cac truong khop regex o test.
3. Do nhay cua danh sach R4 A-role/B voi khoi phan xu S104-0025 (23 dong 'role-def' quyet chung theo L2).
"""
import re
from collections import Counter, defaultdict
from load import *

F = load_all()
O = ops(F)
TD = [f for f in F if f["split"] in ("train", "dev")]
W = {n: derive(docs(TD, n), "R4")[0] for n in ("A-role", "B-low", "B-high")}


def is_low(v, lo, hi):
    v = v.lower()
    return any(w in v for w in lo) and not any(w in v for w in hi)


print("# 1. B_low: hang trong (gia tri thap + phan con lai), rieng danh sach B (khong phu thuoc A-role)")
for sp in ("train+dev", "test"):
    tgt = [f for f in F if (f["split"] != "test") == (sp == "train+dev") and f["A"] in ("role", "perms")
           and f["enum"] and f["B_low"] not in ("", "unordered")]
    for nm, lo, hi in (("hard", HARD["B-low"], HARD["B-high"]), ("R4", W["B-low"], W["B-high"])):
        r1 = by_list = by_order = 0
        for f in tgt:
            op = O[f["row_id"]]
            vocab = []
            for g in op:
                for v in g["enum"]:
                    if v not in vocab:
                        vocab.append(v)
            low = [v for v in vocab if is_low(v, lo, hi)]
            order = low + [v for v in vocab if v not in low]
            if order and order[0] == f["B_low"]:
                r1 += 1
                if low:
                    by_list += 1
                else:
                    by_order += 1
        print("  %-9s %-4s n=%2d hang1=%2d (nho danh sach %2d, nho thu tu enum vi khong gia tri nao khop %2d)" % (
            sp, nm, len(tgt), r1, by_list, by_order))

print("\n# 2. C duong o test khop regex 'phi-nguoi' cua s09 §2")
NONUSER = re.compile(r"token|api[-_]?key|apikey|/keys|client|/apps?\b|/applications|serviceprincipal|oauth", re.I)
for sp in ("train+dev", "test"):
    pos = [f for f in F if (f["split"] != "test") == (sp == "train+dev") and f["C"]]
    nu = [f for f in pos if NONUSER.search(f["path"])]
    print("  %s: %d/%d" % (sp, len(nu), len(pos)))
    if sp == "test":
        for k, v in Counter((f["provider"], f["method"] + " " + f["path"][:75], f["name"]) for f in nu).most_common():
            print("     ", v, k)

print("\n# 3. Do nhay voi khoi phan xu S104-0025 (23 dong role-def theo L2)")
alt = []
for f in TD:
    g = dict(f)
    if f["row_id"] == "S104-0025" and f["adj"]:
        g["A"], g["B_low"], g["B_high"], g["C"] = f["L1"]
    alt.append(g)
n_pos = sum(1 for f in TD if f["A"] in ("role", "perms"))
n_alt = sum(1 for f in alt if f["A"] in ("role", "perms"))
print("  A-role duong train+dev: %d -> %d neu theo L1" % (n_pos, n_alt))
for n in ("A-role", "B-low", "B-high"):
    print("  %s R4: goc %s | theo L1 %s" % (n, derive(docs(TD, n), "R4")[0], derive(docs(alt, n), "R4")[0]))
cfg = [f for f in TD if f["provider"] == "configcat.com" and f["A"] in ("role", "perms")]
print("  configcat: %d truong A-role duong tu %d op: %s" % (len(cfg), len({f['row_id'] for f in cfg}),
                                                            Counter(f["row_id"] for f in cfg)))
