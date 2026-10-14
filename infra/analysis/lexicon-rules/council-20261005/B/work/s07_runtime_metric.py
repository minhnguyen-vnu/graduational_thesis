"""Do theo cach builder dung danh sach luc chay (xap xi, khong chay EvoMaster):
- Don vi la operation 'transition' (co >=1 truong A role/perms/admin VA >=1 truong C), khong phai tung truong.
- A: op co it nhat mot truong A that duoc danh sach bat khong (dieu kien de harvestReducedRoleCandidates != rong,
  RestSecurityBuilder.kt:958-967); bao nhieu truong khong-A cung bi bat (setAllRoleFieldsTo ghi de, :1290-1316).
- C: mo phong setUserInParams (:1053-1077): path truoc, roi body; trong moi nhom thu tu specific -> email -> id;
  truong dau tien khop co phai truong C that khong (top-1).
Mot nha cung cap co nhieu op: bao them so nha cung cap."""
from collections import defaultdict
from lib import *

f1, f2 = all_fields()
H_ROLE = HARD["A-role"]
H_ADMIN = HARD["A-admin"]
H_USER = ["username", "userid", "user_id", "user", "account", "member", "subject", "principal", "id"]
H_EMAIL = ["email"]
LISTS = {
    "hard": dict(role=H_ROLE, admin=H_ADMIN, user=H_USER, email=H_EMAIL),
    "hard-noid": dict(role=H_ROLE, admin=H_ADMIN, user=[w for w in H_USER if w != "id"], email=H_EMAIL),
}
f_r1_all = f1
for r in ("R0", "R4"):
    LISTS["derived-%s" % r] = dict(role=derive(docs(f1, "A-role"), r)[0], admin=derive(docs(f1, "A-admin"), r)[0],
                                   user=derive(docs(f1, "C"), r)[0], email=[])
# danh sach R4 rut tren ca ba tap (merged-lists.json) - de xem, khong co tap do
LISTS["merged-R4(all)"] = dict(role=derive(docs(f1 + f2, "A-role"), "R4")[0], admin=derive(docs(f1 + f2, "A-admin"), "R4")[0],
                               user=derive(docs(f1 + f2, "C"), "R4")[0], email=[])
for k, v in LISTS.items():
    print("%-15s %s" % (k, v))


def m(n, ws):
    return any(n == w or w in n for w in ws)


def ops_of(ff):
    d = defaultdict(list)
    for f in ff:
        d[f["row_id"]].append(f)
    return d


def evaluate(ff, label):
    ops = ops_of(ff)
    trans = {k: v for k, v in ops.items()
             if any(f["A"] in ("role", "perms", "admin") for f in v) and any(f["C"] for f in v)}
    print("\n== %s: %d op transition (A va C), %d nha_cc" % (label, len(trans), len({v[0]['provider'] for v in trans.values()})))
    for name, L in LISTS.items():
        a_hit = a_any = fp_fields = c_top1 = c_any = c_wrong = 0
        prov_hit = set()
        for rid, fs in trans.items():
            named = [f for f in fs if f["leaf"] != "(body)"]
            role_m = [f for f in named if m(f["leaf"], L["role"])]
            adm_m = [f for f in named if f["type"] == "boolean" and m(f["leaf"], L["admin"])]
            matched = role_m + adm_m
            if matched:
                a_any += 1
            if any(f["A"] in ("role", "perms", "admin") for f in matched):
                a_hit += 1
                prov_hit.add(fs[0]["provider"])
            fp_fields += sum(1 for f in role_m if not f["A"])
            # C: setUserInParams path -> body; signals specific, email, id
            spec = [w for w in L["user"] if w != "id"]
            groups = [spec, L["email"]] + ([["id"]] if "id" in L["user"] else [])
            pick = None
            for loc in ("path", "body"):
                for sig in groups:
                    for f in named:
                        if f["loc"] == loc and sig and m(f["leaf"], sig):
                            pick = f
                            break
                    if pick:
                        break
                if pick:
                    break
            if pick is None:  # setInQueryParamsTopLevel voi transitionUserParamSignals
                for f in named:
                    if f["loc"] == "query" and m(f["leaf"], L["user"]):
                        pick = f
                        break
            if pick is not None:
                c_any += 1
                if pick["C"]:
                    c_top1 += 1
                else:
                    c_wrong += 1
        n = len(trans)
        print("  %-15s A: op bat dung >=1 truong A %d/%d (nha_cc %d), op bat gi do %d, truong khong-A bi bat %d | "
              "C top-1 dung %d/%d, chon sai %d, khong chon %d"
              % (name, a_hit, n, len(prov_hit), a_any, fp_fields, c_top1, n, c_wrong, n - c_any))


evaluate([f for f in f1 if f["split"] == "test"], "dev (nua test vong 1)")
evaluate(f2, "test vong 2")
