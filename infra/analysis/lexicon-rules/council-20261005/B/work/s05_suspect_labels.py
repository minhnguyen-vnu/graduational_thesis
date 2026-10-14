"""Nhan dang ngo: truong ten la dung 'role'/'roles'/'is_admin'... ma ca hai luot cung gan am;
truong C ten 'url'; va so truong co ten mang tin hieu manh trong khoi chi doc bang grep (028, 031 vong 1)."""
import re
from collections import Counter
from lib import *

f1, f2 = all_fields()

STRONG_A = re.compile(r"^(role|roles|role_id|roleid|roleids|permission|permissions|permission_level|access_level|"
                      r"is_admin|isadmin|admin|site_admin|superuser|is_superuser|scopes|privileges?)$")
print("== ten la tin hieu A manh nhung nhan cuoi am (khong A)")
for label, ff in (("r1", f1), ("r2", f2)):
    neg = [f for f in ff if STRONG_A.match(f["leaf"]) and not f["A"]]
    print("  %s: %d truong (%d op, %d nha_cc)" % (label, len(neg), len({f['row_id'] for f in neg}), len({f['provider'] for f in neg})))
    for f in neg[:40]:
        print("    - %s %s %s %s | %s %s | %s" % (f["provider"], f["row_id"], f["field"], f["type"], f["method"], f["path"][:70], f["summary"][:60]))

print("\n== C co ten la 'url'/'key'")
for label, ff in (("r1", f1), ("r2", f2)):
    for f in ff:
        if f["C"] and f["leaf"] in ("url", "key", "uid"):
            print("   %s %s %s %s | %s %s | %s" % (label, f["provider"], f["row_id"], f["field"], f["method"], f["path"][:70], f["summary"][:50]))

print("\n== khoi 028, 031 (vong 1, doc bang grep): truong duong / truong co ten tin hieu")
import os
for ch in ("028", "031"):
    ids = set()
    for line in open(os.path.join(R1, "rows", "chunk-%s.txt" % ch)):
        if line.startswith("## "):
            ids.add(line.split()[1])
    ff = [f for f in f1 if f["row_id"] in ids]
    sig = [f for f in ff if re.search(r"role|permission|admin|scope|privilege|access|user|member|account|email|login", f["leaf"])]
    print("  chunk %s: %d op, %d truong, spec %s, duong A=%d C=%d, ten co tin hieu=%d"
          % (ch, len(ids), len(ff), sorted({f['spec'] for f in ff}), sum(1 for f in ff if f["A"]), sum(1 for f in ff if f["C"]), len(sig)))
    print("     ten tin hieu (nhan cuoi am):", Counter(f["leaf"] for f in sig if not f["A"] and not f["C"]).most_common(20))
