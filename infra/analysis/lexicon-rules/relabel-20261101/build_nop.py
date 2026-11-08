import csv
import glob
import hashlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LR = os.path.normpath(os.path.join(HERE, ".."))
OUT = os.path.join(HERE, "nop-hoi-dong")
CORE_B = {"role_set", "role_remove", "perm", "admin_flag", "member_role", "member_remove"}
LABELS = ["A", "B", "C", "victim", "role", "order"]
OP_KEYS = ["row_id", "spec_id", "method", "path", "summary", "description", "fields", "fields_cut", "schema", "pos"]
DROP_OP_KEYS = {"split", "round", "old_label"}
LANES = [("A", "sonnet"), ("B", "opus")]
TRAIN_ROWS = os.path.join(LR, "field-labelling-r4-20261006", "rows-all.jsonl")
TEST_ROWS = os.path.join(HERE, "rows-test.jsonl")
BATCHES = [
    ("2", "handover/test-queue.csv", "sealed/key-test-queue.csv", "tra-ve/ket-qua-dot-2.csv", {"T", "nhieu"}),
    ("3", "handover/train-queue.csv", "sealed/key-train-queue.csv", "tra-ve/ket-qua-dot-3-cuoi-cung.csv", {"lech", "cung_T"}),
    ("4", "handover/dot-4.csv", "sealed/key-dot-4.csv", "tra-ve/ket-qua-dot-4.csv", {"cung_T_con_lai", "N_ngau_nhien_hoc", "N_ngau_nhien_thi"}),
]
TEST_TIERS = {"T", "nhieu", "N_ngau_nhien_thi"}
GUIDES = [
    ("ban-giao-dot4/HUONG-DAN.html", "huong-dan/HUONG-DAN.html"),
    ("ban-giao-dot4/CONG-CU-GAN-NHAN.html", "huong-dan/CONG-CU-GAN-NHAN.html"),
    ("GUIDE.md", "huong-dan/phieu-cho-AI.md"),
]

results = []


def check(ok, msg):
    results.append((bool(ok), msg))


def p(rel):
    return os.path.join(HERE, rel)


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def read_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def t_core(r):
    return r["A"] in ("existing", "self") and r["B"] in CORE_B and r["C"] in ("down", "unclear")


def norm(v):
    return "|".join(sorted(x.strip() for x in v.split("|") if x.strip()))


def load_lane(lane, stage):
    out = {}
    for fn in sorted(glob.glob(p(os.path.join(lane, stage, "chunk-*.csv")))):
        for r in read_csv(fn):
            if r["row_id"] in out:
                check(False, "lane %s %s co row_id lap: %s" % (lane, stage, r["row_id"]))
            out[r["row_id"]] = r
    return out


def inputs():
    files = [TRAIN_ROWS, TEST_ROWS, p("manifest.json"), p("sealed/test-top4-m1.json")]
    for lane, _ in LANES:
        for stage in ("train", "test"):
            files += sorted(glob.glob(p(os.path.join(lane, stage, "chunk-*.csv"))))
    for _, sheet, key, ret, _ in BATCHES:
        files += [p(sheet), p(key), p(ret)]
    files += [p(src) for src, _ in GUIDES]
    return files


def write_csv(rel, fields, rows):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_ops(rel, ops):
    path = os.path.join(OUT, rel)
    with open(path, "w", encoding="utf-8") as fh:
        for op in ops:
            fh.write(json.dumps({k: op[k] for k in OP_KEYS}, ensure_ascii=False) + "\n")


