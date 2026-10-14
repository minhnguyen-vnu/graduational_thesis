"""Tu trong danh sach cuoi den tu dau: liet ke truong duong/am chua tu do (train+dev), va
truong duong long trong mang (con cua truong quyen) ma ten la khong mang nghia quyen."""
from collections import Counter, defaultdict
from lib import *

f1, f2 = all_fields()


def show(word, name, ff, k=12):
    dd = [f for f in ff if f["leaf"] != "(body)" and word in f["leaf"]]
    if name == "A-role":
        pos = [f for f in dd if f["A"] in ("role", "perms")]
    elif name == "C":
        pos = [f for f in dd if f["C"]]
    neg = [f for f in dd if f not in pos]
    print("-- %s / %s: duong %d (nha_cc %s), am %d" % (word, name, len(pos), dict(Counter(f["provider"] for f in pos)), len(neg)))
    for f in pos[:k]:
        print("    + %s %s %s | %s %s | %s" % (f["provider"], f["row_id"], f["field"], f["method"], f["path"][:60], f["A"] or f["C"]))
    return neg


for w in ("approve", "restrict", "privilege", "roles"):
    show(w, "A-role", f1)
neg = show("role", "A-role", f1, 0)
print("   am chua 'role' (ten la):", Counter(f["leaf"] for f in neg).most_common(25))
for w in ("clientid",):
    show(w, "C", f1)

print("\n== truong duong A-role co ten la chung chung (id/name/type/value/key...)")
generic = {"id", "name", "type", "value", "key", "ids", "names", "values", "code", "kind"}
for label, ff in (("train+dev", f1), ("test", f2)):
    pos = [f for f in ff if f["A"] in ("role", "perms") and f["leaf"] != "(body)"]
    g = [f for f in pos if f["leaf"] in generic]
    nested = [f for f in pos if "." in f["name"]]
    print("  %s: duong %d, ten la chung chung %d (%s), long trong object/mang %d"
          % (label, len(pos), len(g), dict(Counter(f["leaf"] for f in g)), len(nested)))
    for f in g[:6]:
        print("     %s %s %s" % (f["provider"], f["field"], f["path"][:60]))

print("\n== truong duong C co ten la chi la 'id' (khong the rut vi MIN_LEN=4)")
for label, ff in (("train+dev", f1), ("test", f2)):
    pos = [f for f in ff if f["C"] and f["leaf"] != "(body)"]
    short = [f for f in pos if not tokens(f["leaf"])]
    print("  %s: C duong %d, ten la khong co token >=4 ky tu: %d %s" % (label, len(pos), len(short), dict(Counter(f["leaf"] for f in short))))
