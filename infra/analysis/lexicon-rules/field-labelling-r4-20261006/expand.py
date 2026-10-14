import csv, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def ids(n):
    return re.findall(r"^## (\S+)", open(os.path.join(HERE, "rows", "chunk-%s.txt" % n)).read(), re.M)


def main(who, n):
    raw = os.path.join(HERE, who, "raw", "chunk-%s.txt" % n)
    got = {}
    for r in csv.reader(io.StringIO(open(raw).read())):
        if not r:
            continue
        r = (r + [""] * 6)[:6]
        got[r[0]] = r
    order = ids(n)
    extra = set(got) - set(order)
    if extra:
        raise SystemExit("unknown row ids in %s: %s" % (raw, sorted(extra)))
    with open(os.path.join(HERE, who, "chunk-%s.csv" % n), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["row_id", "T", "victim", "role", "order", "sub"])
        for rid in order:
            w.writerow(got.get(rid, [rid, "0", "", "", "", ""]))
    print(n, len(order), "ops", len(got), "non-default")


for n in sys.argv[2:]:
    main(sys.argv[1], n)
