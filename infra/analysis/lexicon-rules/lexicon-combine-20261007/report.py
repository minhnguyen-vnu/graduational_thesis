import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = ["A-cur", "A-new", "A-new-0", "A-new-OR", "A-new-bool"]
GENERAL = ["A-new-OR", "A-new-bool"]
RULE = ["top1", "top3", "top8", "M1", "M2"]
NAME = {"top1": "top-1", "top3": "top-3", "top8": "top-8"}


def c(x, d=3):
    return (("%." + str(d) + "f") % x).replace(".", ",") if isinstance(x, float) else str(x)


def pv(p):
    return "< 0,001" if p < 0.001 else c(float(p), 3)


def ci(t):
    a, b = t["ci95_diff"]
    f = lambda v: ("+" if v > 0 else "") + c(float(v))
    return "%s … %s" % (f(a), f(b))


def main():
    cv = json.load(open(os.path.join(HERE, "cv.json")))
    tg = json.load(open(os.path.join(HERE, "targets.json")))
    checks = [l.rstrip("\n") for f in ("checks-pre.txt", "checks-post.txt")
              for l in open(os.path.join(HERE, f)) if l[:1] == "K" and l[1:2].isdigit()]
    r1 = cv["repeats"][0]
    V, T = r1["rates_V"], r1["tests_V"]
    y = lambda a, m: V[a][m]["yes"]
    n = lambda m: V["A-cur"][m]["n"]
    key = lambda b, a, m: T["%s - %s %s" % (b, a, m)]
    tv = {}
    for t in tg:
        tv.setdefault(t["arm"], {})[t["target"]] = t
    ntg = len(tv["A-cur"])
    inv = {a: sum(1 for t in tv[a].values() if t["viable_pos"] is not None) for a in ARMS}
    verdict = {}
    for g in GENERAL:
        worse = [m for m in RULE if key(g, "A-new", m)["p"] < 0.05 and key(g, "A-new", m)["a_only"] > key(g, "A-new", m)["b_only"]]
        lost = [t for t, x in tv[g].items() if x["viable_pos"] is None]
        verdict[g] = (not worse and not lost, worse, lost)
    L = []
    w = L.append
    w("# Thay điểm 0,6 bằng cách chấm tổng quát — kết quả")
    w("")
    w("Chạy 2026-10-07/08, offline, không sửa mã EvoMaster. Protocol: `PROTOCOL.md`. Lệnh: `python3 checks.py pre`,")
    w("`python3 measure2.py .`, `python3 checks.py post`, `python3 report.py`. Mọi bảng và con số do `report.py` sinh từ")
    w("`cv.json`, `targets.json`, `checks-*.txt`.")
    w("")
    w("## 1. Kết luận")
    w("")
    for g in GENERAL:
        ok, worse, lost = verdict[g]
        if ok:
            w("- **%s đạt luật §4.**" % g)
        else:
            why = []
            if worse:
                why.append("thua A-new có ý nghĩa ở %s" % ", ".join(NAME.get(m, m) for m in worse))
            if lost:
                why.append("mất target %s" % ", ".join("%s (hạng %d/%d)" % (t, tv[g][t]["rank_spec_order"], tv[g][t]["write_ops"]) for t in lost))
            w("- **%s không đạt luật §4**: %s." % (g, "; ".join(why)))
        w("  So với A-new: top-1 %d/%d (p = %s), top-3 %d/%d (p = %s), top-8 %d/%d (p = %s), M1 %d/%d (p = %s), M2 %d/%d (p = %s)."
          % (y(g, "top1"), y("A-new", "top1"), pv(key(g, "A-new", "top1")["p"]), y(g, "top3"), y("A-new", "top3"), pv(key(g, "A-new", "top3")["p"]),
             y(g, "top8"), y("A-new", "top8"), pv(key(g, "A-new", "top8")["p"]), y(g, "M1"), y("A-new", "M1"), pv(key(g, "A-new", "M1")["p"]),
             y(g, "M2"), y("A-new", "M2"), pv(key(g, "A-new", "M2")["p"])))
    ak = {a: tv[a]["artifact-keeper"] for a in ARMS}
    w("- artifact-keeper `PATCH /api/v1/users/{id}`: " + "; ".join("%s hạng %d/%d, điểm %s" % (a, ak[a]["rank_spec_order"], ak[a]["write_ops"], c(ak[a]["score"], 4)) for a in ARMS) + ".")
    w("  Runtime chỉ xét 8 endpoint đầu (`MAX_TRANSITION_CANDIDATES = 8`); danh sách khả dụng của A-new-bool là `%s`, của A-new-OR là `%s`."
      % (ak["A-new-bool"]["viable"] or "[]", ak["A-new-OR"]["viable"] or "[]"))
    fe = cv["feature_full"]
    w("- Đặc trưng F trên toàn bộ dữ liệu: cờ `%s`, %d op đổi quyền, %d op không, %d nhà cung cấp, điểm %s. Theo phần (lần lặp 1): %s."
      % (", ".join(fe["flag"]), fe["df_r"], fe["df_n"], fe["ncc"], c(fe["score"], 4),
         "; ".join("%s" % (c(i["feature"]["score"], 4) if i["feature"]["flag"] else "danh sách cờ rỗng") for i in r1["info"])))
    w("- Cả hai arm tổng quát không đạt; theo §4, chọn giữa A-new (kèm 0,6, giữ artifact-keeper) và A-new-0 (bỏ 0,6, mất")
    w("  artifact-keeper) là việc của user. A-new-0 so với A-new: top-1 %d/%d (p = %s), top-3 %d/%d (p = %s), top-8 %d/%d (p = %s), M5 %d/%d."
      % (y("A-new-0", "top1"), y("A-new", "top1"), pv(key("A-new-0", "A-new", "top1")["p"]), y("A-new-0", "top3"), y("A-new", "top3"),
         pv(key("A-new-0", "A-new", "top3")["p"]), y("A-new-0", "top8"), y("A-new", "top8"), pv(key("A-new-0", "A-new", "top8")["p"]),
         y("A-new-0", "M5"), y("A-new", "M5")) if not any(v[0] for v in verdict.values()) else "- Xem §3–§5.")
    nc = cv["negative_control"]
    w("- Đối chứng âm (A-new-OR): top-1 nhãn thật %d, nhãn xáo %d, trên %d spec." % (nc["top1_real"], nc["top1_permuted"], nc["specs"]))
    w("")
    w("## 2. Self-test")
    w("")
    w("| Mã | Kết quả | Chi tiết |")
    w("|---|---|---|")
    for l in checks:
        code, res, msg = l.split(" ", 2)
        w("| %s | %s | %s |" % (code, res, msg.replace("|", "/")))
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
    w("| So | " + " | ".join(NAME.get(m, m) for m in ms) + " |")
    w("|---|" + "---|" * len(ms))
    for a, b in (("A-new", "A-new-0"), ("A-new", "A-new-OR"), ("A-new", "A-new-bool"), ("A-new-0", "A-new-OR"),
                 ("A-new-0", "A-new-bool"), ("A-cur", "A-new-OR"), ("A-cur", "A-new-bool")):
        w("| %s − %s | " % (b, a) + " | ".join("%s; %s" % (pv(key(b, a, m)["p"]), ci(key(b, a, m))) for m in ms) + " |")
    w("")
    w("Lần lặp 2–4:")
    for rr in cv["repeats"][1:]:
        w("- Lần %d: " % rr["repeat"] + "; ".join("%s %d/%d/%d, M1 %d, M2 %d" % (
            a, rr["rates_V"][a]["top1"]["yes"], rr["rates_V"][a]["top3"]["yes"], rr["rates_V"][a]["top8"]["yes"],
            rr["rates_V"][a]["M1"]["yes"], rr["rates_V"][a]["M2"]["yes"]) for a in ARMS) + " (top-1/top-3/top-8).")
    w("")
    w("Nhóm B = RF, lần lặp 1: " + "; ".join("%s M1 %d, M2 %d, M5 %d" % (a, r1["rates_RF"][a]["M1"]["yes"], r1["rates_RF"][a]["M2"]["yes"],
                                                                        r1["rates_RF"][a]["M5"]["yes"]) for a in ARMS) + ".")
    w("")
    w("## 5. Target (rút trên toàn bộ dữ liệu)")
    w("")
    w("Mỗi ô: hạng theo thứ tự spec (khoảng khi hoà) / số op ghi; điểm; vị trí trong danh sách khả dụng (8 đầu, lọc nhóm B")
    w("viết tay), `—` nếu không có.")
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
    w("Số target có transition trong danh sách khả dụng: " + ", ".join("%s %d/%d" % (a, inv[a], ntg) for a in ARMS) + ".")
    w("")
    w("Mười endpoint đầu của artifact-keeper:")
    for a in GENERAL:
        w("- %s: " % a + "; ".join("`%s`" % s for s in ak[a]["top10"]) + ".")
    w("")
    w("## 6. Giới hạn")
    w("")
    w("- F dựa trên %d op đổi quyền của %d nhà cung cấp; ở một phần của lần lặp 1 danh sách cờ rỗng nên F không cộng gì." % (fe["df_r"], fe["ncc"])
      if any(not i["feature"]["flag"] for i in r1["info"]) else "- F dựa trên %d op đổi quyền của %d nhà cung cấp." % (fe["df_r"], fe["ncc"]))
    w("- OR coi các từ như bằng chứng độc lập.")
    w("- Giới hạn của `../lexicon-r4-20261007/PROTOCOL.md` §8 vẫn áp dụng; mô phỏng chưa đối chiếu với lượt EvoMaster thật.")
    open(os.path.join(HERE, "RESULTS.md"), "w").write("\n".join(L) + "\n")
    print("RESULTS.md %d lines; verdict %s; targets %s" % (len(L), verdict, inv))


main()
