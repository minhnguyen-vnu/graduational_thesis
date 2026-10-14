import csv, io, os, re, sys

D = 'labelling-r2/'
PLAN = '../corpus/sampling-plan.md'
OUT = 'lexicon-20260920/'
VERBS = ['PUT', 'PATCH', 'POST', 'DELETE']
KS = [1, 3, 8]


def split_map():
    out = {}
    for l in io.open(PLAN, encoding='utf-8'):
        m = re.match(r'\|\s*(S\d+)\s*\|\s*([^|]+?)\s*\|[^|]*\|[^|]*\|\s*(train|test)\s*\|', l)
        if m:
            out[m.group(1)] = m.group(3)
    return out


def corpus():
    out, order = {}, {}
    for f in sorted(os.listdir(D)):
        if re.match(r'^S\d+\.csv$', f):
            for i, r in enumerate(csv.DictReader(io.open(D + f, encoding='utf-8'))):
                out[r['row_id']] = r
                order[r['row_id']] = i
    return out, order


def scores():
    out = {}
    for r in csv.DictReader(io.open(OUT + 'candidates-1.csv', encoding='utf-8')):
        a, b, p = int(r['df_r']), int(r['df_n']), int(r['nha_cung_cap'])
        out[r['tu']] = (a + 1) / float(a + b + 2) * p / float(p + 1)
    return out


def hay(r):
    p = r['path']
    return (p + ' ' + r['method'] + ':' + p).lower()


def main():
    sp = split_map()
    src, order = corpus()
    sc = scores()
    l2 = [l.strip() for l in io.open(OUT + 'list-2.txt', encoding='utf-8') if l.strip()]
    fin = [r for r in csv.DictReader(io.open(D + 'final.csv', encoding='utf-8'))]
    lab = {r['row_id']: r['final_label'] for r in fin}

    def score(r):
        h = hay(r)
        hit = [sc[w] for w in sc if w in h]
        return max(hit) if hit else 0.0

    def has_user_param(r):
        n = (r['param_names'] or '').lower()
        return any(w in n for w in l2)

    lines = []
    for half in ('train', 'test'):
        specs = sorted({r['spec_id'] for r in fin if sp[r['spec_id']] == half})
        for variant in ('A', 'B', 'C'):
            tot, hits, empty = 0, {k: 0 for k in KS}, 0
            worst = []
            for s in specs:
                rows = [src[r['row_id']] for r in fin if r['spec_id'] == s
                        and src[r['row_id']]['method'].upper() in VERBS]
                if variant == 'B':
                    rows = [r for r in rows if has_user_param(r)]
                pos = [r for r in rows if lab[r['row_id']] == 'R']
                if not pos:
                    empty += 1
                    continue
                tot += 1
                if variant == 'C':
                    rows.sort(key=lambda r: (-score(r), not has_user_param(r),
                                             VERBS.index(r['method'].upper()), order[r['row_id']]))
                else:
                    rows.sort(key=lambda r: (-score(r), VERBS.index(r['method'].upper()),
                                             order[r['row_id']]))
                rank = min(i + 1 for i, r in enumerate(rows) if lab[r['row_id']] == 'R')
                for k in KS:
                    if rank <= k:
                        hits[k] += 1
                if rank > 1:
                    worst.append((s, rank, len(rows), rows[0]['method'] + ' ' + rows[0]['path']))
            lines.append('%-5s bien the %s | %d spec co endpoint R, %d spec khong co' % (half, variant, tot, empty))
            lines.append('      ' + ' | '.join('top-%d %d/%d = %.3f' % (k, hits[k], tot, hits[k] / float(tot))
                                               for k in KS))
            for s, rank, n, top in worst:
                lines.append('      %s hang %d/%d, dung dau la %s' % (s, rank, n, top))
    out = '\n'.join(lines)
    print(out)
    io.open(OUT + 'rank.txt', 'w', encoding='utf-8').write(out + '\n')


main()
