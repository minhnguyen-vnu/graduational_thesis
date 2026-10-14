"""Operation PUT/PATCH/POST co summary/path noi ve quyen nhung khong co truong body nao duoc trich.
Spec tho khong co trong goi, nen day chi la dau hieu, khong kiem duoc truc tiep."""
import re
from collections import Counter
from load import *

F = load_all()
pat = re.compile(r"role|permission|privilege|admin|access level|grant", re.I)
hits = []
for rid, ff in ops(F).items():
    f0 = ff[0]
    if f0["method"] not in ("PUT", "PATCH", "POST"):
        continue
    if not pat.search(f0["path"] + " " + f0["summary"]):
        continue
    body = [f for f in ff if f["loc"] == "body"]
    if not body:
        hits.append((f0["split"], f0["provider"], f0["method"], f0["path"], f0["summary"][:70],
                     [f["name"] for f in ff]))
print("so op:", len(hits), Counter(h[0] for h in hits))
for h in hits:
    print(" ", h)
