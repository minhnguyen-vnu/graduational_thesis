import csv, glob, io, sys
from collections import Counter

D = 'labelling-r2/'

strata = {r['row_id']: r for r in csv.DictReader(io.open(D + 'strata.csv', encoding='utf-8'))}
adj = {r['row_id']: r for r in csv.DictReader(io.open(D + 'adjudication.csv', encoding='utf-8'))}
human = {}
for p in sorted(glob.glob(D + 'S*.human.csv')):
    for r in csv.DictReader(io.open(p, encoding='utf-8')):
        human[r['row_id']] = r

out, why = [], Counter()
for rid in sorted(strata):
    s = strata[rid]
    h = human.get(rid)
    machine = s['l1'] if s['stratum'].startswith('agree') else ''
    if rid in adj:
        fl, src = adj[rid]['final_label'], 'phan xu'
    elif h is None:
        fl, src = machine, 'may trung nhau, khong soat'
    elif h['label'] == machine:
        fl, src = machine, 'ba ben trung'
    elif s['stratum'] == 'disagree' and h['label'] in (s['l1'], s['l2']):
        fl, src = h['label'], 'nguoi co mot may dong tinh'
    else:
        print('CHUA CHOT: %s' % rid)
        sys.exit(1)
    why[src] += 1
    out.append({'row_id': rid, 'spec_id': rid.split('-')[0], 'stratum': s['stratum'],
                'l1': s['l1'], 'l2': s['l2'], 'human': h['label'] if h else '',
                'final_label': fl, 'audited': '1' if h else '0', 'nguon': src})

with io.open(D + 'final.csv', 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, ['row_id', 'spec_id', 'stratum', 'l1', 'l2', 'human', 'final_label', 'audited', 'nguon'],
                       quoting=csv.QUOTE_ALL)
    w.writeheader()
    w.writerows(out)

print('%d dong -> labelling-r2/final.csv' % len(out))
print('nhan chot %s' % dict(Counter(r['final_label'] for r in out)))
print('audited=1 %d | audited=0 %d' % (sum(1 for r in out if r['audited'] == '1'),
                                       sum(1 for r in out if r['audited'] == '0')))
for k, v in why.most_common():
    print('  %-28s %d' % (k, v))
