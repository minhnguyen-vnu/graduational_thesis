"""Do dong y cua nhan B (khong co trong kappa-raw.json) va so phan xu dong vao B."""
from lib import *

for rnd, d in ((1, R1), (2, R2)):
    _, l1, l2, adj = final_labels(d)
    keys = [k for k in set(l1) | set(l2)
            if (l1.get(k, {}).get("B_low") or l2.get(k, {}).get("B_low"))]
    same_low = sum(1 for k in keys if l1.get(k, {}).get("B_low", "") == l2.get(k, {}).get("B_low", ""))
    same_high = sum(1 for k in keys if l1.get(k, {}).get("B_high", "") == l2.get(k, {}).get("B_high", ""))
    print("vong %d: truong co B o it nhat mot luot %d; trung B_low %d; trung B_high %d" % (rnd, len(keys), same_low, same_high))
    for k in sorted(keys):
        a, b = l1.get(k, {}), l2.get(k, {})
        if a.get("B_low", "") != b.get("B_low", "") or a.get("B_high", "") != b.get("B_high", ""):
            print("   ", k, "L1=%s/%s" % (a.get("B_low", ""), a.get("B_high", "")), "L2=%s/%s" % (b.get("B_low", ""), b.get("B_high", "")),
                  "phan xu=%s" % (adj[k]["final"] if k in adj else "-"))
