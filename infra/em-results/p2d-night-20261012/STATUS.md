# Chuỗi đêm P2d — trạng thái

Cập nhật 2026-10-13 11:30. Remeasure dừng 11:27 sau 114 hàng, theo quyết định của user (`STOPPED.md`).
Phần còn lại thay bằng `p2d-af2fired-probe-20261013/`.

Jar P2d (`evomaster-P2d-2e0dbd4d.jar`) qua self-test, probe, FP và cổng hồi quy. Không trích số §4 từ
P2d.

| Bước | Kết quả | File |
|---|---|---|
| self-test | 6/6 PASS | `selftest/p2d-reduce-elevate-20261012.sh`, `em-results/p2d-selftest-20261012-223150/` |
| probe reports seeds 10/13/16 × 3 | 9/9 nổ (AF2 9/9, P2c 0/9) | `probe/runs.csv` |
| FP 6 hàng target đã vá | 6/6 det970 = 0; 4 hàng dựng được bộ ba, follow-up 403 | `fp/runs.csv` |
| cổng hồi quy | 21 MATCH, 0 MISMATCH | `gate/observed.csv` |
| remeasure 180 lượt | dừng sau 114 hàng | `remeasure/runs.csv`, `remeasure/progress.log` |

Probe, đường nổ theo log: seed 10 nâng alice rồi hạ superadmin (sửa A); seed 13 alice hạ thẳng
superadmin (sửa A); seed 16 nâng bob rồi hạ alice (sửa B). Cả 9 bộ ba 200/200/200.

FP trùng từng hàng với P2c (`fp-check-p2c-20261012/runs.csv`).

## Việc của anh

1. Diff 3 dòng `infra/evomaster-ext/wip/p2d-increment-over-p2c-20261012.diff`: user duyệt 2026-10-13 08:32,
   remeasure chạy tiếp. Lệch luật 2 trong `PROTOCOL.md` đã đóng.
2. Sau khi remeasure xong: replay các test 970, snapshot, cập nhật `docs/results.md`, CLAUDE §4/§5, `jars.md`.

## Remeasure

So từng arm với AF2 (`af2-full-remeasure-20261003/runs.csv`). Dòng điền khi arm xong.

| Arm | AF2 | P2d |
|---|---|---|
| reports vuln không reset | 19/20 | 19/20, cùng trượt seed 17 (P2c 16/20) |
| reports fixed không reset | 0/20 | 0/20; 19 lượt dựng được bộ ba, 6 lượt qua restore |
| reports vuln có reset | 20/20 | 20/20 |
| reports fixed có reset | 0/20 | 0/20; 20 lượt dựng được bộ ba |

Reports xong 08:14: 80/80 hàng det970 trùng AF2 từng seed.
| vampi vuln không reset | 7/20 | 6/20; mất seed 11: restore tiêu 1 trong 3 lượt vào `EVOMASTER` (400), không tới operator name2 mà AF2 nâng thành công (`remeasure/logs/t2-ours-vuln-seed11-r0.log`) |
| vampi fixed không reset | 0/20 | 0/14 (seeds 1–14); seed 11 mất một bộ ba 200/200/403 do cùng lỗi restore |
| vampi vuln có reset | 13/20 | |
| vampi fixed có reset | 0/20 | |
| pyLoad vuln không reset | 5/5 | |
| pyLoad vuln có reset | 5/5 | |
| pyLoad fixed không reset | 0/5 | |
| pyLoad fixed có reset | 0/5 | |
