"""Do on dinh cua buoc chon luat (R0-R4) va cua danh sach R4.
(1) Bootstrap theo nha cung cap tren dev: R4 hon R1/R0 bao nhieu lan.
(2) Bootstrap theo nha cung cap tren train+dev: tan suat moi tu vao danh sach R4.
(3) Do nhay theo k cua top-k (R4 = top-5)."""
import random
from collections import Counter, defaultdict
from lib import *

f1, f2 = all_fields()
train = [f for f in f1 if f["split"] == "train"]
dev = [f for f in f1 if f["split"] == "test"]
LISTS = ("A-role", "A-admin", "C", "B-low", "B-high")
RULES = ("R0", "R1", "R2", "R3", "R4")

words = {(r, n): derive(docs(train, n), r)[0] for r in RULES for n in LISTS}


def by_provider(ff):
    d = defaultdict(list)
    for f in ff:
        d[f["provider"]].append(f)
    return d


def mean_f1(ff, rule):
    return sum(prf(n, words[(rule, n)], docs(ff, n))["f1"] for n in LISTS) / len(LISTS)


print("== (1) dev goc:", {r: round(mean_f1(dev, r), 4) for r in RULES})
bp = by_provider(dev)
provs = sorted(bp)
rng = random.Random(1)
B = 1000
wins = Counter()
diffs = defaultdict(list)
for _ in range(B):
    samp = [f for p in (rng.choice(provs) for _ in provs) for f in bp[p]]
    m = {r: mean_f1(samp, r) for r in RULES}
    best = max(m.values())
    for r in RULES:
        if m[r] == best:
            wins[r] += 1
    for r in ("R0", "R1", "R3"):
        diffs[r].append(m["R4"] - m[r])
print("  so lan moi luat dat F1 TB cao nhat (/%d, hoa tinh cho ca hai):" % B, dict(wins))
for r, d in diffs.items():
    d.sort()
    print("  R4 - %s: trung vi %.3f, KTC95%% [%.3f, %.3f], P(R4<=%s)=%.2f"
          % (r, d[B // 2], d[int(0.025 * B)], d[int(0.975 * B)], r, sum(1 for x in d if x <= 0) / B))

print("\n== (2) bootstrap train+dev theo nha cung cap: tan suat tu trong R4 (200 lan)")
bp = by_provider(f1)
provs = sorted(bp)
rng = random.Random(2)
final = {n: derive(docs(f1, n), "R4")[0] for n in LISTS}
for n in LISTS:
    cnt = Counter()
    sizes = []
    for _ in range(200):
        samp = [f for p in (rng.choice(provs) for _ in provs) for f in bp[p]]
        w = derive(docs(samp, n), "R4")[0]
        cnt.update(w)
        sizes.append(len(w))
    same = 0
    print("  %-7s cuoi=%s" % (n, final[n]))
    print("          tan suat:", [(w, c / 200.0) for w, c in cnt.most_common(12)])

print("\n== (3) do nhay theo k (top-k, P1 >= 2 nha_cc, P3) - rut tren train+dev, do tren test r2")
for n in ("A-role", "C", "B-low", "B-high"):
    stats, base = candidates(docs(f1, n))
    ok = sorted([s for s in stats if s["providers"] >= 2], key=lambda s: (-s["score"], s["word"]))
    row = []
    for k in (3, 5, 8, 10, 15):
        kept = sorted(s["word"] for s in ok[:k])
        dropped = {b for a in kept for b in kept if a != b and a in b}
        w = [x for x in kept if x not in dropped]
        row.append((k, prf(n, w, docs(f2, n))["f1"], "role" in w if n == "A-role" else None))
    print("  %-7s (k, F1 test, co 'role'?):" % n, row)
    print("          thu hang 12 tu dau:", [(s["word"], s["score"]) for s in ok[:12]])
