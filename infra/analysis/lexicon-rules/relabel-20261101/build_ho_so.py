import csv, hashlib, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LR = os.path.normpath(os.path.join(HERE, ".."))
NOP = os.path.join(HERE, "nop-hoi-dong")
OUT = os.path.join(HERE, "ho-so-gan-nhan")
M2 = os.path.join(LR, "m2-model-20261107", "stateful-authz-model.csv")
sys.path.insert(0, os.path.join(LR, "p2-model-20261012"))
import derive_model as D

CORE_B = {"role_set", "role_remove", "perm", "admin_flag", "member_role", "member_remove"}
TEN = {"nguoi": "người", "hai_AI": "hai AI", "AI": "hai AI", "opus": "Opus", "sonnet": "Sonnet"}
fails = []


def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        fails.append(msg)


def tn(a, b, c):
    return "T" if a in {"existing", "self"} and b in CORE_B and c in {"down", "unclear"} else "N"


def rows(name):
    return list(csv.DictReader(open(os.path.join(NOP, name), encoding="utf-8-sig")))


def ops(name):
    return {r["row_id"]: r for r in (json.loads(l) for l in open(os.path.join(NOP, name)) if l.strip())}


def to_op(r):
    fields = []
    for f in r["fields"]:
        if f["name"] == "(body)":
            continue
        fields.append({"loc": f["loc"], "name": f["name"], "key": "%s:%s" % (f["loc"], f["name"]),
                       "leaf": D.sim.leaf(f["name"]).lower(), "raw_leaf": D.sim.leaf(f["name"]), "type": f["type"],
                       "enum": [str(v) for v in f["enum"]], "kind": D.sim.gene_kind(f)})
    return {"row_id": r["row_id"], "method": r["method"], "path": r["path"], "fields": fields}


def m2_score():
    t = {}
    for r in csv.DictReader(open(M2)):
        if r["table"] == "op":
            t[r["feature"]] = float(r["weight"])
    return lambda op: t[D.PRIOR] + sum(t.get(f, 0.0) for f in D.op_feats(op))


def lay_theo(cuoi, seen, xem_lai):
    n = cuoi["nguon"]
    if n.endswith("_soat_lai"):
        return "soát lại sau khi chấm M2: chọn " + TEN[n[:-len("_soat_lai")]]
    if cuoi["row_id"] in xem_lai:
        return "xem lại: chọn " + TEN[xem_lai[cuoi["row_id"]]]
    if n == "nguoi" and seen:
        return "người"
    if n in {"AI_chua_xem", "hai_AI"} and not seen:
        return "hai AI (người chưa xem)"
    raise SystemExit("khong xep duoc " + cuoi["row_id"] + " " + n)


def build(phan, ai_file, cuoi_file, op_file, xem_lai_file):
    ai = {r["row_id"]: r for r in rows(ai_file)}
    cuoi = rows(cuoi_file)
    op = ops(op_file)
    nguoi = {r["row_id"]: r for r in rows("nhan-nguoi-gan.csv") if r["phan"] == phan}
    xem_lai = {r["row_id"]: r["chon"] for r in rows(xem_lai_file)}
    score = m2_score() if phan == "thi" else None
    out = []
    for c in cuoi:
        k = c["row_id"]
        a = ai[k]
        s = tn(a["sonnet_A"], a["sonnet_B"], a["sonnet_C"])
        o = tn(a["opus_A"], a["opus_B"], a["opus_C"])
        h = tn(nguoi[k]["A"], nguoi[k]["B"], nguoi[k]["C"]) if k in nguoi else ""
        f = "T" if c["T"] == "1" else "N"
        if f != tn(c["A"], c["B"], c["C"]):
            raise SystemExit("T khong khop A B C " + k)
        row = {"id": k, "api": c["spec_id"], "method": c["method"], "path": c["path"],
               "mo_ta": " ".join((op[k].get("summary") or "").split()),
               "AI_Sonnet": s, "AI_Opus": o, "nguoi_gan": h, "nhan_cuoi": f,
               "lay_theo": lay_theo(c, k in nguoi, xem_lai)}
        if phan == "thi":
            d = score(to_op(op[k]))
            row["diem_M2"] = "%.3f" % d
            row["M2_chon"] = "có" if d > 0 else "không"
            row["ghi_chu"] = "để riêng trước khi bốc mẫu" if c["nhom"] == "hai_AI_cung_N" and c["cho_boc"] == "0" else ""
        out.append(row)
    return out, nguoi


