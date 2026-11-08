import csv, hashlib, io, os, shutil, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "ban-giao-gan-nhan-20261106"
SRC = os.path.join(HERE, "ban-giao")
OUT = os.path.join(HERE, "ban-giao-dot4")
KEEP_2 = {"T", "nhieu"}
KEEP_3 = {"cung_T", "lech"}
RES_2 = os.path.join(HERE, "tra-ve", "ket-qua-dot-2.csv")
RES_3 = os.path.join(HERE, "tra-ve", "ket-qua-dot-3-cuoi-cung.csv")
SHA_RES_2 = "318feeb24789dbae651311b9c2527449b54b6ea746f9bbada5b3233d650f9850"
SHA_RES_3 = "1b1c2f0cf1fd22d20227b9fc5f7b46066a960ad5c1174c993020b8203e7950d3"

GUIDE_EDITS = [
    ('<tr><td><code>du-lieu/dot-1-thu.csv</code></td><td>Đợt 1, 20 dòng làm thử</td></tr>\n'
     '<tr><td><code>du-lieu/dot-2.csv</code></td><td>Đợt 2, 323 dòng</td></tr>\n'
     '<tr><td><code>du-lieu/dot-3.csv</code></td><td>Đợt 3, 134 dòng</td></tr>\n'
     '<tr><td><code>thong-tin-nguoi-gan.txt</code></td><td>Bốn câu hỏi về kinh nghiệm của bạn, gửi kèm đợt 1</td></tr>\n',
     '<tr><td><code>du-lieu/dot-4.csv</code></td><td>Đợt 4, 823 dòng, phần cần gán</td></tr>\n'
     '<tr><td><code>da-gan/</code></td><td>Đợt 2 và đợt 3 đã gán xong, chỉ còn các dòng được dùng; không làm lại</td></tr>\n'
     '<tr><td><code>DANH-MUC.txt</code></td><td>Danh sách mọi file trong gói và số dòng</td></tr>\n'),
    ('<tr><td>1, làm thử</td><td>20</td><td>khoảng 30 phút</td><td>Gửi kết quả và <code>thong-tin-nguoi-gan.txt</code>, chờ phản hồi rồi mới làm đợt 2</td></tr>\n'
     '<tr><td>2</td><td>323</td><td>khoảng 7 giờ</td><td>Gửi kết quả</td></tr>\n'
     '<tr><td>3</td><td>134</td><td>khoảng 3 giờ</td><td>Gửi kết quả</td></tr>\n',
     '<tr><td>4</td><td>823</td><td>khoảng 18 giờ</td><td>Gửi kết quả</td></tr>\n'),
    ('<li>Đợt 1 dùng để tìm chỗ phiếu khó hiểu. Sau đợt 1, người giao việc có thể gửi bản hướng dẫn đã làm rõ; khi đó dùng bản mới cho đợt 2 và 3.</li>\n'
     '<li>Làm xong đợt 2 rồi mới mở đợt 3.</li>\n'
     '<li>Sau đợt 3 có thể có thêm một đợt khoảng 30 dòng.</li>\n',
     '<li>Đợt 2 và đợt 3 đã xong. Chỉ còn đợt 4.</li>\n'),
    ('<li>Không mở hay sửa file trong <code>du-lieu/</code> bằng Excel',
     '<li>Không mở hay sửa file trong <code>du-lieu/</code> và <code>da-gan/</code> bằng Excel'),
    ('chọn <code>du-lieu/dot-1-thu.csv</code>.</li>', 'chọn <code>du-lieu/dot-4.csv</code>.</li>'),
    ('<p>Các ví dụ dưới đây là operation thật, lấy từ các API không thuộc ba đợt của bạn. Mỗi ví dụ',
     '<p>Các ví dụ dưới đây là operation thật. Không ví dụ nào nằm trong các đợt của bạn. Mỗi ví dụ'),
    ('<li>Gửi file <code>ket-qua-dot-N.csv</code> cho người giao việc. Đợt 1 gửi kèm <code>thong-tin-nguoi-gan.txt</code> đã điền.</li>',
     '<li>Gửi file <code>ket-qua-dot-4.csv</code> cho người giao việc.</li>'),
    ('người giao việc trả lời sau đợt 1.</li>', 'người giao việc trả lời sau khi nhận kết quả.</li>'),
]
TOOL_EDITS = [
    ('Bắt đầu với <code>dot-1-thu.csv</code>.</p>', 'Chọn <code>dot-4.csv</code>.</p>'),
]

