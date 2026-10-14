import csv, io, random, sys
from collections import Counter

D = 'labelling/'
SPECS = ['S034', 'S008']
SEED = 20260918
AUDIT_FRACTION = 0.20
PRE_LABELLED = {'S034-0001', 'S034-0002', 'S034-0003'}


def read(f):
    return {r['row_id']: r for r in csv.DictReader(io.open(D + f, encoding='utf-8'))}


def kappa(a, b):
    classes = sorted(set(a) | set(b))
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in classes)
    return po, pe, (po - pe) / (1 - pe) if pe != 1 else float('nan')


rows, l1s, l2s = [], [], []
for spec in SPECS:
    base, one, two = read(spec + '.csv'), read(spec + '.l1.csv'), read(spec + '.l2.csv')
    assert list(base) == list(one) == list(two), spec + ': row_id order differs'
    for rid in base:
        a, b = one[rid]['label'], two[rid]['label']
        stratum = 'agree' if (a == b and a != 'U' and b != 'U') else 'disagree'
        rows.append((rid, spec, a, b, stratum))
        l1s.append(a)
        l2s.append(b)

po, pe, k = kappa(l1s, l2s)
print('TONG %d dong' % len(rows))
print('L1 phan bo: %s' % dict(Counter(l1s)))
print('L2 phan bo: %s' % dict(Counter(l2s)))
print('Dong thuan tho L1-L2: %.3f (%d/%d)' % (po, round(po * len(rows)), len(rows)))
print('Ky vong ngau nhien pe = %.3f ; kappa = %.3f' % (pe, k))

agree = [r for r in rows if r[4] == 'agree']
disagree = [r for r in rows if r[4] == 'disagree']
print('Tang agree %d dong, tang disagree %d dong' % (len(agree), len(disagree)))

pool = sorted(r[0] for r in agree if r[0] not in PRE_LABELLED)
n_audit = max(1, round(len(pool) * AUDIT_FRACTION))
rng = random.Random(SEED)
audit = sorted(rng.sample(pool, n_audit))
print('Mau soat: %d/%d dong tang agree (da tru %d dong nguoi gan truoc)'
      % (n_audit, len(pool), len(agree) - len(pool)))

worklist = sorted([r[0] for r in disagree] + audit)
worklist = [r for r in worklist if r not in PRE_LABELLED]
print('NGUOI PHAI GAN %d dong:' % len(worklist))
for rid in worklist:
    st = next(r[4] for r in rows if r[0] == rid)
    print('  %s  %s%s' % (rid, st, '  [mau soat]' if rid in audit else ''))
