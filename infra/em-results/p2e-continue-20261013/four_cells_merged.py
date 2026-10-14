import csv

M = '/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/em-results/p2e-continue-20261013/merged.csv'
rows = list(csv.DictReader(open(M)))


def performed(r):
    s = (r.get('statuses') or '').strip()
    return s not in ('', 'NA') and '/' in s


print('| Target | Reset | TP | FN, triple, no 970 | FN, no triple | FP | TN (triple, no 970) | Fixed, no triple | Runs vuln/fixed |')
print('|---|---|---|---|---|---|---|---|---|')
for tier, label, va, fa in (('tier1', 'Tier-1', 'vuln', 'fixed'), ('tier2', 'Tier-2', 'ours-vuln', 'ours-fixed'),
                            ('tier2b', 'Tier-2b', 'vuln', 'fixed')):
    for reset in ('0', '1'):
        v = [r for r in rows if r['tier'] == tier and r['arm'] == va and r['reset'] == reset]
        f = [r for r in rows if r['tier'] == tier and r['arm'] == fa and r['reset'] == reset]
        tp = sum(r['det970'] == '1' for r in v)
        fnt = sum(r['det970'] != '1' and performed(r) for r in v)
        fnn = sum(r['det970'] != '1' and not performed(r) for r in v)
        fp = sum(r['det970'] == '1' for r in f)
        tn = sum(r['det970'] != '1' and performed(r) for r in f)
        nf = sum(r['det970'] != '1' and not performed(r) for r in f)
        print(f"| {label} | {'yes' if reset == '1' else 'no'} | {tp} | {fnt} | {fnn} | {fp} | {tn} | {nf} | {len(v)}/{len(f)} |")
