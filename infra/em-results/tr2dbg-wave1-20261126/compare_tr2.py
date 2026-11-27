import csv
import re
from pathlib import Path

HERE = Path(__file__).parent
OLD = HERE.parent / "tr2-wave1-20261121" / "runs.csv"
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
PREFIX = {"tier1": "t1", "tier2": "t2", "tier2b": "t2b"}
ARMS = [("tier1", "vuln"), ("tier1", "fixed"), ("tier2", "ours-vuln"), ("tier2", "ours-fixed"),
        ("tier2b", "vuln"), ("tier2b", "fixed")]
COLS = ["det970", "assembled", "void_count", "restores_ok", "restores_no", "statuses", "faults"]


def load(path):
    return {(r["tier"], r["arm"], r["seed"]): r for r in csv.DictReader(open(path))}


def log_text(tier, arm, seed):
    p = HERE / "logs" / f"{PREFIX[tier]}-{arm}-seed{seed}.log"
    return ANSI.sub("", p.read_text(errors="replace"))


def main():
    old = load(OLD)
    new = load(HERE / "runs.csv")
    print(f"rows TR2 {len(old)} new {len(new)} same keys {set(old) == set(new)}")

    print("\n== 970 per arm")
    for tier, arm in ARMS:
        keys = [k for k in new if k[:2] == (tier, arm)]
        o = sum(old[k]["det970"] == "1" for k in keys)
        n = sum(new[k]["det970"] == "1" for k in keys)
        print(f"{tier:7} {arm:11} TR2 {o}/{len(keys)}  new {n}/{len(keys)}")

    print("\n== rows that differ from TR2, per column")
    order = lambda k: (k[0], k[1], int(k[2]))
    for c in COLS:
        d = sorted((k for k in new if old[k][c] != new[k][c]), key=order)
        print(f"{c:12} {len(d)}")
        for k in d:
            print(f"    {k[0]} {k[1]} seed {k[2]}: TR2 {old[k][c]}  new {new[k][c]}")

    print("\n== debug trail of missed vulnerable runs (new batch)")
    for tier, arm in [("tier1", "vuln"), ("tier2", "ours-vuln")]:
        print(f"-- {tier} {arm}")
        for s in range(1, 21):
            k = (tier, arm, str(s))
            if new[k]["det970"] == "1" and old[k]["det970"] == "1":
                continue
            t = log_text(tier, arm, s)
            sources = re.findall(r"guarded source candidates: (\d+)", t)
            victims = re.findall(r"source (\S+) victims (\[[^\]]*\])", t)
            attempts = re.findall(r"exhausted its sources after (\d+) attempts", t)
            inconclusive = re.findall(r"re-login probe INCONCLUSIVE: (.*)", t)
            print(f"seed {s:2} TR2 970={old[k]['det970']} void={old[k]['void_count']}"
                  f" | new 970={new[k]['det970']} void={new[k]['void_count']}"
                  f" attempts={attempts} sources={sources[:1]} victims={victims}"
                  f" inconclusive={sorted(set(inconclusive))}")

    print("\n== transition ranking printed by the builder (seed 1, vulnerable)")
    for tier, arm in [("tier1", "vuln"), ("tier2", "ours-vuln"), ("tier2b", "vuln")]:
        t = log_text(tier, arm, 1)
        print(f"-- {tier} {arm}")
        for line in re.findall(r"Stateful-authorization (transition candidate .*|transition chosen: .*)", t):
            print("   " + line)


if __name__ == "__main__":
    main()
