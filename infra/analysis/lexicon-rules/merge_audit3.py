import csv, io, os
from collections import Counter

D = 'labelling-r34-audit/'
key = {r['row_id']: r for r in csv.DictReader(io.open(D + 'key.csv', encoding='utf-8'))}
l3 = {r['row_id']: r for r in csv.DictReader(io.open(D + 'audit.l3.csv', encoding='utf-8'))}


def kappa(pairs):
    n = len(pairs)
    if n == 0:
        return 0.0, 0.0, float('nan')
    po = sum(1 for a, b in pairs if a == b) / n
    cls = sorted({x for p in pairs for x in p})
    pe = sum((sum(1 for a, _ in pairs if a == c) / n) * (sum(1 for _, b in pairs if b == c) / n)
             for c in cls)
    return po, pe, (po - pe) / (1 - pe) if pe != 1 else float('nan')


for grp in ('R', 'N'):
    ids = [k for k, v in key.items() if v['consensus'] == grp]
    u = [i for i in ids if l3[i]['label'] == 'U']
    pairs = [(key[i]['consensus'], l3[i]['label']) for i in ids if l3[i]['label'] != 'U']
    po, pe, k = kappa(pairs)
    flip = [i for i in ids if l3[i]['label'] not in ('U', grp)]
    print('nhom dong thuan %s: %d dong, %d U bo, dong thuan tho %.3f, pe %.3f, kappa %.3f'
          % (grp, len(ids), len(u), po, pe, k))
    print('   lat nhan: %d -> %s' % (len(flip), ' '.join(sorted(flip)) or '(khong)'))
    if u:
        print('   U: %s' % ' '.join(sorted(u)))

allids = sorted(key)
pairs = [(key[i]['consensus'], l3[i]['label']) for i in allids if l3[i]['label'] != 'U']
po, pe, k = kappa(pairs)
print('ca 56 dong: dong thuan tho %.3f, pe %.3f, kappa %.3f (bo %d dong U)'
      % (po, pe, k, 56 - len(pairs)))

changed = 0
for d in ('labelling-r3', 'labelling-r4'):
    rows = list(csv.DictReader(io.open(d + '/final.csv', encoding='utf-8')))
    head = list(rows[0].keys())
    for r in rows:
        rid = r['row_id']
        if rid in key and key[rid]['consensus'] == 'R':
            new = l3[rid]['label']
            if new != r['final_label']:
                changed += 1
            r['final_label'] = '' if new == 'U' else new
            r['audited'] = '1'
            r['nguon'] = 'audit-3'
    with io.open(d + '/final.v2.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, head, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)
    print('%s/final.v2.csv: %s' % (d, dict(Counter(r['final_label'] or 'bo' for r in rows))))

print('tong so dong doi nhan: %d' % changed)
