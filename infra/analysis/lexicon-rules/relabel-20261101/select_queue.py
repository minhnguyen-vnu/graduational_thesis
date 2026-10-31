import csv, glob, hashlib, json, math, os, random, re, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("RELABEL_WORK", HERE)
LR = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(LR, "lexicon-r4-20261007"))
sys.path.insert(0, os.path.join(LR, "field-ranking-20261007"))
import measure as M

X, R = M.X, M.R
SEED = 20261101
MODEL = "/Users/minhnguyen/IdeaProjects/EvoMaster/core/src/main/resources/stateful-authz-model.csv"
VERBS = ("POST", "PUT", "PATCH", "DELETE")
CORE_B = {"role_set", "role_remove", "perm", "admin_flag", "member_role", "member_remove"}
SAME_COMPANY = ("1password", "apigee", "redhat")
BUDGET_TOTAL = 507
BUDGET_PILOT = 20
BUDGET_M2 = 30
TOP4_CAP = 80
LECH_CAP = 100
BOTH_T = 30
OLD_T_NEW_N = 15
BAND_MAX = 120
SECONDS_PER_ROW = 79
QUEUE_COLUMNS = ["stt", "method", "path", "mo_ta", "schema", "truong", "A", "B", "C", "U", "victim", "role", "order"]


def t_core(r):
    return r["A"] in ("existing", "self") and r["B"] in CORE_B and r["C"] in ("down", "unclear")


def norm(v):
    return "|".join(sorted(x.strip() for x in v.split("|") if x.strip()))


def load_lane(lane, stage, names=None):
    out = {}
    for fn in sorted(glob.glob(os.path.join(WORK, lane, stage, "chunk-*.csv"))):
        if names is not None and os.path.basename(fn)[:-4] not in names:
            continue
        with open(fn, newline="") as fh:
            for r in csv.DictReader(fh):
                out[r["row_id"]] = r
    return out


def cohen(a, b, keys):
    n = len(keys)
    if not n:
        return None
    pa = sum(t_core(a[k]) for k in keys) / n
    pb = sum(t_core(b[k]) for k in keys) / n
    po = sum(t_core(a[k]) == t_core(b[k]) for k in keys) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe == 1 else (po - pe) / (1 - pe)


def op_feats(op):
    fs = {"v:" + op["method"]}
    fs |= {"p:" + t for t in X.tokens(op["path"])}
    for f in op["fields"]:
        if f["loc"] in ("path", "query", "body"):
            fs |= {"f:" + t for t in X.tokens(f["raw_leaf"])}
    return fs


def field_feats(f):
    fs = {"k:" + f["kind"], "l:" + f["loc"], "w:" + f["leaf"]}
    fs |= {"n:" + t for t in X.tokens(f["raw_leaf"])}
    for p in [p.replace("[]", "") for p in f["name"].split(".")[:-1]]:
        fs |= {"a:" + t for t in X.tokens(p)}
    for v in f["enum"]:
        fs |= {"e:" + t for t in X.tokens(str(v))}
    return fs


def nb(docs):
    npos = sum(1 for _, _, pos in docs if pos)
    nneg = len(docs) - npos
    dp, dn, pv = defaultdict(int), defaultdict(int), defaultdict(set)
    for fs, prov, pos in docs:
        for t in fs:
            if pos:
                dp[t] += 1
                pv[t].add(prov)
            else:
                dn[t] += 1
    w = {t: math.log((dp[t] + 1) / (npos + 2)) - math.log((dn[t] + 1) / (nneg + 2)) for t in dp if len(pv[t]) >= 2}
    return w, math.log(max(npos, 1) / max(nneg, 1))


def company(p):
    base = re.split(r"[.:]", p)[0].lower()
    return base if base in SAME_COMPANY else p


