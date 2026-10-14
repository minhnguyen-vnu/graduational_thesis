"""Kiem hai so cua chuyen gia A.
(1) 'Co mau hieu dung ~28 API' (peer w12/w15 chi tinh A role/admin, bo perms). Dem lai voi ba dinh nghia:
    role/admin; role/admin/perms khong boolean; moi role/perms/admin.
(2) 42 op 'co ve thieu body' (peer w06, regex role|permission|privilege|admin|access level|grant tren path+summary):
    bao nhieu op chi khop nho chu 'admin' trong path."""
import re
from collections import defaultdict
from lib import *

f1, f2 = all_fields()
ff = f1 + f2


def split_of(f):
    return "test" if f["part"] == "r2" else ("dev" if f["part"] == "new-test" else "train")


ops = defaultdict(list)
for f in ff:
    ops[f["row_id"]].append(f)

defs = {
    "role/admin": lambda f: f["A"] in ("role", "admin"),
    "role/admin/perms-khong-bool": lambda f: f["A"] in ("role", "admin") or (f["A"] == "perms" and f["type"] != "boolean"),
    "role/perms/admin": lambda f: f["A"] in ("role", "perms", "admin"),
}
print("== (1) so API co op chua A (theo dinh nghia) va C cung op")
for name, pred in defs.items():
    out = {}
    for sp in ("train", "dev", "test"):
        apis = {fs[0]["spec"] for fs in ops.values() if split_of(fs[0]) == sp and any(map(pred, fs)) and any(f["C"] for f in fs)}
        out[sp] = len(apis)
    print("  %-30s %s tong=%d" % (name, out, sum(out.values())))

print("\n== (2) 42 op PUT/PATCH/POST khong co truong body, path/summary noi ve quyen")
pat = re.compile(r"role|permission|privilege|admin|access level|grant", re.I)
pat_noadmin = re.compile(r"role|permission|privilege|access level|grant", re.I)
hits = []
for rid, fs in ops.items():
    f0 = fs[0]
    if f0["method"] not in ("PUT", "PATCH", "POST"):
        continue
    if not pat.search(f0["path"] + " " + f0["summary"]):
        continue
    if not any(f["loc"] == "body" for f in fs):
        hits.append(f0)
only_admin = [h for h in hits if not pat_noadmin.search(h["path"] + " " + h["summary"])]
print("  tong %d; chi khop nho 'admin': %d; con lai (role/permission/privilege/grant): %d"
      % (len(hits), len(only_admin), len(hits) - len(only_admin)))
for h in hits:
    if h not in only_admin:
        print("    ", h["provider"], h["method"], h["path"][:75])
