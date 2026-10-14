"""Kha thi cua de xuat D4: trong op transition cua train+dev (khong dung test), moi ung vien co bao nhieu
nha cung cap duong (dem moi nha cung cap mot lan), va bao nhieu nha cung cap co truong am trong op transition
cung chua tu do. Ung vien = token (tach camelCase tren ten goc) + tu viet tay."""
import re
from collections import defaultdict
from lib import *

f1, _ = all_fields()
ops = defaultdict(list)
for f in f1:
    ops[f["row_id"]].append(f)
T = {k: v for k, v in ops.items() if any(f["A"] in ("role", "perms", "admin") for f in v) and any(f["C"] for f in v)}
print("op transition train+dev: %d, nha_cc %d" % (len(T), len({v[0]['provider'] for v in T.values()})))


def raw(f):
    return f["name"].split(".")[-1].replace("[]", "")


for col, pred, hard in (("A(role/perms)", lambda f: f["A"] in ("role", "perms"), HARD["A-role"]),
                        ("C", lambda f: bool(f["C"]), HARD["C"])):
    pos = [f for v in T.values() for f in v if pred(f) and f["leaf"] != "(body)"]
    neg = [f for v in T.values() for f in v if not pred(f) and f["leaf"] != "(body)"]
    cand = set(hard)
    for f in pos:
        cand |= tokens(raw(f))
    rows = []
    for w in cand:
        pp = {f["provider"] for f in pos if w in f["leaf"]}
        pn = {f["provider"] for f in neg if w in f["leaf"]}
        rows.append((len(pp), -len(pn), w, len(pn)))
    rows.sort(reverse=True)
    print("\n== %s: duong %d truong / %d nha_cc. Tu co >=2 nha_cc duong (tu, nha_cc duong, nha_cc co am):" %
          (col, len(pos), len({f['provider'] for f in pos})))
    print("  ", [(w, a, n) for a, _, w, n in rows if a >= 2])
    print("   tu viet tay khong co ho tro (0 nha_cc duong):", [w for a, _, w, n in rows if a == 0 and w in hard])
