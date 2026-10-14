import csv, io, os, re, sys
from collections import Counter

D = 'labelling-r2/'
PLAN = '../corpus/sampling-plan.md'
OUT = 'lexicon-20260920/'
VERBS = {'PUT', 'PATCH', 'POST', 'DELETE'}
MIN_LEN = 4

LISTS = [('1', 'transitionPathSignals', 'path'),
         ('2', 'transitionUserParamSignals', 'param_names'),
         ('3', 'roleFieldSignals', 'body_field_names')]


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


def hay(row, field):
    if field == 'path':
        p = row['path']
        return (p + ' ' + row['method'] + ':' + p).lower()
    return (row[field] or '').lower()


def raw(row, field):
    return (row[field] or '').lower()


def tokens(text):
    out = set()
    for piece in re.split(r'[^A-Za-z0-9]+', text):
        if not piece:
            continue
        for t in re.findall(r'[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+', piece):
            t = t.lower()
            if len(t) >= MIN_LEN and not t.isdigit():
                out.add(t)
    return out


def derive(rows, provider, field):
    pos = [r for r in rows if r['final_label'] == 'R']
    neg = [r for r in rows if r['final_label'] == 'N']
    base = len(pos) / float(len(pos) + len(neg))
    thr = 2 * base
    cand = set()
    for r in pos:
        cand |= tokens(raw(r, field))
    stats = []
    for w in sorted(cand):
        hp = [r for r in pos if w in hay(r, field)]
        hn = [r for r in neg if w in hay(r, field)]
        prov = {provider[r['spec_id']] for r in hp}
        prec = len(hp) / float(len(hp) + len(hn)) if hp or hn else 0.0
        stats.append({'tu': w, 'df_r': len(hp), 'df_n': len(hn), 'nha_cung_cap': len(prov),
                      'precision': '%.4f' % prec,
                      'p1': int(len(prov) >= 2), 'p2': int(prec >= thr)})
    kept = sorted(s['tu'] for s in stats if s['p1'] and s['p2'])
    dropped = {b for a in kept for b in kept if a != b and a in b}
    final = [w for w in kept if w not in dropped]
    for s in stats:
        s['p3'] = int(s['tu'] in kept and s['tu'] not in dropped)
    return base, thr, stats, sorted(dropped), final


def main():
    sp = split_map()
    src = corpus()
    final = list(csv.DictReader(io.open(D + 'final.csv', encoding='utf-8')))
    provider = {s: sp[s][0] for s in sp}
    train = [dict(src[r['row_id']], final_label=r['final_label'])
             for r in final if sp[r['spec_id']][1] == 'train' and r['final_label'] in ('R', 'N')]
    if not os.path.isdir(OUT):
        os.mkdir(OUT)
    print('train: %d dong R, %d dong N, %d nha cung cap'
          % (sum(1 for r in train if r['final_label'] == 'R'),
             sum(1 for r in train if r['final_label'] == 'N'),
             len({provider[r['spec_id']] for r in train})))
    for num, name, field in LISTS:
        base, thr, stats, dropped, kept = derive(train, provider, field)
        with io.open(OUT + 'candidates-%s.csv' % num, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, ['tu', 'df_r', 'df_n', 'nha_cung_cap', 'precision', 'p1', 'p2', 'p3'],
                               quoting=csv.QUOTE_ALL)
            w.writeheader()
            w.writerows(sorted(stats, key=lambda s: (-s['p3'], -s['df_r'], s['tu'])))
        io.open(OUT + 'list-%s.txt' % num, 'w', encoding='utf-8').write('\n'.join(kept) + '\n')
        print('')
        print('--- danh sach %s  %s  (truong %s) ---' % (num, name, field))
        print('ung vien %d | qua P1 va P2 %d | P3 bo %d | con %d'
              % (len(stats), sum(1 for s in stats if s['p1'] and s['p2']), len(dropped), len(kept)))
        print('nguong P2 = 2 * %.4f = %.4f' % (base, thr))
        if dropped:
            print('P3 bo: %s' % ' '.join(dropped))
        print('giu: %s' % (' '.join(kept) if kept else '(rong)'))


main()
