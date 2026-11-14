import csv
import glob
import math
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
WAVE2 = os.path.join(BASE, "..", "nd-wave2-20261113")


def binom_cdf(k, n, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))


def bisect(pred):
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if pred(mid):
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def clopper_pearson(k, n, alpha=0.05):
    lo = 0.0 if k == 0 else bisect(lambda p: 1 - binom_cdf(k - 1, n, p) >= alpha / 2)
    hi = 1.0 if k == n else bisect(lambda p: binom_cdf(k, n, p) <= alpha / 2)
    return lo, hi


def fisher_one_sided(a, n1, b, n2):
    total = n1 + n2
    hits = a + b
    def pmf(x):
        return math.comb(n1, x) * math.comb(n2, hits - x) / math.comb(total, hits)
    return sum(pmf(x) for x in range(a, min(n1, hits) + 1))


def assembled(log):
    with open(log, errors="replace") as f:
        return sum(1 for line in f if line.startswith("* Assembled a stateful"))


def statuses(log):
    with open(log, errors="replace") as f:
        return [m.group(1) for line in f if line.startswith("* Assembled a stateful")
                for m in [re.search(r"statuses ([0-9/]+)\)", line)] if m]


def wave1(tier, arm, tag):
    rows = [r for r in csv.DictReader(open(os.path.join(BASE, "runs.csv"))) if r["tier"] == tier and r["arm"] == arm]
    out = []
    for r in rows:
        log = os.path.join(BASE, "logs", f"{tag}-seed{r['seed']}.log")
        out.append(dict(seed=int(r["seed"]), det=r["det970"], triples=assembled(log), st=statuses(log)))
    return out


def ak(arm):
    rows = list(csv.DictReader(open(os.path.join(WAVE2, f"runs-ak-{arm}.csv"))))
    out = []
    for r in rows:
        log = os.path.join(WAVE2, "logs", f"ak-{arm}-seed{r['seed']}.log")
        out.append(dict(seed=int(r["seed"]), det=r["det970"], triples=assembled(log), st=statuses(log)))
    return out


targets = [
    ("reports-api", wave1("tier1", "vuln", "t1-vuln"), wave1("tier1", "fixed", "t1-fixed")),
    ("vampi-seeded", wave1("tier2", "ours-vuln", "t2-ours-vuln"), wave1("tier2", "ours-fixed", "t2-ours-fixed")),
    ("pyLoad", wave1("tier2b", "vuln", "t2b-vuln"), wave1("tier2b", "fixed", "t2b-fixed")),
    ("artifact-keeper", ak("vuln"), ak("fixed")),
]

for name, v, f in targets:
    for side in (v, f):
        for r in side:
            if r["det"] not in ("0", "1"):
                raise SystemExit(f"{name} seed {r['seed']}: det970={r['det']}")

print("## Detection and false positives")
print("| Target | Arm | Runs | Runs with a performed triple | Triples | 970 raised | Clopper-Pearson 95% |")
print("|---|---|---|---|---|---|---|")
for name, v, f in targets:
    for arm, side in (("vuln", v), ("fixed", f)):
        n = len(side)
        withT = sum(1 for r in side if r["triples"] > 0)
        tri = sum(r["triples"] for r in side)
        det = sum(1 for r in side if r["det"] == "1")
        ci = ""
        if arm == "vuln":
            lo, hi = clopper_pearson(det, n)
            ci = f"[{lo * 100:.1f}, {hi * 100:.1f}]"
        print(f"| {name} | {arm} | {n} | {withT}/{n} | {tri} | {det}/{n} | {ci} |")

print()
print("## Four cells per run")
print("| Target | TP | FN, triple, no 970 | FN, no triple | FP | TN | Fixed, no triple | Runs vuln/fixed |")
print("|---|---|---|---|---|---|---|---|")
tot = [0] * 6
for name, v, f in targets:
    tp = sum(1 for r in v if r["det"] == "1")
    fn_t = sum(1 for r in v if r["det"] != "1" and r["triples"] > 0)
    fn_n = sum(1 for r in v if r["det"] != "1" and r["triples"] == 0)
    fp = sum(1 for r in f if r["det"] == "1")
    tn = sum(1 for r in f if r["det"] != "1" and r["triples"] > 0)
    fx = sum(1 for r in f if r["triples"] == 0)
    for i, x in enumerate((tp, fn_t, fn_n, fp, tn, fx)):
        tot[i] += x
    print(f"| {name} | {tp} | {fn_t} | {fn_n} | {fp} | {tn} | {fx} | {len(v)}/{len(f)} |")
nv = sum(len(v) for _, v, _ in targets)
nf = sum(len(f) for _, _, f in targets)
print(f"| Total | {' | '.join(str(x) for x in tot)} | {nv}/{nf} |")

print()
print("## Fisher exact, one-sided, 970 on vulnerable vs fixed")
for name, v, f in targets:
    a = sum(1 for r in v if r["det"] == "1")
    b = sum(1 for r in f if r["det"] == "1")
    print(f"{name}: {a}/{len(v)} vs {b}/{len(f)}, p = {fisher_one_sided(a, len(v), b, len(f)):.6f}")

print()
print("## Performed-triple statuses")
for name, v, f in targets:
    for arm, side in (("vuln", v), ("fixed", f)):
        seen = {}
        for r in side:
            for s in r["st"]:
                seen[s] = seen.get(s, 0) + 1
        print(f"{name} {arm}: {seen}")

fp_n = sum(len(f) for _, _, f in targets)
fp_k = sum(1 for _, _, f in targets for r in f if r["det"] == "1")
fixed_tri = sum(r["triples"] for _, _, f in targets for r in f)
fixed_with = sum(1 for _, _, f in targets for r in f if r["triples"] > 0)
fp_with = sum(1 for _, _, f in targets for r in f if r["triples"] > 0 and r["det"] == "1")
fp_lo, fp_hi = clopper_pearson(fp_with, fixed_with)
print()
print(f"False positives: {fp_k} in {fp_n} fixed-target runs, over {fixed_tri} triples performed on patched code")
print(f"False-positive rate over fixed runs with a triple: {fp_with}/{fixed_with}, "
      f"Clopper-Pearson 95% [{fp_lo * 100:.1f}, {fp_hi * 100:.1f}]")
