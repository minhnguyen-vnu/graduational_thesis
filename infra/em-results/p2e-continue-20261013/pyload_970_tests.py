import collections
import re
import subprocess

dirs = subprocess.run(['python3', 'merged_testdirs.py', 'tier2b'], capture_output=True, text=True, check=True).stdout.split()
n = 0
perm = collections.Counter()
role0 = 0
follow = collections.Counter()
for d in dirs:
    if '-vuln-' not in d:
        continue
    src = open(d + '/EvoMaster_faults_Test.py', encoding='utf-8', errors='replace').read()
    fns = list(re.finditer(r'\n    def (test_\w+_stillAllowedAfterPermissionRevoked)\(', src))
    for m in fns:
        end = src.find('\n    def ', m.end())
        body = src[m.start(): end if end > 0 else len(src)]
        n += 1
        for seg in re.findall(r'set_user_permission\?"((?:\s*\+\s*"[^"]*")+)', body):
            q = ''.join(re.findall(r'"([^"]*)"', seg))
            p = re.search(r'permission=([^&]*)', q)
            perm[p.group(1) if p else 'absent'] += 1
            r = re.search(r'role=([^&]*)', q)
            role0 += bool(r and r.group(1) == '0')
        head = src[max(0, m.start() - 700): m.start()]
        calls = re.findall(r'# \d+ - \((\d+)\) (\w+:\S+)', head)
        follow[calls[-1][1] if calls else '?'] += 1
print(f'pyLoad vuln 970 tests {n}; transition permission values {dict(perm)}; role=0 in {role0}')
print(f'follow-up routes {len(follow)}: {dict(sorted(follow.items()))}')
