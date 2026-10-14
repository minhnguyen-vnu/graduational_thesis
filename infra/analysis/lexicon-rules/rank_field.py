import csv, io, json, os, re, sys

LEX = 'lexicon-20260921-audited/stateful-authz-lexicon.csv'
FIELD_CAND = 'lexicon-20260921-audited/candidates-3.csv'
FINAL3 = 'final.v2.csv'
OUTF = sys.argv[1] if len(sys.argv) > 1 else None
PLAN = '../corpus/sampling-plan.md'
VERBS = ['PUT', 'PATCH', 'POST', 'DELETE']
KS = [1, 3, 8]


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
    f = [(r['tu'].lower(), float(r['diem'])) for r in csv.DictReader(io.open(FIELD_CAND, encoding='utf-8'))]
    return p, q, f


def labels():
    out = {}
    for r in csv.DictReader(io.open('labelling-r2/final.csv', encoding='utf-8')):
        if r['final_label'] in ('R', 'N'):
            out[r['row_id']] = r['final_label']
    for f in ('labelling-r3/' + FINAL3, 'labelling-r4/final.v2.csv'):
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


def path_hay(r):
    return (r['path'] + ' ' + r['method'] + ':' + r['path']).lower()


def field_hay(r):
    return (r.get('body_field_names') or '').replace(';', ' ').replace(',', ' ').lower()


def best(lex, hay):
    hit = [s for w, s in lex if w in hay]
    return max(hit) if hit else 0.0


def scorers(pw, fw):
    return {
        'V0': lambda r: best(pw, path_hay(r)),
        'V1': lambda r: best(pw, path_hay(r) + ' ' + field_hay(r)),
        'V2': lambda r: max(best(pw, path_hay(r)), best(fw, field_hay(r))),
    }


def measure(variant, score, userparam, lab, sp, half):
    specs = sorted({s for s in sp if sp[s] == half})
    rows, tot = [], 0
    hb = {k: 0 for k in KS}
    hw = {k: 0 for k in KS}
    hs = {k: 0 for k in KS}
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
        before, bst, wst, unres = 0, None, None, 0
        for k2 in sorted(groups):
            g = groups[k2]
            nr = sum(1 for r in g if lab.get(r['row_id']) == 'R')
            if nr:
                bst = before + 1
                wst = before + (len(g) - nr) + 1
                break
            before += len(g)
            unres += sum(1 for r in g if r['row_id'] not in lab)
        for k in KS:
            if bst <= k:
                hb[k] += 1
            if wst <= k:
                hw[k] += 1
            if rseq <= k:
                hs[k] += 1
        rows.append('     %s hang %s/%d  thu-tu-spec %d%s'
                    % (s, bst if bst == wst else '%d-%d' % (bst, wst), len(o), rseq,
                       '  (%d dong chua ro xep tren)' % unres if unres else ''))
    head = ['%s %s: %d spec co endpoint R' % (variant, half, tot)]
    head.append('   ' + ' | '.join(
        'top-%d %d/%d = %.3f' % (k, hb[k], tot, hb[k] / float(tot)) if hb[k] == hw[k]
        else 'top-%d %d-%d/%d = %.3f-%.3f' % (k, hw[k], hb[k], tot, hw[k] / float(tot), hb[k] / float(tot))
        for k in KS))
    head.append('   thu tu spec: ' + ' | '.join(
        'top-%d %d/%d = %.3f' % (k, hs[k], tot, hs[k] / float(tot)) for k in KS))
    return head + rows, hs[1] / float(tot)


def targets(sc):
    out = []
    for name, f in (('tier1', '../../em-config/targets-tier1.csv'),
                    ('tier2', '../../em-config/targets-tier2.csv'),
                    ('tier2b', '../../em-config/targets-tier2b.csv')):
        if not os.path.exists(f):
            continue
        rows = [r for r in csv.DictReader(io.open(f, encoding='utf-8')) if r['method'].upper() in VERBS]
        ranked = sorted(rows, key=lambda r: (-sc(r), VERBS.index(r['method'].upper())))
        for i, r in enumerate(ranked):
            if r.get('is_transition') == '1':
                out.append('   %s hang %d/%d diem %.4f  %s %s'
                           % (name, i + 1, len(ranked), sc(r), r['method'], r['path']))
    return out


def main():
    sp, lab = split_map(), labels()
    pw, qw, fw = lexicon()

    def userparam(r):
        n = (r['param_names'] or '').lower()
        return any(w in n for w in (w for w, _ in qw))

    sc = scorers(pw, fw)
    lines, train1 = [], {}
    for v in ('V0', 'V1', 'V2'):
        for half in ('train', 'test'):
            blk, t1 = measure(v, sc[v], userparam, lab, sp, half)
            lines += blk
            if half == 'train':
                train1[v] = t1
        lines.append('')
    lines.append('top-1 thu tu spec tren nua train: ' + ' '.join('%s %.3f' % (v, train1[v]) for v in ('V0', 'V1', 'V2')))
    chosen = 'V1' if train1['V1'] >= train1['V2'] else 'V2'
    lines.append('bien the chon theo §13.4: %s' % chosen)
    txt = '\n'.join(lines)
    print(txt)
    if OUTF:
        io.open(OUTF, 'w', encoding='utf-8').write(txt + '\n')


main()
