import csv, io, os, re, sys
from collections import Counter

PASS = sys.argv[1] if len(sys.argv) > 1 else 'l2'
D = (sys.argv[2] if len(sys.argv) > 2 else 'labelling-r3') + '/'
HEAD9 = ['row_id', 'spec_id', 'method', 'path', 'summary', 'description',
         'param_names', 'body_field_names', 'enum_values']
CODES = set(['R%d' % i for i in range(2, 7)] + ['N%d' % i for i in range(1, 10)] +
            ['U%d' % i for i in range(1, 4)])

errs, n, lab = [], 0, Counter()
srcs = sorted(f for f in os.listdir(D) if f.endswith('.csv') and '.l1.' not in f and '.l2.' not in f)
for f in srcs:
    out = D + f[:-4] + '.' + PASS + '.csv'
    if not os.path.exists(out):
        errs.append('%s: thieu file %s' % (f, os.path.basename(out)))
        continue
    a = list(csv.DictReader(io.open(D + f, encoding='utf-8')))
    b = list(csv.DictReader(io.open(out, encoding='utf-8')))
    if len(a) != len(b):
        errs.append('%s: %d dong nguon, %d dong ra' % (f, len(a), len(b)))
        continue
    for x, y in zip(a, b):
        n += 1
        for c in HEAD9:
            if (x[c] or '') != (y[c] or ''):
                errs.append('%s: cot %s doi' % (y['row_id'], c))
                break
        if y['annotator'] != 'llm':
            errs.append('%s: annotator=%r' % (y['row_id'], y['annotator']))
        if y['label'] not in ('R', 'N', 'U'):
            errs.append('%s: label=%r' % (y['row_id'], y['label']))
            continue
        lab[y['label']] += 1
        if y['rule_id'] not in CODES:
            errs.append('%s: rule_id=%r' % (y['row_id'], y['rule_id']))
        elif y['rule_id'][0] != y['label']:
            errs.append('%s: label %s nhung rule %s' % (y['row_id'], y['label'], y['rule_id']))
        if (y['label'] == 'U') != bool((y['doubt_token'] or '').strip()):
            errs.append('%s: label %s nhung doubt_token=%r' % (y['row_id'], y['label'], y['doubt_token']))
        if (y['final_label'] or '').strip():
            errs.append('%s: final_label khong rong' % y['row_id'])

print('%s: %d dong, %s' % (PASS, n, dict(lab)))
print('%d loi' % len(errs))
for e in errs[:15]:
    print('  ' + e)
