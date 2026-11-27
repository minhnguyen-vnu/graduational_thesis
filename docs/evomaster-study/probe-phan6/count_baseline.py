import glob
import os
import re
import sys

BASE = sys.argv[1]
FILES = ["EvoMaster_faults_Test.py", "EvoMaster_others_Test.py", "EvoMaster_successes_Test.py"]
TARGETS = {"t1-vuln": ("VIEWER", "reports-api"), "t2-ours-vuln": ("user", "vampi-seeded")}
WRITE = {"post", "put", "patch", "delete"}


def parse_tests(path):
    text = open(path).read().split("\n")
    tests = []
    cur = None
    auth = None
    body = []
    in_body = False
    pending = None
    for line in text:
        m = re.match(r"\s*def (test_\d+)\w*\(self\)", line)
        if m:
            cur = {"name": m.group(1), "file": os.path.basename(path), "calls": []}
            tests.append(cur)
            auth, body, in_body, pending = None, [], False, None
            continue
        if cur is None:
            continue
        s = line.strip()
        if s == "headers = {}":
            auth, body = None, []
            continue
        m = re.match(r'headers\["Authorization"\] = auth_(\w+)', s)
        if m:
            auth = m.group(1)
            continue
        if s.startswith("body = ") and s != "body = {}":
            body, in_body = [s], s.endswith("\\")
            continue
        if in_body:
            body.append(s)
            in_body = s.endswith("\\")
            continue
        m = re.match(r"res_(\d+) = requests", s)
        if m:
            pending = {"idx": int(m.group(1)), "auth": auth, "body": " ".join(body)}
            continue
        if pending is not None and "verb" not in pending:
            m = re.match(r"\.(get|post|put|patch|delete)\((.*)", s)
            if m:
                paths = re.findall(r'"(/[^"]*)"', m.group(2))
                pending["verb"] = m.group(1)
                pending["path"] = paths[-1] if paths else "?"
                continue
        m = re.match(r"assert res_(\d+)\.status_code == (\d+)", s)
        if m and pending is not None and int(m.group(1)) == pending["idx"]:
            pending["status"] = int(m.group(2))
            cur["calls"].append(pending)
            pending = None
    return tests


def role_of(body):
    m = re.search(r'\\"role\\" : \\"(\w+)\\"', body)
    return m.group(1) if m else None


def ok(st):
    return 200 <= st < 300


for prefix, (low, label) in TARGETS.items():
    print("==", label, "(" + prefix + ")")
    tot_tests = tot_fault_tests = 0
    demos = []
    runs_with_demo = set()
    for d in sorted(glob.glob(os.path.join(BASE, prefix + "-seed*")), key=lambda p: int(p.rsplit("seed", 1)[1])):
        seed = int(d.rsplit("seed", 1)[1])
        n_tests = n_fault = 0
        for f in FILES:
            p = os.path.join(d, f)
            if not os.path.exists(p):
                continue
            ts = parse_tests(p)
            n_tests += len(ts)
            if f == "EvoMaster_faults_Test.py":
                n_fault += len(ts)
            for t in ts:
                for i, c in enumerate(t["calls"]):
                    if c.get("verb") == "put" and c["path"].endswith("/role") and role_of(c["body"]) == low and ok(c["status"]):
                        victim = c["path"].split("/")[-2]
                        before = [x for x in t["calls"][:i] if x["auth"] == victim]
                        after = [x for x in t["calls"][i + 1:] if x["auth"] == victim]
                        demos.append((seed, t["file"], t["name"], c["auth"], victim, c["status"], before, after))
                        runs_with_demo.add(seed)
        tot_tests += n_tests
        tot_fault_tests += n_fault
        print("seed %2d tests %3d fault-tests %3d" % (seed, n_tests, n_fault))
    print("total tests", tot_tests, "fault tests", tot_fault_tests)
    print("demotions to", low, "with 2xx:", len(demos), "in", len(runs_with_demo), "runs", sorted(runs_with_demo))
    with_before = with_after = with_after_2xx = triple = 0
    for seed, f, name, op, victim, st, before, after in demos:
        b = " ".join("%s:%s->%d" % (x["verb"].upper(), x["path"], x["status"]) for x in before) or "-"
        a = " ".join("%s:%s->%d" % (x["verb"].upper(), x["path"], x["status"]) for x in after) or "-"
        print("  seed %2d %-28s %-8s op=%-10s victim=%-10s %d | before[%s] | after[%s]" % (seed, f, name, op, victim, st, b, a))
        with_before += bool(before)
        with_after += bool(after)
        with_after_2xx += any(ok(x["status"]) for x in after)
        triple += any(x["verb"] in WRITE and ok(x["status"]) for x in before) and any(ok(x["status"]) for x in after)
    print("demotions with a victim call before:", with_before, "after:", with_after, "after with 2xx:", with_after_2xx, "write-2xx before and 2xx after:", triple)
