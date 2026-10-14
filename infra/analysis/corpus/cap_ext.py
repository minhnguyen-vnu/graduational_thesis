import csv, io, os, random

SEED = 20260921
CAP = 36
OUT = '../lexicon-rules/labelling-r3/'

os.makedirs(OUT, exist_ok=True)
tot = 0
for sid in ['S%03d' % (200 + i) for i in range(15)]:
    rows = list(csv.reader(io.open('ops-ext/' + sid + '.csv', encoding='utf-8')))
    head, body = rows[0], rows[1:]
    n_full = len(body)
    if n_full > CAP:
        rng = random.Random(SEED + int(sid[1:]))
        body = [body[i] for i in sorted(rng.sample(range(n_full), CAP))]
    with io.open(OUT + sid + '.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(head)
        w.writerows(body)
    tot += len(body)
    print('%s %d/%d' % (sid, len(body), n_full))
print('tong %d dong' % tot)
