"""Do nhay cua ket qua test theo nguon nhan (cuoi / chi L1 / chi L2), theo viec bo khoi da lo (020-022),
va theo cach phan loai B-low (co / khong loai tru tu cao)."""
from load import *

F = load_all()
TD = [f for f in F if f["split"] in ("train", "dev")]
LISTS = ("A-role", "A-admin", "C", "B-low", "B-high")
W = {n: derive(docs(TD, n), "R4")[0] for n in LISTS}


def relabel(ff, src):
    out = []
    for f in ff:
        g = dict(f)
        if src in ("L1", "L2"):
            g["A"], g["B_low"], g["B_high"], g["C"] = f[src]
        out.append(g)
    return out


te = [f for f in F if f["split"] == "test"]
print("# 1. F1 test theo nguon nhan (hard | R4)")
for src in ("final", "L1", "L2"):
    ff = relabel(te, src)
    print(" %-5s " % src + "  ".join("%s %.3f|%.3f" % (n, prf(n, HARD[n], docs(ff, n))["f1"], prf(n, W[n], docs(ff, n))["f1"])
                                      for n in LISTS))
print("\n# 2. Bo khoi 020-022 (L1 da doc bao cao cua L2)")
ff = [f for f in te if f["chunk"] not in ("020", "021", "022")]
print("  " + "  ".join("%s %.3f|%.3f" % (n, prf(n, HARD[n], docs(ff, n))["f1"], prf(n, W[n], docs(ff, n))["f1"]) for n in LISTS))
print("\n# 3. B-low: anh huong cua viec loai tru tu cao (runtime :711 luon loai tru)")
dd = docs(te, "B-low")
print("  hard co loai tru (nhu bao cao):", prf("B-low", HARD["B-low"], dd))
print("  hard khong loai tru          :", prf("B-low", list(HARD["B-low"]), dd))
print("  R4 khong loai tru (nhu bao cao):", prf("B-low", W["B-low"], dd))
print("  R4 loai tru bang R4 B-high     :", prf("B-low", W["B-low"], dd, hard_high=W["B-high"]))
