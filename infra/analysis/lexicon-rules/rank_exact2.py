import csv, io, json, os, re, sys

LEX = sys.argv[1]
FINAL3 = sys.argv[2] if len(sys.argv) > 2 else 'final.v2.csv'
OUTF = sys.argv[3] if len(sys.argv) > 3 else None
PLAN = '../corpus/sampling-plan.md'
VERBS = ['PUT', 'PATCH', 'POST', 'DELETE']
KS = [1, 3, 8]
EXT = ['S%03d' % (200 + i) for i in range(15)]


def split_map():
    out = {}
    for l in io.open(PLAN, encoding='utf-8'):
        m = re.match(r'\|\s*(S\d+)\s*\|\s*([^|]+?)\s*\|[^|]*\|[^|]*\|\s*(train|test)\s*\|', l)
        if m:
            out[m.group(1)] = m.group(3)
    for a in json.load(io.open('../corpus/sample-ext.json', encoding='utf-8')):
        out[a['spec_id']] = a['split']
    return out


def lexicon():
    p, q = [], []
    for r in csv.DictReader(io.open(LEX, encoding='utf-8')):
        (p if r['kind'] == 'path' else q).append((r['word'].lower(), float(r['score'])))
    return p, q


def labels():
    out = {}
    for r in csv.DictReader(io.open('labelling-r2/final.csv', encoding='utf-8')):
        if r['final_label'] in ('R', 'N'):
            out[r['row_id']] = r['final_label']
    for f in ('labelling-r3/' + FINAL3, 'labelling-r4/final.csv'):
        for r in csv.DictReader(io.open(f, encoding='utf-8')):
            if r['final_label'] in ('R', 'N'):
                out[r['row_id']] = r['final_label']
            else:
                out.pop(r['row_id'], None)
    return out


def ops(spec):
    for d in ('../corpus/ops-full/', '../corpus/ops-ext/'):
        if os.path.exists(d + spec + '.csv'):
            return [r for r in csv.DictReader(io.open(d + spec + '.csv', encoding='utf-8'))
                    if r['method'].upper() in VERBS]
    return []


def main():
    sp, lab = split_map(), labels()
    pw, qw = lexicon()

    def score(r):
        h = (r['path'] + ' ' + r['method'] + ':' + r['path']).lower()
        hit = [s for w, s in pw if w in h]
        return max(hit) if hit else 0.0

    def userparam(r):
        n = (r['param_names'] or '').lower()
        return any(w in n for w in (w for w, _ in qw))

    lines = []
    for half in ('test', 'train'):
        specs = sorted({s for s in sp if sp[s] == half})
        rows_out, tot, hits, hitsw, hitss = [], 0, {k: 0 for k in KS}, {k: 0 for k in KS}, {k: 0 for k in KS}
        for s in specs:
            o = ops(s)
            if not o or not any(lab.get(r['row_id']) == 'R' for r in o):
                continue
            tot += 1
            def key(r):
                return (-score(r), not userparam(r), VERBS.index(r['method'].upper()))
            groups = {}
            for r in o:
                groups.setdefault(key(r), []).append(r)
            idx = {r['row_id']: i for i, r in enumerate(o)}
            oseq = sorted(o, key=lambda r: key(r) + (idx[r['row_id']],))
            rseq = min(i + 1 for i, r in enumerate(oseq) if lab.get(r['row_id']) == 'R')
            before, best, worst, unres = 0, None, None, 0
            for k2 in sorted(groups):
                g = groups[k2]
                nr = sum(1 for r in g if lab.get(r['row_id']) == 'R')
                if nr:
                    best = before + 1
                    worst = before + (len(g) - nr) + 1
                    break
                before += len(g)
                unres += sum(1 for r in g if r['row_id'] not in lab)
            for k in KS:
                if best <= k:
                    hits[k] += 1
                if worst <= k:
                    hitsw[k] += 1
                if rseq <= k:
                    hitss[k] += 1
            rows_out.append('     %s hang %s/%d  thu-tu-spec %d%s'
                            % (s, best if best == worst else '%d-%d' % (best, worst), len(o),
                               rseq, '  (%d dong chua ro xep tren)' % unres if unres else ''))
        lines.append('%s: %d spec co endpoint R' % (half, tot))
        lines.append('   ' + ' | '.join(
            'top-%d %d/%d = %.3f' % (k, hits[k], tot, hits[k] / float(tot)) if hits[k] == hitsw[k]
            else 'top-%d %d-%d/%d = %.3f-%.3f' % (k, hitsw[k], hits[k], tot,
                                                  hitsw[k] / float(tot), hits[k] / float(tot))
            for k in KS))
        lines.append('   thu tu spec: ' + ' | '.join(
            'top-%d %d/%d = %.3f' % (k, hitss[k], tot, hitss[k] / float(tot)) for k in KS))
        lines += rows_out
    txt = '\n'.join(lines)
    print(txt)
    if OUTF:
        io.open(OUTF, 'w', encoding='utf-8').write(txt + '\n')


main()
