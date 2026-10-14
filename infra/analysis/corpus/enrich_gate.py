import csv, glob, os, random, sys
from gate_words import classes

CAP_BOTH = 15
CAP_ONE = 6
SEED = 20260919
OUT = "../lexicon-rules/labelling-r2"


def sampled_ids():
    ids = set()
    for f in sorted(glob.glob("../lexicon-rules/labelling/S1*.csv")):
        if any(t in f for t in (".l1.", ".l2.", ".human.", ".final.")):
            continue
        for x in list(csv.reader(open(f, newline="")))[1:]:
            ids.add(x[0])
    return ids


def main():
    done = sampled_ids()
    os.makedirs(OUT, exist_ok=True)
    head = None
    log = []
    for f in sorted(glob.glob("ops-full/*.csv")):
        rows = list(csv.reader(open(f, newline="")))
        head, body = rows[0], rows[1:]
        if not body:
            continue
        spec = body[0][1]
        keep = [x for x in body if x[0] in done]
        pool_both, pool_one = [], []
        for x in body:
            if x[0] in done:
                continue
            s, p = classes(x)
            if s and p:
                pool_both.append(x)
            elif s or p:
                pool_one.append(x)
        rnd = random.Random(SEED + int(spec[1:]))
        add_both = sorted(rnd.sample(pool_both, min(CAP_BOTH, len(pool_both))), key=lambda x: x[0])
        add_one = sorted(rnd.sample(pool_one, min(CAP_ONE, len(pool_one))), key=lambda x: x[0])
        out = sorted(keep + add_both + add_one, key=lambda x: x[0])
        if not out:
            continue
        with open(os.path.join(OUT, spec + ".csv"), "w", newline="") as fh:
            w = csv.writer(fh, quoting=csv.QUOTE_ALL)
            w.writerow(head)
            w.writerows(out)
        log.append((spec, len(keep), len(add_both), len(add_one), len(out)))
    tot = [sum(r[i] for r in log) for i in (1, 2, 3, 4)]
    print("%-6s %6s %6s %6s %6s" % ("spec", "round1", "+both", "+one", "total"))
    for r in log:
        print("%-6s %6d %6d %6d %6d" % r)
    print("%-6s %6d %6d %6d %6d" % ("TOTAL", *tot))


if __name__ == "__main__":
    main()
