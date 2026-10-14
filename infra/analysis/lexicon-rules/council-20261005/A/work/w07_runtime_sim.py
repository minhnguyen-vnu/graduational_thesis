"""Mo phong xap xi cach RestSecurityBuilder.kt dung cac danh sach, de do o don vi runtime thuc su dung
(operation/API), khong phai tung truong doc lap.

Xap xi (chua kiem tren EvoMaster that):
- ten gene = ten la ha chu (leaf); allGenes = moi truong path/query/body cua operation.
- transitionHay = path + " " + method:path + " " + ten truong body tang dau (khong co '.').
- trySetFromStringValue thanh cong voi kieu string/integer/number, that bai voi object/array/boolean.
- routeLooksMissing, victimRoleValues, ma trang thai HTTP: bo qua.
"""
import csv, os
from collections import Counter, defaultdict
from load import *

LEX = os.path.join(HERE, "..", "code", "stateful-authz-lexicon.csv")
PATH_LEX = [(r["word"].lower(), float(r["score"])) for r in csv.DictReader(open(LEX)) if r["kind"] == "path"]
PARAM_LEX = [(r["word"].lower(), float(r["score"])) for r in csv.DictReader(open(LEX)) if r["kind"] == "param"]
MAX_TRANSITION_CANDIDATES = 8
VERB_ORDER = ["PUT", "PATCH", "POST", "DELETE"]

F = load_all()
OPS = ops(F)
TD = [f for f in F if f["split"] in ("train", "dev")]


def mk(name, dd):
    return derive(dd, "R4")[0]


LISTSETS = {
    "hard": {"role": HARD["A-role"], "admin": HARD["A-admin"], "spec": HARD["C-specific"], "email": ["email"],
             "id": ["id"], "low": HARD["B-low"], "high": HARD["B-high"]},
}
for tag, ff in (("R4_train+dev", TD), ("R4_all", F)):
    LISTSETS[tag] = {"role": mk("A-role", docs(ff, "A-role")), "admin": mk("A-admin", docs(ff, "A-admin")),
                     "spec": mk("C", docs(ff, "C")), "email": [], "id": [],
                     "low": mk("B-low", docs(ff, "B-low")), "high": mk("B-high", docs(ff, "B-high"))}
    # bien the: danh sach rut + lop du phong email, id cua ban viet tay
    LISTSETS[tag + "+fallback"] = dict(LISTSETS[tag], email=["email"], id=["id"])
for k, v in LISTSETS.items():
    print(k, {x: v[x] for x in ("role", "admin", "spec", "low", "high")})


def m(n, words):
    return any(n == w or w in n for w in words)


def hay(op):
    f0 = op[0]
    top = [f["raw_leaf"] for f in op if f["loc"] == "body" and "." not in f["name"]]
    return (f0["path"] + " " + f0["method"] + ":" + f0["path"] + " " + " ".join(top)).lower()


def transition_score(op, L):
    h = hay(op)
    p = max([s for w, s in PATH_LEX if w in h] or [0.0])
    a = 0.6 if any(w in h for w in L["admin"]) else 0.0
    return max(p, a)


def has_user_param(op):
    return any(any(f["leaf"] == w or w in f["leaf"] for w, _ in PARAM_LEX) for f in op)


def role_genes(op, L):
    return [f for f in op if f["leaf"] != "(body)" and m(f["leaf"], L["role"])]


def admin_genes(op, L):
    return [f for f in op if f["type"] == "boolean" and any(w in f["leaf"] for w in L["admin"])]


def is_low(v, L):
    lv = v.lower()
    return any(w in lv for w in L["low"]) and not any(w in lv for w in L["high"])


def reduced_candidates(op, L):
    rg, ag = role_genes(op, L), admin_genes(op, L)
    if not rg and not ag:
        return []
    vocab = []
    for f in op:
        for v in f["enum"]:
            if v not in vocab:
                vocab.append(v)
    low = [v for v in vocab if is_low(v, L)]
    out = (["false"] if ag else []) + low
    if any(f["type"].startswith("array") for f in rg):
        out.append("[]")
    if any(f["type"] in ("integer", "number") for f in rg):
        out += ["1", "0", "2"]
    out += [v for v in vocab if v not in low]
    if any(f["type"] == "string" for f in rg):
        out += ["user", "viewer", "guest", "member", "basic"]
    seen, res = set(), []
    for v in out:
        if v not in seen:
            seen.add(v)
            res.append(v)
    return res


SETTABLE = ("string", "integer", "number")


def pick_victim(op, L):
    groups = [g for g in (L["spec"], L["email"], L["id"]) if g]
    for loc in ("path", "body"):
        params = [f for f in op if f["loc"] == loc and f["leaf"] != "(body)"]
        for sig in groups:
            for f in params:
                if m(f["leaf"], sig) and f["type"] in SETTABLE:
                    return f
    allsig = [w for g in groups for w in g]
    for f in op:
        if f["loc"] == "query" and m(f["leaf"], allsig) and f["type"] in SETTABLE:
            return f
    return None


def true_transition(op):
    return any(f["A"] in ("role", "perms", "admin") for f in op)


# ---------------------------------------------------------------- 1. chon transition theo API
print("\n# 1. Chon transition o muc API (spec). API co it nhat mot op mang truong A role/perms/admin.")
by_spec = defaultdict(list)
for rid, op in OPS.items():
    by_spec[(op[0]["split"], op[0]["spec"])].append(op)

