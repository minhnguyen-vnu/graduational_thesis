import csv, hashlib, json, os, shutil, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
NOP = os.path.join(HERE, "nop-hoi-dong")
REVIEW = os.path.join(HERE, "review-lech-thi", "review-thi.csv")
OUT = os.path.join(NOP, "nhan-thi-cuoi.csv")
OUT_REVIEW = os.path.join(NOP, "review-thi-lech.csv")
SO1 = os.path.join(HERE, "review-lech-thi", "soat-so1.csv")
OUT_SO1 = os.path.join(NOP, "soat-lai-44-thi.csv")
CORE_B = {"role_set", "role_remove", "perm", "admin_flag", "member_role", "member_remove"}
COLS = ["A", "B", "C", "victim", "role", "order"]
SRC = {"nguoi": "nguoi_", "AI": "sonnet_", "sonnet": "sonnet_", "opus": "opus_"}
NGUON = {"nguoi": "nguoi", "AI": "hai_AI", "sonnet": "sonnet", "opus": "opus"}

fails = []


def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        fails.append(msg)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def is_t(r, p=""):
    return r[p + "A"] in {"existing", "self"} and r[p + "B"] in CORE_B and r[p + "C"] in {"down", "unclear"}


def norm(v):
    return "|".join(sorted(x.strip() for x in v.split("|") if x.strip()))


def same_fields(a, pa, b, pb):
    return all(norm(a[pa + c]) == norm(b[pb + c]) for c in ("victim", "role", "order"))


def khop(h, a, p):
    return is_t(h) == is_t(a, p) and (not is_t(h) or same_fields(h, "", a, p))


