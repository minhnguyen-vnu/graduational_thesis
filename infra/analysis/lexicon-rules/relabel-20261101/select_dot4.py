import csv, glob, html, json, math, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LR = os.path.normpath(os.path.join(HERE, ".."))
SEED = 20261101
CORE_B = {"role_set", "role_remove", "perm", "admin_flag", "member_role", "member_remove"}
QUEUE_COLUMNS = ["stt", "method", "path", "mo_ta", "schema", "truong", "A", "B", "C", "U", "victim", "role", "order"]
Z, MARGIN = 1.96, 0.05


def t_core(r):
    return r["A"] in ("existing", "self") and r["B"] in CORE_B and r["C"] in ("down", "unclear")


def norm(v):
    return "|".join(sorted(x.strip() for x in (v or "").split("|") if x.strip()))


def load_lane(lane, stage):
    out = {}
    for fn in sorted(glob.glob(os.path.join(HERE, lane, stage, "chunk-*.csv"))):
        with open(fn, newline="") as fh:
            for r in csv.DictReader(fh):
                out[r["row_id"]] = r
    return out


def rows_by_id(path):
    return {r["row_id"]: r for r in (json.loads(l) for l in open(path))}


def read_key(name):
    with open(os.path.join(HERE, "sealed", name), newline="") as fh:
        return list(csv.DictReader(fh))


def cochran(n_group):
    n0 = Z * Z * 0.25 / (MARGIN * MARGIN)
    return math.ceil(n0 / (1 + (n0 - 1) / n_group))


def human_row(stt, r):
    fields = "\n".join("%s:%s %s%s" % (f["loc"], f["name"], f["type"], " enum[%s]" % "|".join(f["enum"]) if f["enum"] else "")
                       for f in r["fields"])
    d = (r.get("summary") or "") + (" | " if r.get("summary") and r.get("description") else "") + (r.get("description") or "")
    return {"stt": stt, "method": r["method"], "path": r["path"], "mo_ta": d[:400], "schema": r.get("schema") or "",
            "truong": fields, "A": "", "B": "", "C": "", "U": "", "victim": "", "role": "", "order": ""}


def guide_examples(train_rows, keys):
    t = open(os.path.join(HERE, "ban-giao", "HUONG-DAN.html"), encoding="utf-8").read()
    seg = t[t.find('id="vidu"'):]
    found = []
    for blk in seg.split('<div class="ex">')[1:]:
        m = re.search(r"<code>(POST|PUT|PATCH|DELETE) ([^<]*)</code>", blk)
        names = [html.unescape(x) for x in re.findall(r"<tr><td><code>([^<]*)</code></td><td><code>", blk)]
        sch = re.search(r"<b>Schema:</b> ([^<]*)</p>", blk)
        sch = html.unescape(sch.group(1)).strip() if sch else ""
        hit = [k for k in keys if train_rows[k]["method"] == m.group(1) and train_rows[k]["path"] == html.unescape(m.group(2))
               and ["%s:%s" % (f["loc"], f["name"]) for f in train_rows[k]["fields"]] == names
               and (train_rows[k].get("schema") or "") == sch]
        if len(hit) != 1:
            raise SystemExit("HONG: vi du %s %s khop %d dong" % (m.group(1), m.group(2), len(hit)))
        found.append(hit[0])
    return found


