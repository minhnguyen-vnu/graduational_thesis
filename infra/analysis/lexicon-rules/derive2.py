import csv, io, os, re
from collections import Counter

R2, R3 = 'labelling-r2/', 'labelling-r3/'
PLAN = '../corpus/sampling-plan.md'
OUT = 'lexicon-20260921/'
VERBS = ['PUT', 'PATCH', 'POST', 'DELETE']
MIN_LEN = 4
KS = [1, 3, 8]
EXT = ['S%03d' % (200 + i) for i in range(15)]


def split_map():
    import json
    out = {}
    for l in io.open(PLAN, encoding='utf-8'):
        m = re.match(r'\|\s*(S\d+)\s*\|\s*([^|]+?)\s*\|[^|]*\|[^|]*\|\s*(train|test)\s*\|', l)
        if m:
            out[m.group(1)] = (m.group(2).strip(), m.group(3))
    for a in json.load(io.open('../corpus/sample-ext.json', encoding='utf-8')):
        out[a['spec_id']] = (a['provider'], a['split'])
    return out


def corpus():
    out, order = {}, {}
    for d in (R2, R3):
        for f in sorted(os.listdir(d)):
            if not re.match(r'^S\d+(\.v2)?\.csv$', f):
                continue
            for i, r in enumerate(csv.DictReader(io.open(d + f, encoding='utf-8'))):
                out[r['row_id']] = r
                order.setdefault(r['row_id'], i)
    return out, order


def labels(sp):
    out = {}
    for r in csv.DictReader(io.open(R2 + 'final.csv', encoding='utf-8')):
        if r['final_label'] in ('R', 'N'):
            out[r['row_id']] = (r['final_label'], sp[r['spec_id']][1])
    for r in csv.DictReader(io.open(R3 + 'final.csv', encoding='utf-8')):
        if not r['final_label']:
            out.pop(r['row_id'], None)
            continue
        half = 'train' if r['spec_id'] in EXT else sp[r['spec_id']][1]
        out[r['row_id']] = (r['final_label'], half)
    return out


def tokens(text):
    s = set()
    for piece in re.split(r'[^A-Za-z0-9]+', text):
        for t in re.findall(r'[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+', piece or ''):
            t = t.lower()
            if len(t) >= MIN_LEN and not t.isdigit():
                s.add(t)
    return s


def hay(r):
    p = r['path']
    return (p + ' ' + r['method'] + ':' + p).lower()


def main():
    sp = split_map()
    src, order = corpus()
    lab = labels(sp)
    prov = {s: sp[s][0] for s in sp}
    if not os.path.isdir(OUT):
        os.mkdir(OUT)

    half_rows = {'train': [], 'test': []}
    for rid, (lb, hf) in lab.items():
        half_rows[hf].append(dict(src[rid], final_label=lb))
    for h in half_rows:
        print('%-5s %d dong | %s | %d nha cung cap'
              % (h, len(half_rows[h]), dict(Counter(r['final_label'] for r in half_rows[h])),
                 len({prov[r['spec_id']] for r in half_rows[h]})))

    pos = [r for r in half_rows['train'] if r['final_label'] == 'R']
    neg = [r for r in half_rows['train'] if r['final_label'] == 'N']
    base = len(pos) / float(len(pos) + len(neg))
    print('ti le nen train %.4f | nguong P2 %.4f | nha cung cap co R: %d'
          % (base, 2 * base, len({prov[r['spec_id']] for r in pos})))

    cand = set()
    for r in pos:
        cand |= tokens(r['path'])
    stats = []
    for w in sorted(cand):
        hp = [r for r in pos if w in hay(r)]
        hn = [r for r in neg if w in hay(r)]
        np_ = len({prov[r['spec_id']] for r in hp})
        prec = len(hp) / float(len(hp) + len(hn)) if hp or hn else 0.0
        stats.append({'tu': w, 'df_r': len(hp), 'df_n': len(hn), 'nha_cung_cap': np_,
                      'precision': '%.4f' % prec,
                      'diem': '%.4f' % ((len(hp) + 1) / float(len(hp) + len(hn) + 2) * np_ / float(np_ + 1)),
                      'p1': int(np_ >= 2), 'p2': int(prec >= 2 * base)})
    kept = sorted(s['tu'] for s in stats if s['p1'] and s['p2'])
    dropped = {b for a in kept for b in kept if a != b and a in b}
    final4 = [w for w in kept if w not in dropped]
    with io.open(OUT + 'candidates-1.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, ['tu', 'df_r', 'df_n', 'nha_cung_cap', 'precision', 'diem', 'p1', 'p2'],
                           quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(sorted(stats, key=lambda s: -float(s['diem'])))
    print('ung vien %d | qua P1+P2 %d | sau P3 %d: %s' % (len(stats), len(kept), len(final4), ' '.join(final4)))

    sc = {s['tu']: float(s['diem']) for s in stats}

    def score(r):
        h = hay(r)
        hit = [sc[w] for w in sc if w in h]
        return max(hit) if hit else 0.0

    lines = []
    for h in ('train', 'test'):
        rows_all = half_rows[h]
        specs = sorted({r['spec_id'] for r in rows_all})
        tot, hits = 0, {k: 0 for k in KS}
        for s in specs:
            rows = [r for r in rows_all if r['spec_id'] == s and r['method'].upper() in VERBS]
            if not any(r['final_label'] == 'R' for r in rows):
                continue
            tot += 1
            rows.sort(key=lambda r: (-score(r), VERBS.index(r['method'].upper()), order[r['row_id']]))
            rk = min(i + 1 for i, r in enumerate(rows) if r['final_label'] == 'R')
            for k in KS:
                if rk <= k:
                    hits[k] += 1
        lines.append('%-5s xep hang | %d spec co R | %s' % (h, tot, ' | '.join(
            'top-%d %d/%d = %.3f' % (k, hits[k], tot, hits[k] / float(tot)) for k in KS)))
        tp = sum(1 for r in rows_all if r['final_label'] == 'R' and any(w in hay(r) for w in final4)
                 and r['method'].upper() in VERBS)
        fn = sum(1 for r in rows_all if r['final_label'] == 'R' and not (
            any(w in hay(r) for w in final4) and r['method'].upper() in VERBS))
        fp = sum(1 for r in rows_all if r['final_label'] == 'N' and any(w in hay(r) for w in final4)
                 and r['method'].upper() in VERBS)
        lines.append('%-5s bo loc  | TP %d FN %d FP %d | precision %.3f | recall %.3f'
                     % (h, tp, fn, fp, tp / float(tp + fp) if tp + fp else 0, tp / float(tp + fn)))
    print('\n'.join(lines))
    io.open(OUT + 'rank.txt', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

    with io.open(OUT + 'stateful-authz-lexicon.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['kind', 'word', 'score'])
        for s in sorted(stats, key=lambda s: (-float(s['diem']), s['tu'])):
            w.writerow(['path', s['tu'], s['diem']])


main()
