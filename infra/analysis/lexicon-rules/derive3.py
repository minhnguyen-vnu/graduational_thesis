import csv, io, json, os, re, sys

R2, R3 = 'labelling-r2/', 'labelling-r3/'
PLAN = '../corpus/sampling-plan.md'
OUT = 'lexicon-20260921-audited/'
MIN_LEN = 4
EXT = ['S%03d' % (200 + i) for i in range(15)]
LISTS = [('1', 'transitionPathSignals', 'path'),
         ('2', 'transitionUserParamSignals', 'param_names'),
         ('3', 'roleFieldSignals', 'body_field_names')]
FINAL3 = sys.argv[1] if len(sys.argv) > 1 else 'final.v2.csv'


def split_map():
    out = {}
    for l in io.open(PLAN, encoding='utf-8'):
        m = re.match(r'\|\s*(S\d+)\s*\|\s*([^|]+?)\s*\|[^|]*\|[^|]*\|\s*(train|test)\s*\|', l)
        if m:
            out[m.group(1)] = (m.group(2).strip(), m.group(3))
    for a in json.load(io.open('../corpus/sample-ext.json', encoding='utf-8')):
        out[a['spec_id']] = (a['provider'], a['split'])
    return out


def corpus():
    out = {}
    for d in (R2, R3):
        for f in sorted(os.listdir(d)):
            if re.match(r'^S\d+(\.v2)?\.csv$', f):
                for r in csv.DictReader(io.open(d + f, encoding='utf-8')):
                    out[r['row_id']] = r
    return out


def labels(sp):
    out = {}
    for r in csv.DictReader(io.open(R2 + 'final.csv', encoding='utf-8')):
        if r['final_label'] in ('R', 'N'):
            out[r['row_id']] = (r['final_label'], sp[r['spec_id']][1])
    for r in csv.DictReader(io.open(R3 + FINAL3, encoding='utf-8')):
        if not r['final_label']:
            out.pop(r['row_id'], None)
            continue
        half = 'train' if r['spec_id'] in EXT else sp[r['spec_id']][1]
        out[r['row_id']] = (r['final_label'], half)
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
        cand |= tokens(r[field] if field != 'path' else r['path'])
    stats = []
    for w in sorted(cand):
        hp = [r for r in pos if w in hay(r, field)]
        hn = [r for r in neg if w in hay(r, field)]
        prov = {provider[r['spec_id']] for r in hp}
        prec = len(hp) / float(len(hp) + len(hn)) if hp or hn else 0.0
        stats.append({'tu': w, 'df_r': len(hp), 'df_n': len(hn), 'nha_cung_cap': len(prov),
                      'precision': '%.4f' % prec,
                      'diem': '%.4f' % ((len(hp) + 1) / float(len(hp) + len(hn) + 2)
                                        * len(prov) / float(len(prov) + 1)),
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
    lab = labels(sp)
    provider = {s: sp[s][0] for s in sp}
    train = [dict(src[rid], final_label=lb) for rid, (lb, hf) in lab.items() if hf == 'train']
    if not os.path.isdir(OUT):
        os.mkdir(OUT)
    print('nhan r3 doc tu %s' % FINAL3)
    print('train: %d dong R, %d dong N, %d nha cung cap, %d nha cung cap co R'
          % (sum(1 for r in train if r['final_label'] == 'R'),
             sum(1 for r in train if r['final_label'] == 'N'),
             len({provider[r['spec_id']] for r in train}),
             len({provider[r['spec_id']] for r in train if r['final_label'] == 'R'})))
    lex = []
    for num, name, field in LISTS:
        base, thr, stats, dropped, kept = derive(train, provider, field)
        with io.open(OUT + 'candidates-%s.csv' % num, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, ['tu', 'df_r', 'df_n', 'nha_cung_cap', 'precision', 'diem',
                                   'p1', 'p2', 'p3'], quoting=csv.QUOTE_ALL)
            w.writeheader()
            w.writerows(sorted(stats, key=lambda s: (-s['p3'], -float(s['diem']), s['tu'])))
        io.open(OUT + 'list-%s.txt' % num, 'w', encoding='utf-8').write('\n'.join(kept) + '\n')
        print('danh sach %s (%s, truong %s): ung vien %d | P1+P2 %d | P3 bo %d | giu %d: %s'
              % (num, name, field, len(stats),
                 sum(1 for s in stats if s['p1'] and s['p2']), len(dropped), len(kept),
                 ' '.join(kept) if kept else '(rong)'))
        if num in ('1', '2'):
            kind = 'path' if num == '1' else 'param'
            for s in stats:
                lex.append((kind, s['tu'], float(s['diem'])))
    lex.sort(key=lambda r: (0 if r[0] == 'path' else 1, -r[2], r[1]))
    with io.open(OUT + 'stateful-authz-lexicon.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['kind', 'word', 'score'])
        for kind, word, s in lex:
            w.writerow([kind, word, '%.4f' % s])
    print('%sstateful-authz-lexicon.csv: %d path, %d param'
          % (OUT, sum(1 for r in lex if r[0] == 'path'), sum(1 for r in lex if r[0] == 'param')))


main()
