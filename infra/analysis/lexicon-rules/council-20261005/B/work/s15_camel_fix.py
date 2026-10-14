"""Do nhay: neu tach camelCase truoc khi ha chu thuong (dung nhu PROTOCOL vong 1 §5 mo ta),
tap ung vien va danh sach R0/R4 (train+dev) doi the nao. Khop van bang chuoi con tren ten la ha chu thuong."""
from lib import *

f1, f2 = all_fields()


def raw_leaf(f):
    return f["name"].split(".")[-1].replace("[]", "")


def docs_raw(ff, name):
    usable = [f for f in ff if f["leaf"] != "(body)"]
    if name == "A-role":
        return [(f["leaf"], f["A"] in ("role", "perms"), f["provider"], raw_leaf(f)) for f in usable]
    if name == "C":
        return [(f["leaf"], bool(f["C"]), f["provider"], raw_leaf(f)) for f in usable]
    if name == "A-admin":
        return [(f["leaf"], f["A"] == "admin", f["provider"], raw_leaf(f)) for f in usable if f["type"] == "boolean" or f["A"] == "admin"]


def cands(dd):
    pos = [d for d in dd if d[1]]
    neg = [d for d in dd if not d[1]]
    base = len(pos) / float(len(dd))
    c = set()
    for d in pos:
        c |= tokens(d[3])
    stats = []
    for w in sorted(c):
        hp = [d for d in pos if w in d[0]]
        hn = [d for d in neg if w in d[0]]
        ncc = len({d[2] for d in hp})
        prec = len(hp) / float(len(hp) + len(hn))
        stats.append({"word": w, "df_pos": len(hp), "df_neg": len(hn), "providers": ncc, "precision": round(prec, 4),
                      "score": round((len(hp) + 1) / float(len(hp) + len(hn) + 2) * ncc / float(ncc + 1), 4)})
    return stats, base


for n in ("A-role", "C", "A-admin"):
    old_stats, b = candidates(docs(f1, n))
    new_stats, b2 = cands(docs_raw(f1, n))
    o = {s["word"] for s in old_stats}
    nw = {s["word"] for s in new_stats}
    print("== %s: ung vien cu %d, moi %d; them %s" % (n, len(o), len(nw), sorted(nw - o)[:25]))
    for r in ("R0", "R4"):
        print("   %s cu=%s\n      moi=%s | F1 test cu=%.3f moi=%.3f" % (
            r, select(old_stats, b, r), select(new_stats, b2, r),
            prf(n, select(old_stats, b, r), docs(f2, n))["f1"], prf(n, select(new_stats, b2, r), docs(f2, n))["f1"]))
