import collections
import csv
import glob
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(BASE, "runs.csv"))))
by = {(r["tier"], r["arm"], int(r["seed"]), r["reset"]): r for r in rows}

print("| Target | Reset | TP | FN, triple, no 970 | FN, no triple | FP | TN | Fixed, no triple | Runs vuln/fixed |")
print("|---|---|---|---|---|---|---|---|---|")
for tier, vuln, fixed in [("tier1", "vuln", "fixed"), ("tier2", "ours-vuln", "ours-fixed"), ("tier2b", "vuln", "fixed")]:
    for reset in ("0", "1"):
        v = [r for r in rows if r["tier"] == tier and r["arm"] == vuln and r["reset"] == reset]
        f = [r for r in rows if r["tier"] == tier and r["arm"] == fixed and r["reset"] == reset]
        tp = sum(1 for r in v if r["det970"] == "1")
        fn_t = sum(1 for r in v if r["det970"] != "1" and int(r["assembled"]) > 0)
        fn_n = sum(1 for r in v if r["det970"] != "1" and int(r["assembled"]) == 0)
        fp = sum(1 for r in f if r["det970"] == "1")
        tn = sum(1 for r in f if r["det970"] != "1" and int(r["assembled"]) > 0)
        fx = sum(1 for r in f if int(r["assembled"]) == 0)
        print(f"| {tier} | {'yes' if reset == '1' else 'no'} | {tp} | {fn_t} | {fn_n} | {fp} | {tn} | {fx} | {len(v)}/{len(f)} |")

fixed_triples = collections.Counter()
for r in rows:
    if "fixed" in r["arm"]:
        fixed_triples[r["tier"]] += int(r["assembled"])
print("triples on fixed targets", dict(fixed_triples), "total", sum(fixed_triples.values()))

statuses = collections.Counter()
for r in rows:
    if int(r["assembled"]) > 0:
        side = "fixed" if "fixed" in r["arm"] else "vuln"
        for s in r["statuses"].split(";"):
            statuses[(side, s)] += 1
print("performed-triple statuses", dict(statuses))

for tier, arm in [("tier1", "vuln"), ("tier2", "ours-vuln")]:
    gained = [s for s in range(1, 21) if by[(tier, arm, s, "1")]["det970"] == "1" and by[(tier, arm, s, "0")]["det970"] != "1"]
    lost = [s for s in range(1, 21) if by[(tier, arm, s, "0")]["det970"] == "1" and by[(tier, arm, s, "1")]["det970"] != "1"]
    print(f"reset ablation {tier}: gained {gained} lost {lost}")

n = 0
perm = collections.Counter()
role0 = 0
follow = collections.Counter()
for d in sorted(glob.glob(os.path.join(BASE, "tests", "t2b-vuln-*"))):
    src = open(os.path.join(d, "EvoMaster_faults_Test.py"), encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"\n    def (test_\w+_stillAllowedAfterPermissionRevoked)\(", src):
        end = src.find("\n    def ", m.end())
        body = src[m.start(): end if end > 0 else len(src)]
        n += 1
        for seg in re.findall(r'set_user_permission\?"((?:\s*\+\s*"[^"]*")+)', body):
            q = "".join(re.findall(r'"([^"]*)"', seg))
            p = re.search(r"permission=([^&]*)", q)
            perm[p.group(1) if p else "absent"] += 1
            r = re.search(r"role=([^&]*)", q)
            role0 += bool(r and r.group(1) == "0")
        head = src[max(0, m.start() - 700): m.start()]
        calls = re.findall(r"# \d+ - \((\d+)\) (\w+:\S+)", head)
        follow[calls[-1][1] if calls else "?"] += 1
print(f"pyLoad vuln 970 tests {n}; transition permission values {dict(perm)}; role=0 in {role0}")
print(f"follow-up routes {len(follow)}: {dict(sorted(follow.items()))}")
