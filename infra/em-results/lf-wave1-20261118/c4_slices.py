import re
import sys
import glob
import os

ROOTS = sys.argv[1:]

req_re = re.compile(r'res_(\d+) = requests \\\s*\n\s*\.(get|post|put|patch|delete)\(\s*(.*?)\n', re.S)


def tests_in(path):
    src = open(path).read()
    parts = re.split(r'\n    (?=# Calls:|@timeout_decorator)', src)
    out = []
    buf = ''
    for p in re.split(r'\n    def (test_\w+)\(self\):', src)[1:]:
        out.append(p)
    names = re.findall(r'\n    def (test_\w+)\(self\):', src)
    bodies = re.split(r'\n    def test_\w+\(self\):', src)[1:]
    return list(zip(names, bodies))


def calls_of(body):
    body = body.split('# Cleanup actions')[0]
    body = re.split(r'\n    # Calls:|\n    @timeout_decorator|\n    def ', body)[0]
    marker = body.find('# Fault970')
    calls = []
    for blk in re.split(r'\n\s*headers = \{\}\n', body):
        m = re.search(r'res_(\d+) = requests \\\s*\n\s*\.(get|post|put|patch|delete)\((.*?)(?:,\s*\n|\n)', blk)
        if not m:
            continue
        a = re.search(r'headers\["Authorization"\] = \S+ # (\S+)', blk)
        st = re.search(r'assert res_%s\.status_code == (\d+)' % m.group(1), blk)
        pos = body.find(blk)
        calls.append({
            'i': int(m.group(1)), 'verb': m.group(2).upper(), 'url': m.group(3).strip(),
            'auth': a.group(1) if a else '-', 'status': st.group(1) if st else '?',
            'after_marker': marker >= 0 and pos > marker,
        })
    return calls


for root in ROOTS:
    for f in sorted(glob.glob(os.path.join(root, '*', '*faults_Test.py'))):
        run = os.path.basename(os.path.dirname(f))
        for name, body in tests_in(f):
            if '# Fault970' not in body:
                continue
            calls = calls_of(body)
            fu_idx = next(k for k, c in enumerate(calls) if c['after_marker'])
            fu = calls[fu_idx]
            tr = calls[fu_idx - 1]
            sl = calls[:fu_idx - 1]
            victim = fu['auth']
            vcalls = [c for c in sl if c['auth'] == victim]
            earlier = vcalls[:-1]
            def short(c):
                u = re.sub(r'self\.baseUrlOfSut \+ ', '', c['url'])
                return '%s %s [%s] %s' % (c['verb'], u[:70], c['auth'], c['status'])
            print('%s\t%s\tvictim=%s\tslice_len=%d\tvictim_calls=%d\tfollowup=%s' % (
                run, name, victim, len(sl), len(vcalls), fu['status']))
            for c in sl:
                print('    slice  ' + short(c))
            print('    trans  ' + short(tr))
            print('    follow ' + short(fu))
