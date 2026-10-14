# P2e chạy tiếp từ các hàng P2d, 2026-10-13

Jar `EvoMaster/evomaster-P2e-6ae8277b.jar` = P2d + sửa C (`RestSecurityBuilder.kt:1265–1269`, giá trị nâng quyền
của trường enum chỉ gồm các giá trị mô hình chấm `high > low`). Self-test 7/7 (`p2e-selftest-20261013-134225/`).

Mục đích: một bộ 180 hàng đầy đủ arm và seed để so với AF2, chạy ~10h thay vì 20h. Bộ này trộn hai jar theo hàng,
không vào §4. Số §4 và cổng hồi quy lấy từ các lượt đầy đủ trên một jar sau này (user, 2026-10-13).

## Hàng P2d giữ lại

130 hàng P2d đã có (`p2d-night-20261012/remeasure/runs.csv` 114, `p2d-af2fired-probe-20261013/runs.csv` 16).
Phân loại theo các dòng `Privilege-restore … with role '<v>'` trong log từng hàng:

| Nhóm | Hàng | Xử lý |
|---|---|---|
| có lời gọi restore với giá trị enum mô hình chấm `high ≤ low` (`EVOMASTER`) | 10: vampi không reset, vuln và fixed, seeds 3 5 7 9 11 | chạy lại (bước 1) |
| không có lời gọi restore | 106 | giữ |
| restore chỉ với `ADMIN` | 11: reports không reset, vuln 4 8 9 10 16, fixed 4 8 9 10 16 20 | giữ, chạy lại để kiểm (bước 3) |
| pyLoad, trường `permission`, `role` kiểu integer (`openapi-merged.json`), không vào nhánh enum | 3 | giữ |

Lập luận giữ: `restoreValues` chỉ được gọi từ `restorePlans` (`:1286`). Danh sách enum của P2e là phần đầu danh
sách của P2d (lọc giữ thứ tự xếp hạng; giá trị `high > low` xếp trước). P2e chỉ đi khác P2d khi P2d gọi restore
với một giá trị nằm sau phần đầu đó; 120 hàng giữ lại không có lời gọi như thế.

## Hàng P2e (`continue.sh`)

| Bước | Hàng |
|---|---|
| 1 | vampi không reset seeds 3 5 7 9 11, vuln rồi fixed (10) |
| 2 | vampi fixed không reset 15–20; vampi vuln có reset 2 4 6 13 14 15 18; vampi fixed có reset 1–20 (33) |
| 3 | 11 hàng reports của nhóm `ADMIN`; so từng hàng với P2d trên det970, assembled, void, resets, restores_ok, restores_no, statuses |
| 4 | pyLoad vuln không reset 4–5; fixed không reset 1–5; vuln có reset 1–5; fixed có reset 1–5 (17) |
| 5 | hàng bước 3 lệch P2d: chạy lại một lần, vào `verify-rerun.csv` |

Hàm `t1`, `t2`, `t2b` trùng `af2_full_remeasure.sh`, chỉ thêm hậu tố `$SUF` vào tên thư mục và log của bước 5.

## Luật dừng (viết trước lượt chạy)

Kiểm sau mỗi hàng: hàng fixed có det970 = 1; 2 hàng liên tiếp det970 = ERR; có `Entering Sleep` mới trong
`pmset -g log`.

## Gộp

`merge.py`, chốt trước lượt chạy: mỗi (tier, arm, seed, reset) lấy hàng P2e nếu có, nếu không lấy hàng P2d; cột
`jar` ghi jar của hàng. Ra `merged.csv` và bảng so từng arm với AF2 (`merge.out`).

## Lệch luật đã khai

1. Chạy qua đêm không người trông (CLAUDE §6), theo yêu cầu user 2026-10-13.
2. Bộ gộp trộn hai jar theo hàng (CLAUDE §2 Đo đạc: một bảng không trộn jar); chỉ dùng để so với AF2, không trích vào
   §4.