def main():
    if os.path.exists(OUT) or os.path.exists(OUT_REVIEW) or os.path.exists(OUT_SO1):
        sys.exit("output exists: " + OUT)
    ins = [os.path.join(NOP, f) for f in ("op-thi.jsonl", "nhan-ai-thi.csv", "nhan-nguoi-gan.csv")] + [REVIEW, SO1]
    before = {p: sha(p) for p in ins}
    ops = [json.loads(l) for l in open(os.path.join(NOP, "op-thi.jsonl")) if l.strip()]
    ai = {r["row_id"]: r for r in csv.DictReader(open(os.path.join(NOP, "nhan-ai-thi.csv")))}
    hum_rows = [r for r in csv.DictReader(open(os.path.join(NOP, "nhan-nguoi-gan.csv"))) if r["phan"] == "thi"]
    hum = {r["row_id"]: r for r in hum_rows}
    rv = {r["row_id"]: r for r in csv.DictReader(open(REVIEW, encoding="utf-8-sig"))}

    check(len(ops) == 8674 and len(ai) == 8674, "8674 op thi va 8674 dong nhan AI")
    check([o["row_id"] for o in ops] == list(ai), "thu tu row_id op-thi trung nhan-ai-thi")
    check(len(hum_rows) == 544 and len(hum) == 544, "544 nhan nguoi phan thi, khong lap")
    seen_groups = Counter((ai[k]["nhom"], ai[k]["cho_boc"]) for k in hum)
    check(seen_groups == Counter({("it_nhat_mot_AI_T", "0"): 176, ("hai_AI_cung_N", "1"): 368}),
          "nguoi xem 176 op it nhat mot AI T va 368 op cho_boc 1")
    lech = {k for k, h in hum.items() if not khop(h, ai[k], "sonnet_") and not khop(h, ai[k], "opus_")}
    check(len(rv) == 53 and set(rv) == lech, "53 dong review dung bang tap op nguoi khac ca hai AI")
    check(all(r["chon"] in SRC for r in rv.values()), "moi dong review co chon hop le")
    check(all(r["chon"] != "AI" or same_fields(r, "sonnet_", r, "opus_") and is_t(r, "sonnet_") == is_t(r, "opus_")
              for r in rv.values()), "chon AI chi o dong hai AI cung T/N va cung truong")
    check(all(all(r["nguoi_" + c] == hum[k][c] for c in COLS) for k, r in rv.items()), "nhan nguoi trong review trung nhan-nguoi-gan")
    check(all(all(r["sonnet_" + c] == ai[k]["sonnet_" + c] and r["opus_" + c] == ai[k]["opus_" + c] for c in COLS)
              for k, r in rv.items()), "nhan AI trong review trung nhan-ai-thi")

    so1 = {r["row_id"]: r for r in csv.DictReader(open(SO1, encoding="utf-8-sig"))}
    lech_t = {k for k, a in ai.items() if is_t(a, "sonnet_") != is_t(a, "opus_")}
    check(len(so1) == 44 and set(so1) == lech_t, "44 dong soat lai dung bang tap op mot AI T, mot AI N")
    check(all(r["chon"] in {"giu", "nguoi", "sonnet", "opus"} for r in so1.values()), "moi dong soat lai co chon hop le")
    check(all(all(r["nguoi_" + c] == hum[k][c] and r["sonnet_" + c] == ai[k]["sonnet_" + c] and r["opus_" + c] == ai[k]["opus_" + c]
                  for c in COLS) for k, r in so1.items()), "nhan trong soat lai trung nhan-nguoi-gan va nhan-ai-thi")
    doi = {k: r for k, r in so1.items() if r["chon"] != "giu"}

    rows = []
    for o in ops:
        k = o["row_id"]
        a = ai[k]
        if k in doi:
            r = doi[k]
            src, p, nguon = r, SRC[r["chon"]], NGUON[r["chon"]] + "_soat_lai"
        elif k in rv:
            r = rv[k]
            src, p, nguon = r, SRC[r["chon"]], NGUON[r["chon"]]
        elif k in hum:
            src, p, nguon = hum[k], "", "nguoi"
        else:
            src, p, nguon = a, "sonnet_", "AI_chua_xem"
        t = is_t(src, p)
        vals = {c: src[p + c] for c in COLS}
        if not t:
            vals.update(victim="", role="", order="")
        rows.append({"row_id": k, "spec_id": o["spec_id"], "method": o["method"], "path": o["path"], "nhom": a["nhom"],
                     "cho_boc": a["cho_boc"], "nguon": nguon, "T": "1" if t else "0", **vals})

    unseen = [r for r in rows if r["nguon"] == "AI_chua_xem"]
    check(Counter(r["cho_boc"] for r in unseen) == Counter({"1": 8014, "0": 116}), "op chua xem: 8014 cho_boc 1 va 116 cho_boc 0")
    check(all(r["nhom"] == "hai_AI_cung_N" and not is_t(ai[r["row_id"]], "sonnet_") and not is_t(ai[r["row_id"]], "opus_")
              for r in unseen), "op chua xem deu hai AI cung N")
    check(all(r["T"] == "0" for r in unseen), "op chua xem deu N")
    seen_ok = [r for r in rows if r["nguon"] == "nguoi" and r["row_id"] not in rv]
    check(len(seen_ok) == 491 - len(doi) and all(r["T"] == ("1" if is_t(hum[r["row_id"]]) else "0") for r in seen_ok),
          "%d op nguoi da xem ngoai hai lan soat lay theo nguoi" % (491 - len(doi)))
    check(all(r["T"] == ("1" if is_t(doi[r["row_id"]], SRC[doi[r["row_id"]]["chon"]]) else "0") for r in rows if r["row_id"] in doi),
          "%d op doi o lan soat lai lay theo lua chon" % len(doi))
    check(all(r["victim"] == r["role"] == r["order"] == "" for r in rows if r["T"] == "0"), "op N khong mang victim, role, order")
    check(all(after == before[p] for p, after in ((p, sha(p)) for p in ins)), "input khong doi")

    nT = sum(r["T"] == "1" for r in rows)
    print("INFO T:", nT, "| nguon:", dict(Counter(r["nguon"] for r in rows)))
    print("INFO T theo nguon:", dict(Counter(r["nguon"] for r in rows if r["T"] == "1")))
    print("INFO T theo nhom:", dict(Counter((r["nhom"], r["cho_boc"]) for r in rows if r["T"] == "1")))
    if fails:
        sys.exit("%d FAIL, khong ghi file" % len(fails))

    fields = ["row_id", "spec_id", "method", "path", "nhom", "cho_boc", "nguon", "T"] + COLS
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fields)
        w.writeheader()
        w.writerows(rows)
    shutil.copyfile(REVIEW, OUT_REVIEW)
    shutil.copyfile(SO1, OUT_SO1)
    back = {r["row_id"]: r for r in csv.DictReader(open(OUT))}
    print(("PASS " if len(back) == 8674 and sum(r["T"] == "1" for r in back.values()) == nT else "FAIL ") + "doc lai file ghi ra")
    print("PASS ban sao review" if sha(OUT_REVIEW) == sha(REVIEW) and sha(OUT_SO1) == sha(SO1) else "FAIL ban sao review")


main()
