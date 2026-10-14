"""Khoi 028, 031 vong 1 (doc qua grep): liet ke truong am co tu khoa quyen/chu the; so voi ty le duong o khoi khac."""
from collections import Counter
from load import *

F = [f for f in load_round(1)]
pat = ("role", "permission", "admin", "privilege", "scope", "access", "user", "member", "account", "owner", "group")
part = [f for f in F if f["chunk"] in ("028", "031")]
rest = [f for f in F if f["chunk"] not in ("028", "031")]
for f in part:
    if any(p in f["leaf"] for p in pat) and not f["A"] and not f["C"]:
        print(f["spec"], f["provider"], f["method"], f["path"][:70], f["loc"] + ":" + f["name"], f["type"], "|".join(f["enum"][:6]))
print()
for name, ff in (("khoi 028/031", part), ("khoi khac", rest)):
    ops_ = ops(ff)
    print("%s: ops=%d fields=%d A+=%d C+=%d A+/1000 truong=%.2f C+/1000=%.2f" % (
        name, len(ops_), len(ff), sum(1 for f in ff if f["A"]), sum(1 for f in ff if f["C"]),
        1000.0 * sum(1 for f in ff if f["A"]) / len(ff), 1000.0 * sum(1 for f in ff if f["C"]) / len(ff)))
print("spec trong khoi 028/031:", Counter((f["spec"], f["provider"]) for f in part))
