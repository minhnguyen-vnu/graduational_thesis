import csv, glob, os, sys

RULES = {"R2","R3","R4","R5","R6","N1","N2","N3","N4","N5","N6","N7","N8","N9","U1","U2","U3"}
DIR = "labelling-r2"


def rows(p):
    with open(p, newline="") as f:
        return list(csv.reader(f))


def check(suffix):
    bad, n, dist = [], 0, {"R": 0, "N": 0, "U": 0}
    specs = sorted(os.path.basename(p)[:-4] for p in glob.glob(DIR + "/S*.csv") if ".l1." not in p and ".l2." not in p)
    missing = []
    for s in specs:
        out = "%s/%s.%s.csv" % (DIR, s, suffix)
        if not os.path.exists(out):
            missing.append(s)
            continue
        src, got = rows("%s/%s.csv" % (DIR, s)), rows(out)
        if got[0] != src[0]:
            bad.append((s, "header"))
        if len(got) != len(src):
            bad.append((s, "len %d vs %d" % (len(got) - 1, len(src) - 1)))
            continue
        for a, b in zip(src[1:], got[1:]):
            n += 1
            if a[:9] != b[:9]:
                bad.append((b[0], "input columns changed"))
            if b[10] not in ("R", "N", "U"):
                bad.append((b[0], "label %r" % b[10]))
                continue
            dist[b[10]] += 1
            if b[11] not in RULES or b[11][0] != b[10]:
                bad.append((b[0], "rule %r for %s" % (b[11], b[10])))
            if b[10] == "U" and not b[12].strip():
                bad.append((b[0], "U without doubt_token"))
            if b[10] != "U" and b[12].strip():
                bad.append((b[0], "doubt_token on non-U"))
            if b[14].strip():
                bad.append((b[0], "final_label filled"))
            if b[9] != "llm":
                bad.append((b[0], "annotator %r" % b[9]))
    print("%s: %d rows, %s, missing specs: %s" % (suffix, n, dist, missing or "none"))
    for b in bad[:20]:
        print("   FAIL", b)
    print("   total problems:", len(bad))


for s in sys.argv[1:] or ["l1", "l2"]:
    check(s)
