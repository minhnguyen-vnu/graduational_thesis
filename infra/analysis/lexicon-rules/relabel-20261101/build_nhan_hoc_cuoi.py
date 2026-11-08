import csv, hashlib, json, os, shutil, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
NOP = os.path.join(HERE, "nop-hoi-dong")
REVIEW = os.path.join(HERE, "review-lech-hoc", "review-66.csv")
OUT = os.path.join(NOP, "nhan-hoc-cuoi.csv")
OUT_REVIEW = os.path.join(NOP, "review-66-lech.csv")
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


def main():
    if os.path.exists(OUT) or os.path.exists(OUT_REVIEW):
        sys.exit("output exists: " + OUT)
    ins = [os.path.join(NOP, f) for f in ("op-hoc.jsonl", "nhan-ai-hoc.csv", "nhan-nguoi-gan.csv")] + [REVIEW]
    before = {p: sha(p) for p in ins}
    ops = [json.loads(l) for l in open(os.path.join(NOP, "op-hoc.jsonl")) if l.strip()]
    ai = {r["row_id"]: r for r in csv.DictReader(open(os.path.join(NOP, "nhan-ai-hoc.csv")))}
    hum = {r["row_id"]: r for r in csv.DictReader(open(os.path.join(NOP, "nhan-nguoi-gan.csv"))) if r["phan"] == "hoc"}
    rv = {r["row_id"]: r for r in csv.DictReader(open(REVIEW, encoding="utf-8-sig"))}

    check(len(ops) == 10381 and len(ai) == 10381, "10381 op hoc va 10381 dong nhan AI")
    check([o["row_id"] for o in ops] == list(ai), "thu tu row_id op-hoc trung nhan-ai-hoc")
    check(len(hum) == 602, "602 nhan nguoi phan hoc")
    check(len(rv) == 66 and set(rv) <= set(hum), "66 dong review, deu nam trong 602")
    check(all(r["chon"] in SRC for r in rv.values()), "moi dong review co chon hop le")
    check(all(r["chon"] != "AI" or same_fields(r, "sonnet_", r, "opus_") and is_t(r, "sonnet_") == is_t(r, "opus_")
              for r in rv.values()), "chon AI chi o dong hai AI cung T/N va cung truong")
    check(all(all(r["nguoi_" + c] == hum[k][c] for c in COLS) for k, r in rv.items()), "nhan nguoi trong review trung nhan-nguoi-gan")
    check(all(all(r["sonnet_" + c] == ai[k]["sonnet_" + c] and r["opus_" + c] == ai[k]["opus_" + c] for c in COLS)
              for k, r in rv.items()), "nhan AI trong review trung nhan-ai-hoc")

    rows = []
    for o in ops:
        k = o["row_id"]
        a = ai[k]
        if k in rv:
            r = rv[k]
            src, p, nguon = r, SRC[r["chon"]], NGUON[r["chon"]]
        elif k in hum:
            src, p, nguon = hum[k], "", "nguoi"
        elif a["nhom"] == "hai_AI_cung_T":
            src, p, nguon = a, "sonnet_", "hai_AI"
        else:
            src, p, nguon = a, "sonnet_", "AI_chua_xem"
        t = is_t(src, p)
        vals = {c: src[p + c] for c in COLS}
        if not t:
            vals.update(victim="", role="", order="")
        rows.append({"row_id": k, "spec_id": o["spec_id"], "method": o["method"], "path": o["path"], "nhom": a["nhom"],
                     "nguon": nguon, "T": "1" if t else "0", **vals})

    unseen = [r for r in rows if r["row_id"] not in hum]
    check(all(ai[r["row_id"]]["nhom"] in {"hai_AI_cung_N", "hai_AI_cung_T"} for r in unseen), "op chua xem chi thuoc hai nhom hai AI cung y")
    vidu = [r for r in unseen if ai[r["row_id"]]["nhom"] == "hai_AI_cung_T"]
    check(len(vidu) == 8 and all(r["nguon"] == "hai_AI" and r["T"] == "1" for r in vidu), "8 op vi du ghi hai_AI, deu T")
    check(Counter(r["nguon"] for r in rows)["hai_AI"] == 43, "hai_AI = 35 op review + 8 op vi du")
    check(all(is_t(ai[r["row_id"]], "sonnet_") == is_t(ai[r["row_id"]], "opus_")
              and (not is_t(ai[r["row_id"]], "sonnet_") or same_fields(ai[r["row_id"]], "sonnet_", ai[r["row_id"]], "opus_"))
              for r in unseen),
          "op chua xem: Sonnet va Opus cung T/N, op T cung truong")
    check(Counter(r["nguon"] for r in rows)["AI_chua_xem"] == 9771, "9771 op AI_chua_xem, deu hai AI cung N")
    check(all(r["T"] == "0" for r in rows if r["nguon"] == "AI_chua_xem"), "op AI_chua_xem deu N")
    seen_ok = [r for r in rows if r["nguon"] == "nguoi" and r["row_id"] not in rv]
    check(len(seen_ok) == 536 and all(r["T"] == ("1" if is_t(hum[r["row_id"]]) else "0") for r in seen_ok),
          "536 op nguoi da xem ngoai review lay theo nguoi")
    check(all(r["victim"] == r["role"] == r["order"] == "" for r in rows if r["T"] == "0"), "op N khong mang victim, role, order")
    check(all(after == before[p] for p, after in ((p, sha(p)) for p in ins)), "input khong doi")

    nT = sum(r["T"] == "1" for r in rows)
    print("INFO T:", nT, "| nguon:", dict(Counter(r["nguon"] for r in rows)))
    print("INFO T theo nguon:", dict(Counter(r["nguon"] for r in rows if r["T"] == "1")))
    if fails:
        sys.exit("%d FAIL, khong ghi file" % len(fails))

    fields = ["row_id", "spec_id", "method", "path", "nhom", "nguon", "T"] + COLS
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fields)
        w.writeheader()
        w.writerows(rows)
    shutil.copyfile(REVIEW, OUT_REVIEW)
    back = {r["row_id"]: r for r in csv.DictReader(open(OUT))}
    print(("PASS " if len(back) == 10381 and sum(r["T"] == "1" for r in back.values()) == nT else "FAIL ") + "doc lai file ghi ra")
    print("PASS ban sao review" if sha(OUT_REVIEW) == sha(REVIEW) else "FAIL ban sao review")


main()
