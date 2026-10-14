import csv
import os
import sys

R = '/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/em-results'
P2E = f'{R}/p2e-continue-20261013/runs.csv'
P2D = [f'{R}/p2d-night-20261012/remeasure/runs.csv', f'{R}/p2d-af2fired-probe-20261013/runs.csv']
AF2 = f'{R}/af2-full-remeasure-20261003/runs.csv'
OUT = f'{R}/p2e-continue-20261013/merged.csv'

ARMS = [('tier1', 'vuln', 20), ('tier1', 'fixed', 20), ('tier2', 'ours-vuln', 20), ('tier2', 'ours-fixed', 20),
        ('tier2b', 'vuln', 5), ('tier2b', 'fixed', 5)]


def load(path):
    return {(r['tier'], r['arm'], r['seed'], r['reset']): r for r in csv.DictReader(open(path))}


p2e = load(P2E)
p2d = {}
for p in P2D:
    p2d.update(load(p))
af2 = load(AF2)

rows, missing = [], []
for tier, arm, n in ARMS:
    for reset in ('0', '1'):
        for seed in range(1, n + 1):
            k = (tier, arm, str(seed), reset)
            if k in p2e:
                rows.append(dict(p2e[k], jar='P2e-6ae8277b'))
            elif k in p2d:
                rows.append(dict(p2d[k], jar='P2d-2e0dbd4d'))
            else:
                missing.append(k)

cols = list(next(iter(af2.values())).keys()) + ['jar']
with open(OUT, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

print(f'rows {len(rows)} (expect 180), missing {len(missing)}: {missing}')
print(f"jar P2e {sum(r['jar'].startswith('P2e') for r in rows)}, P2d {sum(r['jar'].startswith('P2d') for r in rows)}")
print('arm,reset,af2_det970,merged_det970,seeds_af2_only,seeds_merged_only')
for tier, arm, n in ARMS:
    for reset in ('0', '1'):
        m = {r['seed']: r['det970'] for r in rows if (r['tier'], r['arm'], r['reset']) == (tier, arm, reset)}
        a = {k[2]: v['det970'] for k, v in af2.items() if (k[0], k[1], k[3]) == (tier, arm, reset)}
        ao = sorted((s for s in a if a[s] == '1' and m.get(s) != '1'), key=int)
        mo = sorted((s for s in m if m[s] == '1' and a.get(s) != '1'), key=int)
        print(f"{tier} {arm},{reset},{sum(v == '1' for v in a.values())}/{len(a)},"
              f"{sum(v == '1' for v in m.values())}/{len(m)},{' '.join(ao) or '-'},{' '.join(mo) or '-'}")
sys.exit(0 if not missing else 1)
