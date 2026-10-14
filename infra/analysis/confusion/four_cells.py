import csv
import sys

R = "/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/em-results/"


def rows(path):
    return list(csv.DictReader(open(R + path, encoding="utf-8")))


def performed(r):
    s = (r.get("statuses") or "").strip()
    return s not in ("", "NA") and "/" in s


def cells(vuln, fixed):
    tp = sum(r["det970"] == "1" for r in vuln)
    fn_triple = sum(r["det970"] != "1" and performed(r) for r in vuln)
    fn_none = sum(r["det970"] != "1" and not performed(r) for r in vuln)
    fp = sum(r["det970"] == "1" for r in fixed)
    tn = sum(r["det970"] != "1" and performed(r) for r in fixed)
    none_fixed = sum(r["det970"] != "1" and not performed(r) for r in fixed)
    return tp, fn_triple, fn_none, fp, tn, none_fixed, len(vuln), len(fixed)


def jar_r():
    t1 = rows("tier1-clean-remeasure/runs.csv")
    t2 = rows("restore-remeasure/runs.csv")
    t2r = rows("restore-reset-remeasure/runs.csv")
    t2b = rows("tier2b-restore-trials/runs.csv")
    out = []
    for reset in ("0", "1"):
        out.append(("Tier-1", reset,
                    [r for r in t1 if r["tier"] == "tier1" and r["reset"] == reset and r["arm"].startswith("vuln")],
                    [r for r in t1 if r["tier"] == "tier1" and r["reset"] == reset and r["arm"].startswith("fixed")]))
    out.append(("Tier-2", "0",
                [r for r in t2 if r["tier"] == "tier2" and r["arm"] == "ours-vuln" and r["reset"] == "0"],
                [r for r in t2 if r["tier"] == "tier2" and r["arm"] == "ours-fixed" and r["reset"] == "0"]))
    out.append(("Tier-2", "1",
                [r for r in t2r if r["tier"] == "tier2" and r["arm"] == "ours-vuln-reset"],
                [r for r in t2r if r["tier"] == "tier2" and r["arm"] == "ours-fixed-reset"]))
    for reset, tag in (("0", "noreset"), ("1", "reset")):
        out.append(("Tier-2b", reset,
                    [r for r in t2b if r["arm"] == "vuln-" + tag],
                    [r for r in t2b if r["arm"] == "fixed-" + tag]))
    return out


def jar_runs(path):
    rs = rows(path)
    out = []
    for tier, label in (("tier1", "Tier-1"), ("tier2", "Tier-2"), ("tier2b", "Tier-2b")):
        v = [r for r in rs if r["tier"] == tier and r["arm"] == "vuln"]
        f = [r for r in rs if r["tier"] == tier and r["arm"] == "fixed"]
        out.append((label, "0", v, f))
    return out


groups = jar_r() if len(sys.argv) < 2 else jar_runs(sys.argv[1])
print("| Target | Reset | TP | FN, triple, no 970 | FN, no triple | FP | TN (triple, no 970) | Fixed, no triple | Runs vuln/fixed |")
print("|---|---|---|---|---|---|---|---|---|")
for name, reset, v, f in groups:
    tp, fnt, fnn, fp, tn, nf, nv, nfx = cells(v, f)
    print(f"| {name} | {'yes' if reset == '1' else 'no'} | {tp} | {fnt} | {fnn} | {fp} | {tn} | {nf} | {nv}/{nfx} |")
