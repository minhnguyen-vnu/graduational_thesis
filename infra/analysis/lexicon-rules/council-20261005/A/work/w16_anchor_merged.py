"""Neo target (r2 PROTOCOL.md:76-83, evaluate.py:9-16) cho ba bo: viet tay, R4 train+dev, R4 ca ba tap (merged)."""
from load import *

F = load_all()
TD = [f for f in F if f["split"] in ("train", "dev")]
SETS = {"hard": HARD}
for tag, ff in (("R4_train+dev", TD), ("R4_all", F)):
    SETS[tag] = {n: derive(docs(ff, n), "R4")[0] for n in ("A-role", "A-admin", "C", "B-low", "B-high")}
ANCHOR = [("reports-api", ["role"], "role", ["username"], "VIEWER", "ADMIN"),
          ("vampi-seeded", ["role"], "role", ["username"], "user", "admin"),
          ("pyLoad", ["permission", "role"], "role", ["user"], None, None),
          ("artifact-keeper", ["is_admin"], "admin", ["id"], None, None),
          ("Airflow", ["roles"], "perms", ["username"], None, None),
          ("bamf", [], None, ["email"], None, None)]
for tag, L in SETS.items():
    hits = []
    for t, afs, kind, cfs, lo, hi in ANCHOR:
        al = "A-admin" if kind == "admin" else "A-role"
        a = [classify(al, L[al], n) for n in afs]
        c = [classify("C", L["C"], n) for n in cfs]
        b = None
        if lo:
            hh = HARD["B-high"] if tag == "hard" else L["B-high"]
            b = (any(w in lo.lower() for w in L["B-low"]) and not any(w in lo.lower() for w in hh),
                 any(w in hi.lower() for w in L["B-high"]))
        hits.append("%s A=%s C=%s B(low,high)=%s" % (t, a, c, b))
    print(tag)
    for h in hits:
        print("   ", h)
