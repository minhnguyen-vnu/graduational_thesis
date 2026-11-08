import csv, glob, io, math, sys
from collections import Counter, defaultdict

D = 'labelling-r2/'
N_POP = None


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
    if n == 0:
        return (0.0, 1.0)
    lo = 0.0 if k == 0 else bisect(lambda p: 1 - binom_cdf(k - 1, n, p) >= alpha / 2)
    hi = 1.0 if k == n else bisect(lambda p: binom_cdf(k, n, p) <= alpha / 2)
    return (lo, hi)


def kappa_weighted(pairs):
    W = sum(w for _, _, w in pairs)
    classes = sorted({a for a, _, _ in pairs} | {b for _, b, _ in pairs})
    po = sum(w for a, b, w in pairs if a == b) / W
    ra = defaultdict(float)
    rb = defaultdict(float)
    for a, b, w in pairs:
        ra[a] += w
        rb[b] += w
    pe = sum((ra[c] / W) * (rb[c] / W) for c in classes)
    k = (po - pe) / (1 - pe) if pe != 1 else float('nan')
    return po, pe, k, W


strata = {r['row_id']: r for r in csv.DictReader(io.open(D + 'strata.csv', encoding='utf-8'))}
human = {}
for p in sorted(glob.glob(D + 'S*.human.csv')):
    for r in csv.DictReader(io.open(p, encoding='utf-8')):
        human[r['row_id']] = r['label']
final = {}
for p in sorted(glob.glob(D + 'S*.human.csv')):
    for r in csv.DictReader(io.open(p, encoding='utf-8')):
        final[r['row_id']] = r['final_label'].strip() or r['label']
adj = {r['row_id']: r for r in csv.DictReader(io.open(D + 'adjudication.csv', encoding='utf-8'))}

n_R = sum(1 for r in strata.values() if r['stratum'] == 'agree-R')
n_N = sum(1 for r in strata.values() if r['stratum'] == 'agree-N')
audit_R = [r for r in strata.values() if r['stratum'] == 'agree-R']
audit_N = [r for r in strata.values() if r['stratum'] == 'agree-N' and r['audit'] == '1']
disag = [r for r in strata.values() if r['stratum'] == 'disagree']
wN = n_N / len(audit_N)

print('== 1. L1 voi L2, toan bo 519 dong ==')
l1 = [r['l1'] for r in strata.values()]
l2 = [r['l2'] for r in strata.values()]
po, pe, k, _ = kappa_weighted(list(zip(l1, l2, [1.0] * len(l1))))
print('   tho %.3f | pe %.3f | kappa %.3f' % (po, pe, k))

for tag, H in (('nhan doc lap cua nguoi', human), ('sau phan xu', final)):
    print('== 2. Nguoi voi LLM tren tang dong thuan, %s ==' % tag)
    pairs = [(H[r['row_id']], r['l1'], 1.0) for r in audit_R] + \
            [(H[r['row_id']], r['l1'], wN) for r in audit_N]
    po, pe, k, W = kappa_weighted(pairs)
    eR = sum(1 for r in audit_R if H[r['row_id']] != r['l1'])
    eN = sum(1 for r in audit_N if H[r['row_id']] != r['l1'])
    lo, hi = clopper_pearson(eN, len(audit_N))
    est = (eR + n_N * (eN / len(audit_N))) / (n_R + n_N)
    print('   kappa co trong so %.3f (tho %.3f, pe %.3f, trong so tong %.0f)' % (k, po, pe, W))
    print('   tang R: %d/%d lech | tang N: %d/%d lech' % (eR, len(audit_R), eN, len(audit_N)))
    print('   ti le sai ca tang dong thuan %.4f | ClopperPearson95 tang N [%.4f, %.4f] quy ve [%.4f, %.4f]'
          % (est, lo, hi, lo * n_N / (n_R + n_N), hi * n_N / (n_R + n_N)))

print('== 3. Tang lech nhau, %d dong ==' % len(disag))
for tag, H in (('nhan goc', human), ('sau phan xu', final)):
    a1 = sum(1 for r in disag if H[r['row_id']] == r['l1'])
    a2 = sum(1 for r in disag if H[r['row_id']] == r['l2'])
    ne = sum(1 for r in disag if H[r['row_id']] not in (r['l1'], r['l2']))
    print('   %s: theo L1 %d | theo L2 %d | khac ca hai %d' % (tag, a1, a2, ne))
print('   nguoi gan: %s' % dict(Counter(human[r['row_id']] for r in disag)))

print('== 4. Phan xu: %d dong ==' % len(adj))
print('   nhan sau phan xu %s' % dict(Counter(r['final_label'] for r in adj.values())))
print('   giu nguyen nhan cua nguoi: %d' % sum(1 for r in adj.values() if r['final_label'] == r['human_label']))
print('   theo L1: %d | theo L2: %d' % (sum(1 for r in adj.values() if r['final_label'] == r['l1']),
                                        sum(1 for r in adj.values() if r['final_label'] == r['l2'])))
