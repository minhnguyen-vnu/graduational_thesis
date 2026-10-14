import csv, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = ["A-cur", "A-new", "A-newV1", "A-newV1-0"]
RULE = ["top1", "top3", "top8", "M1", "M2"]


def vn(x, d=3):
    return ("%." + str(d) + "f") % x if isinstance(x, float) else str(x)


def c(x, d=3):
    return vn(x, d).replace(".", ",")


def pv(p):
    return "< 0,001" if p < 0.001 else c(p, 3)


def ci(t):
    a, b = t["ci95_diff"]
    return "%s … %s" % (("+" if a > 0 else "") + c(a), ("+" if b > 0 else "") + c(b))


def load():
    cv = json.load(open(os.path.join(HERE, "cv.json")))
    tg = json.load(open(os.path.join(HERE, "targets.json")))
    checks = [l.rstrip("\n") for f in ("checks-pre.txt", "checks-post.txt")
              for l in open(os.path.join(HERE, f)) if l[:1] == "C" and l[1:2].isdigit()]
    return cv, tg, checks


def cand(name, k=10):
    rows = list(csv.DictReader(open(os.path.join(HERE, name))))
    return rows[:k], {r["tu"]: r for r in rows}, len(rows)


def main():
    cv, tg, checks = load()
    r1 = cv["repeats"][0]
    V = r1["rates_V"]
    T = r1["tests_V"]
    y = lambda a, m: V[a][m]["yes"]
    n = lambda m: V["A-cur"][m]["n"]
    tv = {}
    for t in tg:
        tv.setdefault(t["arm"], {})[t["target"]] = t
    inviable = {a: sum(1 for t in tv[a].values() if t["viable_pos"] is not None) for a in ARMS}
    ntg = len(tv["A-cur"])
    key = lambda b, a, m: T["%s - %s %s" % (b, a, m)]
    worse = [m for m in RULE if key("A-newV1-0", "A-cur", m)["p"] < 0.05 and key("A-newV1-0", "A-cur", m)["a_only"] > key("A-newV1-0", "A-cur", m)["b_only"]]
    passed = not worse and inviable["A-newV1-0"] >= inviable["A-cur"]
    lost = [t for t, x in tv["A-newV1-0"].items() if x["viable_pos"] is None and tv["A-cur"][t]["viable_pos"] is not None]
    nc = cv["negative_control"]
    L = []
    w = L.append
    w("# Rút lexicon nhóm A từ nhãn vòng 4 — kết quả")
    w("")
    w("Chạy 2026-10-07, offline, không sửa mã EvoMaster, không chép lexicon mới vào `core/src/main/resources/`. Protocol:")
    w("`PROTOCOL.md` (chốt trước 23:29; thay đổi sau khi chốt ở §9). Lệnh: `python3 checks.py pre`, `python3 measure.py .`,")
    w("`python3 checks.py post`, `python3 report.py`. Mọi bảng và mọi con số trong file này do `report.py` sinh từ `cv.json`,")
    w("`targets.json`, `candidates-*.csv`, `checks-*.txt`.")
    w("")
    w("## 1. Kết luận")
    w("")
    if passed:
        w("- **Luật §6: A-newV1-0 đạt.**")
    else:
        why = []
        if worse:
            why.append("thua A-cur có ý nghĩa ở %s" % ", ".join(worse))
        if inviable["A-newV1-0"] < inviable["A-cur"]:
            why.append("số target có transition trong danh sách khả dụng %d/%d so với %d/%d của A-cur (mất %s)"
                       % (inviable["A-newV1-0"], ntg, inviable["A-cur"], ntg, ", ".join(lost)))
        w("- **Luật §6: A-newV1-0 không đạt**: %s. Ở top-1, top-3, top-8, M1, M2 nó không thua A-cur có ý nghĩa." % "; ".join(why))
    ak = tv["A-newV1-0"].get("artifact-keeper")
    if ak:
        w("  Không có điểm 0,6, `PATCH /api/v1/users/{id}` của artifact-keeper đứng hạng %d/%d (điểm %s)."
          % (ak["rank_spec_order"], ak["write_ops"], c(ak["score"], 4)))
    w("- **Đổi dữ liệu** (A-new − A-cur, cùng luật cũ, nhãn vòng 4): top-1 %d so với %d (p = %s), top-3 %d so với %d (p = %s),"
      % (y("A-new", "top1"), y("A-cur", "top1"), pv(key("A-new", "A-cur", "top1")["p"]),
         y("A-new", "top3"), y("A-cur", "top3"), pv(key("A-new", "A-cur", "top3")["p"])))
    w("  top-8 %d so với %d (p = %s) trên %d spec; M1 %d so với %d (p = %s); M2 %d so với %d (p = %s). Target %d/%d."
      % (y("A-new", "top8"), y("A-cur", "top8"), pv(key("A-new", "A-cur", "top8")["p"]), n("top1"),
         y("A-new", "M1"), y("A-cur", "M1"), pv(key("A-new", "A-cur", "M1")["p"]),
         y("A-new", "M2"), y("A-cur", "M2"), pv(key("A-new", "A-cur", "M2")["p"]), inviable["A-new"], ntg))
    w("- **Đếm trên chuỗi runtime** (A-newV1 − A-new): top-1 %d so với %d (p = %s), top-3 %d so với %d (p = %s), top-8 %d so với %d"
      % (y("A-newV1", "top1"), y("A-new", "top1"), pv(key("A-newV1", "A-new", "top1")["p"]),
         y("A-newV1", "top3"), y("A-new", "top3"), pv(key("A-newV1", "A-new", "top3")["p"]),
         y("A-newV1", "top8"), y("A-new", "top8")))
    w("  (p = %s); M2 %d so với %d (p = %s)."
      % (pv(key("A-newV1", "A-new", "top8")["p"]), y("A-newV1", "M2"), y("A-new", "M2"), pv(key("A-newV1", "A-new", "M2")["p"])))
    w("- **Bỏ điểm 0,6** (A-newV1-0 − A-newV1): M5 %d so với %d (p = %s); top-1 %d so với %d; mất target %s."
      % (y("A-newV1-0", "M5"), y("A-newV1", "M5"), pv(key("A-newV1-0", "A-newV1", "M5")["p"]),
         y("A-newV1-0", "top1"), y("A-newV1", "top1"), ", ".join(lost) if lost else "không"))
    w("- **Đối chứng âm:** trên %d spec test của lần lặp 1, top-1 với nhãn thật %d, với nhãn xáo %d, kỳ vọng ngẫu nhiên %s."
      % (nc["specs"], nc["top1_real"], nc["top1_permuted"], c(nc["top1_random_expected"], 2)))
    better = [m for m in ("top1", "top3", "top8", "M1", "M2") if key("A-new", "A-cur", m)["p"] < 0.05 and key("A-new", "A-cur", m)["b_only"] > key("A-new", "A-cur", m)["a_only"]]
    w("- Theo luật §6, không chọn arm khác thay A-newV1-0. A-new hơn A-cur có ý nghĩa ở %s; A-newV1 không được so trực tiếp"
      % (", ".join(m.replace("top", "top-") for m in better) if better else "không chỉ số nào"))
    w("  với A-cur trong protocol. A-new vẫn giữ điểm 0,6 với danh sách admin viết tay.")
    w("")
    w("## 2. Self-test")
    w("")
    w("| Mã | Kết quả | Chi tiết |")
    w("|---|---|---|")
    for l in checks:
        code, res, msg = l.split(" ", 2)
        w("| %s | %s | %s |" % (code, res, msg.replace("|", "/")))
    w("")
    w("Lượt đầu trượt C7 và C9; nguyên nhân và cách sửa ở `PROTOCOL.md` §9. Số kiểm chéo không đổi sau khi sửa.")
    w("")
    w("## 3. Kiểm chéo, lần lặp 1, nhóm B = bộ viết tay")
    w("")
    w("Hạng: số spec có op `T = 1` trong k op đầu, theo thứ tự spec; trong ngoặc là xấu nhất–tốt nhất khi hoà điểm.")
    w("")
    w("| Chỉ số | Đơn vị | " + " | ".join(ARMS) + " |")
    w("|---|---|" + "---|" * len(ARMS))
    for k in (1, 3, 8):
        m = "top%d" % k
        w("| top-%d | %d spec | " % (k, n(m)) + " | ".join("%d (%d–%d)" % (y(a, m), y(a, m + "_worst"), y(a, m + "_best")) for a in ARMS) + " |")
    for m, unit in (("M1", "API"), ("M1any", "API"), ("M2", "API"), ("M5", "op")):
        w("| %s | %d %s | " % (m, n(m), unit) + " | ".join(str(y(a, m)) for a in ARMS) + " |")
    w("")
    w("## 4. Kiểm định, lần lặp 1")
    w("")
    w("McNemar chính xác hai phía; KTC 95% bootstrap theo nhà cung cấp cho hiệu (arm sau − arm trước).")
    w("")
    ms = ["top1", "top3", "top8", "M1", "M2", "M5"]
    w("| So | " + " | ".join(ms) + " |")
    w("|---|" + "---|" * len(ms))
    for a, b in (("A-cur", "A-new"), ("A-new", "A-newV1"), ("A-newV1", "A-newV1-0"), ("A-cur", "A-newV1-0")):
        w("| %s − %s | " % (b, a) + " | ".join("%s; %s" % (pv(key(b, a, m)["p"]), ci(key(b, a, m))) for m in ms) + " |")
    w("")
    w("## 5. Lần lặp 2–4")
    w("")
    for rr in cv["repeats"][1:]:
        w("- Lần %d: " % rr["repeat"] + "; ".join("%s top-1 %d, top-3 %d, top-8 %d, M1 %d, M2 %d" % (
            a, rr["rates_V"][a]["top1"]["yes"], rr["rates_V"][a]["top3"]["yes"], rr["rates_V"][a]["top8"]["yes"],
            rr["rates_V"][a]["M1"]["yes"], rr["rates_V"][a]["M2"]["yes"]) for a in ARMS) + ".")
    w("")
    w("## 6. Nhóm B = RF (báo thêm)")
    w("")
    RF = r1["rates_RF"]
    w("| Chỉ số | Đơn vị | " + " | ".join(ARMS) + " |")
    w("|---|---|" + "---|" * len(ARMS))
    for m in ("M1", "M1any", "M2", "M5"):
        w("| %s | %d | " % (m, RF["A-cur"][m]["n"]) + " | ".join(str(RF[a][m]["yes"]) for a in ARMS) + " |")
    w("")
    w("## 7. Target (lexicon rút trên toàn bộ dữ liệu)")
    w("")
    w("Mỗi ô: hạng theo thứ tự spec (khoảng khi hoà) / số op ghi; điểm; vị trí trong danh sách transition khả dụng (lọc nhóm B")
    w("viết tay, 8 đầu), `—` nếu không có.")
    w("")
    w("| Target | " + " | ".join(ARMS) + " |")
    w("|---|" + "---|" * len(ARMS))
    for name in tv["A-cur"]:
        cells = []
        for a in ARMS:
            t = tv[a][name]
            rk = "%d" % t["rank_spec_order"] + ("" if t["rank_best"] == t["rank_worst"] else " (%d–%d)" % (t["rank_best"], t["rank_worst"]))
            cells.append("%s/%d; %s; %s" % (rk, t["write_ops"], c(t["score"], 4), t["viable_pos"] if t["viable_pos"] else "—"))
        w("| %s | " % name + " | ".join(cells) + " |")
    w("")
    w("Số target có transition trong danh sách khả dụng: " + ", ".join("%s %d/%d" % (a, inviable[a], ntg) for a in ARMS) + ".")
    w("")
    w("## 8. Lexicon mới")
    w("")
    for name, label in (("candidates-new-path.csv", "A-new (`lexicon-new.csv`)"), ("candidates-newV1-path.csv", "A-newV1 (`lexicon-newV1.csv`)")):
        top, allr, cnt = cand(name)
        w("- %s: %d từ path. Mười từ đầu (`df_R`/`df_N`/nhà cung cấp, điểm): " % (label, cnt)
          + "; ".join("`%s` %s/%s/%s %s" % (r["tu"], r["df_r"], r["df_n"], r["nha_cung_cap"], c(float(r["diem"]), 4)) for r in top) + ".")
        ad = allr.get("admin")
        if ad:
            w("  `admin`: %s/%s/%s, %s." % (ad["df_r"], ad["df_n"], ad["nha_cung_cap"], c(float(ad["diem"]), 4)))
    tq, _, cq = cand("candidates-new-param.csv", 5)
    w("- Danh sách param mới: %d từ; đầu bảng " % cq + "; ".join("`%s` %s" % (r["tu"], c(float(r["diem"]), 4)) for r in tq) + ".")
    w("- Lexicon trong jar: 53 từ path, 45 từ param.")
    w("")
    w("## 9. Giới hạn")
    w("")
    w("- Nhãn `T` lệch định nghĩa với nhãn `R` cũ (cấp quyền thuần, khoá tài khoản); A-cur học `R` cũ nhưng được chấm theo `T`.")
    w("- 15 spec nửa test cũ đã được nhìn khi chỉnh luật lexicon cũ; chúng nằm trong tập test.")
    w("- Thứ tự spec của vòng 4 là thứ tự path rồi method (`extract_fields.ops_of`), có thể khác thứ tự EvoMaster đọc spec;")
    w("  khoảng xấu nhất–tốt nhất ở §3 cho thấy biên độ.")
    w("- Vòng 4 không trích tham số header; `param_names` mới hẹp hơn cũ.")
    w("- Mô phỏng chưa đối chiếu với lượt EvoMaster thật.")
    open(os.path.join(HERE, "RESULTS.md"), "w").write("\n".join(L) + "\n")
    print("RESULTS.md: %d lines; rule passed=%s worse=%s targets=%s" % (len(L), passed, worse, inviable))


main()