def main():
    manifest = json.load(open(os.path.join(HERE, "manifest.json")))
    train_rows = rows_by_id(os.path.join(LR, "field-labelling-r4-20261006", "rows-all.jsonl"))
    test_rows = rows_by_id(os.path.join(HERE, "rows-test.jsonl"))
    a, b = load_lane("A", "train"), load_lane("B", "train")
    keys = [i for c in manifest["train"].values() for i in c if i in train_rows]
    both = [k for k in keys if t_core(a[k]) and t_core(b[k])]
    agree_t = [k for k in both if all(norm(a[k][c]) == norm(b[k][c]) for c in ("victim", "role", "order"))]
    both_n = [k for k in keys if not t_core(a[k]) and not t_core(b[k])]
    examples = guide_examples(train_rows, keys)
    pilot = {r["row_id"] for r in read_key("key-pilot.csv")}
    q3 = read_key("key-train-queue.csv")
    seen_t = {r["row_id"] for r in q3 if r["tang"] == "cung_T"}
    rest_t = sorted(set(agree_t) - seen_t - set(examples))
    pool_hoc = sorted(set(both_n) - set(examples))
    n_hoc = cochran(len(both_n))
    pick_hoc = random.Random(SEED + 30).sample(pool_hoc, n_hoc)

    ta, tb = load_lane("A", "test"), load_lane("B", "test")
    tkeys = [i for c in manifest["test"].values() for i in c]
    t_set = {k for k in tkeys if t_core(ta[k]) or t_core(tb[k])}
    tops = json.load(open(os.path.join(HERE, "sealed", "test-top4-m1.json")))
    top_all = {k for v in tops.values() for k in v}
    pool_thi = sorted(k for k in tkeys if k not in t_set and k not in top_all)
    q2 = read_key("key-test-queue.csv")
    old_51 = [r["row_id"] for r in q2 if r["tang"] == "nhieu"]
    redraw = random.Random(SEED + 11).sample(pool_thi, len(old_51))
    n_thi = cochran(len(tkeys) - len(t_set))
    pick_thi = random.Random(SEED + 31).sample(sorted(set(pool_thi) - set(old_51)), n_thi - len(old_51))

    items = [(k, "cung_T_con_lai") for k in rest_t] + [(k, "N_ngau_nhien_hoc") for k in pick_hoc] + \
            [(k, "N_ngau_nhien_thi") for k in pick_thi]
    random.Random(SEED + 32).shuffle(items)
    q3_ids = {r["row_id"] for r in q3}
    checks = [
        ("hoc: hai AI cung T, cung truong = 173", len(agree_t) == 173, len(agree_t)),
        ("hoc: hai AI cung khong = 10142", len(both_n) == 10142, len(both_n)),
        ("hoc: 30 dong cung_T dot 3 nam trong 173", len(seen_t) == 30 and seen_t <= set(agree_t), len(seen_t & set(agree_t))),
        ("hoc: 18 vi du huong dan, moi vi du khop dung 1 dong", len(set(examples)) == 18, len(set(examples))),
        ("hoc: vi du trong 173 = 8, trong 10142 = 10",
         len(set(examples) & set(agree_t)) == 8 and len(set(examples) & set(both_n)) == 10,
         "%d / %d" % (len(set(examples) & set(agree_t)), len(set(examples) & set(both_n)))),
        ("hoc: 173 con lai = 173 - 30 - 8 = 135", len(rest_t) == 135, len(rest_t)),
        ("hoc: co mau 10142 = 371", n_hoc == 371, n_hoc),
        ("hoc: 371 dong boc nam trong 10142, khong co vi du", set(pick_hoc) <= set(both_n) and not set(pick_hoc) & set(examples),
         len(pick_hoc)),
        ("thi: hai AI cung khong = 8498", len(tkeys) - len(t_set) == 8498, len(tkeys) - len(t_set)),
        ("thi: cho boc = 8382", len(pool_thi) == 8382, len(pool_thi)),
        ("thi: boc lai seed cu ra dung 51 dong nhieu", set(redraw) == set(old_51) and len(old_51) == 51, len(set(redraw) & set(old_51))),
        ("thi: co mau = 368, boc them 317", n_thi == 368 and len(pick_thi) == 317, "%d / %d" % (n_thi, len(pick_thi))),
        ("thi: 317 dong moi khong trung 51 dong cu", not set(pick_thi) & set(old_51), len(set(pick_thi) & set(old_51))),
        ("thi: 317 dong moi khong trung hang doi dot 2", not set(pick_thi) & {r["row_id"] for r in q2}, len(set(pick_thi) & {r["row_id"] for r in q2})),
        ("hoc va thi khong trung dong", not (set(rest_t) | set(pick_hoc)) & set(pick_thi), len((set(rest_t) | set(pick_hoc)) & set(pick_thi))),
        ("dot 4: tong 823 dong, khong lap", len(items) == 823 and len({k for k, _ in items}) == 823, len(items)),
    ]
    info = [
        ("hoc: dong pilot trong 135", len(set(rest_t) & pilot)),
        ("hoc: dong boc trung hang doi dot 3", len(set(pick_hoc) & q3_ids)),
        ("hoc: dong boc trung pilot", len(set(pick_hoc) & pilot)),
    ]
    bad = 0
    for name, ok, val in checks:
        print("%s  %s  (%s)" % ("PASS" if ok else "FAIL", name, val))
        bad += not ok
    for name, val in info:
        print("INFO  %s  (%s)" % (name, val))
    if bad:
        sys.exit(1)
    src = {**train_rows, **test_rows}
    with open(os.path.join(HERE, "handover", "dot-4.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, QUEUE_COLUMNS)
        w.writeheader()
        for i, (rid, _) in enumerate(items, 1):
            w.writerow(human_row(i, src[rid]))
    with open(os.path.join(HERE, "sealed", "key-dot-4.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["stt", "row_id", "tang"])
        for i, (rid, tier) in enumerate(items, 1):
            w.writerow([i, rid, tier])

    print("da ghi handover/dot-4.csv va sealed/key-dot-4.csv")


main()
