"""Danh sach R4 rut tu train+dev khi dung nhan cuoi / chi L1 / chi L2: nhieu nhan lan vao bo tu den dau."""
from load import *

F = load_all()
TD = [f for f in F if f["split"] in ("train", "dev")]
for src in ("final", "L1", "L2"):
    ff = []
    for f in TD:
        g = dict(f)
        if src != "final":
            g["A"], g["B_low"], g["B_high"], g["C"] = f[src]
        ff.append(g)
    print(src, {n: derive(docs(ff, n), "R4")[0] for n in ("A-role", "A-admin", "C", "B-low", "B-high")})
