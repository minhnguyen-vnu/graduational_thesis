"""KTC 95% bootstrap theo nha cung cap (cum) cho F1 va chenh F1 (R4 - viet tay) tren test vong 2.
McNemar cua tac gia coi moi truong la doc lap; o day lay mau lai theo nha cung cap."""
import random
from collections import defaultdict
from lib import *

f1, f2 = all_fields()
LISTS = ("A-role", "A-admin", "C", "B-low", "B-high")
final = {n: derive(docs(f1, n), "R4")[0] for n in LISTS}
byp = defaultdict(list)
for f in f2:
    byp[f["provider"]].append(f)
provs = sorted(byp)
rng = random.Random(7)
B = 2000
res = {n: [] for n in LISTS}
for _ in range(B):
    samp = [f for p in (rng.choice(provs) for _ in provs) for f in byp[p]]
    for n in LISTS:
        dd = docs(samp, n)
        a = prf(n, final[n], dd)["f1"]
        h = prf(n, HARD[n], dd)["f1"]
        res[n].append((a, h, a - h))
for n in LISTS:
    dd = docs(f2, n)
    a, h = prf(n, final[n], dd)["f1"], prf(n, HARD[n], dd)["f1"]
    d = sorted(x[2] for x in res[n])
    fa = sorted(x[0] for x in res[n])
    fh = sorted(x[1] for x in res[n])
    q = lambda v: (round(v[int(0.025 * B)], 3), round(v[int(0.975 * B)], 3))
    print("%-7s F1 R4=%.3f KTC%s | viet tay=%.3f KTC%s | chenh=%.3f KTC%s P(chenh<=0)=%.2f"
          % (n, a, q(fa), h, q(fh), a - h, q(d), sum(1 for x in d if x <= 0) / B))
