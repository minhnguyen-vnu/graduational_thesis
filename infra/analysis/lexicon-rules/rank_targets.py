import csv, io, json, sys

LEX = 'lexicon-20260921-audited/stateful-authz-lexicon.csv'
OLD = ["role", "permission", "member", "subscription", "plan", "owner", "grant", "access"]
VERBS = ['PUT', 'PATCH', 'POST', 'DELETE']
SPECS = sys.argv[1]
TRANS = {
    'tier1': ('PUT', '/users/{username}/role'),
    'tier2': ('PUT', '/users/v1/{username}/role'),
    'tier2b': ('POST', '/api/set_user_permission'),
    'airflow': ('PATCH', '/auth/fab/v1/users/{username}'),
}


def lexicon():
    p = []
    for r in csv.DictReader(io.open(LEX, encoding='utf-8')):
        if r['kind'] == 'path':
            p.append((r['word'].lower(), float(r['score'])))
    return p


def deref(doc, node, depth=0):
    while isinstance(node, dict) and '$ref' in node and depth < 20:
        ref = node['$ref']
        if not ref.startswith('#/'):
            return {}
        cur = doc
        for part in ref[2:].split('/'):
            cur = cur.get(part, {}) if isinstance(cur, dict) else {}
        node, depth = cur, depth + 1
    return node if isinstance(node, dict) else {}


def body_fields(doc, op):
    rb = deref(doc, op.get('requestBody') or {})
    out = []
    for ct in (rb.get('content') or {}).values():
        sch = deref(doc, ct.get('schema') or {})
        if sch.get('type') == 'array':
            sch = deref(doc, sch.get('items') or {})
        for key in ('properties',):
            out += list((sch.get(key) or {}).keys())
        for comb in ('allOf', 'oneOf', 'anyOf'):
            for sub in sch.get(comb) or []:
                out += list((deref(doc, sub).get('properties') or {}).keys())
    return sorted(set(out))


def param_names(doc, path_item, op):
    out = []
    for p in (path_item.get('parameters') or []) + (op.get('parameters') or []):
        p = deref(doc, p)
        if p.get('name'):
            out.append(p['name'])
    return sorted(set(out))


def ops(doc):
    rows = []
    for path, item in (doc.get('paths') or {}).items():
        item = deref(doc, item)
        for verb, op in item.items():
            if verb.upper() not in VERBS or not isinstance(op, dict):
                continue
            rows.append({'method': verb.upper(), 'path': path,
                         'body': body_fields(doc, op), 'params': param_names(doc, item, op)})
    return rows


def main():
    pw = lexicon()

    def pathhay(r):
        return (r['path'] + ' ' + r['method'] + ':' + r['path']).lower()

    def fieldhay(r):
        return ' '.join(r['body']).lower()

    def sc_old(r):
        return 1.0 if any(w in pathhay(r) for w in OLD) else 0.0

    def sc_v0(r):
        hit = [s for w, s in pw if w in pathhay(r)]
        return max(hit) if hit else 0.0

    def sc_v1(r):
        h = pathhay(r) + ' ' + fieldhay(r)
        hit = [s for w, s in pw if w in h]
        return max(hit) if hit else 0.0

    for name in ('tier1', 'tier2', 'tier2b', 'airflow'):
        doc = json.load(io.open('%s/%s.json' % (SPECS, name), encoding='utf-8'))
        rows = ops(doc)
        tv, tp = TRANS[name]
        for label, sc in (('8 tu cung', sc_old), ('V0', sc_v0), ('V1', sc_v1)):
            cand = [r for r in rows if sc(r) > 0.0]
            ranked = sorted(cand, key=lambda r: (-sc(r), VERBS.index(r['method'])))
            pos = [i + 1 for i, r in enumerate(ranked) if r['method'] == tv and r['path'] == tp]
            tied = None
            if pos:
                s0 = sc(ranked[pos[0] - 1])
                lo = sum(1 for r in ranked if sc(r) > s0) + 1
                hi = sum(1 for r in ranked if sc(r) >= s0)
                tied = '%d' % lo if lo == hi else '%d-%d' % (lo, hi)
            print('%-8s %-10s ung vien %3d / %3d ghi | transition %s  diem %.4f'
                  % (name, label, len(cand), len(rows),
                     ('hang %s' % tied) if pos else 'KHONG QUA CONG',
                     sc(next((r for r in rows if r['method'] == tv and r['path'] == tp), {'method': tv, 'path': tp, 'body': [], 'params': []}))))
        b = next((r['body'] for r in rows if r['method'] == tv and r['path'] == tp), None)
        print('         truong than: %s' % (', '.join(b) if b else '(khong co)'))
        print()


main()
