import csv, io, sys

OUT = 'lexicon-20260920/stateful-authz-lexicon.csv'
SRC = [('path', 'lexicon-20260920/candidates-1.csv'),
       ('param', 'lexicon-20260920/candidates-2.csv')]


def score(r):
    a, b, p = int(r['df_r']), int(r['df_n']), int(r['nha_cung_cap'])
    return (a + 1) / float(a + b + 2) * p / float(p + 1)


rows = []
for kind, path in SRC:
    for r in csv.DictReader(io.open(path, encoding='utf-8')):
        rows.append((kind, r['tu'], score(r)))
rows.sort(key=lambda r: (r[0], -r[2], r[1]))

with io.open(OUT, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f)
    w.writerow(['kind', 'word', 'score'])
    for kind, word, s in rows:
        w.writerow([kind, word, '%.4f' % s])
print('%s: %d dong (%d path, %d param)' % (OUT, len(rows),
      sum(1 for r in rows if r[0] == 'path'), sum(1 for r in rows if r[0] == 'param')))