DOC_TRUOC = "\n".join([
    "GÓI GÁN NHÃN, ĐỢT 4",
    "",
    "1. Giải nén cả thư mục.",
    "2. Mở HUONG-DAN.html bằng trình duyệt (Chrome, Edge hoặc Firefox). Phiếu gán nhãn giữ nguyên như các đợt trước.",
    "3. Gán nhãn bằng CONG-CU-GAN-NHAN.html, mở du-lieu/dot-4.csv (823 dòng). Không mở file dữ liệu bằng Excel.",
    "4. Thư mục da-gan chứa đợt 2 và đợt 3 đã gán xong. Không làm lại.",
    "5. Xong thì gửi ket-qua-dot-4.csv.",
    "",
])


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def edit(text, edits, name):
    for old, new in edits:
        n = text.count(old)
        if n != 1:
            raise SystemExit("HONG: %s: doan can sua xuat hien %d lan: %s" % (name, n, old[:60]))
        text = text.replace(old, new)
    return text


def key_stt(name, keep):
    with open(os.path.join(HERE, "sealed", name), newline="") as fh:
        return [r["stt"] for r in csv.DictReader(fh) if r["tang"] in keep]


def filter_sheet(src, dst, stts):
    with open(src, newline="", encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        cols = rd.fieldnames
        rows = [r for r in rd if r["stt"] in stts]
    with open(dst, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, cols)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def filter_result(src, dst, stts):
    raw = open(src, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    rd = csv.reader(io.StringIO(text, newline=""))
    head = next(rd)
    i = head.index("stt")
    rows = [r for r in rd if r[i] in stts]
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(head)
    w.writerows(rows)
    with open(dst, "wb") as fh:
        fh.write((b"\xef\xbb\xbf" if bom else b"") + buf.getvalue().encode("utf-8"))
    return len(rows)


def count_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def main():
    checks = [("ket qua dot 2 trung ban tra ve", sha(RES_2) == SHA_RES_2),
              ("ket qua dot 3 trung ban tra ve", sha(RES_3) == SHA_RES_3)]
    if not all(ok for _, ok in checks):
        for n, ok in checks:
            print("%s  %s" % ("PASS" if ok else "FAIL", n))
        sys.exit(1)
    zpath = os.path.join(HERE, NAME + ".zip")
    if os.path.exists(zpath):
        raise SystemExit("HONG: %s da co, khong ghi de" % zpath)
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "du-lieu"))
    os.makedirs(os.path.join(OUT, "da-gan"))
    guide = edit(open(os.path.join(SRC, "HUONG-DAN.html"), encoding="utf-8").read(), GUIDE_EDITS, "HUONG-DAN")
    open(os.path.join(OUT, "HUONG-DAN.html"), "w", encoding="utf-8").write(guide)
    tool = edit(open(os.path.join(SRC, "CONG-CU-GAN-NHAN.html"), encoding="utf-8").read(), TOOL_EDITS, "CONG-CU")
    open(os.path.join(OUT, "CONG-CU-GAN-NHAN.html"), "w", encoding="utf-8").write(tool)
    open(os.path.join(OUT, "00-DOC-TRUOC.txt"), "w", encoding="utf-8").write(DOC_TRUOC)
    shutil.copyfile(os.path.join(HERE, "handover", "dot-4.csv"), os.path.join(OUT, "du-lieu", "dot-4.csv"))

    s2, s3 = set(key_stt("key-test-queue.csv", KEEP_2)), set(key_stt("key-train-queue.csv", KEEP_3))
    n2 = filter_sheet(os.path.join(SRC, "du-lieu", "dot-2.csv"), os.path.join(OUT, "da-gan", "dot-2.csv"), s2)
    n3 = filter_sheet(os.path.join(SRC, "du-lieu", "dot-3.csv"), os.path.join(OUT, "da-gan", "dot-3.csv"), s3)
    r2 = filter_result(RES_2, os.path.join(OUT, "da-gan", "ket-qua-dot-2.csv"), s2)
    r3 = filter_result(RES_3, os.path.join(OUT, "da-gan", "ket-qua-dot-3.csv"), s3)
    n4 = count_rows(os.path.join(OUT, "du-lieu", "dot-4.csv"))

    danh_muc = "\n".join([
        "DANH MỤC GÓI %s" % NAME, "",
        "File | Số dòng | Là gì",
        "00-DOC-TRUOC.txt | | Các bước làm",
        "HUONG-DAN.html | | Phiếu gán nhãn và cách dùng công cụ; phần phiếu giữ nguyên từ gói 2026-11-01",
        "CONG-CU-GAN-NHAN.html | | Công cụ gán nhãn chạy trong trình duyệt",
        "du-lieu/dot-4.csv | %d | Đợt 4, phần cần gán" % n4,
        "da-gan/dot-2.csv | %d | Đợt 2, các dòng còn dùng, giữ số thứ tự gốc" % n2,
        "da-gan/ket-qua-dot-2.csv | %d | Kết quả đợt 2 của các dòng đó" % r2,
        "da-gan/dot-3.csv | %d | Đợt 3, các dòng còn dùng, giữ số thứ tự gốc" % n3,
        "da-gan/ket-qua-dot-3.csv | %d | Kết quả đợt 3 của các dòng đó" % r3,
        "",
        "Đã bỏ khỏi gói so với gói 2026-11-01:",
        "- Đợt 1 làm thử, 20 dòng, và thong-tin-nguoi-gan.txt.",
        "- Đợt 2: %d dòng không còn dùng." % (323 - n2),
        "- Đợt 3: %d dòng không còn dùng." % (134 - n3),
        "",
    ])
    open(os.path.join(OUT, "DANH-MUC.txt"), "w", encoding="utf-8").write(danh_muc)

    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in sorted(os.walk(OUT)):
            for f in sorted(files):
                p = os.path.join(root, f)
                z.write(p, os.path.join(NAME, os.path.relpath(p, OUT)))

    with zipfile.ZipFile(zpath) as z:
        names = sorted(z.namelist())
        d4 = z.read(NAME + "/du-lieu/dot-4.csv")
    checks += [
        ("dot 4 trong zip trung handover/dot-4.csv", hashlib.sha256(d4).hexdigest() == sha(os.path.join(HERE, "handover", "dot-4.csv"))),
        ("dot 4 co 823 dong", n4 == 823),
        ("dot 2 con 227 dong (176 + 51), ket qua cung 227", n2 == 227 and r2 == 227),
        ("dot 3 con 96 dong (30 + 25 + 41), ket qua cung 96", n3 == 96 and r3 == 96),
        ("zip khong co dot-1-thu, thong-tin-nguoi-gan", not any("dot-1-thu" in n or "thong-tin" in n for n in names)),
        ("zip co 9 file", len(names) == 9),
    ]
    bad = 0
    for n, ok in checks:
        print("%s  %s" % ("PASS" if ok else "FAIL", n))
        bad += not ok
    for n in names:
        print("      %s" % n)
    print("sha256 %s  %s" % (sha(zpath), os.path.basename(zpath)))
    sys.exit(1 if bad else 0)


main()
