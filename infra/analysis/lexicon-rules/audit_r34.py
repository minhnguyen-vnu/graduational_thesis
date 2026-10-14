import csv, io, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'labelling-r34-audit', 'audit.csv')
HEAD = ['row_id', 'src', 'spec_id', 'user_label', 'note']


def targets():
    out = []
    for d in ('labelling-r4', 'labelling-r3'):
        p = os.path.join(BASE, d, 'final.csv')
        for r in csv.DictReader(io.open(p, encoding='utf-8')):
            if r['final_label'] == 'R':
                out.append((d, r['row_id'], r['spec_id']))
    return out


def done():
    if not os.path.exists(OUT):
        return {}
    return {r['row_id']: r['user_label']
            for r in csv.DictReader(io.open(OUT, encoding='utf-8'))}


def source_row(d, rid, spec):
    p = os.path.join(BASE, d, spec + '.csv')
    for r in csv.DictReader(io.open(p, encoding='utf-8')):
        if r['row_id'] == rid:
            return r
    raise SystemExit('khong thay %s trong %s' % (rid, p))


def record(rid, label, note):
    tg = {t[1]: t for t in targets()}
    if rid not in tg:
        raise SystemExit('%s khong nam trong danh sach soat' % rid)
    if label not in ('R', 'N', 'U'):
        raise SystemExit('nhan phai la R, N hoac U')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    new = not os.path.exists(OUT)
    with io.open(OUT, 'a', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, HEAD, quoting=csv.QUOTE_ALL)
        if new:
            w.writeheader()
        w.writerow({'row_id': rid, 'src': tg[rid][0], 'spec_id': tg[rid][2],
                    'user_label': label, 'note': note})


def show(n):
    tg, dn = targets(), done()
    todo = [t for t in tg if t[1] not in dn]
    print('Da soat %d/%d, con %d' % (len(tg) - len(todo), len(tg), len(todo)))
    for d, rid, spec in todo[:n]:
        r = source_row(d, rid, spec)
        print('')
        print('=== %s  (%s)' % (rid, 'r4 do hang' if d == 'labelling-r4' else 'r3 mo rong train'))
        print('method + path    : %s %s' % (r['method'], r['path']))
        print('summary          : ' + (r['summary'] or '(trong)'))
        desc = r['description'] or '(trong)'
        print('description      : ' + (desc[:400] + (' ...' if len(desc) > 400 else '')))
        print('param_names      : ' + (r['param_names'] or '(trong)'))
        print('body_field_names : ' + (r['body_field_names'] or '(trong)'))
        print('enum_values      : ' + (r['enum_values'] or '(trong)'))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--record':
        record(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else '')
    else:
        show(int(sys.argv[1]) if len(sys.argv) > 1 else 4)
