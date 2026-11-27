# Bộ 100 lượt của khoá luận, jar TR2

Mọi số đo của khoá luận (Chương 5, tóm tắt, Chương 1 và 6) lấy từ thư mục này.

- Jar `EvoMaster/evomaster-TR2-3beccb00.jar`, sha256 `3beccb0086b6983a6676eaf8df5c2b09cf90fc6ab72d22da7115ca0a5b4edb9f`.
- Mọi lượt chạy với log debug của builder (`infra/em-config/logback-builder-debug.xml`).
- reports-api, vampi-seeded: 20 seed mỗi biến thể; pyLoad, artifact-keeper: 5 seed mỗi biến thể.

## File

| File | Nội dung | Chép từ (harness, cờ, luật dừng, dựng target) |
|---|---|---|
| `runs.csv`, `logs/t1-*`, `logs/t2-*`, `logs/t2b-*`, `logs/t1v.log` … `logs/t2bf.log`, `tests/t1-*`, `tests/t2-*`, `tests/t2b-*` | reports-api, vampi-seeded, pyLoad: 90 lượt | `../tr2dbg-wave1-20261126/` (`tr2dbg_wave1.sh`, `PROTOCOL.md`) |
| `runs-ak-vuln.csv`, `runs-ak-fixed.csv`, `logs/ak-*`, `tests/ak-*`, `traffic/` | artifact-keeper: 10 lượt | `../tr2-wave2-20261121/` (`ak_vuln.sh`, `ak_fixed.sh`, `PROTOCOL.md`) |

Chép bằng `cp -p`, so từng file với nguồn bằng `cmp`/`diff -r`: 0 khác. Harness không chép sang đây vì harness `rm -rf`
thư mục ghi của nó.

## Đếm

- `tr2_counts.py` → `tr2-counts.out`: Bảng 5.1 (lượt có bộ ba, lượt báo vi phạm, Clopper–Pearson), Bảng 5.2 (TP, FN,
  FP, TN), Fisher một phía, chuỗi mã trạng thái, tỷ lệ báo động giả trên lượt có bộ ba.
- `tr2_details.py` → `tr2-details.out`: bộ ba từng seed, VOID, UNCONFIRMED, lý do bước đăng nhập lại hủy bộ ba, khôi
  phục quyền; so ghép đôi det970 với jar LF và CS2 (McNemar).
- Bước đăng nhập lại (`chapter5.tex:81`, `chapter6.tex:15`): áp dụng cho mọi bộ ba có follow-up 2xx trên bản lỗi, tức 36 bộ ba giữ lại
  (`tr2-counts.out`: 14 + 7 + 5 + 10) cộng 24 bộ ba hủy (`tr2-details.out`, `total C4 INCONCLUSIVE`) = 60.
- `vampi-missed-void.out` (lệnh `awk`/`grep` trên `runs.csv` và `logs/t2-ours-vuln-*`, ghi trong lịch sử phiên): các
  lượt vampi-seeded bản lỗi bỏ sót, chia theo có hay không có lần thử, và mã của từng lần thử VOID (`chapter5.tex:127`,
  `:129`).
- `audit970.out` (`../audit970_seeded.py tests/*`): 31 PASS, 5 FAIL. 5 FAIL là 5 test pyLoad, xác thực bằng cookie
  nên checker không đọc được thông tin đăng nhập (`"cred": "None / op None"`).

Chạy lại: `cd infra/em-results/tr2-final-20261126 && python3 tr2_counts.py && python3 tr2_details.py`.