for split in ("train", "dev", "test"):
    specs = {s: v for (sp, s), v in by_spec.items() if sp == split}
    pos_specs = [s for s, v in specs.items() if any(true_transition(op) for op in v)]
    print(" split=%s: %d API, %d API co op A" % (split, len(specs), len(pos_specs)))
    for tag, L in LISTSETS.items():
        if tag.endswith("+fallback"):
            continue
        first_true = any_true = n_viable_api = victim_ok = 0
        false_first = 0
        for s, oplist in specs.items():
            ranked = [op for op in oplist if op[0]["method"] in VERB_ORDER and transition_score(op, L) > 0]
            ranked.sort(key=lambda op: (-transition_score(op, L), not has_user_param(op), VERB_ORDER.index(op[0]["method"])))
            viable = [op for op in ranked[:MAX_TRANSITION_CANDIDATES] if reduced_candidates(op, L)]
            if viable:
                n_viable_api += 1
            if s in pos_specs:
                if viable and true_transition(viable[0]):
                    first_true += 1
                    v = pick_victim(viable[0], L)
                    if v is not None and v["C"]:
                        victim_ok += 1
                if any(true_transition(op) for op in viable):
                    any_true += 1
            else:
                if viable:
                    false_first += 1
        print("   %-14s API co ung vien viable=%2d | API co A: op dau la A=%2d, mot trong <=8 la A=%2d,"
              " op dau la A va nan nhan dung=%2d | API khong A nhung co ung vien=%2d" % (
                  tag, n_viable_api, first_true, any_true, victim_ok, false_first))

# ---------------------------------------------------------------- 2. tac dong phu cua A-admin len transitionScore
print("\n# 2. A-admin trong transitionScore (RestSecurityBuilder.kt:108-112): op ghi co diem >0 chi nho danh sach admin")
for tag, L in LISTSETS.items():
    if tag.endswith("+fallback"):
        continue
    only_admin = top_by_admin = 0
    for rid, op in OPS.items():
        h = hay(op)
        p = max([s for w, s in PATH_LEX if w in h] or [0.0])
        a = any(w in h for w in L["admin"])
        if a and p == 0:
            only_admin += 1
        if a and p < 0.6:
            top_by_admin += 1
    print("   %-14s admin=%s: op chi co diem nho admin=%d, op duoc day len 0.6=%d (tren %d op)" % (
        tag, L["admin"], only_admin, top_by_admin, len(OPS)))

# ---------------------------------------------------------------- 3. chon nan nhan tren op co ca A va C
print("\n# 3. Chon truong nan nhan (setUserTargetToVictim, :1053-1077) tren op co truong A va truong C")
for split in ("train", "dev", "test"):
    cand = [op for op in OPS.values() if op[0]["split"] == split and true_transition(op) and any(f["C"] for f in op)]
    res = {}
    for tag, L in LISTSETS.items():
        ok = none = wrong = 0
        for op in cand:
            v = pick_victim(op, L)
            if v is None:
                none += 1
            elif v["C"]:
                ok += 1
            else:
                wrong += 1
        res[tag] = (ok, wrong, none)
    print("   split=%s n=%d  (dung, sai truong, khong chon duoc): %s" % (split, len(cand), res))

# ---------------------------------------------------------------- 4. tim truong role o muc operation
print("\n# 4. Tim truong role/admin o muc operation (harvestReducedRoleCandidates khac rong)")
for split in ("train", "dev", "test"):
    oo = [op for op in OPS.values() if op[0]["split"] == split]
    pos = [op for op in oo if true_transition(op)]
    neg = [op for op in oo if not true_transition(op)]
    row = {}
    for tag, L in LISTSETS.items():
        if tag.endswith("+fallback"):
            continue
        tp = sum(1 for op in pos if reduced_candidates(op, L))
        fp = sum(1 for op in neg if reduced_candidates(op, L))
        p, r, f1 = prf_counts(tp, fp, len(pos) - tp)
        row[tag] = "tp=%d fp=%d fn=%d P=%.2f R=%.2f F1=%.2f" % (tp, fp, len(pos) - tp, p, r, f1)
    print("   split=%s op A=%d op khong A=%d" % (split, len(pos), len(neg)))
    for k, v in row.items():
        print("      %-14s %s" % (k, v))

# ---------------------------------------------------------------- 5. thu tu gia tri ha quyen
print("\n# 5. Gia tri ha quyen: hang cua B_low trong danh sach ung vien (1 = thu dau tien)")
for tag, L in LISTSETS.items():
    if tag.endswith("+fallback"):
        continue
    ranks = []
    for op in OPS.values():
        for f in op:
            if f["A"] in ("role", "perms") and f["enum"] and f["B_low"] not in ("", "unordered"):
                c = reduced_candidates(op, L)
                r = c.index(f["B_low"]) + 1 if f["B_low"] in c else None
                ranks.append((f["split"], r))
    for split in ("train", "dev", "test"):
        rr = [r for s, r in ranks if s == split]
        print("   %-14s %-5s n=%2d hang1=%2d hang<=3=%2d khong co=%2d" % (
            tag, split, len(rr), sum(1 for r in rr if r == 1), sum(1 for r in rr if r and r <= 3),
            sum(1 for r in rr if r is None)))