def oof_scores(ops, final_t):
    groups = sorted({company(o["provider"]) for o in ops})
    random.Random(SEED).shuffle(groups)
    fold = {g: i % 5 for i, g in enumerate(groups)}
    feats = {o["row_id"]: op_feats(o) for o in ops}
    scores = {}
    for k in range(5):
        docs = [(feats[o["row_id"]], o["provider"], final_t[o["row_id"]]) for o in ops
                if fold[company(o["provider"])] != k and o["row_id"] in final_t]
        w, prior = nb(docs)
        for o in ops:
            if fold[company(o["provider"])] == k:
                scores[o["row_id"]] = prior + sum(w.get(t, 0.0) for t in feats[o["row_id"]])
    return scores


def load_m1():
    tables = defaultdict(dict)
    for r in csv.DictReader(open(MODEL)):
        tables[r["table"]][r["feature"]] = float(r["weight"])
    return tables["op"], tables["role"]


def top4(tops, op_w, role_w):
    usable = []
    for o in tops:
        s = op_w["__prior__"] + sum(op_w.get(t, 0.0) for t in op_feats(o))
        if s <= 0:
            continue
        if any(role_w["__prior__"] + sum(role_w.get(t, 0.0) for t in field_feats(f)) > 0
               for f in o["fields"][:80] if f["loc"] != "path"):
            usable.append((s, o))
    usable.sort(key=lambda x: -x[0])
    return usable[:4]


def rows_by_id(path):
    return {r["row_id"]: r for r in (json.loads(l) for l in open(path))}


def human_row(stt, r):
    fields = "\n".join("%s:%s %s%s" % (f["loc"], f["name"], f["type"], " enum[%s]" % "|".join(f["enum"]) if f["enum"] else "")
                       for f in r["fields"])
    d = (r.get("summary") or "") + (" | " if r.get("summary") and r.get("description") else "") + (r.get("description") or "")
    return {"stt": stt, "method": r["method"], "path": r["path"], "mo_ta": d[:400], "schema": r.get("schema") or "",
            "truong": fields, "A": "", "B": "", "C": "", "U": "", "victim": "", "role": "", "order": ""}


