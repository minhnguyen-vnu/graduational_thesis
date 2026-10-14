"""(1) Tokenizer co tach camelCase nhu PROTOCOL §5 noi khong; (2) do tap trung cua nhan duong
theo nha cung cap va theo ten la (bao nhieu ten khac nhau, bao nhieu lan lap)."""
import re
from collections import Counter, defaultdict
from lib import *

print("== (1) tokenizer")
for raw in ("accessType", "isAdmin", "userId", "permissionLevel", "is_admin", "user_name", "roleIds"):
    print("  %-16s leaf=%-16s tokens(leaf)=%-28s tokens(raw)=%s"
          % (raw, leaf(raw), sorted(tokens(leaf(raw))), sorted(tokens(raw))))

f1, f2 = all_fields()
allf = f1 + f2
for name in ("A-role", "A-admin", "C"):
    pos = [f for f in f1 if f["split"] == "train" or f["split"] == "test"]
    pos = [f for f in pos if (f["A"] in ("role", "perms") if name == "A-role" else f["A"] == "admin" if name == "A-admin" else bool(f["C"]))
           and f["leaf"] != "(body)"]
    raw_leaf = [f["name"].split(".")[-1].replace("[]", "") for f in pos]
    camel = [n for n in raw_leaf if re.search(r"[a-z][A-Z]", n)]
    print("  %s train+dev: %d truong duong, %d co ten camelCase (vd %s)" % (name, len(pos), len(camel), sorted(set(camel))[:8]))

print("\n== (2) tap trung nhan duong (train+dev r1 | test r2)")


def is_pos(f, name):
    if name == "A-role":
        return f["A"] in ("role", "perms")
    if name == "A-admin":
        return f["A"] == "admin"
    if name == "A-active":
        return f["A"] == "active"
    return bool(f["C"])


for label, ff in (("train+dev", f1), ("test", f2)):
    for name in ("A-role", "A-admin", "A-active", "C"):
        pos = [f for f in ff if is_pos(f, name) and f["leaf"] != "(body)"]
        byp = Counter(f["provider"] for f in pos)
        leaves = Counter(f["leaf"] for f in pos)
        top = byp.most_common(3)
        print("  %-9s %-8s duong=%3d nha_cc=%2d top3=%s (top1 chiem %.0f%%) | ten la khac nhau=%d, top ten=%s"
              % (label, name, len(pos), len(byp), top, 100.0 * top[0][1] / len(pos) if pos else 0,
                 len(leaves), leaves.most_common(6)))

print("\n== (3) B: so truong role co enum va B co thu tu, so enum khac nhau")
for label, ff in (("train", [f for f in f1 if f["split"] == "train"]), ("dev", [f for f in f1 if f["split"] == "test"]), ("test", f2)):
    b = [f for f in ff if f["A"] in ("role", "perms") and f["enum"] and f["B_low"] not in ("", "unordered")]
    distinct = Counter(tuple(f["enum"]) for f in b)
    print("  %-5s truong=%d, enum khac nhau=%d, nha_cc=%d" % (label, len(b), len(distinct), len({f['provider'] for f in b})))
    for e, n in distinct.most_common():
        ex = next(f for f in b if tuple(f["enum"]) == e)
        print("      x%d %s | %s -> low=%s high=%s" % (n, ex["provider"], "|".join(e)[:90], ex["B_low"], ex["B_high"]))
    un = [f for f in ff if f["A"] in ("role", "perms") and f["enum"] and f["B_low"] == "unordered"]
    print("      unordered: %d; role/perms khong enum: %d; role/perms tong: %d"
          % (len(un), sum(1 for f in ff if f["A"] in ("role", "perms") and not f["enum"]),
             sum(1 for f in ff if f["A"] in ("role", "perms"))))
