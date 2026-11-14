import csv, hashlib, math, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))


def doc(name):
    return list(csv.DictReader(open(os.path.join(HERE, name), encoding="utf-8-sig")))


def cdf(k, n, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))


def chia_doi(f):
    a, b = 0.0, 1.0
    for _ in range(100):
        m = (a + b) / 2
        a, b = (m, b) if f(m) else (a, m)
    return a


def cp(k, n):
    lo = 0.0 if k == 0 else chia_doi(lambda p: 1 - cdf(k - 1, n, p) < 0.025)
    hi = 1.0 if k == n else chia_doi(lambda p: cdf(k, n, p) > 0.025)
    return lo, hi


def ty_le(k, n):
    lo, hi = cp(k, n)
    return ("%d/%d = %.1f%% (khoảng tin cậy 95%%: %.1f–%.1f%%)" % (k, n, 100.0 * k / n, 100 * lo, 100 * hi)).replace(".", ",")


def hai_ai_N(r):
    return r["AI_Sonnet"] == "N" and r["AI_Opus"] == "N"


def mau_ngau_nhien(rows, chua_xem_rows):
    mau = [r for r in rows if r["nguoi_gan"] != "" and hai_ai_N(r)]
    k = sum(r["nhan_cuoi"] == "T" for r in mau)
    lo, hi = cp(k, len(mau))
    n = len(chua_xem_rows)
    return "%s; suy cho %d op chưa xem: sót %d–%d op T" % (ty_le(k, len(mau)), n, round(lo * n), round(hi * n))


hoc = doc("nhan-hoc.csv")
thi = doc("nhan-thi.csv")
out = []
say = out.append

say("1. Dữ liệu")
for ten, rows in (("Học", hoc), ("Thi", thi)):
    say("   %s: %d API, %d op ghi; người xem %d op; nhãn cuối T: %d op" % (
        ten, len({r["api"] for r in rows}), len(rows), sum(r["nguoi_gan"] != "" for r in rows),
        sum(r["nhan_cuoi"] == "T" for r in rows)))

say("")
say("2. Nhãn cuối lấy theo đâu (số op, trong đó T)")
for ten, rows in (("Học", hoc), ("Thi", thi)):
    say("   " + ten)
    c = Counter(r["lay_theo"] for r in rows)
    t = Counter(r["lay_theo"] for r in rows if r["nhan_cuoi"] == "T")
    for k in sorted(c, key=lambda x: -c[x]):
        say("     %-40s %5d   T %d" % (k, c[k], t[k]))

say("")
say("3. Nhãn AI đúng tới đâu (so với nhãn cuối)")
mot_ai_T = [r for r in thi if "T" in (r["AI_Sonnet"], r["AI_Opus"])]
say("   Thi, op ít nhất một AI gọi T (người xem hết): nhãn cuối T ở %d/%d op" % (
    sum(r["nhan_cuoi"] == "T" for r in mot_ai_T), len(mot_ai_T)))
for ten, f in (("hai AI cùng gọi T", lambda r: r["AI_Sonnet"] == r["AI_Opus"] == "T"),
               ("một AI gọi T, AI kia gọi N", lambda r: r["AI_Sonnet"] != r["AI_Opus"])):
    g = [r for r in mot_ai_T if f(r)]
    say("     %-28s %d/%d" % (ten, sum(r["nhan_cuoi"] == "T" for r in g), len(g)))
say("   Thi, op T ngoài nhóm trên: %d" % sum(r["nhan_cuoi"] == "T" for r in thi if r not in mot_ai_T))
say("   Thi, mẫu ngẫu nhiên op hai AI cùng N, người xem: " + mau_ngau_nhien(
    thi, [r for r in thi if r["nguoi_gan"] == "" and hai_ai_N(r) and r["ghi_chu"] == ""]))
say("   Học, mẫu ngẫu nhiên op hai AI cùng N, người xem: " + mau_ngau_nhien(
    hoc, [r for r in hoc if r["nguoi_gan"] == "" and hai_ai_N(r)]))

say("")
say("4. Mô hình M2 (học trên nhan-hoc.csv) chấm phần thi; M2 chọn op khi điểm > 0")
T = [r for r in thi if r["nhan_cuoi"] == "T"]
chon = [r for r in thi if r["M2_chon"] == "có"]
say("   mo-hinh-M2.csv sha256: " + hashlib.sha256(open(os.path.join(HERE, "mo-hinh-M2.csv"), "rb").read()).hexdigest()[:16])
say("   Bắt được: op T mà M2 chọn: " + ty_le(sum(r["M2_chon"] == "có" for r in T), len(T)))
say("   Báo nhầm: op M2 chọn mà nhãn cuối N: " + ty_le(sum(r["nhan_cuoi"] == "N" for r in chon), len(chon)))

print("\n".join(out))
with open(os.path.join(HERE, "ket-qua.txt"), "w") as fh:
    fh.write("\n".join(out) + "\n")