def write(name, data):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(data[0]))
        w.writeheader()
        w.writerows(data)


def main():
    if os.path.exists(OUT):
        sys.exit("output exists: " + OUT)
    hoc, ng_hoc = build("hoc", "nhan-ai-hoc.csv", "nhan-hoc-cuoi.csv", "op-hoc.jsonl", "review-66-lech.csv")
    thi, ng_thi = build("thi", "nhan-ai-thi.csv", "nhan-thi-cuoi.csv", "op-thi.jsonl", "review-thi-lech.csv")
    check(len(hoc) == 10381 and len(thi) == 8674, "10381 op hoc, 8674 op thi")
    check(sum(r["nhan_cuoi"] == "T" for r in hoc) == 209 and sum(r["nhan_cuoi"] == "T" for r in thi) == 153, "209 T hoc, 153 T thi")
    check(len(ng_hoc) + len(ng_thi) == 1146 and sum(r["nguoi_gan"] != "" for r in hoc + thi) == 1146, "1146 op nguoi xem")
    check(all(r["AI_Sonnet"] == r["AI_Opus"] == r["nhan_cuoi"] for r in hoc + thi if r["nguoi_gan"] == ""),
          "op nguoi chua xem: hai AI giong nhau va bang nhan cuoi")
    check(all(r["nguoi_gan"] == r["nhan_cuoi"] for r in hoc + thi if r["lay_theo"] in {"người", "xem lại: chọn người"}),
          "op lay theo nguoi: nhan cuoi bang nhan nguoi")
    check(sum(r["lay_theo"].startswith("xem lại") for r in hoc) == 66 and sum(r["lay_theo"].startswith("xem lại") for r in thi) == 53,
          "66 op hoc va 53 op thi xem lai")
    check(sum(r["lay_theo"].startswith("soát lại") for r in thi) == 4, "4 op thi doi o lan soat lai")
    check(sum(r["ghi_chu"] != "" for r in thi) == 116, "116 op thi de rieng")
    pos = [r for r in thi if r["M2_chon"] == "có"]
    check(len(pos) == 880 and sum(r["nhan_cuoi"] == "N" for r in pos) == 763
          and sum(r["nhan_cuoi"] == "T" for r in pos) == 117, "M2: 880 op chon, 763 N, 117 T (khop cham-thi)")
    check(hashlib.sha256(open(M2, "rb").read()).hexdigest().startswith("b2deef150bf8"), "M2 sha256 b2deef150bf8")
    if fails:
        sys.exit("%d FAIL, khong ghi" % len(fails))
    os.makedirs(os.path.join(OUT, "phieu"))
    os.makedirs(os.path.join(OUT, "goc"))
    write("nhan-hoc.csv", hoc)
    write("nhan-thi.csv", thi)
    shutil.copy(M2, os.path.join(OUT, "mo-hinh-M2.csv"))
    shutil.copy(os.path.join(NOP, "huong-dan", "phieu-cho-AI.md"), os.path.join(OUT, "phieu", "phieu-cho-AI.md"))
    shutil.copy(os.path.join(NOP, "huong-dan", "HUONG-DAN.html"), os.path.join(OUT, "phieu", "huong-dan-nguoi-gan.html"))
    for f in ("op-hoc.jsonl", "op-thi.jsonl", "nhan-ai-hoc.csv", "nhan-ai-thi.csv", "nhan-nguoi-gan.csv",
              "nhan-hoc-cuoi.csv", "nhan-thi-cuoi.csv",
              "review-66-lech.csv", "review-thi-lech.csv", "soat-lai-44-thi.csv", "SHA256SUMS.txt"):
        shutil.copy(os.path.join(NOP, f), os.path.join(OUT, "goc", f))
    print(OUT)


main()
