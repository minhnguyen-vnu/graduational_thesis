import csv, io, os, re
from collections import Counter

import sys
D = (sys.argv[1] if len(sys.argv) > 1 else 'labelling-r3') + '/'


def read(f):
    return {r['row_id']: r for r in csv.DictReader(io.open(D + f, encoding='utf-8'))}


def kappa(a, b):
    cl = sorted(set(a) | set(b))
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / float(n)
    pe = sum((a.count(c) / float(n)) * (b.count(c) / float(n)) for c in cl)
    return po, pe, (po - pe) / (1 - pe) if pe != 1 else float('nan')


srcs = sorted(f for f in os.listdir(D) if re.match('^S\\d+(\\.v2)?\\.csv$', f))
rows, l1s, l2s = [], [], []
for f in srcs:
    base, one, two = read(f), read(f[:-4] + '.l1.csv'), read(f[:-4] + '.l2.csv')
    assert list(base) == list(one) == list(two), f + ': row_id lech'
    for rid in base:
        a, b = one[rid]['label'], two[rid]['label']
        settled = a if (a == b and a in ('R', 'N')) else ''
        rows.append({'row_id': rid, 'spec_id': base[rid]['spec_id'], 'l1': a, 'l2': b,
                     'l1_rule': one[rid]['rule_id'], 'l2_rule': two[rid]['rule_id'],
                     'final_label': settled, 'audited': '0',
                     'nguon': 'may trung nhau, khong soat' if settled else 'loai: hai may lech hoac co U'})
        l1s.append(a)
        l2s.append(b)

po, pe, k = kappa(l1s, l2s)
keep = [r for r in rows if r['final_label']]
drop = [r for r in rows if not r['final_label']]

with io.open(D + 'final.csv', 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, ['row_id', 'spec_id', 'l1', 'l2', 'l1_rule', 'l2_rule',
                           'final_label', 'audited', 'nguon'], quoting=csv.QUOTE_ALL)
    w.writeheader()
    w.writerows(rows)

print('%d spec, %d dong' % (len(srcs), len(rows)))
print('L1 %s | L2 %s' % (dict(Counter(l1s)), dict(Counter(l2s))))
print('L1 vs L2: dong thuan tho %.3f | pe %.3f | kappa %.3f' % (po, pe, k))
print('giu %d (%s) | loai %d' % (len(keep), dict(Counter(r['final_label'] for r in keep)), len(drop)))
print('ly do loai: %s' % dict(Counter('%s/%s' % (r['l1'], r['l2']) for r in drop)))
