import csv, io, os, random

SEED = 20260921
HEAD = ['row_id', 'spec_id', 'method', 'path', 'summary', 'description',
        'param_names', 'body_field_names', 'enum_values',
        'annotator', 'label', 'rule_id', 'doubt_token', 'note']
OUT = 'labelling-r34-audit/audit-in.csv'


def src(d, spec, rid):
    p = '%s/%s.csv' % (d, spec)
    if not os.path.exists(p):
        p = '%s/%s.v2.csv' % (d, spec)
    for r in csv.DictReader(io.open(p, encoding='utf-8')):
        if r['row_id'] == rid:
            return r
    raise SystemExit('khong thay ' + rid)


pos, neg = [], []
for d in ('labelling-r4', 'labelling-r3'):
    for r in csv.DictReader(io.open(d + '/final.csv', encoding='utf-8')):
        if r['final_label'] == 'R':
            pos.append((d, r['spec_id'], r['row_id']))
        elif r['final_label'] == 'N':
            neg.append((d, r['spec_id'], r['row_id']))

rnd = random.Random(SEED)
drawn = rnd.sample(sorted(neg), len(pos))
rows = [src(*t) for t in pos] + [src(*t) for t in drawn]
rnd.shuffle(rows)

os.makedirs('labelling-r34-audit', exist_ok=True)
with io.open(OUT, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, HEAD, quoting=csv.QUOTE_ALL)
    w.writeheader()
    for r in rows:
        w.writerow({k: ('' if k in ('annotator', 'label', 'rule_id', 'doubt_token', 'note')
                        else r[k]) for k in HEAD})

with io.open('labelling-r34-audit/key.csv', 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, quoting=csv.QUOTE_ALL)
    w.writerow(['row_id', 'src', 'consensus'])
    for d, s, rid in pos:
        w.writerow([rid, d, 'R'])
    for d, s, rid in drawn:
        w.writerow([rid, d, 'N'])

print('%d dong R + %d dong nhieu = %d dong -> %s' % (len(pos), len(drawn), len(rows), OUT))
