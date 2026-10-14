import csv
import os
import sys

E = '/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/em-results'
rows = list(csv.DictReader(open(f'{E}/p2e-continue-20261013/merged.csv')))
tiers = sys.argv[1].split(',')
for r in rows:
    if r['tier'] not in tiers:
        continue
    name = {'tier1': 't1', 'tier2': 't2', 'tier2b': 't2b'}[r['tier']] + f"-{r['arm']}-seed{r['seed']}-r{r['reset']}"
    if r['jar'].startswith('P2e'):
        d = f'{E}/p2e-continue-20261013/tests/{name}'
    elif os.path.isdir(f'{E}/p2d-af2fired-probe-20261013/tests/{name}'):
        d = f'{E}/p2d-af2fired-probe-20261013/tests/{name}'
    else:
        d = f'{E}/p2d-night-20261012/remeasure/tests/{name}'
    if not os.path.isdir(d):
        sys.exit(f'missing {d}')
    print(d)
