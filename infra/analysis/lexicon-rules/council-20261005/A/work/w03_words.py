"""Nguon goc cac tu duoc rut; anh huong cua ha chu truoc khi tach camelCase; tu viet tay khong co ho tro;
truong duong bi bo sot trong khoi doc thieu."""
from collections import Counter, defaultdict
from load import *

F = load_all()
TD = [f for f in F if f["split"] in ("train", "dev")]
ALL = F


def show(name, word, ff, n=12):
    dd = [(f, d) for f, d in zip([f for f in ff if f["leaf"] != "(body)" and
                                  (name != "A-admin" or f["type"] == "boolean" or f["A"] == "admin")], docs(ff, name))]
    pos = [f for f, d in dd if d[1] and word in d[0]]
    neg = [f for f, d in dd if not d[1] and word in d[0]]
    print("  [%s] '%s': pos=%d neg=%d" % (name, word, len(pos), len(neg)))
    print("    pos:", Counter((f["provider"], f["name"]) for f in pos).most_common(n))
    print("    neg:", Counter((f["provider"], f["name"]) for f in neg).most_common(n))


print("# 1. Nguon goc tu trong danh sach R4 (train+dev) va danh sach gop (ca ba tap)")
for name, word in (("A-role", "approve"), ("A-role", "restrict"), ("A-role", "privilege"), ("A-role", "roles"),
                   ("A-role", "role"), ("A-role", "permission"), ("A-role", "groupids"), ("C", "clientid"),
                   ("C", "member"), ("C", "user"), ("C", "membershipid")):
    show(name, word, TD if name != "A-role" or word != "groupids" else ALL)
show("A-admin", "owner", ALL)
show("A-admin", "admin", ALL)

print("\n# 2. Ha chu truoc khi tach camelCase (derive_eval.leaf + tokens)")
for name in ("A-role", "C"):
    dl = docs(TD, name)
    dr = docs(TD, name, key="raw_leaf")
    cand_l = set().union(*[tokens(d[0]) for d in dl if d[1]])
    cand_r = set().union(*[tokens(d[0]) for d in dr if d[1]])
    print(" %s: ung vien tu leaf ha chu=%d, tu ten goc=%d, chi co khi tach dung=%d" % (
        name, len(cand_l), len(cand_r), len(cand_r - cand_l)))
    print("   vi du them:", sorted(cand_r - cand_l)[:40])
    print("   vi du mat (ghep):", sorted(cand_l - cand_r)[:40])
    w_l, _, _ = derive(dl, "R4")
    w_r, _, _ = derive(dr, "R4")
    print("   R4 voi leaf ha chu:", w_l, " | R4 voi tach camelCase dung:", w_r)
    te = [f for f in F if f["split"] == "test"]
    print("   test F1: ha chu", prf(name, w_l, docs(te, name))["f1"], " tach dung", prf(name, w_r, docs(te, name))["f1"])

print("\n# 3. Tu viet tay: ho tro tren ca ba tap (df_pos, df_neg, so nha cung cap duong)")
for name in ("A-role", "A-admin", "C", "B-low", "B-high"):
    dd = docs(ALL, name)
    row = []
    for w in HARD[name]:
        hp = [d for d in dd if d[1] and w in d[0]]
        hn = [d for d in dd if not d[1] and w in d[0]]
        row.append("%s %d/%d/%d" % (w, len(hp), len(hn), len({d[2] for d in hp})))
    print(" %s: %s" % (name, ", ".join(row)))
# tu viet tay o cac truong bat ky (khong loc boolean) cho A-admin
print(" A-admin tren moi truong (khong loc kieu):",
      {w: sum(1 for f in ALL if w in f["leaf"]) for w in HARD["A-admin"]})

print("\n# 4. Khoi 028, 031 vong 1 (doc qua grep): truong co ten giong truong quyen nhung nhan am")
ff = [f for f in F if f["round"] == 1 and f["chunk"] in ("028", "031")]
pat = ("role", "permission", "admin", "privilege", "scope", "access", "user", "member", "account")
sus = [f for f in ff if any(p in f["leaf"] for p in pat) and not f["A"] and not f["C"]]
print(" %d truong am co tu khoa %s; theo spec: %s" % (len(sus), pat, Counter(f["spec"] for f in sus)))
print(" vi du:", sorted({(f["spec"], f["method"] + " " + f["path"][:60], f["name"]) for f in sus
                        if any(p in f["leaf"] for p in ("role", "permission", "admin", "privilege"))})[:25])

print("\n# 5. Gia tri enum B tren test: liet ke")
te = [f for f in F if f["split"] == "test" and f["A"] in ("role", "perms") and f["enum"]]
for f in te:
    print(" ", f["provider"], f["name"], f["A"], "|".join(f["enum"]), "->", f["B_low"], "/", f["B_high"])