def write_queue(name, items, rows, seed):
    rng = random.Random(seed)
    rng.shuffle(items)
    os.makedirs(os.path.join(WORK, "handover"), exist_ok=True)
    os.makedirs(os.path.join(WORK, "sealed"), exist_ok=True)
    with open(os.path.join(WORK, "handover", name + ".csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, QUEUE_COLUMNS)
        w.writeheader()
        for i, (rid, _) in enumerate(items, 1):
            w.writerow(human_row(i, rows[rid]))
    with open(os.path.join(WORK, "sealed", "key-" + name + ".csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["stt", "row_id", "tang"])
        for i, (rid, tier) in enumerate(items, 1):
            w.writerow([i, rid, tier])


def gate():
    names = {"chunk-%03d" % i for i in range(1, 6)}
    a, b = load_lane("A", "train", names), load_lane("B", "train", names)
    keys = sorted(set(a) & set(b))
    print("dong", len(keys), "A T_core", sum(t_core(a[k]) for k in keys), "B T_core", sum(t_core(b[k]) for k in keys),
          "lech", sum(t_core(a[k]) != t_core(b[k]) for k in keys), "kappa", cohen(a, b, keys))
    print("A B", Counter(a[k]["B"] for k in keys).most_common())
    print("B B", Counter(b[k]["B"] for k in keys).most_common())
    print("U A", sum(a[k]["U"] == "1" for k in keys), "U B", sum(b[k]["U"] == "1" for k in keys))


def train_part(report, pilot_ids):
    manifest = json.load(open(os.path.join(WORK, "manifest.json")))
    rows = rows_by_id(os.path.join(LR, "field-labelling-r4-20261006", "rows-all.jsonl"))
    a, b = load_lane("A", "train"), load_lane("B", "train")
    all_ids = [i for c in manifest["train"].values() for i in c]
    missing_specs = {rows[i]["spec_id"] for i in all_ids if i in rows and not (i in a and i in b)}
    keys = [i for i in all_ids if i in rows and rows[i]["spec_id"] not in missing_specs]
    lech_t = [k for k in keys if t_core(a[k]) != t_core(b[k])]
    both = [k for k in keys if t_core(a[k]) and t_core(b[k])]
    lech_col = [k for k in both if any(norm(a[k][c]) != norm(b[k][c]) for c in ("victim", "role", "order"))]
    agree_t = [k for k in both if k not in set(lech_col)]
    both_n = [k for k in keys if not t_core(a[k]) and not t_core(b[k])]
    lab, ops, _, _ = X.new_data()
    rng = random.Random(SEED)
    pick_lech = rng.sample(sorted(lech_t), len(lech_t)) + rng.sample(sorted(lech_col), len(lech_col))
    overflow = pick_lech[LECH_CAP:]
    pick_lech = [k for k in pick_lech[:LECH_CAP] if k not in pilot_ids]
    pool_t = sorted(k for k in agree_t if k not in pilot_ids)
    pick_t = rng.sample(pool_t, min(BOTH_T, len(pool_t)))
    pool_old = sorted(k for k in both_n if lab.get(k, {}).get("T") and k not in pilot_ids)
    pick_old = rng.sample(pool_old, min(OLD_T_NEW_N, len(pool_old)))
    final_t = {k: True for k in agree_t}
    final_t.update({k: False for k in both_n})
    scores = oof_scores([o for o in ops if o["row_id"] in rows], final_t)
    report["train_keys"] = len(keys)
    report["train_missing_specs"] = len(missing_specs)
    report["train_kappa"] = cohen(a, b, keys)
    report["train_A_T"] = sum(t_core(a[k]) for k in keys)
    report["train_B_T"] = sum(t_core(b[k]) for k in keys)
    report["train_lech_t"] = len(lech_t)
    report["train_lech_col"] = len(lech_col)
    report["train_agree_t"] = len(agree_t)
    report["train_overflow"] = len(overflow)
    report["train_old_t_new_n_all"] = len(pool_old)
    report["train_old_t"] = sum(1 for k in keys if lab.get(k, {}).get("T"))
    report["train_U"] = (sum(a[k]["U"] == "1" for k in keys), sum(b[k]["U"] == "1" for k in keys))
    with open(os.path.join(WORK, "sealed", "train-overflow.csv"), "w") as fh:
        fh.write("row_id\n" + "".join(k + "\n" for k in overflow))
    return rows, pick_lech, pick_t, pick_old, both_n, scores


def test_part(report):
    manifest = json.load(open(os.path.join(WORK, "manifest.json")))
    rows = rows_by_id(os.path.join(WORK, "rows-test.jsonl"))
    a, b = load_lane("A", "test"), load_lane("B", "test")
    all_ids = [i for c in manifest["test"].values() for i in c]
    missing_specs = {rows[i]["spec_id"] for i in all_ids if not (i in a and i in b)}
    keys = [i for i in all_ids if rows[i]["spec_id"] not in missing_specs]
    t_rows = [k for k in keys if t_core(a[k]) or t_core(b[k])]
    op_w, role_w = load_m1()
    specs = sorted({rows[k]["spec_id"] for k in keys})
    random.Random(SEED + 10).shuffle(specs)
    tops = {}
    for sid in specs:
        got = R.spec_ops(os.path.join(WORK, "test-specs", sid + ".json"))
        got = [o for o in got if o["method"] in VERBS]
        tops[sid] = ["%s-N%04d" % (sid, o["pos"]) for _, o in top4(got, op_w, role_w)]
    with open(os.path.join(WORK, "sealed", "test-top4-m1.json"), "w") as fh:
        json.dump(tops, fh, indent=0)
    t_set = set(t_rows)
    pick_top = []
    for sid in specs:
        extra = [k for k in tops[sid] if k not in t_set]
        if len(pick_top) + len(extra) > TOP4_CAP:
            break
        pick_top.extend(extra)
    chosen = t_set | set(pick_top) | {k for v in tops.values() for k in v}
    pool = sorted(k for k in keys if k not in chosen)
    n_noise = round((len(t_rows) + len(pick_top)) / 5)
    pick_noise = random.Random(SEED + 11).sample(pool, min(n_noise, len(pool)))
    report["test_keys"] = len(keys)
    report["test_specs"] = len(specs)
    report["test_missing_specs"] = len(missing_specs)
    report["test_kappa"] = cohen(a, b, keys)
    report["test_A_T"] = sum(t_core(a[k]) for k in keys)
    report["test_B_T"] = sum(t_core(b[k]) for k in keys)
    report["test_lech_t"] = sum(t_core(a[k]) != t_core(b[k]) for k in keys)
    report["test_spec_T"] = len({rows[k]["spec_id"] for k in t_rows})
    report["test_specs_with_top4"] = sum(1 for v in tops.values() if v)
    report["test_top4_all"] = sum(len([k for k in v if k not in t_set]) for v in tops.values())
    report["test_U"] = (sum(a[k]["U"] == "1" for k in keys), sum(b[k]["U"] == "1" for k in keys))
    return rows, t_rows, pick_top, pick_noise


def seals():
    paths = [os.path.join(WORK, p) for p in ("GUIDE.md", "PROTOCOL.md", "manifest.json", "test-specs.json", "rows-test.jsonl", "rows-known.jsonl")]
    for pat in ("A/test/*.csv", "B/test/*.csv", "A/known/*.csv", "B/known/*.csv", "A/train/*.csv", "B/train/*.csv",
                "handover/*.csv", "sealed/*"):
        paths.extend(sorted(glob.glob(os.path.join(WORK, pat))))
    with open(os.path.join(WORK, "SEALS.txt"), "w") as fh:
        for p in paths:
            if os.path.exists(p):
                fh.write("%s  %s\n" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.relpath(p, WORK)))
    return len(paths)


def pilot_part():
    path = os.path.join(WORK, "sealed", "pilot-answers.csv")
    if not os.path.exists(path):
        raise SystemExit("HONG: thieu sealed/pilot-answers.csv")
    return [r["row_id"] for r in csv.DictReader(open(path))]


def usage_summary(report):
    p = os.path.join(WORK, "usage.csv")
    if not os.path.exists(p):
        return
    lines = [l.strip().split(",") for l in open(p)]
    report["usage_blocks"] = len(lines)
    report["usage_usd"] = round(sum(float(l[10] or 0) for l in lines), 2)
    report["usage_first"] = lines[0][0]
    report["usage_last"] = lines[-1][0]
    report["seven_day_last"] = lines[-1][12]


def write_report(r, counts):
    lines = ["# Báo cáo phần AI, đợt gán lại", "",
             "Số dòng người gán dưới đây là số thật sau khi AI gán xong. Mức 79 giây một dòng là giá của phiếu cũ.", "",
             "## Hai lượt AI", "",
             "| Phần | Dòng | Bộ thiếu nhãn, đã loại | Sonnet T_core | Opus T_core | Lệch T_core | Cohen kappa | U Sonnet / Opus |",
             "|---|---|---|---|---|---|---|---|",
             "| Train | %d | %d | %d | %d | %d | %.3f | %d / %d |" % (r["train_keys"], r["train_missing_specs"], r["train_A_T"], r["train_B_T"], r["train_lech_t"], r["train_kappa"] or 0, *r["train_U"]),
             "| Test | %d | %d | %d | %d | %d | %.3f | %d / %d |" % (r["test_keys"], r["test_missing_specs"], r["test_A_T"], r["test_B_T"], r["test_lech_t"], r["test_kappa"] or 0, *r["test_U"]),
             "",
             "Train: hai AI cùng T và khớp cột %d dòng; cùng T nhưng lệch `victim`, `role` hoặc `order` %d dòng; nhãn cũ T %d dòng." % (r["train_agree_t"], r["train_lech_col"], r["train_old_t"]),
             "Test: %d bộ có op T theo ít nhất một AI; %d bộ có ứng viên top-4 P2f; %d dòng top-4 ngoài nhóm AI gọi T." % (r["test_spec_T"], r["test_specs_with_top4"], r["test_top4_all"]),
             "Trên 8 transition biết đáp án: Sonnet nhận T_core %d, Opus %d." % (r["known_A"], r["known_B"]),
             "", "## Hàng đợi người gán", "",
             "| Nhóm | Dự toán | Số thật |", "|---|---|---|"]
    for name, plan, real in counts:
        lines.append("| %s | %s | %d |" % (name, plan, real))
    total = sum(c[2] for c in counts)
    lines += ["| Tổng | 507 | %d |" % total, "",
              "Khoảng %.1f giờ theo 79 giây một dòng." % (total * SECONDS_PER_ROW / 3600),
              "Train lệch vượt trần 100: %d dòng, loại khỏi huấn luyện theo §2 (`sealed/train-overflow.csv`)." % r["train_overflow"],
              "", "## Chi phí", "",
              "%s khối, quy đổi %s USD, từ %s tới %s, quota tuần lúc cuối %s." % (r.get("usage_blocks"), r.get("usage_usd"), r.get("usage_first"), r.get("usage_last"), r.get("seven_day_last")),
              ""]
    with open(os.path.join(WORK, "AI-REPORT.md"), "w") as fh:
        fh.write("\n".join(lines))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "gate":
        gate()
        return
    report = {}
    pilot_ids = pilot_part()
    os.makedirs(os.path.join(WORK, "sealed"), exist_ok=True)
    train_rows, pick_lech, pick_t, pick_old, both_n, scores = train_part(report, set(pilot_ids))
    test_rows, t_rows, pick_top, pick_noise = test_part(report)
    known_rows = rows_by_id(os.path.join(WORK, "rows-known.jsonl"))
    ka, kb = load_lane("A", "known"), load_lane("B", "known")
    pos = [k for k, r in known_rows.items() if r["known_positive"]]
    report["known_A"] = sum(1 for k in pos if k in ka and t_core(ka[k]))
    report["known_B"] = sum(1 for k in pos if k in kb and t_core(kb[k]))
    test_items = [(k, "T") for k in t_rows] + [(k, "top4") for k in pick_top] + [(k, "nhieu") for k in pick_noise] + [(k, "biet") for k in known_rows]
    write_queue("test-queue", test_items, {**test_rows, **known_rows}, SEED + 20)
    used = set(pick_lech) | set(pick_t) | set(pick_old) | set(pilot_ids)
    n_band = BUDGET_TOTAL - BUDGET_PILOT - BUDGET_M2 - len(test_items) - len(pick_lech) - len(pick_t) - len(pick_old)
    n_band = max(0, min(BAND_MAX, n_band))
    band = sorted((k for k in both_n if k not in used and k in scores), key=lambda k: (-scores[k], k))[:n_band]
    train_items = [(k, "lech") for k in pick_lech] + [(k, "cung_T") for k in pick_t] + [(k, "cu_T_moi_N") for k in pick_old] + [(k, "N_diem_cao") for k in band]
    write_queue("train-queue", train_items, train_rows, SEED + 21)
    pilot_items = [(k, "pilot") for k in pilot_ids]
    write_queue("pilot", pilot_items, train_rows, SEED + 22)
    counts = [("Pilot", 20, len(pilot_ids)), ("Test: AI gọi T", 130, len(t_rows)), ("Test: top-4 P2f AI không gọi T", 80, len(pick_top)),
              ("Test: ngẫu nhiên", 42, len(pick_noise)), ("Test: biết đáp án", 16, len(known_rows)),
              ("Test: top-4 mô hình mới, làm sau", 30, BUDGET_M2),
              ("Train: hai AI lệch", 100, len(pick_lech)), ("Train: hai AI cùng T", 30, len(pick_t)),
              ("Train: cũ T, mới N", 15, len(pick_old)), ("Train: N điểm cao", 44, len(band))]
    usage_summary(report)
    write_report(report, counts)
    n = seals()
    print("select_queue xong: test %d dong, train %d dong, pilot %d dong, seals %d" % (len(test_items), len(train_items), len(pilot_ids), n))


main()
