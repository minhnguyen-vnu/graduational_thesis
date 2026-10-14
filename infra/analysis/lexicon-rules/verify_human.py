import csv, glob, io, os, sys
from collections import Counter

D = 'labelling-r2/'
RULES = {"R2","R3","R4","R5","R6","N1","N2","N3","N4","N5","N6","N7","N8","N9","U1","U2","U3"}
HEAD = ["row_id","spec_id","method","path","summary","description","param_names",
        "body_field_names","enum_values","annotator","label","rule_id","doubt_token",
        "note","final_label"]
KEY = HEAD[:9]

ADJ = {r['row_id'] for r in csv.DictReader(io.open(D + 'adjudication.csv', encoding='utf-8'))}

problems = []
wl = [l.split()[0] for l in io.open(D + 'worklist.txt', encoding='utf-8') if l.strip()]
seen = {}

for path in sorted(glob.glob(D + 'S*.human.csv')):
    spec = os.path.basename(path).split('.')[0]
    src = {r['row_id']: r for r in csv.DictReader(io.open(D + spec + '.csv', encoding='utf-8'))}
    rows = list(csv.DictReader(io.open(path, encoding='utf-8')))
    if list(rows[0]) != HEAD:
        problems.append('%s: header sai' % spec)
    for r in rows:
        rid = r['row_id']
        if rid in seen:
            problems.append('%s: %s ghi hai lan' % (spec, rid))
        seen[rid] = r
        if rid not in src:
            problems.append('%s: %s khong co trong ban goc' % (spec, rid))
            continue
        for c in KEY:
            if r[c] != src[rid][c]:
                problems.append('%s %s: cot %s lech ban goc' % (spec, rid, c))
        if r['annotator'] != 'human':
            problems.append('%s %s: annotator=%s' % (spec, rid, r['annotator']))
        if r['label'] not in ('R', 'N', 'U'):
            problems.append('%s %s: nhan %s' % (spec, rid, r['label']))
        if r['rule_id'] not in RULES or r['rule_id'][0] != r['label']:
            problems.append('%s %s: ma %s khong khop nhan %s' % (spec, rid, r['rule_id'], r['label']))
        if (r['label'] == 'U') != bool(r['doubt_token'].strip()):
            problems.append('%s %s: doubt_token khong dung voi nhan %s' % (spec, rid, r['label']))
        fl = r['final_label'].strip()
        if fl and (fl not in ('R', 'N', 'U') or rid not in ADJ):
            problems.append('%s %s: final_label %r khong co trong adjudication.csv' % (spec, rid, fl))

thieu = [r for r in wl if r not in seen]
thua = [r for r in seen if r not in wl]
if thieu:
    problems.append('thieu %d dong: %s' % (len(thieu), ' '.join(thieu)))
if thua:
    problems.append('thua %d dong: %s' % (len(thua), ' '.join(thua)))

print('worklist %d | da ghi %d' % (len(wl), len(seen)))
print('nhan %s' % dict(Counter(r['label'] for r in seen.values())))
print('ma   %s' % dict(sorted(Counter(r['rule_id'] for r in seen.values()).items())))
print('co note: %d' % sum(1 for r in seen.values() if r['note'].strip()))
print('da phan xu: %d' % sum(1 for r in seen.values() if r['final_label'].strip()))
print('%d loi' % len(problems))
for p in problems:
    print('  ' + p)
sys.exit(1 if problems else 0)
