import csv
import sys

old_path, new_path = sys.argv[1], sys.argv[2]


def load(p):
    return {(r['tier'], r['arm'], r['seed']): r for r in csv.DictReader(open(p, encoding='utf-8'))}


old, new = load(old_path), load(new_path)
keys = sorted(set(old) & set(new), key=lambda k: (k[0], k[1], int(k[2])))
only_old = sorted(set(old) - set(new))
only_new = sorted(set(new) - set(old))

print(f"old {old_path}")
print(f"new {new_path}")
print(f"paired rows {len(keys)}, only in old {len(only_old)}, only in new {len(only_new)}")

groups = {}
lost, gained, faults_changed = [], [], []
for k in keys:
    o, n = old[k], new[k]
    g = groups.setdefault((k[0], k[1]), [0, 0, 0])
    g[0] += 1
    g[1] += o['det970'] == '1'
    g[2] += n['det970'] == '1'
    if o['det970'] == '1' and n['det970'] != '1':
        lost.append(k)
    if o['det970'] != '1' and n['det970'] == '1':
        gained.append(k)
    if o['faults'] != n['faults']:
        faults_changed.append((k, o['faults'], n['faults']))

print("tier,arm,runs,old_970,new_970")
for (t, a), (n_runs, o970, n970) in groups.items():
    print(f"{t},{a},{n_runs},{o970},{n970}")

fixed_raised = [k for k in keys if k[1] == 'fixed' and new[k]['det970'] == '1']
errors = [k for k in keys if new[k]['det970'] not in ('0', '1')]
print(f"970 lost {len(lost)} {lost}")
print(f"970 gained {len(gained)} {gained}")
print(f"970 on fixed arm in new {len(fixed_raised)} {fixed_raised}")
print(f"unreadable reports in new {len(errors)} {errors}")
print(f"rows whose fault-code set changed {len(faults_changed)}")
for k, a, b in faults_changed:
    print(f"  {k[0]} {k[1]} seed={k[2]}: {a} -> {b}")
