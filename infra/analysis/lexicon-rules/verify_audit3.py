import csv, io, sys
from collections import Counter

D = 'labelling-r34-audit/'
SRC = ['row_id', 'spec_id', 'method', 'path', 'summary', 'description',
       'param_names', 'body_field_names', 'enum_values']
CODES = {'R1', 'R2', 'R3', 'R4', 'R5', 'R6',
         'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7', 'N8', 'N9'}

a = list(csv.DictReader(io.open(D + 'audit-in.csv', encoding='utf-8')))
b = list(csv.DictReader(io.open(D + 'audit.l3.csv', encoding='utf-8')))
err = []

if len(a) != len(b):
    err.append('so dong lech: %d vs %d' % (len(a), len(b)))
for i, (x, y) in enumerate(zip(a, b)):
    for c in SRC:
        if x[c] != y[c]:
            err.append('dong %d cot %s bi sua' % (i + 1, c))
    if y['annotator'] != 'llm':
        err.append('%s annotator=%r' % (y['row_id'], y['annotator']))
    if y['label'] not in ('R', 'N', 'U'):
        err.append('%s nhan=%r' % (y['row_id'], y['label']))
    if y['label'] == 'U':
        if y['rule_id']:
            err.append('%s U nhung co rule_id' % y['row_id'])
        if not y['doubt_token']:
            err.append('%s U nhung khong co doubt_token' % y['row_id'])
    else:
        if y['rule_id'] not in CODES:
            err.append('%s rule_id=%r ngoai bo ma' % (y['row_id'], y['rule_id']))
        elif y['rule_id'][0] != y['label']:
            err.append('%s nhan %s nhung ma %s' % (y['row_id'], y['label'], y['rule_id']))
        if y['doubt_token']:
            err.append('%s khong phai U nhung co doubt_token' % y['row_id'])

print('%d dong, phan bo %s' % (len(b), dict(Counter(r['label'] for r in b))))
print('ma: %s' % dict(Counter(r['rule_id'] for r in b if r['rule_id'])))
for e in err[:20]:
    print('LOI ' + e)
print('%d loi' % len(err))
sys.exit(1 if err else 0)
