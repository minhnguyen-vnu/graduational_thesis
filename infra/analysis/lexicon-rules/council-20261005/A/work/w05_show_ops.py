"""In mot vai operation (method, path, truong, nhan cuoi) theo tu khoa duong dan."""
import sys
from load import *

F = load_all()
keys = sys.argv[1:] or ["permissions-config"]
for rid, ff in ops(F).items():
    f0 = ff[0]
    if any(k in f0["path"] for k in keys):
        print("==", rid, f0["provider"], f0["split"], f0["method"], f0["path"], "|", f0["summary"][:80])
        for f in ff:
            lab = "/".join(x for x in (f["A"], f["B_low"], f["B_high"], f["C"]))
            print("   %-6s %-45s %-14s %-40s %s" % (f["loc"], f["name"][:45], f["type"][:14], "|".join(f["enum"])[:40],
                                                   lab if lab.strip("/") else ""))
