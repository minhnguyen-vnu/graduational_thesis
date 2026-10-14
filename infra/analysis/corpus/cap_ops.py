import csv, io, json, os, random, sys

SEED = 20260918
CAP = 15
LAB = '../lexicon-rules/labelling/'
FULL = 'ops-full/'

os.makedirs(FULL, exist_ok=True)
picked = json.load(open('sample-picked.json')) + json.load(open('sample-replacements.json'))
empty = set(json.load(open('empty-specs.json')))

report = []
for a in picked:
    sid = a['spec_id']
    src = LAB + sid + '.csv'
    if not os.path.exists(src):
        continue
    rows = list(csv.reader(io.open(src, encoding='utf-8')))
    head, body = rows[0], rows[1:]
    if not body:
        os.rename(src, FULL + sid + '.csv')
        report.append((sid, a['provider'], 0, 0, 'bo: khong co operation ghi'))
        continue
    io.open(FULL + sid + '.csv', 'w', encoding='utf-8').write(io.open(src, encoding='utf-8').read())
    if len(body) > CAP:
        rng = random.Random(SEED + int(sid[1:]))
        keep = sorted(rng.sample(range(len(body)), CAP))
        body = [body[i] for i in keep]
    with io.open(src, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(head)
        w.writerows(body)
    n_full = sum(1 for _ in io.open(FULL + sid + '.csv', encoding='utf-8')) - 1
    report.append((sid, a['provider'], n_full, len(body), 'giu' if n_full <= CAP else 'boc %d/%d' % (CAP, n_full)))

json.dump(report, open('cap-report.json', 'w'))
print('%d spec | tong operation sau cap: %d' % (sum(1 for r in report if r[3] > 0), sum(r[3] for r in report)))
