"""Kiem cheo nhom theo nha cung cap tren ca 228 nha cung cap (5 phan, lap 4 lan): R0-R4, mot luat tham lam
toi da F1 (G), va danh sach viet tay. Muc dich: xem do dao dong giua cac phan, khong de chon danh sach."""
import random, statistics
from collections import defaultdict
from load import *

F = load_all()
LISTS = ("A-role", "A-admin", "C")
provs = sorted({f["provider"] for f in F})


def greedy(dd, max_words=8):
    stats, base = candidates(dd)
    ok = [s["word"] for s in stats if s["providers"] >= 2]
    chosen, best = [], 0.0
    while len(chosen) < max_words:
        cand = None
        for w in ok:
            if w in chosen or any(c in w for c in chosen):
                continue
            f1 = prf("x", chosen + [w], dd)["f1"]
            if f1 > best + 1e-9:
                best, cand = f1, w
        if cand is None:
            break
        chosen.append(cand)
    return chosen


res = defaultdict(list)
for rep in range(4):
    rng = random.Random(100 + rep)
    p = provs[:]
    rng.shuffle(p)
    folds = [set(p[i::5]) for i in range(5)]
    for k, fold in enumerate(folds):
        trn = [f for f in F if f["provider"] not in fold]
        tst = [f for f in F if f["provider"] in fold]
        for name in LISTS:
            dtr, dte = docs(trn, name), docs(tst, name)
            if not any(d[1] for d in dte):
                continue
            hard = prf(name, HARD[name], dte)["f1"]
            res[(name, "hard")].append(hard)
            for rule in ("R0", "R1", "R2", "R3", "R4"):
                res[(name, rule)].append(prf(name, derive(dtr, rule)[0], dte)["f1"])
            res[(name, "G")].append(prf(name, greedy(dtr), dte)["f1"])

for name in LISTS:
    h = res[(name, "hard")]
    print(name, "so phan co duong:", len(h))
    for r in ("hard", "R0", "R1", "R2", "R3", "R4", "G"):
        v = res[(name, r)]
        d = [a - b for a, b in zip(v, h)]
        print("   %-4s F1 tb=%.3f sd=%.3f min=%.3f max=%.3f | hieu so voi hard tb=%+.3f, so phan thang hard=%d/%d" % (
            r, statistics.mean(v), statistics.pstdev(v), min(v), max(v), statistics.mean(d), sum(1 for x in d if x > 0), len(d)))
