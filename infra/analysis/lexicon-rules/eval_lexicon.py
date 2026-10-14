import csv, io, os, re, sys

D = 'labelling-r2/'
PLAN = '../corpus/sampling-plan.md'
OUT = 'lexicon-20260920/'
VERBS = {'PUT', 'PATCH', 'POST', 'DELETE'}
OLD = ['role', 'permission', 'member', 'subscription', 'plan', 'owner', 'grant', 'access']


def split_map():
    out = {}
    for l in io.open(PLAN, encoding='utf-8'):
        m = re.match(r'\|\s*(S\d+)\s*\|\s*([^|]+?)\s*\|[^|]*\|[^|]*\|\s*(train|test)\s*\|', l)
        if m:
            out[m.group(1)] = (m.group(2).strip(), m.group(3))
    return out


def corpus():
    out = {}
    for f in sorted(os.listdir(D)):
        if re.match(r'^S\d+\.csv$', f):
            for r in csv.DictReader(io.open(D + f, encoding='utf-8')):
                out[r['row_id']] = r
    return out


def hay(row):
    p = row['path']
    return (p + ' ' + row['method'] + ':' + p).lower()


def fires(row, words):
    return row['method'].upper() in VERBS and any(w in hay(row) for w in words)


def score(rows, words):
    tp = [r for r in rows if r['final_label'] == 'R' and fires(r, words)]
    fn = [r for r in rows if r['final_label'] == 'R' and not fires(r, words)]
    fp = [r for r in rows if r['final_label'] == 'N' and fires(r, words)]
    tn = [r for r in rows if r['final_label'] == 'N' and not fires(r, words)]
    p = len(tp) / float(len(tp) + len(fp)) if tp or fp else 0.0
    rc = len(tp) / float(len(tp) + len(fn)) if tp or fn else 0.0
    return tp, fn, fp, tn, p, rc


def main():
    sp, src = split_map(), corpus()
    fin = list(csv.DictReader(io.open(D + 'final.csv', encoding='utf-8')))
    new = [l.strip() for l in io.open(OUT + 'list-1.txt', encoding='utf-8') if l.strip()]
    half = sys.argv[1] if len(sys.argv) > 1 else 'test'
    rows = [dict(src[r['row_id']], final_label=r['final_label'])
            for r in fin if sp[r['spec_id']][1] == half and r['final_label'] in ('R', 'N')]
    print('%s: %d dong R, %d dong N' % (half,
          sum(1 for r in rows if r['final_label'] == 'R'),
          sum(1 for r in rows if r['final_label'] == 'N')))
    for name, words in (('bo rut ra (%d tu)' % len(new), new), ('bo 56 tu, phan path (%d tu)' % len(OLD), OLD)):
        tp, fn, fp, tn, p, rc = score(rows, words)
        print('')
        print('%s: %s' % (name, ' '.join(words)))
        print('  TP %d  FN %d  FP %d  TN %d | precision %.3f | recall %.3f'
              % (len(tp), len(fn), len(fp), len(tn), p, rc))
        if half == 'test':
            with io.open(OUT + 'miss-%s.csv' % ('moi' if words is new else 'cu'), 'w',
                         encoding='utf-8', newline='') as f:
                w = csv.DictWriter(f, ['row_id', 'method', 'path'], quoting=csv.QUOTE_ALL)
                w.writeheader()
                for r in fn:
                    w.writerow({'row_id': r['row_id'], 'method': r['method'], 'path': r['path']})
            for r in fn:
                print('  bo sot %s %s %s' % (r['row_id'], r['method'], r['path']))


main()
