"""Dem op 'transition' (co A role/perms/admin va co C) theo tung phan, so voi tong so truong da gan."""
from collections import defaultdict
from lib import *

f1, f2 = all_fields()
tot_fields = tot_T = 0
for part in ("old", "new-train", "new-test", "r2"):
    ff = [f for f in f1 + f2 if f["part"] == part]
    ops = defaultdict(list)
    for f in ff:
        ops[f["row_id"]].append(f)
    T = [k for k, v in ops.items() if any(f["A"] in ("role", "perms", "admin") for f in v) and any(f["C"] for f in v)]
    anyA = [k for k, v in ops.items() if any(f["A"] in ("role", "perms", "admin") for f in v)]
    tot_fields += len(ff)
    tot_T += len(T)
    print("%-9s op=%4d truong=%5d | op co A=%3d | op transition (A va C)=%3d, nha_cc=%2d"
          % (part, len(ops), len(ff), len(anyA), len(T), len({ops[k][0]['provider'] for k in T})))
print("tong: %d truong x 2 luot = %d nhan truong; %d op transition" % (tot_fields, 2 * tot_fields, tot_T))
