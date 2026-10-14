"""Do ben thong ke:
1. CI bootstrap theo nha cung cap (cum) cho F1 test cua viet tay va R4, va hieu so.
2. Do on dinh cua tu R4: bootstrap nha cung cap tren train+dev, tan suat moi tu duoc chon.
3. Chon luat tren dev: bootstrap nha cung cap cua dev, ty le moi luat thang.
4. Tran cua bo phan loai chi dua vao ten la: oracle theo leaf tren test; ty le duong test co leaf chua thay o train+dev.
"""
import random
from collections import Counter, defaultdict
from load import *

B = 1000
rng = random.Random(7)
F = load_all()
tr = [f for f in F if f["split"] == "train"]
dv = [f for f in F if f["split"] == "dev"]
te = [f for f in F if f["split"] == "test"]
LISTS = ("A-role", "A-admin", "C", "B-low", "B-high")


def by_prov(dd):
    g = defaultdict(list)
    for d in dd:
        g[d[2]].append(d)
    return g


def f1_of(name, words, dd):
    return prf(name, words, dd)["f1"]


def boot_dd(groups, keys):
    out = []
    for k in keys:
        out += groups[k]
    return out


print("# 1. Test: F1 viet tay vs R4(train+dev), CI 95%% bootstrap theo nha cung cap (B=%d)" % B)
for name in LISTS:
    w = derive(docs(tr + dv, name), "R4")[0]
    dd = docs(te, name)
    g = by_prov(dd)
    # gom ca nha cung cap khong co tai lieu duong (van co am)
    provs = sorted(g)
    diffs, fh, fd = [], [], []
    for _ in range(B):
        ks = [rng.choice(provs) for _ in provs]
        x = boot_dd(g, ks)
        a, b = f1_of(name, HARD[name], x), f1_of(name, w, x)
        fh.append(a); fd.append(b); diffs.append(b - a)
    q = lambda v, p: sorted(v)[int(p * (len(v) - 1))]
    print(" %-7s hard F1=%.3f [%.3f,%.3f]  R4 F1=%.3f [%.3f,%.3f]  R4-hard=%.3f CI[%.3f,%.3f]  P(R4>hard)=%.2f  nha cung cap=%d" % (
        name, f1_of(name, HARD[name], dd), q(fh, .025), q(fh, .975), f1_of(name, w, dd), q(fd, .025), q(fd, .975),
        f1_of(name, w, dd) - f1_of(name, HARD[name], dd), q(diffs, .025), q(diffs, .975),
        sum(1 for d in diffs if d > 0) / float(B), len(provs)))

print("\n# 2. On dinh tu R4: bootstrap nha cung cap tren train+dev (B=%d)" % (B // 2))
for name in LISTS:
    dd = docs(tr + dv, name)
    g = by_prov(dd)
    provs = sorted(g)
    base = derive(dd, "R4")[0]
    print(" %-7s R4 goc=%s" % (name, base))
    for variant in ("ban sao = cum moi", "ban sao giu ten (P1 dem nha cung cap that)"):
        cnt = Counter()
        same = 0
        for _ in range(B // 2):
            ks = [rng.choice(provs) for _ in provs]
            x = []
            for i, k in enumerate(ks):
                tag = "%s#%d" % (k, i) if variant.startswith("ban sao = cum") else k
                x += [(d[0], d[1], tag) for d in g[k]]
            w = derive(x, "R4")[0]
            cnt.update(w)
            same += int(w == base)
        print("         [%s] trung danh sach goc=%.2f; tan suat: %s" % (
            variant, same / float(B // 2), ", ".join("%s %.2f" % (w, c / float(B // 2)) for w, c in cnt.most_common(12))))

print("\n# 3. Chon luat tren dev: bootstrap nha cung cap dev, ty le moi luat co mean F1 cao nhat (hoa theo thu tu protocol)")
words = {r: {n: derive(docs(tr, n), r)[0] for n in LISTS} for r in ("R0", "R1", "R2", "R3", "R4")}
devdocs = {n: docs(dv, n) for n in LISTS}
dprov = sorted({f["provider"] for f in dv})
TIE = ("R2", "R3", "R1", "R4", "R0")
wins = Counter()
for _ in range(B):
    ks = [rng.choice(dprov) for _ in dprov]
    kc = Counter(ks)
    means = {}
    for r in words:
        s = 0
        for n in LISTS:
            x = [d for d in devdocs[n] for _ in range(kc.get(d[2], 0))]
            s += f1_of(n, words[r][n], x)
        means[r] = s / len(LISTS)
    best = max(means.values())
    wins[next(r for r in TIE if means[r] == best)] += 1
print(" ", {r: round(wins[r] / float(B), 3) for r in TIE})
# bo mot nha cung cap
loo = Counter()
for p in dprov:
    means = {}
    for r in words:
        means[r] = sum(f1_of(n, words[r][n], [d for d in devdocs[n] if d[2] != p]) for n in LISTS) / len(LISTS)
    best = max(means.values())
    loo[next(r for r in TIE if means[r] == best)] += 1
print("  bo mot nha cung cap dev (46 lan):", dict(loo))
print("  dong gop F1 dev theo danh sach (R4 - R1):", {n: round(f1_of(n, words["R4"][n], devdocs[n]) - f1_of(n, words["R1"][n], devdocs[n]), 3) for n in LISTS})

print("\n# 4. Tran cua bo phan loai theo ten la tren test")
for name in ("A-role", "A-admin", "C"):
    dd = docs(te, name)
    st = defaultdict(lambda: [0, 0])
    for d in dd:
        st[d[0]][0 if d[1] else 1] += 1
    tp = sum(p for p, n in st.values() if p >= n and p > 0)
    fp = sum(n for p, n in st.values() if p >= n and p > 0)
    fn = sum(p for p, n in st.values() if not (p >= n and p > 0))
    P, R, F1 = prf_counts(tp, fp, fn)
    mixed = sum(1 for p, n in st.values() if p and n)
    seen = {d[0] for d in docs(tr + dv, name) if d[1]}
    pos = [d for d in dd if d[1]]
    print(" %-7s oracle-leaf F1=%.3f (P=%.2f R=%.2f); leaf vua duong vua am=%d/%d leaf duong;"
          " truong duong test co leaf da thay duong o train+dev=%d/%d" % (
              name, F1, P, R, mixed, sum(1 for p, n in st.values() if p), sum(1 for d in pos if d[0] in seen), len(pos)))
