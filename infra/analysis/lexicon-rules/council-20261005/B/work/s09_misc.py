"""So lieu phu cho bao cao: ti le nen theo phan; nhan cu R/N; chu the khong phai user; enum bi cat 12;
cau truc cap lech McNemar; neo cho danh sach merged; so spec bi 'admin' anh huong; tin hieu tu gia tri enum;
hieu suat neu boc co muc tieu."""
import re
from collections import Counter, defaultdict
from lib import *

f1, f2 = all_fields()
allf = f1 + f2


def A(f):
    return f["A"] in ("role", "perms", "admin")


print("== (1) ti le nen theo phan")
for part in ("old", "new-train", "new-test", "r2"):
    ff = [f for f in allf if f["part"] == part]
    ops = {f["row_id"] for f in ff}
    specs = {f["spec"] for f in ff}
    print("  %-9s truong=%5d op=%4d spec=%3d | A(role/perms/admin)=%3d (%.2f%%) C=%3d (%.2f%%) | spec co A: %d/%d"
          % (part, len(ff), len(ops), len(specs), sum(map(A, ff)), 100.0 * sum(map(A, ff)) / len(ff),
             sum(1 for f in ff if f["C"]), 100.0 * sum(1 for f in ff if f["C"]) / len(ff),
             len({f["spec"] for f in ff if A(f)}), len(specs)))
old_ops = {}
for f in f1:
    if f["part"] == "old":
        old_ops[f["row_id"]] = f["old_label"]
print("  nhan cu cua 760 op phan old:", Counter(old_ops.values()))
opA = defaultdict(bool)
for f in f1:
    if f["part"] == "old" and A(f):
        opA[f["row_id"]] = True
print("  op old co A theo nhan cu:", Counter((old_ops[r], opA[r]) for r in old_ops))

print("\n== (2) chu the khong phai nguoi dung (path chua token/key/client/app/serviceprincipal)")
NONUSER = re.compile(r"token|api[-_]?key|apikey|/keys|client|/apps?\b|/applications|serviceprincipal|oauth", re.I)
for label, ff in (("train+dev", f1), ("test", f2)):
    for col, pred in (("A", A), ("C", lambda f: bool(f["C"]))):
        pos = [f for f in ff if pred(f)]
        nu = [f for f in pos if NONUSER.search(f["path"])]
        print("  %-9s %s duong %d, path chu the phi-nguoi %d (%.0f%%), nha_cc %s"
              % (label, col, len(pos), len(nu), 100.0 * len(nu) / len(pos), sorted({f['provider'] for f in nu})[:8]))

print("\n== (3) enum bi cat o 12 gia tri (MAX_ENUM)")
for label, ff in (("train+dev", f1), ("test", f2)):
    r = [f for f in ff if f["A"] in ("role", "perms") and f["enum"]]
    print("  %s: truong role/perms co enum %d, co dung 12 gia tri (co the bi cat) %d: %s"
          % (label, len(r), sum(1 for f in r if len(f["enum"]) == 12), sorted({f['provider'] + ':' + f['leaf'] for f in r if len(f['enum']) == 12})))

print("\n== (4) cap lech McNemar C (test r2): hard vs R4")
w = derive(docs(f1, "C"), "R4")[0]
dd = [(f, f["leaf"]) for f in f2 if f["leaf"] != "(body)"]
only_final = [f for f, n in dd if not f["C"] and classify("C", HARD["C"], n) and not classify("C", w, n)]
print("  only_final_correct (am, hard bat nham) = %d; ten la khac nhau %d; nha_cc %d; top ten %s"
      % (len(only_final), len({f['leaf'] for f in only_final}), len({f['provider'] for f in only_final}),
         Counter(f["leaf"] for f in only_final).most_common(8)))
print("  trong do chi do tu 'id' (khong khop tu hard nao khac): %d"
      % sum(1 for f in only_final if not classify("C", HARD["C-noid"], f["leaf"])))

print("\n== (5) neo target cho danh sach merged-R4(all) va R4")
ANCH = [("reports-api", "role", "username", "VIEWER", "ADMIN"), ("vampi", "role", "username", "user", "admin"),
        ("pyLoad", "permission", "user", None, None), ("pyLoad", "role", "user", None, None),
        ("artifact-keeper", "is_admin", "id", None, None), ("Airflow", "roles", "username", None, None),
        ("bamf", None, "email", None, None)]
for nm, src in (("R4", f1), ("merged", f1 + f2)):
    L = {n: derive(docs(src, n), "R4")[0] for n in ("A-role", "A-admin", "C", "B-low", "B-high")}
    out = []
    for t, a, c, lo, hi in ANCH:
        al = "A-admin" if a == "is_admin" else "A-role"
        out.append("%s[A:%s C:%s%s]" % (t, classify(al, L[al], a) if a else "-", classify("C", L["C"], c),
                                         " lo:%s hi:%s" % (classify("B-low", L["B-low"], lo.lower()), classify("B-high", L["B-high"], hi.lower())) if lo else ""))
    print("  %-6s %s" % (nm, " ".join(out)))

print("\n== (6) spec bi anh huong neu 'admin' vao transitionScore (op khong co A ma hay chua 'admin')")
for label, ff in (("train+dev", f1), ("test", f2)):
    ops = defaultdict(list)
    for f in ff:
        ops[f["row_id"]].append(f)
    sp = Counter()
    for rid, fs in ops.items():
        top = [f["name"] for f in fs if f["loc"] == "body" and "." not in f["name"] and "[]" not in f["name"]]
        hay = (fs[0]["path"] + " " + " ".join(top)).lower()
        if "admin" in hay and not any(map(A, fs)):
            sp[fs[0]["provider"]] += 1
    print("  %s: %d spec, %s" % (label, len(sp), sp.most_common(6)))

print("\n== (7) tin hieu tu gia tri enum: truong co enum chua tu cao (hard) - la A bao nhieu")
for label, ff in (("train+dev", f1), ("test", f2)):
    e = [f for f in ff if f["enum"] and any(any(w in v.lower() for w in ("admin", "owner", "superuser")) for v in f["enum"])]
    print("  %s: %d truong co enum chua admin/owner/superuser, trong do A role/perms %d; ten la cua A: %s; ten la cua am: %s"
          % (label, len(e), sum(1 for f in e if f["A"] in ("role", "perms")),
             Counter(f["leaf"] for f in e if f["A"]).most_common(6), Counter(f["leaf"] for f in e if not f["A"]).most_common(8)))

print("\n== (8) boc co muc tieu: spec co path chua users|members|roles|permissions|collaborators")
TGT = re.compile(r"/(users?|members?|roles?|permissions?|collaborators?|accounts?|teams?|groups?)(/|$|\{)", re.I)
for label, ff in (("train+dev", f1), ("test", f2)):
    specs = defaultdict(list)
    for f in ff:
        specs[f["spec"]].append(f)
    hit = {s for s, fs in specs.items() if any(TGT.search(f["path"]) for f in fs)}
    withA = {s for s, fs in specs.items() if any(map(A, fs))}
    print("  %s: spec %d; spec co path muc tieu %d; spec co A %d; spec co A nam trong nhom muc tieu %d; truong trong nhom muc tieu %d/%d"
          % (label, len(specs), len(hit), len(withA), len(withA & hit), sum(len(specs[s]) for s in hit), len(ff)))
