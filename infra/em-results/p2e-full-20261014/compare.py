import csv
import sys
from math import comb

R = '/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/em-results'
P2E = f'{R}/p2e-full-20261014/runs.csv'
GATE = f'{R}/p2e-full-20261014/gate.csv'
AF2 = f'{R}/af2-full-remeasure-20261003/runs.csv'

ARMS = [('tier1', 'vuln', 20), ('tier1', 'fixed', 20), ('tier2', 'ours-vuln', 20), ('tier2', 'ours-fixed', 20),
        ('tier2b', 'vuln', 5), ('tier2b', 'fixed', 5)]


def load(path):
    return {(r['tier'], r['arm'], r['seed'], r['reset']): r for r in csv.DictReader(open(path))}


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, k) for k in range(min(b, c) + 1)) / 2 ** n)


p2e = load(P2E)
af2 = load(AF2)
gate = list(csv.DictReader(open(GATE)))

expected = [(t, a, str(s), r) for t, a, n in ARMS for r in ('0', '1') for s in range(1, n + 1)]
missing = [k for k in expected if k not in p2e]
err = [k for k, v in p2e.items() if v['det970'] == 'ERR']
unbacked = [k for k, v in p2e.items() if v['det970'] == '1' and v['assembled'] == '0']
fp = [k for k, v in p2e.items() if 'fixed' in k[1] and v['det970'] == '1']

print(f'rows {len(p2e)} (expect 180), missing {len(missing)}, ERR {len(err)}, 970 without assembled {len(unbacked)}, '
      f'fixed FP {len(fp)}')
print(f"gate {sum(g['verdict'] == 'MATCH' for g in gate)}/{len(gate)} MATCH")
for k in missing + err + unbacked + fp:
    print('  flagged', k)
print('tier,arm,reset,af2_det970,p2e_det970,seeds_af2_only,seeds_p2e_only,mcnemar_exact_p,af2_assembled,p2e_assembled')
for tier, arm, n in ARMS:
    for reset in ('0', '1'):
        ks = [(tier, arm, str(s), reset) for s in range(1, n + 1)]
        a = {k[2]: af2[k]['det970'] for k in ks if k in af2}
        m = {k[2]: p2e[k]['det970'] for k in ks if k in p2e}
        ao = sorted((s for s in a if a[s] == '1' and m.get(s) == '0'), key=int)
        mo = sorted((s for s in m if m[s] == '1' and a.get(s) == '0'), key=int)
        aa = sum(int(af2[k]['assembled']) for k in ks if k in af2)
        ma = sum(int(p2e[k]['assembled']) for k in ks if k in p2e)
        print(f"{tier},{arm},{reset},{sum(v == '1' for v in a.values())}/{len(a)},"
              f"{sum(v == '1' for v in m.values())}/{len(m)},{' '.join(ao) or '-'},{' '.join(mo) or '-'},"
              f"{mcnemar_exact(len(ao), len(mo)):.3f},{aa},{ma}")
sys.exit(0 if not (missing or err or unbacked or fp) else 1)
