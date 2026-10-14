import csv, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LR = os.path.normpath(os.path.join(HERE, ".."))
CORPUS = os.path.normpath(os.path.join(LR, "..", "corpus"))
R4DIR = os.path.join(LR, "field-labelling-r4-20261006")
JAR_LEX = os.path.join(LR, "lexicon-20260921-audited", "stateful-authz-lexicon.csv")
sys.path.insert(0, R4DIR)
import sim

MIN_LEN = 4
EXT = ['S%03d' % (200 + i) for i in range(15)]
VERBS = ['PUT', 'PATCH', 'POST', 'DELETE']


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


def score(a, b, p):
    return (a + 1) / float(a + b + 2) * p / float(p + 1)


def derive(rows, provider, cand_fn, hay_fn):
    pos = [r for r in rows if r['final_label'] == 'R']
    neg = [r for r in rows if r['final_label'] == 'N']
    cand = set()
    for r in pos:
        cand |= tokens(cand_fn(r))
    hp_h = [hay_fn(r) for r in pos]
    hn_h = [hay_fn(r) for r in neg]
    stats = []
    for w in sorted(cand):
        idx = [i for i, h in enumerate(hp_h) if w in h]
        dn = sum(1 for h in hn_h if w in h)
        prov = {provider[pos[i]['spec_id']] for i in idx}
        stats.append({'tu': w, 'df_r': len(idx), 'df_n': dn, 'nha_cung_cap': len(prov),
                      'diem': '%.4f' % score(len(idx), dn, len(prov))})
    return stats


def lexicon_rows(path_stats, param_stats):
    lex = [('path', s['tu'], float(s['diem'])) for s in path_stats]
    lex += [('param', s['tu'], float(s['diem'])) for s in param_stats]
    lex.sort(key=lambda r: (0 if r[0] == 'path' else 1, -r[2], r[1]))
    return lex


def write_lexicon(path, lex):
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['kind', 'word', 'score'])
        for kind, word, s in lex:
            w.writerow([kind, word, '%.4f' % s])


def write_candidates(path, stats):
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, ['tu', 'df_r', 'df_n', 'nha_cung_cap', 'diem'], quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(sorted(stats, key=lambda s: (-float(s['diem']), s['tu'])))


def read_lexicon(path):
    pw, qw = [], []
    for r in csv.DictReader(io.open(path, encoding='utf-8')):
        (pw if r['kind'] == 'path' else qw).append((r['word'].lower(), float(r['score'])))
    return pw, qw


def old_split_map():
    out = {}
    for l in io.open(os.path.join(CORPUS, 'sampling-plan.md'), encoding='utf-8'):
        m = re.match(r'\|\s*(S\d+)\s*\|\s*([^|]+?)\s*\|[^|]*\|[^|]*\|\s*(train|test)\s*\|', l)
        if m:
            out[m.group(1)] = (m.group(2).strip(), m.group(3))
    for a in json.load(io.open(os.path.join(CORPUS, 'sample-ext.json'), encoding='utf-8')):
        out[a['spec_id']] = (a['provider'], a['split'])
    return out


def old_corpus():
    out = {}
    for d in ('labelling-r2', 'labelling-r3'):
        p = os.path.join(LR, d)
        for f in sorted(os.listdir(p)):
            if re.match(r'^S\d+(\.v2)?\.csv$', f):
                for r in csv.DictReader(io.open(os.path.join(p, f), encoding='utf-8')):
                    out[r['row_id']] = r
    return out


def old_labels(sp):
    out = {}
    for r in csv.DictReader(io.open(os.path.join(LR, 'labelling-r2', 'final.csv'), encoding='utf-8')):
        if r['final_label'] in ('R', 'N'):
            out[r['row_id']] = (r['final_label'], sp[r['spec_id']][1])
    for r in csv.DictReader(io.open(os.path.join(LR, 'labelling-r3', 'final.v2.csv'), encoding='utf-8')):
        if not r['final_label']:
            out.pop(r['row_id'], None)
            continue
        half = 'train' if r['spec_id'] in EXT else sp[r['spec_id']][1]
        out[r['row_id']] = (r['final_label'], half)
    return out


def old_train():
    sp = old_split_map()
    src = old_corpus()
    lab = old_labels(sp)
    provider = {s: sp[s][0] for s in sp}
    rows = [dict(src[rid], final_label=lb) for rid, (lb, hf) in lab.items() if hf == 'train']
    return rows, provider


def old_train_specs():
    rows, _ = old_train()
    return sorted({r['spec_id'] for r in rows})


def path_hay(r):
    return (r['path'] + ' ' + r['method'] + ':' + r['path']).lower()


def param_hay(r):
    return (r['param_names'] or '').lower()


def derive_old_rule(rows, provider):
    p = derive(rows, provider, lambda r: r['path'], path_hay)
    q = derive(rows, provider, lambda r: r['param_names'] or '', param_hay)
    return p, q


def new_data():
    lab = sim.load_labels(os.path.join(R4DIR, 'final-all.csv'))
    ops = sim.load_ops(set(lab))
    rows = []
    for op in ops:
        top = [f['name'] for f in op['fields'] if f['loc'] == 'body' and '.' not in f['name'] and '[' not in f['name']]
        rows.append({'row_id': op['row_id'], 'spec_id': op['spec'], 'method': op['method'], 'path': op['path'],
                     'param_names': ';'.join(f['name'] for f in op['fields'] if f['loc'] in ('path', 'query')),
                     'body_top': ' '.join(top), 'v1hay': sim.hay(op),
                     'final_label': 'R' if lab[op['row_id']]['T'] else 'N'})
    provider = {op['spec']: op['provider'] for op in ops}
    return lab, ops, rows, provider


def derive_new(rows, provider, v1):
    if v1:
        p = derive(rows, provider, lambda r: r['path'] + ' ' + r['body_top'], lambda r: r['v1hay'])
    else:
        p = derive(rows, provider, lambda r: r['path'], path_hay)
    q = derive(rows, provider, lambda r: r['param_names'] or '', param_hay)
    return p, q


def as_lex(path_stats, param_stats):
    lex = lexicon_rows(path_stats, param_stats)
    return [(w, s) for k, w, s in lex if k == 'path'], [(w, s) for k, w, s in lex if k == 'param']
