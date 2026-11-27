from math import comb


def fisher_two_sided(a, b, c, d):
    r1, r2, c1, n = a + b, c + d, a + c, a + b + c + d

    def p(x):
        return comb(r1, x) * comb(r2, c1 - x) / comb(n, c1)

    obs = p(a)
    lo, hi = max(0, c1 - r2), min(r1, c1)
    return sum(p(x) for x in range(lo, hi + 1) if p(x) <= obs * (1 + 1e-9))


def mcnemar_exact(b, c):
    n = b + c
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


for name, hit in [("reports-api", 12), ("vampi-seeded", 6)]:
    print("%s TR2 %d/20 baseline 0/20 Fisher two-sided p = %.3g; McNemar exact by seed (b=%d, c=0) p = %.3g"
          % (name, hit, fisher_two_sided(hit, 20 - hit, 0, 20), hit, mcnemar_exact(hit, 0)))
