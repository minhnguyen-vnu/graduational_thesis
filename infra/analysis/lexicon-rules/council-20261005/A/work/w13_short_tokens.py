"""Truong/gia tri duong ma luat rut tu (token >= 4 ky tu) khong the tao ra tu khoa khop duoc."""
from collections import Counter
from load import *

F = load_all()
for sp in ("train", "dev", "test"):
    ff = [f for f in F if f["split"] == sp]
    c = [f for f in ff if f["C"]]
    no_tok = [f for f in c if not tokens(f["leaf"])]
    print("%s: C duong=%d, leaf khong co token >=4 ky tu=%d %s" % (sp, len(c), len(no_tok), Counter(f["leaf"] for f in no_tok).most_common(5)))
    b = docs(ff, "B-low") + docs(ff, "B-high")
    short = sorted({d[0] for d in b if d[1] and not tokens(d[0])})
    print("    gia tri B duong khong co token >=4 ky tu:", short)
