import csv, glob, io, json, os, random, sys
from collections import Counter

D = 'labelling/'
SEED = 20260918
AUDIT_FRACTION = 0.20
AUDIT_MIN = 30
PILOT = {'S034', 'S008'}


def read(f):
    return {r['row_id']: r for r in csv.DictReader(io.open(D + f, encoding='utf-8'))}


def kappa(a, b):
    classes = sorted(set(a) | set(b))
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in classes)
    return po, pe, (po - pe) / (1 - pe) if pe != 1 else float('nan')


specs = sorted({os.path.basename(p).split('.')[0] for p in glob.glob(D + 'S*.l1.csv')} -
               PILOT)
missing = [s for s in specs if not os.path.exists(D + s + '.l2.csv')]
if missing:
    print('CHUA CO L2: %s' % ' '.join(missing))
    sys.exit(1)

rows, l1s, l2s = [], [], []
for spec in specs:
    base, one, two = read(spec + '.csv'), read(spec + '.l1.csv'), read(spec + '.l2.csv')
    assert list(base) == list(one) == list(two), spec + ': row_id lech'
    for rid in base:
        a, b = one[rid]['label'], two[rid]['label']
        agree = a == b and a != 'U' and b != 'U'
        rows.append({'row_id': rid, 'spec': spec, 'l1': a, 'l1_rule': one[rid]['rule_id'],
                     'l2': b, 'l2_rule': two[rid]['rule_id'],
                     'stratum': 'agree' if agree else 'disagree'})
        l1s.append(a)
        l2s.append(b)

po, pe, k = kappa(l1s, l2s)
agree = [r for r in rows if r['stratum'] == 'agree']
disagree = [r for r in rows if r['stratum'] == 'disagree']

pool = sorted(r['row_id'] for r in agree)
n_audit = max(AUDIT_MIN, round(len(pool) * AUDIT_FRACTION))
n_audit = min(n_audit, len(pool))
audit = set(random.Random(SEED).sample(pool, n_audit))
for r in rows:
    r['audit'] = 1 if r['row_id'] in audit else 0

worklist = sorted([r for r in rows if r['stratum'] == 'disagree' or r['audit']],
                  key=lambda r: r['row_id'])

with io.open(D + 'strata.csv', 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, ['row_id', 'spec', 'l1', 'l1_rule', 'l2', 'l2_rule', 'stratum', 'audit'],
                       quoting=csv.QUOTE_ALL)
    w.writeheader()
    w.writerows(rows)

io.open(D + 'worklist.txt', 'w', encoding='utf-8').write(
    "\n".join('%s %s%s' % (r['row_id'], r['stratum'], ' mau-soat' if r['audit'] else '')
              for r in worklist) + "\n")

print('%d spec, %d dong' % (len(specs), len(rows)))
print('L1 %s | L2 %s' % (dict(Counter(l1s)), dict(Counter(l2s))))
print('dong thuan tho %.3f (%d/%d) | pe %.3f | kappa %.3f' % (po, round(po * len(rows)), len(rows), pe, k))
print('agree %d | disagree %d | mau soat %d' % (len(agree), len(disagree), n_audit))
print('NGUOI PHAI GAN: %d dong -> labelling/worklist.txt' % len(worklist))
