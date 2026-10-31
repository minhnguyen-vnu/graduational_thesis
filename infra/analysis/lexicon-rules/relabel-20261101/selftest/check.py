import collections, csv, json, os, sys

W, at_kill, rc = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
manifest = json.load(open(os.path.join(W, "manifest.json")))
calls = [l.split() for l in open(os.path.join(W, "state", "calls.log"))]
log = open(os.path.join(W, "run.log")).read()
fails = 0


def check(name, ok, detail=""):
    global fails
    print("%s  %s %s" % ("PASS" if ok else "FAIL", name, detail))
    fails += 0 if ok else 1


expected = [(s, n) for s in manifest for n in manifest[s]]
bad = ("test", "chunk-003")
missing, wrong = [], []
for lane in ("A", "B"):
    for s, n in expected:
        p = os.path.join(W, lane, s, n + ".csv")
        if (s, n) == bad:
            continue
        if not os.path.exists(p):
            missing.append((lane, s, n))
            continue
        if {r["row_id"] for r in csv.DictReader(open(p))} != set(manifest[s][n]):
            wrong.append((lane, s, n))
check("moi khoi tot co du file o ca hai luot", not missing, str(missing[:3]))
check("khong file nao thieu dong (khoi tra thieu dong bi gan lai)", not wrong, str(wrong[:3]))
check("khoi luon tra sai khong duoc ghi", not any(os.path.exists(os.path.join(W, l, *bad[:1], bad[1] + ".csv")) for l in "AB"))
check("khoi hong hien trong STATUS.md", "Khoi hong" in open(os.path.join(W, "STATUS.md")).read() and "test/chunk-003" in open(os.path.join(W, "STATUS.md")).read())
check("driver ket thuc voi ma 0", rc == 0, "rc=%d" % rc)
check("bi giet giua chung roi chay tiep", at_kill >= 9 and len(calls) > at_kill, "at_kill=%d tong=%d" % (at_kill, len(calls)))

t0, reset = [float(x) for x in open(os.path.join(W, "state", "limit-window")).read().split()]
in_pause = [c for c in calls if t0 + 0.35 < float(c[0]) < reset]
check("khong goi nao trong luc cho reset", not in_pause, "%d goi" % len(in_pause))
after = [c for c in calls if float(c[0]) >= reset]
check("chay lai sau reset", len(after) > 0, "%d goi" % len(after))
check("log ghi LIMIT tu su kien rate_limit_event", "LIMIT" in log)
check("log ghi loi truyen (exit 1 khong result)", "loi truyen" in log)
check("log ghi dau ra sai (csv thieu dong)", "dau ra sai" in log)

first_id = {}
for s, n in expected:
    first_id[manifest[s][n][0]] = (s, n)
per = collections.Counter((c[2], c[3]) for c in calls)
over = {k: v for k, v in per.items() if k[1] in first_id and first_id[k[1]] != bad and v > 4}
check("khoi da xong khong bi goi lai nhieu lan", not over, str(list(over.items())[:3]))
check("moi loi goi co --safe-mode va --tools rong", all(c[4] == "1" and c[5] == "True" for c in calls))
check("bien moi truong phien chinh bi go", all(c[6] == "0" for c in calls))
order = [first_id[c[3]][0] for c in calls if c[3] in first_id and c[2] == "claude-sonnet-5-5"]
seen = list(dict.fromkeys(order))
check("thu tu: train dau, known, test, train con lai", seen[:3] == ["train", "known", "test"], str(seen))
print("KET QUA", "DAT" if fails == 0 else "TRUOT %d" % fails)
sys.exit(1 if fails else 0)