def main():
    if os.path.exists(OUT):
        print("FAIL thu muc ra da ton tai, khong ghi de: " + OUT)
        sys.exit(1)
    before = {f: sha(f) for f in inputs()}

    manifest = json.load(open(p("manifest.json")))
    train_ids = [i for c in manifest["train"].values() for i in c]
    test_ids = [i for c in manifest["test"].values() for i in c]
    train_ops = {r["row_id"]: r for r in read_jsonl(TRAIN_ROWS)}
    test_ops = {r["row_id"]: r for r in read_jsonl(TEST_ROWS)}
    check(set(train_ids) == set(train_ops) and len(train_ids) == len(train_ops), "op hoc: manifest %d, rows-all %d, cung tap" % (len(train_ids), len(train_ops)))
    check(set(test_ids) == set(test_ops) and len(test_ids) == len(test_ops), "op thi: manifest %d, rows-test %d, cung tap" % (len(test_ids), len(test_ops)))
    check(not set(train_ops) & set(test_ops), "op hoc va op thi khong chung row_id")

    lanes = {}
    for lane, name in LANES:
        for stage, ids in (("train", train_ids), ("test", test_ids)):
            got = load_lane(lane, stage)
            lanes[(lane, stage)] = got
            check(set(got) == set(ids), "nhan AI %s (%s) %s: %d dong, khop manifest" % (lane, name, stage, len(got)))

    a, b = lanes[("A", "train")], lanes[("B", "train")]
    lech_t = {k for k in train_ids if t_core(a[k]) != t_core(b[k])}
    both_t = {k for k in train_ids if t_core(a[k]) and t_core(b[k])}
    lech_col = {k for k in both_t if any(norm(a[k][c]) != norm(b[k][c]) for c in ("victim", "role", "order"))}
    agree_t = both_t - lech_col
    both_n = {k for k in train_ids if not t_core(a[k]) and not t_core(b[k])}
    train_group = {}
    for name, ids in (("hai_AI_cung_T", agree_t), ("cung_T_lech_truong", lech_col), ("lech_T", lech_t), ("hai_AI_cung_N", both_n)):
        for k in ids:
            train_group[k] = name
    check(len(train_group) == len(train_ids), "nhom hoc phu het %d op, khong chong: 173=%d 25=%d 41=%d 10142=%d" % (len(train_ids), len(agree_t), len(lech_col), len(lech_t), len(both_n)))
    check((len(agree_t), len(lech_col), len(lech_t), len(both_n)) == (173, 25, 41, 10142), "co nhom hoc trung so da chot 173, 25, 41, 10.142")

    ta, tb = lanes[("A", "test")], lanes[("B", "test")]
    t_set = {k for k in test_ids if t_core(ta[k]) or t_core(tb[k])}
    test_n = set(test_ids) - t_set
    tops = json.load(open(p("sealed/test-top4-m1.json")))
    top_all = {k for v in tops.values() for k in v}
    set_aside = (top_all - t_set) & set(test_ids)
    pool = test_n - top_all
    check(top_all <= set(test_ids), "116 op de rieng deu thuoc op thi")
    check((len(t_set), len(test_n), len(set_aside), len(pool)) == (176, 8498, 116, 8382), "co nhom thi: 176=%d 8498=%d de_rieng=%d cho_boc=%d" % (len(t_set), len(test_n), len(set_aside), len(pool)))

    human = []
    seen = {}
    for dot, sheet_rel, key_rel, ret_rel, keep in BATCHES:
        sheet = {r["stt"]: r for r in read_csv(p(sheet_rel))}
        key = {r["stt"]: r for r in read_csv(p(key_rel))}
        ret = {r["stt"]: r for r in read_csv(p(ret_rel))}
        check(set(sheet) == set(key) == set(ret), "dot %s: phieu %d, khoa %d, tra ve %d, cung tap stt" % (dot, len(sheet), len(key), len(ret)))
        kept = 0
        for stt in sorted(ret, key=int):
            k = key[stt]
            if k["tang"] not in keep:
                continue
            r = ret[stt]
            rid = k["row_id"]
            ops = test_ops if k["tang"] in TEST_TIERS else train_ops
            op = ops.get(rid)
            if op is None or (op["method"], op["path"]) != (r["method"], r["path"]) or (op["method"], op["path"]) != (sheet[stt]["method"], sheet[stt]["path"]):
                check(False, "dot %s stt %s: row_id %s khong khop method/path" % (dot, stt, rid))
            if rid in seen:
                check(False, "row_id %s co nhan nguoi o hai dot: %s va %s" % (rid, seen[rid], dot + ":" + stt))
            seen[rid] = dot + ":" + stt
            row = {"dot": dot, "stt": stt, "row_id": rid, "phan": "thi" if k["tang"] in TEST_TIERS else "hoc", "tang": k["tang"], "method": r["method"], "path": r["path"]}
            row.update({c: r[c] for c in LABELS})
            human.append(row)
            kept += 1
        print("INFO dot %s: giu %d dong, bo %d dong (tang bo: %s)" % (dot, kept, len(ret) - kept, ", ".join(sorted({key[s]["tang"] for s in key} - keep)) or "khong"))

    by_tier = {}
    for r in human:
        by_tier.setdefault(r["tang"], set()).add(r["row_id"])
    check(by_tier.get("T", set()) == t_set, "tang T dot 2 dung bang toan bo 176 op it nhat mot AI goi T")
    check(by_tier.get("lech", set()) == lech_t | lech_col, "tang lech dot 3 dung bang toan bo 66 op nhom 25 va 41")
    seen_173 = by_tier.get("cung_T", set()) | by_tier.get("cung_T_con_lai", set())
    check(seen_173 <= agree_t and not by_tier.get("cung_T", set()) & by_tier.get("cung_T_con_lai", set()), "30 va 135 thuoc nhom 173, khong chong")
    print("INFO nhom 173: nguoi xem %d op, %d op con lai la vi du trong huong dan" % (len(seen_173), len(agree_t - seen_173)))
    check(by_tier.get("N_ngau_nhien_hoc", set()) <= both_n, "371 op ngau nhien hoc thuoc nhom 10.142")
    rand_test = by_tier.get("nhieu", set()) | by_tier.get("N_ngau_nhien_thi", set())
    check(rand_test <= pool and len(rand_test) == len(by_tier.get("nhieu", set())) + len(by_tier.get("N_ngau_nhien_thi", set())), "51 va 317 thuoc cho boc 8.382, khong chong, tong %d" % len(rand_test))
    check(len(human) == 1146, "nhan nguoi giu %d dong" % len(human))

    final_t = len(agree_t) + sum(1 for r in human if r["tang"] == "lech" and t_core(r))
    check(final_t == 214, "so op T de hoc M2: 173 + T nguoi trong 66 op lech = %d" % final_t)

    if not all(ok for ok, _ in results):
        for ok, msg in results:
            print(("PASS " if ok else "FAIL ") + msg)
        print("FAIL dung truoc khi ghi, chua tao " + OUT)
        sys.exit(1)
    os.makedirs(OUT)
    write_ops("op-hoc.jsonl", [train_ops[k] for k in train_ids])
    write_ops("op-thi.jsonl", [test_ops[k] for k in test_ids])
    lane_cols = ["%s_%s" % (name, c) for _, name in LANES for c in LABELS]

    def ai_row(k, ops, stage, extra):
        op = ops[k]
        row = {"row_id": k, "spec_id": op["spec_id"], "method": op["method"], "path": op["path"]}
        row.update(extra)
        for lane, name in LANES:
            for c in LABELS:
                row["%s_%s" % (name, c)] = lanes[(lane, stage)][k][c]
        return row

    write_csv("nhan-ai-hoc.csv", ["row_id", "spec_id", "method", "path", "nhom"] + lane_cols,
              [ai_row(k, train_ops, "train", {"nhom": train_group[k]}) for k in train_ids])
    test_rows = []
    for k in test_ids:
        group = "it_nhat_mot_AI_T" if k in t_set else "hai_AI_cung_N"
        test_rows.append(ai_row(k, test_ops, "test", {"nhom": group, "cho_boc": "1" if k in pool else "0"}))
    write_csv("nhan-ai-thi.csv", ["row_id", "spec_id", "method", "path", "nhom", "cho_boc"] + lane_cols, test_rows)
    write_csv("nhan-nguoi-gan.csv", ["dot", "stt", "row_id", "phan", "tang", "method", "path"] + LABELS, human)
    for src, dst in GUIDES:
        os.makedirs(os.path.dirname(os.path.join(OUT, dst)), exist_ok=True)
        shutil.copyfile(p(src), os.path.join(OUT, dst))
        check(sha(p(src)) == sha(os.path.join(OUT, dst)), "huong dan chep nguyen van: %s" % dst)

    back_h = read_csv(os.path.join(OUT, "nhan-nguoi-gan.csv"))
    raw = {}
    for dot, _, _, ret_rel, _ in BATCHES:
        for r in read_csv(p(ret_rel)):
            raw[(dot, r["stt"])] = r
    diff = sum(1 for r in back_h if any(r[c] != raw[(r["dot"], r["stt"])][c] for c in LABELS))
    check(diff == 0 and len(back_h) == len(human), "nhan nguoi doc lai %d dong, lech so voi file tra ve %d o" % (len(back_h), diff))
    for rel, stage, ids in (("nhan-ai-hoc.csv", "train", train_ids), ("nhan-ai-thi.csv", "test", test_ids)):
        back = read_csv(os.path.join(OUT, rel))
        bad = 0
        for r in back:
            for lane, name in LANES:
                if any(r["%s_%s" % (name, c)] != lanes[(lane, stage)][r["row_id"]][c] for c in LABELS):
                    bad += 1
        check(len(back) == len(ids) and bad == 0, "%s doc lai %d dong, lech so voi chunk AI %d dong" % (rel, len(back), bad))
    for rel in ("op-hoc.jsonl", "op-thi.jsonl"):
        back = read_jsonl(os.path.join(OUT, rel))
        check(all(set(r) == set(OP_KEYS) for r in back), "%s: %d dong, chi co cot %s" % (rel, len(back), ",".join(OP_KEYS)))
    headers = []
    for rel in ("nhan-ai-hoc.csv", "nhan-ai-thi.csv", "nhan-nguoi-gan.csv"):
        with open(os.path.join(OUT, rel), encoding="utf-8") as fh:
            headers += fh.readline().strip().split(",")
    banned = {"U", "ghi_chu"} | DROP_OP_KEYS | {"%s_U" % name for _, name in LANES}
    check(not banned & set(headers), "khong file nhan nao co cot U, ghi_chu, split, round, old_label")

    after = {f: sha(f) for f in inputs()}
    check(before == after, "%d file nguon khong doi sha256" % len(before))

    sums = []
    for root, _, files in os.walk(OUT):
        for fn in sorted(files):
            full = os.path.join(root, fn)
            sums.append("%s  %s" % (sha(full), os.path.relpath(full, OUT)))
    with open(os.path.join(OUT, "SHA256SUMS.txt"), "w") as fh:
        fh.write("\n".join(sorted(sums, key=lambda s: s.split("  ")[1])) + "\n")

    for ok, msg in results:
        print(("PASS " if ok else "FAIL ") + msg)
    sys.exit(0 if all(ok for ok, _ in results) else 1)


if __name__ == "__main__":
    main()
